"""
Statistical Hypothesis Testing Module (Section I)
Calculates all required chi-square, Mann-Whitney U, Kruskal-Wallis, Spearman, and linear regression tests.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
from scipy import stats


def test_avoidable_by_category(esc_df: pd.DataFrame) -> Dict[str, Any]:
    """Chi-Square test: Avoidable escalation rate differs by category."""
    ct = pd.crosstab(esc_df["category"], esc_df["is_avoidable_esc"])
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    return {
        "hypothesis": "Avoidable escalation rate differs by category",
        "test": f"Chi-Square (dof={dof})",
        "statistic": f"chi2 = {chi2:.3f}",
        "p_value": p,
        "significant_0.05": p < 0.05
    }


def test_reopen_by_agent(df: pd.DataFrame) -> Dict[str, Any]:
    """Chi-Square test: Reopen rate differs by assigned agent."""
    ct = pd.crosstab(df["assigned_agent"], df["is_reopened"])
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    return {
        "hypothesis": "Reopen rate differs by assigned agent",
        "test": f"Chi-Square (dof={dof})",
        "statistic": f"chi2 = {chi2:.3f}",
        "p_value": p,
        "significant_0.05": p < 0.05
    }


def test_resolution_escalated_vs_non_escalated(df: pd.DataFrame) -> Dict[str, Any]:
    """Mann-Whitney U test: Resolution time for escalated vs. non-escalated."""
    res_esc = df.loc[df["is_escalated"] == 1, "resolution_hrs"].dropna()
    res_non = df.loc[df["is_escalated"] == 0, "resolution_hrs"].dropna()
    u, p = stats.mannwhitneyu(res_esc, res_non, alternative="two-sided")
    return {
        "hypothesis": f"Resolution time differs: Escalated ({res_esc.median():.1f}h) vs Non-Esc ({res_non.median():.1f}h)",
        "test": "Mann-Whitney U",
        "statistic": f"U = {u:,.1f}",
        "p_value": p,
        "significant_0.05": p < 0.05
    }


def test_resolution_avoidable_vs_fixed(esc_df: pd.DataFrame) -> Dict[str, Any]:
    """Mann-Whitney U test: Resolution time for avoidable vs. real-fix escalations."""
    res_avoid = esc_df.loc[esc_df["is_avoidable_esc"] == 1, "resolution_hrs"].dropna()
    res_fixed = esc_df.loc[esc_df["is_avoidable_esc"] == 0, "resolution_hrs"].dropna()
    u, p = stats.mannwhitneyu(res_avoid, res_fixed, alternative="two-sided")
    return {
        "hypothesis": f"Resolution time differs: Avoidable ({res_avoid.median():.1f}h) vs Fixed ({res_fixed.median():.1f}h)",
        "test": "Mann-Whitney U",
        "statistic": f"U = {u:,.1f}",
        "p_value": p,
        "significant_0.05": p < 0.05
    }


def test_csat_across_handoffs(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Kruskal-Wallis & Spearman correlation: CSAT across engineering handoff counts."""
    csat_valid = df.dropna(subset=["csat_score"]).copy()
    groups = [grp["csat_score"].values for _, grp in csat_valid.groupby("eng_handoffs")]
    kw_stat, p_kw = stats.kruskal(*groups)
    rho, p_sp = stats.spearmanr(csat_valid["eng_handoffs"], csat_valid["csat_score"])

    return [
        {
            "hypothesis": "CSAT differs across engineering handoff counts (0, 1, 2, 3)",
            "test": "Kruskal-Wallis H",
            "statistic": f"H = {kw_stat:.3f}",
            "p_value": p_kw,
            "significant_0.05": p_kw < 0.05
        },
        {
            "hypothesis": "CSAT correlates negatively with handoff count",
            "test": "Spearman Rank Corr",
            "statistic": f"rho = {rho:.3f}",
            "p_value": p_sp,
            "significant_0.05": p_sp < 0.05
        }
    ]


def test_volume_and_resolution_trends(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Linear regression test: Weekly volume trends upward while resolution time stays flat."""
    full_wks = df[df["is_partial_week"] == 0].copy()
    wk_stats = full_wks.groupby("week_start").agg(
        weekly_volume=("ticket_id", "count"),
        median_res_hrs=("resolution_hrs", "median")
    ).reset_index()
    wk_stats["week_num"] = np.arange(len(wk_stats))

    sl_v, _, r_v, p_v, _ = stats.linregress(wk_stats["week_num"], wk_stats["weekly_volume"])
    sl_r, _, r_r, p_r, _ = stats.linregress(wk_stats["week_num"], wk_stats["median_res_hrs"])

    return [
        {
            "hypothesis": f"Weekly ticket volume trends upward (+{sl_v:.2f} tkts/wk)",
            "test": "Linear Trend (OLS)",
            "statistic": f"r = {r_v:.3f}",
            "p_value": p_v,
            "significant_0.05": p_v < 0.05
        },
        {
            "hypothesis": f"Weekly median resolution time stays flat ({sl_r:+.2f} hrs/wk)",
            "test": "Linear Trend (OLS)",
            "statistic": f"r = {r_r:.3f}",
            "p_value": p_r,
            "significant_0.05": p_r < 0.05
        }
    ]


def run_all_hypothesis_tests(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run all 7 hypothesis tests and return a formatted DataFrame with p-values.
    """
    esc_df = df[df["is_escalated"] == 1].copy()
    results = [
        test_avoidable_by_category(esc_df),
        test_reopen_by_agent(df),
        test_resolution_escalated_vs_non_escalated(df),
        test_resolution_avoidable_vs_fixed(esc_df)
    ]
    results.extend(test_csat_across_handoffs(df))
    results.extend(test_volume_and_resolution_trends(df))

    hyp_df = pd.DataFrame(results)
    hyp_df["p_value_fmt"] = hyp_df["p_value"].apply(
        lambda p: f"{p:.4e}" if p < 0.001 else f"{p:.4f}"
    )
    return hyp_df
