"""
Data Visualization and Diagnostic Plots Module
Generates all 4 comprehensive dashboard charts with headless backend compatibility.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Headless backend for automation and CLI runs
import matplotlib.pyplot as plt
import seaborn as sns

from src.config import FIGURES_DIR
from src.models.evaluate import compute_calibration_curve_points, extract_hybrid_coefficients


sns.set_theme(style="whitegrid")


def plot_volume_and_backlog(
    weekly_vol: pd.DataFrame,
    cat_growth: pd.DataFrame,
    save_path: Optional[Path] = None
) -> plt.Figure:
    """
    Plot 1: Weekly Volume & Backlog + Category Growth Drivers.
    """
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))

    # Left: Weekly intake vs closure & open backlog EOW
    x = np.arange(len(weekly_vol))
    axes[0].plot(x, weekly_vol["created"], marker="o", label="Created", linewidth=2)
    axes[0].plot(x, weekly_vol["closed"], marker="s", label="Closed", linewidth=2, linestyle="--")
    ax0_twin = axes[0].twinx()
    ax0_twin.bar(x, weekly_vol["open_eow"], alpha=0.22, color="tab:red", label="Open Backlog (EOW)")

    # Shade partial weeks
    for idx, row in weekly_vol.iterrows():
        if row.get("is_partial_week", 0) == 1:
            axes[0].axvspan(idx - 0.4, idx + 0.4, color="gray", alpha=0.15)

    axes[0].set_xticks(x)
    axes[0].set_xticklabels(weekly_vol["week_start"].astype(str), rotation=45, ha="right", fontsize=8)
    axes[0].set_ylabel("Weekly Tickets (Created / Closed)")
    ax0_twin.set_ylabel("Open Tickets at End of Week", color="tab:red")
    axes[0].set_title("Weekly Volume vs. Open Backlog (Shaded = Partial Weeks)")
    axes[0].legend(loc="upper left")

    # Right: Category Contribution to Jul -> Sep Volume Growth
    delta_col = "Jul_to_Sep_delta" if "Jul_to_Sep_delta" in cat_growth.columns else "total_delta"
    growth_sorted = cat_growth.sort_values(delta_col, ascending=True)
    colors = ["tab:red" if v > 0 else "tab:blue" for v in growth_sorted[delta_col]]
    axes[1].barh(growth_sorted.index, growth_sorted[delta_col], color=colors)
    axes[1].axvline(0, color="black", linewidth=0.8)
    axes[1].set_title("Category Ticket Growth (July vs. September)")
    axes[1].set_xlabel("Change in Monthly Ticket Volume (Sep - Jul)")

    plt.tight_layout()
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150)
    return fig


def plot_speed_and_escalations(
    d2_handoffs: pd.DataFrame,
    esc_df: pd.DataFrame,
    save_path: Optional[Path] = None
) -> plt.Figure:
    """
    Plot 2: Resolution Time by Handoffs + Avoidable Escalation Mix by Category.
    """
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))

    # Left: Resolution Time by Handoff Count
    x_h = np.arange(len(d2_handoffs))
    axes[0].bar(x_h - 0.18, d2_handoffs["median_hrs"], width=0.36, label="Median (P50) Hrs", color="steelblue")
    axes[0].bar(x_h + 0.18, d2_handoffs["p90_hrs"], width=0.36, label="90th Percentile (P90) Hrs", color="coral")
    axes[0].set_xticks(x_h)
    axes[0].set_xticklabels([f"{int(h)} Handoffs\n(n={int(n)})" for h, n in zip(d2_handoffs.index, d2_handoffs["n"])])
    axes[0].set_ylabel("Resolution Time (Hours)")
    axes[0].set_title("Resolution Time Explosion by Engineering Handoffs")
    axes[0].legend()

    # Right: Stacked Bar of Avoidable vs Real-Fix Escalations by Category
    cat_esc_stack = esc_df.groupby(["category", "is_avoidable_esc"], observed=False).size().unstack(fill_value=0)
    if 0 not in cat_esc_stack.columns:
        cat_esc_stack[0] = 0
    if 1 not in cat_esc_stack.columns:
        cat_esc_stack[1] = 0
    cat_esc_stack = cat_esc_stack[[0, 1]]
    cat_esc_stack.columns = ["Fixed (Legitimate)", "Avoidable (Non-Fix)"]
    cat_esc_stack = cat_esc_stack.loc[cat_esc_stack.sum(axis=1).sort_values(ascending=True).index]

    cat_esc_stack.plot(kind="barh", stacked=True, ax=axes[1], color=["#2ca02c", "#d62728"])
    axes[1].set_title("Escalated Tickets by Category: Fixed vs. Avoidable")
    axes[1].set_xlabel("Number of Escalated Tickets")
    axes[1].set_ylabel("")
    axes[1].legend(loc="lower right")

    plt.tight_layout()
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150)
    return fig


def plot_agent_benchmarking(
    agent_card_pct: pd.DataFrame,
    save_path: Optional[Path] = None
) -> plt.Figure:
    """
    Plot 3: Actual vs Expected Escalation Rate + Speed vs Quality (The Karan Check).
    """
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))

    # Left: Actual vs Expected Escalation Rate by Agent
    ag_plot = agent_card_pct.sort_values("actual_vs_expected_ratio", ascending=True)
    y_pos = np.arange(len(ag_plot))

    axes[0].barh(y_pos - 0.18, ag_plot["expected_esc_rate"], height=0.35, label="Expected (Category Mix)", color="lightgray", edgecolor="gray")
    axes[0].barh(y_pos + 0.18, ag_plot["actual_esc_rate"], height=0.35, label="Actual Escalation Rate", color="steelblue")

    for idx, row in enumerate(ag_plot.itertuples()):
        axes[0].text(
            max(row.actual_esc_rate, row.expected_esc_rate) + 1.0,
            idx,
            f"{row.actual_vs_expected_ratio:.2f}x",
            va="center", fontsize=9, fontweight="bold"
        )

    axes[0].set_yticks(y_pos)
    axes[0].set_yticklabels(ag_plot["assigned_agent"])
    axes[0].set_xlim(0, ag_plot["actual_esc_rate"].max() + 12)
    axes[0].set_xlabel("Escalation Rate (%)")
    axes[0].set_title("Agent Escalation Rate: Actual vs. Category-Mix Expected")
    axes[0].legend(loc="lower right")

    # Right: Speed vs Quality Trade-Off (Non-Escalated Median Close Hrs vs Reopen Rate)
    axes[1].scatter(
        agent_card_pct["non_esc_median_close_hrs"],
        agent_card_pct["reopen_rate"],
        s=agent_card_pct["total_tickets"] * 1.2,
        alpha=0.75, color="darkorange", edgecolor="black"
    )
    for row in agent_card_pct.itertuples():
        axes[1].annotate(
            row.assigned_agent,
            (row.non_esc_median_close_hrs, row.reopen_rate),
            xytext=(5, 4), textcoords="offset points", fontsize=9
        )

    axes[1].axhline(agent_card_pct["reopen_rate"].mean(), color="gray", linestyle="--", linewidth=0.9, label="Avg Reopen Rate")
    axes[1].axvline(agent_card_pct["non_esc_median_close_hrs"].mean(), color="gray", linestyle=":", linewidth=0.9, label="Avg L1 Close Time")
    axes[1].set_xlabel("Median Non-Escalated Close Time (Hours)")
    axes[1].set_ylabel("Overall Reopen Rate (%)")
    axes[1].set_title("Agent Speed vs. Quality Check (Bubble = Ticket Volume)")
    axes[1].legend()

    plt.tight_layout()
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150)
    return fig


def plot_model_calibration_and_features(
    fitted_models: Dict[str, Any],
    X_test: pd.DataFrame,
    y_test: np.ndarray,
    cat_features,
    num_features,
    save_path: Optional[Path] = None
) -> plt.Figure:
    """
    Plot 4: Calibration Curves + Hybrid Model Predictive Features.
    """
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))

    # Left: Calibration Curves on September Holdout
    axes[0].plot([0, 1], [0, 1], "k--", linewidth=1, label="Perfectly Calibrated")
    for name, model in fitted_models.items():
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(X_test)[:, 1]
            frac_pos, mean_pred = compute_calibration_curve_points(y_test, probs, n_bins=5)
            axes[0].plot(mean_pred, frac_pos, marker="o", label=name)

    axes[0].set_xlabel("Mean Predicted Probability (Avoidable)")
    axes[0].set_ylabel("Observed Fraction of Avoidable Escalations")
    axes[0].set_title("Calibration Curves (September Temporal Holdout)")
    axes[0].legend(loc="upper left", fontsize=8.5)

    # Right: Top 12 Drivers from Hybrid Model (Logistic Regression Coefficients)
    if "Hybrid (Tabular + TF-IDF)" in fitted_models:
        hyb_pipe = fitted_models["Hybrid (Tabular + TF-IDF)"]
        coef_df = extract_hybrid_coefficients(hyb_pipe, cat_features, num_features)
        top_drivers = pd.concat([
            coef_df.sort_values("coef", ascending=False).head(7),
            coef_df.sort_values("coef", ascending=True).head(5)
        ]).sort_values("coef", ascending=True)

        colors = ["#2ca02c" if c < 0 else "#d62728" for c in top_drivers["coef"]]
        axes[1].barh(top_drivers["feature"], top_drivers["coef"], color=colors)
        axes[1].axvline(0, color="black", linewidth=0.8)
        axes[1].set_xlabel("Log-Odds Coefficient (+ = More Likely Avoidable)")
        axes[1].set_title("Top Predictive Signals (Hybrid Tabular + TF-IDF Model)")

    plt.tight_layout()
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150)
    return fig
