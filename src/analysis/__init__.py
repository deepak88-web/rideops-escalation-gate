"""
Analysis Package Root
"""

from src.analysis.volume_backlog import (
    compute_weekly_volume_and_backlog,
    compute_monthly_volume_clients,
    compute_category_growth_drivers,
    compute_client_concentration,
    compute_channel_and_tier_mix,
)

from src.analysis.speed import (
    compute_p50_p90_summary,
    compute_first_response_speed,
    compute_resolution_speed_by_category,
    compute_resolution_speed_by_handoffs,
    compute_resolution_speed_by_escalation,
    compute_first_response_sla,
    compute_open_backlog_age_bands,
    assign_age_band,
)

from src.analysis.escalation import (
    compute_escalation_by_month,
    compute_escalation_by_category,
    compute_escalation_by_agent_raw,
    compute_engineering_outcome_mix,
    compute_escalation_quality_kpis,
    compute_resolution_hours_consumption,
    compute_duplicate_issues_by_category,
)

from src.analysis.quality_csat import (
    compute_reopen_rate_by_dimension,
    compute_reopen_by_category,
    compute_reopen_by_agent,
    compute_reopen_by_escalation,
    compute_csat_summary_by_dimension,
    compute_csat_respondent_profile,
    compute_first_contact_resolution,
)

from src.analysis.agent_benchmarks import (
    compute_agent_scorecard,
    compute_agent_category_workload_mix,
)

from src.analysis.repeat_trends import (
    compute_repeat_contacts_by_month,
    compute_repeat_contacts_by_category,
    compute_top_repeat_clients,
)

__all__ = [
    "compute_weekly_volume_and_backlog",
    "compute_monthly_volume_clients",
    "compute_category_growth_drivers",
    "compute_client_concentration",
    "compute_channel_and_tier_mix",
    "compute_p50_p90_summary",
    "compute_first_response_speed",
    "compute_resolution_speed_by_category",
    "compute_resolution_speed_by_handoffs",
    "compute_resolution_speed_by_escalation",
    "compute_first_response_sla",
    "compute_open_backlog_age_bands",
    "compute_escalation_by_month",
    "compute_escalation_by_category",
    "compute_escalation_by_agent_raw",
    "compute_engineering_outcome_mix",
    "compute_escalation_quality_kpis",
    "compute_resolution_hours_consumption",
    "compute_duplicate_issues_by_category",
    "compute_reopen_rate_by_dimension",
    "compute_reopen_by_category",
    "compute_reopen_by_agent",
    "compute_reopen_by_escalation",
    "compute_csat_summary_by_dimension",
    "compute_csat_respondent_profile",
    "compute_first_contact_resolution",
    "compute_agent_scorecard",
    "compute_agent_category_workload_mix",
    "compute_repeat_contacts_by_month",
    "compute_repeat_contacts_by_category",
    "compute_top_repeat_clients",
]
