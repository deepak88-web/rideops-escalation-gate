"""
End-to-End Orchestration Pipeline for RideOps Escalation Gate Analysis
Executes full data ingestion, quality audit, feature engineering, analysis metrics,
hypothesis testing, machine learning model training & evaluation, and visualization.
"""

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())
import pandas as pd

# Project roots and module paths
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    RAW_DATA_PATH,
    PROCESSED_DATA_PATH,
    TABLES_DIR,
    FIGURES_DIR,
    MODEL_PATH,
    DEFAULT_MODEL_THRESHOLD,
)
from src.data.loader import load_raw_tickets
from src.data.quality import run_data_quality_audit
from src.features.pipeline import build_feature_pipeline
from src.analysis import (
    compute_weekly_volume_and_backlog,
    compute_monthly_volume_clients,
    compute_category_growth_drivers,
    compute_first_response_speed,
    compute_resolution_speed_by_category,
    compute_resolution_speed_by_handoffs,
    compute_first_response_sla,
    compute_open_backlog_age_bands,
    compute_escalation_by_month,
    compute_escalation_by_category,
    compute_engineering_outcome_mix,
    compute_duplicate_issues_by_category,
    compute_reopen_by_category,
    compute_csat_respondent_profile,
    compute_first_contact_resolution,
    compute_agent_scorecard,
    compute_agent_category_workload_mix,
    compute_repeat_contacts_by_month,
    compute_repeat_contacts_by_category,
    compute_top_repeat_clients,
)
from src.utils.hypothesis_tests import run_all_hypothesis_tests
from src.models import (
    CAT_FEATURES,
    NUM_FEATURES,
    prepare_model_dataset,
    run_cross_validation,
    run_temporal_validation,
    train_and_save_champion,
    train_and_validate_live_gate,
)
from src.logging import seed_sample_overrides_if_empty
from src.visualization.plots import (
    plot_volume_and_backlog,
    plot_speed_and_escalations,
    plot_agent_benchmarking,
    plot_model_calibration_and_features,
)


