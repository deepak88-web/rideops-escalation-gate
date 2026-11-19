"""
Logging and Persistence Module for RideOps Escalation Gate
"""
from src.logging.override_logger import (
    init_override_db,
    log_escalation_decision,
    get_logged_decisions,
    compute_override_metrics,
    seed_sample_overrides_if_empty
)

__all__ = [
    "init_override_db",
    "log_escalation_decision",
    "get_logged_decisions",
    "compute_override_metrics",
    "seed_sample_overrides_if_empty"
]
