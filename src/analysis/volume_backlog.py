"""
Volume, Backlog Dynamics, and Client Mix Module (Section C)
"""

from typing import Dict, Any, Tuple
import pandas as pd
from src.config import SNAPSHOT_AS_OF_DATE, PARTIAL_WEEKS


def compute_weekly_volume_and_backlog(
    df: pd.DataFrame,
    as_of_date: pd.Timestamp = SNAPSHOT_AS_OF_DATE
) -> pd.DataFrame:
    """
    Compute weekly created, closed, net backlog, and end-of-week open tickets.
    """
    df_calc = df.copy()
    if "week_start" not in df_calc.columns and "created_at" in df_calc.columns:
        created = pd.to_datetime(df_calc["created_at"])
        df_calc["week_start"] = created.dt.to_period("W-SUN").apply(lambda r: r.start_time)
        df_calc["is_partial_week"] = df_calc["week_start"].isin(PARTIAL_WEEKS).astype(int)

    weeks = sorted(df_calc["week_start"].unique())
    weekly_rows = []

    for w_start in weeks:
        w_end = w_start + pd.Timedelta(days=6, hours=23, minutes=59, seconds=59)
        eval_end = min(w_end, as_of_date)
        is_partial = int(df_calc.loc[df_calc["week_start"] == w_start, "is_partial_week"].iloc[0])

        created_cnt = ((df_calc["created_at"] >= w_start) & (df_calc["created_at"] <= eval_end)).sum()
        closed_cnt = ((df_calc["final_closed_at"] >= w_start) & (df_calc["final_closed_at"] <= eval_end)).sum()
        open_eow = (
            (df_calc["created_at"] <= eval_end) &
            ((df_calc["final_closed_at"].isna()) | (df_calc["final_closed_at"] > eval_end))
        ).sum()

        weekly_rows.append({
            "week_start": w_start.strftime("%Y-%m-%d"),
            "is_partial_week": is_partial,
            "created": int(created_cnt),
            "closed": int(closed_cnt),
            "net_backlog": int(created_cnt - closed_cnt),
            "open_eow": int(open_eow)
        })

    return pd.DataFrame(weekly_rows)


def compute_monthly_volume_clients(df: pd.DataFrame) -> pd.DataFrame:
    """Compute monthly created, closed, unique active clients, and tickets per client."""
    monthly_vol = df.groupby("month").agg(
        tickets_created=("ticket_id", "count"),
        tickets_closed=("final_closed_at", lambda s: s.notna().sum()),
        unique_active_clients=("client_id", "nunique")
    ).reset_index()
    monthly_vol["tickets_per_client"] = (monthly_vol["tickets_created"] / monthly_vol["unique_active_clients"]).round(2)
    return monthly_vol


def compute_category_growth_drivers(df: pd.DataFrame) -> pd.DataFrame:
    """Compute category volume mix by month and each category's contribution to total ticket growth."""
    cat_month = pd.crosstab(df["category"], df["month"])
    cat_mix_pct = pd.crosstab(df["category"], df["month"], normalize="columns") * 100

    start_month = cat_month.columns[0]
    end_month = cat_month.columns[-1]
    total_growth = cat_month[end_month].sum() - cat_month[start_month].sum()

    cat_growth = pd.DataFrame({
        f"{start_month}_vol": cat_month[start_month],
        f"{cat_month.columns[1]}_vol": cat_month[cat_month.columns[1]],
        f"{end_month}_vol": cat_month[end_month],
        f"{start_month}_mix_%": cat_mix_pct[start_month].round(2),
        f"{cat_month.columns[1]}_mix_%": cat_mix_pct[cat_month.columns[1]].round(2),
        f"{end_month}_mix_%": cat_mix_pct[end_month].round(2),
        "total_delta": cat_month[end_month] - cat_month[start_month],
        "Jul_to_Sep_delta": cat_month[end_month] - cat_month[start_month],
        "pct_of_total_growth": (((cat_month[end_month] - cat_month[start_month]) / total_growth) * 100).round(2)
    }).sort_values("total_delta", ascending=False)

    return cat_growth


def compute_client_concentration(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute Top 10 and Top 20 client share and rank clients by ticket volume."""
    client_vol = df.groupby(["client_id", "client_name", "client_tier"]).size().reset_index(name="tickets")
    client_vol = client_vol.sort_values("tickets", ascending=False).reset_index(drop=True)
    total_tickets = len(df)

    top10_share = round((client_vol.head(10)["tickets"].sum() / total_tickets) * 100, 2)
    top20_share = round((client_vol.head(20)["tickets"].sum() / total_tickets) * 100, 2)

    return {
        "total_unique_clients": len(client_vol),
        "top_10_share_pct": top10_share,
        "top_20_share_pct": top20_share,
        "client_ranking": client_vol
    }


def compute_channel_and_tier_mix(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Compute volume and percentage share across channels and client tiers."""
    results = {}
    for col in ["channel", "client_tier"]:
        if col in df.columns:
            mix = df[col].value_counts().to_frame("tickets")
            mix["share_%"] = (mix["tickets"] / len(df) * 100).round(2)
            results[col] = mix
    return results
