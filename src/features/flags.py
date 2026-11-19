"""
Operational and Escalation Flags Calculation Module
"""

import pandas as pd
from src.config import REAL_FIX_OUTCOME, RETURNED_TO_L1_OUTCOMES


def compute_operational_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute binary operational flags:
    - is_escalated: 1 if escalated_to_eng == 'Yes' else 0
    - is_avoidable_esc: 1 if escalated AND eng_outcome != 'Fixed' else 0
    - is_returned_to_l1: 1 if escalated AND outcome is Config or Insufficient info else 0
    - is_reopened: 1 if reopen_count >= 1 else 0
    """
    df_out = df.copy()

    df_out["is_escalated"] = (df_out["escalated_to_eng"].astype(str).str.strip().str.lower() == "yes").astype(int)

    df_out["is_avoidable_esc"] = (
        (df_out["is_escalated"] == 1) &
        (df_out["eng_outcome"] != REAL_FIX_OUTCOME)
    ).astype(int)

    df_out["is_returned_to_l1"] = (
        (df_out["is_escalated"] == 1) &
        (df_out["eng_outcome"].isin(RETURNED_TO_L1_OUTCOMES))
    ).astype(int)

    if "reopen_count" in df_out.columns:
        df_out["is_reopened"] = (df_out["reopen_count"] >= 1).astype(int)
    else:
        df_out["is_reopened"] = 0

    # First-Contact Resolution (FCR): closed by L1 with no escalation and no reopen
    if "final_closed_at" in df_out.columns:
        df_out["is_fcr"] = (
            (df_out["is_escalated"] == 0) &
            (df_out["is_reopened"] == 0) &
            (df_out["final_closed_at"].notna())
        ).astype(int)
    else:
        df_out["is_fcr"] = 0

    return df_out
