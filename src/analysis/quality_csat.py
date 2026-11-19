"""
Quality, CSAT, and First-Contact Resolution Analysis Module (Section F)
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def compute_reopen_rate_by_dimension(
    df: pd.DataFrame, dimension: str
) -> pd.DataFrame:
    """
    Compute reopen rate for any categorical dimension (category, agent, escalation).
    """
    tbl = df.groupby(dimension, observed=False)["is_reopened"].agg(
        tickets="count",
        reopened="sum",
        reopen_rate_pct=lambda s: s.mean() * 100
    )
    if dimension == "is_escalated":
        tbl.index = ["Non-Escalated (0)", "Escalated (1)"]
    return tbl.sort_values("reopen_rate_pct", ascending=False)


def compute_reopen_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute reopen rate by ticket category (F1).
    """
    return compute_reopen_rate_by_dimension(df, "category")


def compute_reopen_by_agent(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute reopen rate by assigned agent (F1).
    """
    return compute_reopen_rate_by_dimension(df, "assigned_agent")


def compute_reopen_by_escalation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute reopen rate by escalation status (F1).
    """
    return compute_reopen_rate_by_dimension(df, "is_escalated")


def compute_csat_summary_by_dimension(
    df: pd.DataFrame, dimension: str
) -> pd.DataFrame:
    """
    Compute CSAT metrics by dimension (is_escalated, eng_handoffs, is_reopened, assigned_agent).
    """
    csat_tbl = df.groupby(dimension, observed=False)["csat_score"].agg(
        total_tickets="count",
        rated_tickets=lambda s: s.notna().sum(),
        mean_csat="mean",
        pct_low_csat_1_2=lambda s: (s.dropna() <= 2).mean() * 100 if s.notna().sum() > 0 else np.nan
    )
    if dimension == "is_escalated":
        csat_tbl.index = ["Non-Escalated (0)", "Escalated (1)"]
    elif dimension == "is_reopened":
        csat_tbl.index = ["Not Reopened (0)", "Reopened (1)"]
    return csat_tbl


def compute_csat_respondent_profile(
    df: pd.DataFrame,
    dimensions: List[str] = None
) -> pd.DataFrame:
    """
    Compute CSAT survey response rate and responder profile across dimensions (F3).
    """
    if dimensions is None:
        dimensions = ["channel", "client_tier", "is_escalated", "is_reopened", "status"]

    df_resp = df.copy()
    if "has_csat" not in df_resp.columns:
        df_resp["has_csat"] = df_resp["csat_score"].notna().astype(int)

    resp_dfs = []
    for dim in dimensions:
        resp_tbl = (
            df_resp.groupby(dim, observed=False)["has_csat"]
            .agg(
                tickets="count",
                responded="sum",
                response_rate_pct=lambda s: s.mean() * 100
            )
            .reset_index()
        )
        resp_tbl.rename(columns={dim: "segment_value"}, inplace=True)
        resp_tbl.insert(0, "dimension", dim)
        resp_dfs.append(resp_tbl)

    return pd.concat(resp_dfs, ignore_index=True)


def compute_first_contact_resolution(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute First-Contact Resolution (FCR) rate by category (F4).
    FCR definition: closed by L1 with no escalation and no reopen.
    """
    df_fcr = df.copy()
    if "is_fcr" not in df_fcr.columns:
        df_fcr["is_fcr"] = (
            (df_fcr["is_escalated"] == 0) &
            (df_fcr["is_reopened"] == 0) &
            (df_fcr["final_closed_at"].notna())
        ).astype(int)

    f4_cat = (
        df_fcr.groupby("category", observed=False)["is_fcr"]
        .agg(
            tickets="count",
            fcr_tickets="sum",
            fcr_rate_pct=lambda s: s.mean() * 100
        )
        .sort_values("fcr_rate_pct", ascending=False)
    )
    return f4_cat
