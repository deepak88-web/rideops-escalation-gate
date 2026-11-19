"""
Model 2: Live Triage Escalation Gate Pipeline (Phases 4 & 5)
Predicts whether a newly received incoming ticket is avoidable / L1-resolvable
vs. a legitimate engineering defect requiring code intervention.
Trained on all closed tickets (N=1,304 clean ground truth) using pre-escalation features only.
"""

from pathlib import Path
from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd
import joblib

from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, precision_score, recall_score, f1_score

from src.config import (
    LIVE_MODEL_PATH,
    LIVE_OPERATING_THRESHOLD,
    TABLES_DIR,
    CAT_FEATURES,
    NUM_FEATURES,
    TEXT_FEATURE
)
from src.models.leakage_guard import check_leakage
from src.models.text_nlp import (
    build_tabular_preprocessor,
    build_hybrid_preprocessor
)
from src.models.evaluate import evaluate_probabilities


def build_live_triage_labels(
    df: pd.DataFrame,
    regime: str = "strict"
) -> pd.DataFrame:
    """
    Construct rigorously validated labels for pre-escalation triage across the ticket population.
    - Excludes currently open tickets (outcomes are censored / pending).
    - Under 'strict' regime:
        * Escalated + Fixed -> target_avoidable = 0 (Confirmed defect requiring Tier 3 fix)
        * Escalated + Non-Fixed -> target_avoidable = 1 (Avoidable escalation returned to L1 / duplicate)
        * Non-escalated + 0 reopens -> target_avoidable = 1 (Clean FCR resolution by L1)
        * Non-escalated + Reopened -> Excluded from ground truth due to resolution ambiguity.
    """
    df_clean = df[df["is_open"] == 0].copy()

    if regime == "strict":
        # Drop ambiguous non-escalated tickets that were reopened without engineering log
        ambiguous_mask = (df_clean["is_escalated"] == 0) & (df_clean["reopen_count"] > 0)
        labeled = df_clean[~ambiguous_mask].copy()
    elif regime == "audit_adjusted":
        labeled = df_clean.copy()
    else:
        raise ValueError(f"Unknown labeling regime: {regime}")

    # Default to 1 (Avoidable / L1-resolvable)
    labeled["target_avoidable"] = 1

    # Escalated tickets with confirmed code/schema fix required Tier 3
    fixed_mask = (labeled["is_escalated"] == 1) & (labeled["eng_outcome"] == "Fixed")
    labeled.loc[fixed_mask, "target_avoidable"] = 0

    if regime == "audit_adjusted":
        # Reopened multiple times in core software categories flagged as potential latent defect
        software_cats = ["Report export failing", "Roster / booking not syncing", "Live tracking / GPS incorrect"]
        latent_bug = (
            (labeled["is_escalated"] == 0) &
            (labeled["reopen_count"] >= 2) &
            (labeled["category"].isin(software_cats))
        )
        labeled.loc[latent_bug, "target_avoidable"] = 0

    return labeled


def prepare_live_model_dataset(
    df: pd.DataFrame,
    regime: str = "strict"
) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Sort chronologically, compute pre-escalation feature history,
    verify leakage guard, and generate temporal split mask.
    """
    df_chrono = df.sort_values(["created_at", "ticket_id"]).reset_index(drop=True).copy()
    df_chrono["client_prior_tickets"] = df_chrono.groupby("client_id").cumcount()

    labeled = build_live_triage_labels(df_chrono, regime=regime)

    selected_features = CAT_FEATURES + NUM_FEATURES + [TEXT_FEATURE]
    check_leakage(selected_features)

    X = labeled[selected_features].copy()
    y = labeled["target_avoidable"].copy()
    is_sep = labeled["created_at"].dt.month == 9

    return X, y, is_sep


def get_live_model_pipelines() -> Dict[str, Pipeline]:
    """Candidate architectures for Live Triage Gate."""
    tabular_prep = build_tabular_preprocessor(CAT_FEATURES, NUM_FEATURES)
    hybrid_prep = build_hybrid_preprocessor(CAT_FEATURES, NUM_FEATURES, TEXT_FEATURE, max_features=300)

    return {
        "Logistic Regression": Pipeline([
            ("prep", tabular_prep),
            ("clf", LogisticRegression(max_iter=1000, C=0.5, random_state=42))
        ]),
        "Random Forest": Pipeline([
            ("prep", tabular_prep),
            ("clf", RandomForestClassifier(n_estimators=300, max_depth=6, min_samples_leaf=5, random_state=42))
        ]),
        "Gradient Boosting": Pipeline([
            ("prep", tabular_prep),
            ("clf", GradientBoostingClassifier(n_estimators=150, learning_rate=0.05, max_depth=3, random_state=42))
        ]),
        "Hybrid (Tabular + TF-IDF)": Pipeline([
            ("prep", hybrid_prep),
            ("clf", LogisticRegression(max_iter=1000, C=0.5, random_state=42))
        ])
    }


def train_and_validate_live_gate(
    df: pd.DataFrame,
    threshold: float = LIVE_OPERATING_THRESHOLD,
    save_model: bool = True
) -> Tuple[pd.DataFrame, Pipeline]:
    """
    Train and temporally validate Model 2 on chronological split (Jul-Aug Train vs Sep Test).
    Saves champion pipeline and returns comparison table.
    """
    X, y, is_sep = prepare_live_model_dataset(df, regime="strict")

    X_train, y_train = X[~is_sep], y[~is_sep]
    X_test, y_test = X[is_sep], y[is_sep]
    y_test_arr = y_test.values

    rows = []

    # 1. Baseline: Historical Category Avoidable Rate
    cat_rates = pd.Series(y_train.values, index=X_train["category"]).groupby(level=0).mean()
    base_probs = X_test["category"].map(cat_rates).fillna(y_train.mean()).values
    rows.append({
        "Model": "Baseline (Category Rate)",
        **evaluate_probabilities(y_test_arr, base_probs, threshold=threshold)
    })

    # 2. Pipeline models
    pipelines = get_live_model_pipelines()
    champion_pipe = None
    champion_roc = -1.0

    for name, pipe in pipelines.items():
        pipe.fit(X_train, y_train)
        probs = pipe.predict_proba(X_test)[:, 1]
        metrics = evaluate_probabilities(y_test_arr, probs, threshold=threshold)
        rows.append({"Model": name, **metrics})

        if metrics["ROC_AUC"] > champion_roc:
            champion_roc = metrics["ROC_AUC"]
            champion_pipe = pipe

    results_df = pd.DataFrame(rows).set_index("Model")

    # Save metrics table
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    table_path = TABLES_DIR / "j3_live_triage_model_comparison.csv"
    results_df.to_csv(table_path)

    # Save champion model artifact
    if save_model and champion_pipe is not None:
        LIVE_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(champion_pipe, LIVE_MODEL_PATH)

    return results_df, champion_pipe
