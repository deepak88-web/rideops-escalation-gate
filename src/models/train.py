"""
Model Training, Cross-Validation, and Temporal Evaluation Pipeline (Section J)
"""

from pathlib import Path
from typing import Dict, Tuple, Any
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

from src.config import DEFAULT_MODEL_THRESHOLD, MODEL_PATH
from src.models.leakage_guard import (
    CAT_FEATURES, NUM_FEATURES, TEXT_FEATURE, prepare_model_dataset
)
from src.models.text_nlp import (
    build_tabular_preprocessor,
    build_tfidf_preprocessor,
    build_hybrid_preprocessor
)
from src.models.baseline import CategoryRateBaselineClassifier
from src.models.evaluate import evaluate_probabilities


def get_model_pipelines(
    cat_features=CAT_FEATURES,
    num_features=NUM_FEATURES,
    text_feature=TEXT_FEATURE
) -> Dict[str, Pipeline]:
    """
    Construct model pipelines for all benchmark architectures.
    """
    tabular_prep = build_tabular_preprocessor(cat_features, num_features)
    tfidf_prep = build_tfidf_preprocessor(text_feature=text_feature, max_features=300)
    hybrid_prep = build_hybrid_preprocessor(cat_features, num_features, text_feature=text_feature, max_features=300)

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
        "TF-IDF Text Model": Pipeline([
            ("prep", tfidf_prep),
            ("clf", LogisticRegression(max_iter=1000, C=1.0, random_state=42))
        ]),
        "Hybrid (Tabular + TF-IDF)": Pipeline([
            ("prep", hybrid_prep),
            ("clf", LogisticRegression(max_iter=1000, C=0.5, random_state=42))
        ])
    }


def run_cross_validation(
    X: pd.DataFrame,
    y: pd.Series,
    threshold: float = DEFAULT_MODEL_THRESHOLD,
    n_splits: int = 5
) -> pd.DataFrame:
    """
    Execute 5-fold stratified cross-validation for baseline and all models (J1).
    """
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    y_arr = y.values
    cv_rows = []

    # 1. Baseline out-of-fold predictions (category historical rate)
    oof_base = np.zeros(len(X))
    for tr_idx, va_idx in cv.split(X, y_arr):
        cat_rates = pd.Series(y_arr[tr_idx], index=X.iloc[tr_idx]["category"]).groupby(level=0).mean()
        oof_base[va_idx] = X.iloc[va_idx]["category"].map(cat_rates).fillna(y_arr[tr_idx].mean())

    cv_rows.append({"Model": "Baseline (Category Rate)", **evaluate_probabilities(y_arr, oof_base, threshold)})

    # 2. Pipeline models
    models = get_model_pipelines()
    for name, pipe in models.items():
        oof_probs = cross_val_predict(pipe, X, y_arr, cv=cv, method="predict_proba")[:, 1]
        cv_rows.append({"Model": name, **evaluate_probabilities(y_arr, oof_probs, threshold)})

    return pd.DataFrame(cv_rows).set_index("Model")


def run_temporal_validation(
    X: pd.DataFrame,
    y: pd.Series,
    is_sep: pd.Series,
    threshold: float = DEFAULT_MODEL_THRESHOLD
) -> Tuple[pd.DataFrame, Dict[str, Any], pd.DataFrame, np.ndarray, pd.DataFrame, np.ndarray]:
    """
    Execute temporal validation: Train on July-August, evaluate on September holdout (J2).
    Returns (time_results_df, fitted_models, X_train, y_train, X_test, y_test).
    """
    y_arr = y.values
    X_train = X[~is_sep].reset_index(drop=True)
    y_train = y_arr[~is_sep]
    X_test = X[is_sep].reset_index(drop=True)
    y_test = y_arr[is_sep]

    # Baseline evaluation
    cat_train_rates = pd.Series(y_train, index=X_train["category"]).groupby(level=0).mean()
    base_test_probs = X_test["category"].map(cat_train_rates).fillna(y_train.mean()).values

    time_rows = [{"Model": "Baseline (Category Rate)", **evaluate_probabilities(y_test, base_test_probs, threshold)}]
    fitted_models = {}

    models = get_model_pipelines()
    for name, pipe in models.items():
        pipe.fit(X_train, y_train)
        fitted_models[name] = pipe
        test_probs = pipe.predict_proba(X_test)[:, 1]
        time_rows.append({"Model": name, **evaluate_probabilities(y_test, test_probs, threshold)})

    time_results_df = pd.DataFrame(time_rows).set_index("Model")
    return time_results_df, fitted_models, X_train, y_train, X_test, y_test


def train_and_save_champion(
    fitted_models: Dict[str, Any],
    time_results_df: pd.DataFrame,
    save_path: Path = MODEL_PATH
) -> str:
    """
    Save the top-performing temporal validation model to the models directory.
    """
    save_path.parent.mkdir(parents=True, exist_ok=True)
    best_model_name = time_results_df["ROC_AUC"].idxmax()
    best_model = fitted_models[best_model_name]
    joblib.dump(best_model, save_path)
    return best_model_name