def main():
    print("=" * 70)
    print("STARTING RIDEOPS ESCALATION GATE MODULAR PIPELINE")
    print("=" * 70)

    # 1. Ingestion
    print("\n[Step 1/6] Loading raw ticket data...")
    raw_df = load_raw_tickets(RAW_DATA_PATH)
    print(f"Loaded {len(raw_df):,} raw records from {RAW_DATA_PATH.name}")

    # 2. Quality Audit
    print("\n[Step 2/6] Running Data Quality Checks (Section A)...")
    audit_results = run_data_quality_audit(raw_df)
    print(f" - Duplicate ticket IDs:       {audit_results['duplicate_check']['duplicate_count']}")
    print(f" - Impossible timestamps:      {audit_results['timestamp_validation']['total_violations']}")
    print(f" - Escalation inconsistencies: {audit_results['escalation_consistency']['inconsistent_rows_count']}")
    null_counts = audit_results['null_counts']
    eng_outcome_nulls = int(null_counts.loc["eng_outcome", "null_count"]) if "eng_outcome" in null_counts.index else 0
    print(f" - Missing eng_outcome:        {eng_outcome_nulls} (expected for non-escalated)")

    # 3. Feature Engineering Pipeline
    print("\n[Step 3/6] Deriving operational features & flags (Section B)...")
    df = build_feature_pipeline(raw_df)
    PROCESSED_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_DATA_PATH, index=False)
    print(f"Engineered dataset saved to {PROCESSED_DATA_PATH} (Shape: {df.shape})")

    # 4. Operations Analysis (Sections C, D, E, F, G, H)
    print("\n[Step 4/6] Computing analytics metrics and saving report tables...")
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    # Section C
    weekly_vol = compute_weekly_volume_and_backlog(df)
    weekly_vol.to_csv(TABLES_DIR / "c1_weekly_volume_backlog.csv", index=False)
    monthly_vol = compute_monthly_volume_clients(df)
    monthly_vol.to_csv(TABLES_DIR / "c2_monthly_volume_clients.csv", index=False)
    cat_growth = compute_category_growth_drivers(df)
    cat_growth.to_csv(TABLES_DIR / "c3_category_mix_and_growth.csv")

    # Section D
    d1_speed = compute_first_response_speed(df)
    d1_speed.to_csv(TABLES_DIR / "d1_first_response_speed.csv")
    d2_cat = compute_resolution_speed_by_category(df)
    d2_cat.to_csv(TABLES_DIR / "d2_resolution_speed_by_category.csv")
    d2_handoffs = compute_resolution_speed_by_handoffs(df)
    d2_handoffs.to_csv(TABLES_DIR / "d2_resolution_speed_by_handoffs.csv")
    d3_sla = compute_first_response_sla(df)
    d3_sla.to_csv(TABLES_DIR / "d3_first_response_sla.csv")
    d4_age = compute_open_backlog_age_bands(df)
    d4_age.to_csv(TABLES_DIR / "d4_open_backlog_age_bands.csv", index=False)

    # Section E
    e1_month = compute_escalation_by_month(df)
    e1_month.to_csv(TABLES_DIR / "e1_escalation_by_month.csv", index=False)
    e1_cat = compute_escalation_by_category(df)
    e1_cat.to_csv(TABLES_DIR / "e1_escalation_by_category.csv")
    e2_outcome, e2_cat_outcome = compute_engineering_outcome_mix(df)
    e2_outcome.to_csv(TABLES_DIR / "e2_eng_outcome_overall.csv")
    e2_cat_outcome.to_csv(TABLES_DIR / "e2_eng_outcome_by_category.csv")
    e5_dup = compute_duplicate_issues_by_category(df)
    e5_dup.to_csv(TABLES_DIR / "e5_duplicate_issues_by_category.csv")

    # Section F
    f1_cat = compute_reopen_by_category(df)
    f1_cat.to_csv(TABLES_DIR / "f1_reopen_by_category.csv")
    f3_resp = compute_csat_respondent_profile(df)
    f3_resp.to_csv(TABLES_DIR / "f3_csat_respondent_profile.csv", index=False)
    f4_fcr = compute_first_contact_resolution(df)
    f4_fcr.to_csv(TABLES_DIR / "f4_fcr_by_category.csv")

    # Section G
    g1_card = compute_agent_scorecard(df)
    g1_card.to_csv(TABLES_DIR / "g1_agent_scorecard.csv", index=False)
    g1_card.to_csv(TABLES_DIR / "g1_agent_casemix_scorecard.csv", index=False)
    g2_mix = compute_agent_category_workload_mix(df)
    g2_mix.to_csv(TABLES_DIR / "g2_agent_category_workload_mix.csv")
    g2_mix.to_csv(TABLES_DIR / "g2_agent_category_mix.csv")

    # Section H
    h1_month = compute_repeat_contacts_by_month(df)
    h1_month.to_csv(TABLES_DIR / "h1_repeat_contacts_by_month.csv", index=False)
    h2_cat = compute_repeat_contacts_by_category(df)
    h2_cat.to_csv(TABLES_DIR / "h2_repeat_contacts_by_category.csv")
    h3_clients = compute_top_repeat_clients(df, top_n=20)
    h3_clients.to_csv(TABLES_DIR / "h3_top_repeat_clients.csv", index=False)
    print(f"Generated 20+ reporting tables in {TABLES_DIR}")

    # 5. Statistical Hypothesis Testing (Section I)
    print("\n[Step 5/6] Executing Statistical Hypothesis Tests (Section I)...")
    hyp_df = run_all_hypothesis_tests(df)
    hyp_df.to_csv(TABLES_DIR / "i1_hypothesis_tests.csv", index=False)
    print(f"Hypothesis tests completed and saved to {TABLES_DIR / 'i1_hypothesis_tests.csv'}")

    # 6. Machine Learning Modeling (Section J)
    print("\n[Step 6/6] Training & Evaluating Avoidable Escalation Gate Models (Section J)...")
    X, y, is_sep = prepare_model_dataset(df)

    # 5-Fold Stratified Cross-Validation
    print(" - Running 5-fold Stratified Cross-Validation...")
    cv_df = run_cross_validation(X, y, threshold=DEFAULT_MODEL_THRESHOLD)
    cv_df.to_csv(TABLES_DIR / "j1_cv_model_comparison.csv")

    # Temporal Validation (Train: Jul-Aug, Test: Sep)
    print(" - Running Temporal Validation (Train Jul-Aug, Test Sep holdout)...")
    time_df, fitted_models, X_train, y_train, X_test, y_test = run_temporal_validation(
        X, y, is_sep, threshold=DEFAULT_MODEL_THRESHOLD
    )
    time_df.to_csv(TABLES_DIR / "j2_temporal_split_comparison.csv")

    # Save Champion Model 1
    champion_name = train_and_save_champion(fitted_models, time_df, save_path=MODEL_PATH)
    print(f"Champion Model 1 '{champion_name}' saved to {MODEL_PATH}")

    # 7. Model 2: Live Escalation Triage Gate (Pre-Escalation Decision Support)
    print("\n[Step 7/7] Training & Evaluating Live Triage Gate Model (Model 2)...")
    live_df, live_champ = train_and_validate_live_gate(df)
    print("Live Triage Gate Temporal Validation Results (Sep Holdout):")
    print(live_df[["ROC_AUC", "PR_AUC", "Precision", "Recall", "F1"]])

    # Initialize and seed override logging database
    seed_sample_overrides_if_empty()
    print("Initialized persistent SQLite decision & override tracking database.")

    # Visualizations
    print("\nGenerating figures...")
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    esc_df = df[df["is_escalated"] == 1].copy()

    plot_volume_and_backlog(weekly_vol, cat_growth, save_path=FIGURES_DIR / "c_volume_and_backlog.png")
    plot_speed_and_escalations(d2_handoffs, esc_df, save_path=FIGURES_DIR / "de_speed_and_escalations.png")
    plot_agent_benchmarking(g1_card, save_path=FIGURES_DIR / "fg_agent_benchmarking.png")
    plot_model_calibration_and_features(
        fitted_models, X_test, y_test, CAT_FEATURES, NUM_FEATURES,
        save_path=FIGURES_DIR / "j_model_calibration_and_features.png"
    )
    print(f"Generated 4 diagnostic figures in {FIGURES_DIR}")

    print("\n" + "=" * 70)
    print("RIDEOPS ESCALATION GATE PIPELINE RUN COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    main()
