"""
Repeat Contact Trends Analysis Module (Section H)
"""

from typing import Tuple
import pandas as pd


def compute_repeat_contacts_by_month(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute repeat-contact rate by month (H1).
    Benchmark: 14.9% July, 18.0% August, 24.8% September.
    """
    return df.groupby("month", observed=False).agg(
        total_tickets=("ticket_id", "count"),
        repeat_tickets=("is_repeat_contact", "sum"),
        repeat_rate_pct=("is_repeat_contact", lambda s: s.mean() * 100)
    ).reset_index()


def compute_repeat_contacts_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute repeat-contact rate by category (H2).
    """
    return df.groupby("category", observed=False).agg(
        total_tickets=("ticket_id", "count"),
        repeat_tickets=("is_repeat_contact", "sum"),
        repeat_rate_pct=("is_repeat_contact", lambda s: s.mean() * 100)
    ).sort_values("repeat_rate_pct", ascending=False)


def compute_top_repeat_clients(
    df: pd.DataFrame, top_n: int = 10
) -> pd.DataFrame:
    """
    Compute top clients generating repeat contacts (H3).
    """
    h3_client = df.groupby(
        ["client_id", "client_name", "client_tier"], observed=False
    ).agg(
        total_tickets=("ticket_id", "count"),
        repeat_tickets=("is_repeat_contact", "sum"),
        repeat_rate_pct=("is_repeat_contact", lambda s: s.mean() * 100)
    ).sort_values(
        ["repeat_tickets", "repeat_rate_pct"], ascending=False
    ).reset_index()

    return h3_client.head(top_n)
