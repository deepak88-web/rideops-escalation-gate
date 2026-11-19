"""
Agent Benchmarking, Fair Case-Mix Adjustment, and Behavioral Check Module (Section G)
"""

from typing import Tuple
import pandas as pd


def compute_agent_scorecard(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute fair case-mix adjusted agent scorecard (G1):
    - Actual escalation rate
    - Category-mix expected escalation rate
    - actual_vs_expected_ratio (Rahul ~1.8x, Karan ~0.5x)
    - Avoidable escalation rate
    - Reopen rate
    - Non-escalated median resolution hours (the Karan check)
    - FCR rate
    - Mean CSAT
    """
    df_calc = df.copy()

    # Category baseline escalation rates
    cat_base_esc = df_calc.groupby("category", observed=False)["is_escalated"].mean().rename("cat_expected_esc_rate")
    df_ag = df_calc.merge(cat_base_esc, on="category", how="left")

    # Non-escalated median resolution hours per agent (the Karan check)
    non_esc_speed = (
        df_ag[df_ag["is_escalated"] == 0]
        .groupby("assigned_agent", observed=False)["resolution_hrs"]
        .median()
        .rename("non_esc_median_close_hrs")
    )

    agent_card = df_ag.groupby("assigned_agent", observed=False).agg(
        total_tickets=("ticket_id", "count"),
        escalated_tickets=("is_escalated", "sum"),
        actual_esc_rate=("is_escalated", "mean"),
        expected_esc_rate=("cat_expected_esc_rate", "mean"),
        avoidable_esc_rate=(
            "is_avoidable_esc",
            lambda s: s.sum() / max(df_ag.loc[s.index, "is_escalated"].sum(), 1)
        ),
        reopen_rate=("is_reopened", "mean"),
        fcr_rate=("is_fcr", "mean"),
        mean_csat=("csat_score", "mean")
    ).reset_index()

    agent_card["actual_vs_expected_ratio"] = (
        agent_card["actual_esc_rate"] / agent_card["expected_esc_rate"]
    )
    agent_card = agent_card.merge(non_esc_speed, on="assigned_agent", how="left")

    # Convert rates to percentages for presentation
    agent_card_pct = agent_card.copy()
    for col in [
        "actual_esc_rate",
        "expected_esc_rate",
        "avoidable_esc_rate",
        "reopen_rate",
        "fcr_rate"
    ]:
        agent_card_pct[col] = agent_card_pct[col] * 100

    agent_card_pct = agent_card_pct.sort_values(
        "actual_vs_expected_ratio", ascending=False
    ).reset_index(drop=True)

    return agent_card_pct


def compute_agent_category_workload_mix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute agent workload distribution across categories (% of agent's tickets) (G2).
    """
    return pd.crosstab(
        df["assigned_agent"],
        df["category"],
        normalize="index"
    ) * 100
