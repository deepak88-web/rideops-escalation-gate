"""
Central Configuration Module for RideOps Escalation Gate
Loads parameters from config/config.yaml and provides constants.
"""

from pathlib import Path
from typing import Dict, List, Any
import os
import tempfile
import yaml
import pandas as pd

# Set writable directories for matplotlib & loky on Windows
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


def load_yaml_config(path: Path = CONFIG_PATH) -> Dict[str, Any]:
    """Load configuration dictionary from YAML file."""
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


_cfg = load_yaml_config()

# Directory & File Paths
RAW_DATA_PATH = PROJECT_ROOT / _cfg.get("paths", {}).get("raw_tickets", "data/raw/rideops_support_tickets.csv")
DATA_DICT_PATH = PROJECT_ROOT / _cfg.get("paths", {}).get("data_dictionary", "data/raw/rideops_data_dictionary.csv")
PROCESSED_DATA_PATH = PROJECT_ROOT / _cfg.get("paths", {}).get("processed_tickets", "data/processed/tickets_clean.csv")

MODELS_DIR = PROJECT_ROOT / _cfg.get("paths", {}).get("models_dir", "models")
MODEL_PATH = MODELS_DIR / "avoidable_escalation_gate.joblib"
REPORTS_DIR = PROJECT_ROOT / _cfg.get("paths", {}).get("reports_dir", "reports")
FIGURES_DIR = PROJECT_ROOT / _cfg.get("paths", {}).get("figures_dir", "reports/figures")
TABLES_DIR = PROJECT_ROOT / _cfg.get("paths", {}).get("tables_dir", "reports/tables")

# Business & Operational Constants
SNAPSHOT_AS_OF_DATE = pd.Timestamp(_cfg.get("data_quality", {}).get("snapshot_as_of", "2026-09-30 23:59:59"))
PARTIAL_WEEKS = {pd.Timestamp(w) for w in _cfg.get("data_quality", {}).get("partial_weeks", ["2026-06-29", "2026-09-28"])}

EXPECTED_NULLS = _cfg.get("data_quality", {}).get("expected_nulls", {
    "first_response_at": 5,
    "first_closed_at": 42,
    "final_closed_at": 48,
    "eng_outcome": 958,
    "eng_ticket_id": 958,
    "csat_score": 796
})

REPEAT_CONTACT_MAX_DAYS_EXCLUSIVE = float(_cfg.get("business_rules", {}).get("repeat_contact_max_days_exclusive", 15.0))
REAL_FIX_OUTCOME = _cfg.get("business_rules", {}).get("real_fix_outcome", "Fixed")
RETURNED_TO_L1_OUTCOMES = set(_cfg.get("business_rules", {}).get("returned_to_l1_outcomes", [
    "Config issue - returned to L1",
    "Insufficient info - returned to L1"
]))

SLA_TARGETS_HOURS = _cfg.get("business_rules", {}).get("sla_targets_hours", {
    "P1": 1.0,
    "P2": 4.0,
    "P3": 8.0,
    "P4": 24.0
})

# Modeling Settings
OPERATING_THRESHOLD = float(_cfg.get("modeling", {}).get("operating_threshold", 0.55))
DEFAULT_MODEL_THRESHOLD = OPERATING_THRESHOLD
CV_FOLDS = int(_cfg.get("modeling", {}).get("cv_folds", 5))
RANDOM_STATE = int(_cfg.get("modeling", {}).get("random_state", 42))
TEMPORAL_SPLIT_MONTH = int(_cfg.get("modeling", {}).get("temporal_split_month", 9))

CAT_FEATURES: List[str] = _cfg.get("modeling", {}).get("pre_escalation_features", {}).get("categorical", [
    "category", "priority", "channel", "client_tier", "assigned_agent", "weekday"
])
NUM_FEATURES: List[str] = _cfg.get("modeling", {}).get("pre_escalation_features", {}).get("numerical", [
    "hrs_to_first_response", "hour_of_day", "is_repeat_contact", "client_prior_tickets"
])
TEXT_FEATURE: str = _cfg.get("modeling", {}).get("pre_escalation_features", {}).get("text", "description")

FORBIDDEN_LEAKAGE_COLS = set(_cfg.get("modeling", {}).get("forbidden_leakage_columns", [
    "eng_outcome", "eng_handoffs", "eng_ticket_id", "first_closed_at",
    "final_closed_at", "hrs_to_first_close", "hrs_to_final_close",
    "resolution_hrs", "reopen_count", "is_reopened", "csat_score",
    "status", "is_open", "open_age_hrs", "is_avoidable_esc", "is_returned_to_l1"
]))
FORBIDDEN_LEAKAGE_COLUMNS = FORBIDDEN_LEAKAGE_COLS
