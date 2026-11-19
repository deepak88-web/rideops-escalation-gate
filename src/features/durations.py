"""
Duration Metrics Calculation Module
"""

import pandas as pd


def compute_durations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute operational durations in hours:
    - hrs_to_first_response: first reply time from creation
    - hrs_to_first_close: first closure time from creation
    - hrs_to_final_close: final closure time from creation
    - resolution_hrs: alias for hrs_to_final_close (NaN if ticket is still open)
    """
    df_out = df.copy()
    created = pd.to_datetime(df_out["created_at"], errors="coerce")
    first_resp = pd.to_datetime(df_out["first_response_at"], errors="coerce")
    first_closed = pd.to_datetime(df_out["first_closed_at"], errors="coerce")
    final_closed = pd.to_datetime(df_out["final_closed_at"], errors="coerce")

    df_out["hrs_to_first_response"] = (first_resp - created).dt.total_seconds() / 3600.0
    df_out["hrs_to_first_close"] = (first_closed - created).dt.total_seconds() / 3600.0
    df_out["hrs_to_final_close"] = (final_closed - created).dt.total_seconds() / 3600.0
    df_out["resolution_hrs"] = df_out["hrs_to_final_close"]

    return df_out


# Functional alias for pipeline compatibility
compute_duration_metrics = compute_durations
