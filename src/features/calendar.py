"""
Temporal, Calendar, and Snapshot Backlog Age Features
"""

from typing import Optional
import pandas as pd
import numpy as np
from src.config import SNAPSHOT_AS_OF_DATE, PARTIAL_WEEKS


def compute_calendar_and_age_features(
    df: pd.DataFrame,
    as_of_date: Optional[pd.Timestamp] = None
) -> pd.DataFrame:
    """
    Compute calendar features and ticket age for open tickets as of a reference snapshot date:
    - week_start: starting date of the ticket's week
    - month: YYYY-MM period string
    - hour_of_day: 0-23
    - weekday: Monday - Sunday
    - is_partial_week: 1 if week is partial (start or end of quarter)
    - is_open: 1 if final_closed_at is null
    - open_age_hrs: hours ticket was open up to snapshot date
    """
    df_out = df.copy()
    created = pd.to_datetime(df_out["created_at"], errors="coerce")
    final_closed = pd.to_datetime(df_out["final_closed_at"], errors="coerce")
    ref_date = as_of_date or SNAPSHOT_AS_OF_DATE

    df_out["week_start"] = created.dt.to_period("W-SUN").apply(lambda r: r.start_time)
    df_out["month"] = created.dt.to_period("M").astype(str)
    df_out["hour_of_day"] = created.dt.hour
    df_out["weekday"] = created.dt.day_name()
    df_out["is_partial_week"] = df_out["week_start"].isin(PARTIAL_WEEKS).astype(int)

    df_out["is_open"] = final_closed.isna().astype(int)
    df_out["open_age_hrs"] = np.where(
        df_out["is_open"] == 1,
        (ref_date - created).dt.total_seconds() / 3600.0,
        np.nan
    )

    return df_out


# Functional alias for pipeline compatibility
compute_calendar_features = compute_calendar_and_age_features
