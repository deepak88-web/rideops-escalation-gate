"""
Leakage Guard and Model Feature Preparation Module (Section J)
Ensures only features available at the exact moment of escalation are used in modeling.
"""

from typing import Tuple, List
import pandas as pd
from src.config import FORBIDDEN_LEAKAGE_COLUMNS


CAT_FEATURES = ["category", "priority", "channel", "client_tier", "assigned_agent", "weekday"]
NUM_FEATURES = ["hrs_to_first_response", "hour_of_day", "is_repeat_contact", "client_prior_tickets"]
TEXT_FEATURE = "description"


def check_leakage(features: List[str]) -> None:
    """
    Asserts that no post-escalation outcome or leakage columns exist in the feature set.
    """
    inter = set(features).intersection(FORBIDDEN_LEAKAGE_COLUMNS)
    if inter:
        raise ValueError(f"LEAKAGE DETECTED! Forbidden features in matrix: {inter}")


def prepare_model_dataset(
    df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Prepare leakage-free feature matrix X, target y, and temporal train/test mask.
    - Sorts chronologically
    - Computes leakage-free historical prior ticket count per client
    - Filters to escalated tickets only
    - Verifies leakage guard
    Returns (X, y, is_sep_mask).
    """
    df_chrono = df.sort_values(["created_at", "ticket_id"]).reset_index(drop=True).copy()
    df_chrono["client_prior_tickets"] = df_chrono.groupby("client_id").cumcount()

    # Filter to escalated tickets only (n = 486)
    model_df = df_chrono[df_chrono["is_escalated"] == 1].reset_index(drop=True).copy()

    selected_features = CAT_FEATURES + NUM_FEATURES + [TEXT_FEATURE]
    check_leakage(selected_features)

    X = model_df[selected_features].copy()
    y = model_df["is_avoidable_esc"].copy()
    is_sep = model_df["created_at"].dt.month == 9

    return X, y, is_sep
