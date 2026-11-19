"""
Repeat-Contact Detection Module (Section B & H)
Identifies recurring support tickets from the same client and category within a 14-day window.
"""

from typing import Optional
import pandas as pd
from src.config import REPEAT_CONTACT_MAX_DAYS_EXCLUSIVE


def compute_repeat_contacts(
    df: pd.DataFrame,
    max_days: Optional[float] = None
) -> pd.DataFrame:
    """
    Compute repeat-contact flag:
    1 if the same client_id raised an earlier ticket in the exact same category
    within the past 14 days (inclusive of same-day hours, i.e. < 15.0 days).
    """
    df_out = df.copy()
    threshold = max_days if max_days is not None else REPEAT_CONTACT_MAX_DAYS_EXCLUSIVE

    # Sort strictly chronologically by client, category, and creation time
    df_out = df_out.sort_values(["client_id", "category", "created_at", "ticket_id"]).reset_index(drop=True)

    # Shift to find prior ticket timestamp for the same client and category
    df_out["prev_same_cat_created_at"] = df_out.groupby(["client_id", "category"])["created_at"].shift(1)
    df_out["days_since_prev_same_cat"] = (df_out["created_at"] - df_out["prev_same_cat_created_at"]).dt.total_seconds() / 86400.0

    df_out["is_repeat_contact"] = (
        (df_out["days_since_prev_same_cat"].notna()) &
        (df_out["days_since_prev_same_cat"] < threshold)
    ).astype(int)

    # Restore chronological order
    df_out = df_out.sort_values(["created_at", "ticket_id"]).reset_index(drop=True)
    return df_out
