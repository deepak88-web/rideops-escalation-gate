"""
Models Package Root
"""

from src.models.leakage_guard import (
    CAT_FEATURES,
    NUM_FEATURES,
    TEXT_FEATURE,
    check_leakage,
    prepare_model_dataset,
)

from src.models.baseline import CategoryRateBaselineClassifier

from src.models.text_nlp import (
    build_tabular_preprocessor,
    build_tfidf_preprocessor,
    build_hybrid_preprocessor,
)

from src.models.evaluate import (
    evaluate_probabilities,
    compute_calibration_curve_points,
    extract_hybrid_coefficients,
    extract_tree_importances,
)

from src.models.train import (
    get_model_pipelines,
    run_cross_validation,
    run_temporal_validation,
    train_and_save_champion,
)

from src.models.live_gate import (
    build_live_triage_labels,
    prepare_live_model_dataset,
    get_live_model_pipelines,
    train_and_validate_live_gate,
)

__all__ = [
    "CAT_FEATURES",
    "NUM_FEATURES",
    "TEXT_FEATURE",
    "check_leakage",
    "prepare_model_dataset",
    "CategoryRateBaselineClassifier",
    "build_tabular_preprocessor",
    "build_tfidf_preprocessor",
    "build_hybrid_preprocessor",
    "evaluate_probabilities",
    "compute_calibration_curve_points",
    "extract_hybrid_coefficients",
    "extract_tree_importances",
    "get_model_pipelines",
    "run_cross_validation",
    "run_temporal_validation",
    "train_and_save_champion",
    "build_live_triage_labels",
    "prepare_live_model_dataset",
    "get_live_model_pipelines",
    "train_and_validate_live_gate",
]
