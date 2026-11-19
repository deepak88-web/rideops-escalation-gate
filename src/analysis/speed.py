"""
Speed and SLA Metrics Analysis Module (Section D)
"""

from typing import Dict, Optional
import numpy as np
import pandas as pd
from src.config import SLA_TARGETS_HOURS


def compute_p50_p90_summary(group: pd.DataFrame, col: str) -> pd.Series:
    """Compute count (n), median (p50), and 90th percentile (p90) for a numeric column."""
    s = group[col].dropna()
    return pd.Series({
        "n": int(len(s)),
        "median_hrs": s.median() if len(s) > 0 else np.nan,
        "p90_hrs": np.percentile(s, 90) if len(s) > 0 else np.nan
    })


def compute_first_response_speed(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute median and 90th percentile first response speed overall and by priority (D1).
    """
    d1_overall = compute_p50_p90_summary(df, "hrs_to_first_response").to_frame("Overall").T
    d1_prio = df.groupby("priority", observed=False).apply(
        compute_p50_p90_summary, col="hrs_to_first_response"
    ).sort_index()
    d1_table = pd.concat([d1_overall, d1_prio])
    return d1_table


def compute_resolution_speed_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute median and 90th percentile resolution speed by category (D2b).
    """
    return (
        df.groupby("category", observed=False)
        .apply(compute_p50_p90_summary, col="resolution_hrs")
        .sort_values("median_hrs", ascending=False)
    )


def compute_resolution_speed_by_handoffs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute median and 90th percentile resolution speed by engineering handoffs (D2c).
    """
    return (
        df.groupby("eng_handoffs", observed=False)
        .apply(compute_p50_p90_summary, col="resolution_hrs")
        .sort_index()
    )


def compute_resolution_speed_by_escalation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute median and 90th percentile resolution speed overall and escalated vs not (D2a).
    """
    d2_overall = compute_p50_p90_summary(df, "resolution_hrs").to_frame("Overall").T
    d2_esc = df.groupby("is_escalated", observed=False).apply(
        compute_p50_p90_summary, col="resolution_hrs"
    )
    d2_esc.index = ["Non-Escalated (L1 Only)", "Escalated to Eng"]
    return pd.concat([d2_overall, d2_esc])


def compute_first_response_sla(
    df: pd.DataFrame,
    sla_targets: Optional[Dict[str, float]] = None
) -> pd.DataFrame:
    """
    Compute share of tickets with first response within priority target (D3).
    """
    if sla_targets is None:
        sla_targets = SLA_TARGETS_HOURS

    df_sla = df.copy()
    df_sla["frt_sla_target_hrs"] = df_sla["priority"].map(sla_targets)
    df_sla["met_frt_sla"] = np.where(
        df_sla["hrs_to_first_response"].notna(),
        (df_sla["hrs_to_first_response"] <= df_sla["frt_sla_target_hrs"]).astype(int),
        np.nan
    )

    d3_sla = df_sla.groupby("priority", observed=False).agg(
        sla_target_hrs=("frt_sla_target_hrs", "first"),
        responded_tickets=("met_frt_sla", "count"),
        within_sla_count=("met_frt_sla", "sum"),
        sla_attainment_pct=("met_frt_sla", lambda s: s.mean() * 100)
    ).sort_index()

    return d3_sla


def compute_open_backlog_age_bands(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute open backlog age bands (>24h, >48h, >7d) as of snapshot date (D4).
    """
    open_df = df[df["is_open"] == 1].copy()
    total_open = len(open_df)

    d4_age = pd.DataFrame({
        "age_band": ["Open > 24 hours", "Open > 48 hours", "Open > 7 days (168h)"],
        "open_tickets": [
            (open_df["open_age_hrs"] > 24).sum(),
            (open_df["open_age_hrs"] > 48).sum(),
            (open_df["open_age_hrs"] > 168).sum()
        ]
    })
    d4_age["pct_of_open"] = d4_age["open_tickets"] / max(total_open, 1) * 100
    return d4_age
