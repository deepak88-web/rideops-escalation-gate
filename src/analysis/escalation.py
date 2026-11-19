"""
Escalation Quality and Handoff Metrics Analysis Module (Section E)
"""

from typing import Dict, Any, Tuple
import pandas as pd


def compute_escalation_by_month(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute escalation rate and avoidable rate by month.
    """
    return df.groupby("month", observed=False).agg(
        tickets=("ticket_id", "count"),
        escalated=("is_escalated", "sum"),
        esc_rate_pct=("is_escalated", lambda s: s.mean() * 100),
        avoidable_esc=("is_avoidable_esc", "sum"),
        avoidable_rate_of_esc_pct=(
            "is_avoidable_esc",
            lambda s: s.sum() / max(df.loc[s.index, "is_escalated"].sum(), 1) * 100
        )
    ).reset_index()


def compute_escalation_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute escalation rate and avoidable escalation rate by category (E1).
    """
    return df.groupby("category", observed=False).agg(
        tickets=("ticket_id", "count"),
        escalated=("is_escalated", "sum"),
        esc_rate_pct=("is_escalated", lambda s: s.mean() * 100),
        avoidable_esc=("is_avoidable_esc", "sum"),
        avoidable_rate_pct=(
            "is_avoidable_esc",
            lambda s: s.sum() / max(df.loc[s.index, "is_escalated"].sum(), 1) * 100
        )
    ).sort_values("esc_rate_pct", ascending=False)


def compute_escalation_by_agent_raw(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute raw escalation rate and avoidable rate by assigned agent.
    """
    return df.groupby("assigned_agent", observed=False).agg(
        tickets=("ticket_id", "count"),
        escalated=("is_escalated", "sum"),
        esc_rate_pct=("is_escalated", lambda s: s.mean() * 100),
        avoidable_rate_pct=(
            "is_avoidable_esc",
            lambda s: s.sum() / max(df.loc[s.index, "is_escalated"].sum(), 1) * 100
        )
    ).sort_values("esc_rate_pct", ascending=False)


def compute_engineering_outcome_mix(
    df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute engineering outcome mix overall and by category (E2).
    Returns (outcome_overall_df, cat_outcome_crosstab).
    """
    esc_df = df[df["is_escalated"] == 1].copy()
    outcome_overall = esc_df["eng_outcome"].value_counts().to_frame("tickets")
    outcome_overall["share_of_esc_pct"] = (
        outcome_overall["tickets"] / max(len(esc_df), 1) * 100
    )

    cat_outcome = pd.crosstab(esc_df["category"], esc_df["eng_outcome"])
    return outcome_overall, cat_outcome


def compute_escalation_quality_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute key escalation quality summary KPIs (E3):
    - avoidable escalation rate
    - return-to-L1 rate
    - avg handoffs per escalated ticket
    - share with 2+ handoffs
    """
    esc_df = df[df["is_escalated"] == 1].copy()
    n_esc = len(esc_df)

    if n_esc == 0:
        return {
            "avoidable_esc_rate_pct": 0.0,
            "returned_to_l1_rate_pct": 0.0,
            "avg_handoffs_per_escalated": 0.0,
            "share_2plus_handoffs_pct": 0.0,
            "total_escalated": 0
        }

    return {
        "avoidable_esc_rate_pct": float(esc_df["is_avoidable_esc"].mean() * 100),
        "returned_to_l1_rate_pct": float(esc_df["is_returned_to_l1"].mean() * 100),
        "avg_handoffs_per_escalated": float(esc_df["eng_handoffs"].mean()),
        "share_2plus_handoffs_pct": float((esc_df["eng_handoffs"] >= 2).mean() * 100),
        "total_escalated": int(n_esc)
    }


def compute_resolution_hours_consumption(df: pd.DataFrame) -> Dict[str, float]:
    """
    Compute share of total resolution hours used by escalated tickets and avoidable escalations (E4).
    """
    closed_df = df[df["resolution_hrs"].notna()]
    total_res_hrs = float(closed_df["resolution_hrs"].sum())

    esc_res_hrs = float(closed_df.loc[closed_df["is_escalated"] == 1, "resolution_hrs"].sum())
    avoid_res_hrs = float(closed_df.loc[closed_df["is_avoidable_esc"] == 1, "resolution_hrs"].sum())
    fixed_res_hrs = float(
        closed_df.loc[
            (closed_df["is_escalated"] == 1) & (closed_df["is_avoidable_esc"] == 0),
            "resolution_hrs"
        ].sum()
    )

    return {
        "total_resolution_hours": total_res_hrs,
        "escalated_hours": esc_res_hrs,
        "escalated_share_pct": (esc_res_hrs / max(total_res_hrs, 1e-9)) * 100,
        "avoidable_hours": avoid_res_hrs,
        "avoidable_share_pct": (avoid_res_hrs / max(total_res_hrs, 1e-9)) * 100,
        "fixed_hours": fixed_res_hrs,
        "fixed_share_pct": (fixed_res_hrs / max(total_res_hrs, 1e-9)) * 100
    }


def compute_duplicate_issues_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute duplicate-of-known-issue counts by category (E5).
    """
    esc_df = df[df["is_escalated"] == 1].copy()
    dup_df = esc_df[esc_df["eng_outcome"] == "Duplicate of known issue"]

    e5_dup = (
        dup_df["category"]
        .value_counts()
        .reindex(df["category"].unique(), fill_value=0)
        .to_frame("duplicate_count")
    )
    e5_dup["total_cat_escalations"] = esc_df["category"].value_counts().reindex(e5_dup.index, fill_value=0)
    e5_dup["pct_of_cat_escalations"] = (
        e5_dup["duplicate_count"] / e5_dup["total_cat_escalations"] * 100
    ).fillna(0)
    return e5_dup.sort_values("duplicate_count", ascending=False)
