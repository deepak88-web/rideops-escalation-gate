"""
Model Evaluation and Diagnostic Metrics Module (Section J)
"""

from typing import Dict, Tuple, List
import numpy as np
import pandas as pd
from sklearn.metrics import (
    roc_auc_score, average_precision_score,
    precision_score, recall_score, f1_score
)
from sklearn.calibration import calibration_curve


def evaluate_probabilities(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.55
) -> Dict[str, float]:
    """
    Compute key binary classification performance metrics:
    - ROC-AUC
    - PR-AUC (Average Precision)
    - Precision at threshold
    - Recall at threshold
    - F1 at threshold
    """
    y_true_arr = np.asarray(y_true)
    y_prob_arr = np.asarray(y_prob)
    y_pred = (y_prob_arr >= threshold).astype(int)

    return {
        "ROC_AUC": float(roc_auc_score(y_true_arr, y_prob_arr)),
        "PR_AUC": float(average_precision_score(y_true_arr, y_prob_arr)),
        "Precision": float(precision_score(y_true_arr, y_pred, zero_division=0)),
        "Recall": float(recall_score(y_true_arr, y_pred, zero_division=0)),
        "F1": float(f1_score(y_true_arr, y_pred, zero_division=0))
    }


def compute_calibration_curve_points(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 5
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute calibration curve points (fraction of positives, mean predicted probability).
    """
    return calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="quantile")


def extract_hybrid_coefficients(
    pipeline,
    cat_features: List[str],
    num_features: List[str]
) -> pd.DataFrame:
    """
    Extract logistic regression log-odds coefficients from a fitted hybrid pipeline.
    """
    prep = pipeline.named_steps["prep"]
    cat_names = prep.named_transformers_["cat"].get_feature_names_out(cat_features)
    tfidf_names = [f"text: {w}" for w in prep.named_transformers_["tfidf"].get_feature_names_out()]
    all_feature_names = np.concatenate([num_features, cat_names, tfidf_names])

    coefs = pipeline.named_steps["clf"].coef_[0]
    return pd.DataFrame({"feature": all_feature_names, "coef": coefs})


def extract_tree_importances(
    pipeline,
    cat_features: List[str],
    num_features: List[str]
) -> pd.DataFrame:
    """
    Extract feature importances from a tree-based pipeline (Random Forest / Gradient Boosting).
    """
    prep = pipeline.named_steps["prep"]
    cat_names = prep.named_transformers_["cat"].get_feature_names_out(cat_features)
    all_feature_names = np.concatenate([num_features, cat_names])

    importances = pipeline.named_steps["clf"].feature_importances_
    return pd.DataFrame({
        "feature": all_feature_names,
        "importance": importances
    }).sort_values("importance", ascending=False)
