"""
Feature Engineering Master Pipeline Module
"""

import pandas as pd
from .durations import compute_durations
from .flags import compute_operational_flags
from .calendar import compute_calendar_and_age_features
from .repeat_contacts import compute_repeat_contacts


def build_feature_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Executes the end-to-end feature engineering pipeline:
    1. Duration calculations (first response, first close, final close)
    2. Operational and escalation flags
    3. Calendar and open backlog age features
    4. Repeat-contact 14-day detection
    """
    return (
        df.pipe(compute_durations)
          .pipe(compute_operational_flags)
          .pipe(compute_calendar_and_age_features)
          .pipe(compute_repeat_contacts)
    )
