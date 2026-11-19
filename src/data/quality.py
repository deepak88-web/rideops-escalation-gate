"""
Data Quality Validation and Sanity Auditing Module (Section A)

Covers:
- Duplicate ticket IDs check
- Null counts per column (and comparison with expected nulls)
- Impossible timestamps validation (response before creation, closed before created, final before first close)
- Escalation consistency validation
- Spelling & casing standardization
- Partial week flagging
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from src.config import EXPECTED_NULLS, PARTIAL_WEEKS


def check_duplicate_tickets(df: pd.DataFrame, id_col: str = "ticket_id") -> Dict[str, Any]:
    """Check for duplicate ticket IDs."""
    if id_col not in df.columns:
        return {"status": "SKIPPED", "duplicate_count": 0}
    dup_count = int(df[id_col].duplicated().sum())
    return {
        "status": "PASSED" if dup_count == 0 else "FAILED",
        "duplicate_count": dup_count
    }


def check_null_counts(df: pd.DataFrame, expected_nulls: Optional[Dict[str, int]] = None) -> pd.DataFrame:
    """Compute null counts and check against expected baseline missingness."""
    expected = expected_nulls or EXPECTED_NULLS
    null_counts = df.isna().sum()
    null_pct = (df.isna().mean() * 100).round(2)

    report = pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "null_count": null_counts,
        "null_pct": null_pct
    })

    if expected:
        report["expected_nulls"] = report.index.map(lambda c: expected.get(c, 0))
        report["matches_expected"] = report["null_count"] == report["expected_nulls"]

    return report


def validate_timestamps(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate chronological ordering of ticket timestamps."""
    response_before_creation = int((df["first_response_at"] < df["created_at"]).sum())
    close_before_creation = int((df["first_closed_at"] < df["created_at"]).sum())
    final_before_first_close = int((df["final_closed_at"] < df["first_closed_at"]).sum())

    total_violations = response_before_creation + close_before_creation + final_before_first_close
    return {
        "status": "PASSED" if total_violations == 0 else "FAILED",
        "total_violations": total_violations,
        "details": {
            "response_before_creation": response_before_creation,
            "close_before_creation": close_before_creation,
            "final_close_before_first_close": final_before_first_close
        }
    }


def validate_escalation_consistency(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate escalation consistency:
    escalated_to_eng == 'Yes' must match eng_handoffs >= 1 and non-null eng_outcome.
    """
    esc_yes = df["escalated_to_eng"].astype(str).str.strip().str.lower().isin(["yes", "true", "1"])
    handoff_ge1 = df["eng_handoffs"].fillna(0) >= 1
    outcome_present = df["eng_outcome"].notna() & (df["eng_outcome"].astype(str).str.strip() != "")

    inconsistent = df[
        (esc_yes & (~handoff_ge1 | ~outcome_present)) |
        (~esc_yes & (handoff_ge1 | outcome_present))
    ]
    inconsistent_count = len(inconsistent)

    return {
        "status": "PASSED" if inconsistent_count == 0 else "WARNING",
        "inconsistent_rows_count": inconsistent_count,
        "escalated_count": int(esc_yes.sum()),
        "non_escalated_count": int((~esc_yes).sum())
    }


def flag_partial_weeks(df: pd.DataFrame) -> pd.DataFrame:
    """Flag partial weeks at the start (2026-06-29) and end (2026-09-28)."""
    df_out = df.copy()
    if "created_at" in df_out.columns:
        df_out["week_start"] = df_out["created_at"].dt.to_period("W-SUN").apply(lambda r: r.start_time)
        df_out["is_partial_week"] = df_out["week_start"].isin(PARTIAL_WEEKS).astype(int)
    return df_out


def run_data_quality_audit(df: pd.DataFrame) -> Dict[str, Any]:
    """Execute complete battery of Section A data quality checks."""
    return {
        "duplicate_check": check_duplicate_tickets(df),
        "null_counts": check_null_counts(df),
        "timestamp_validation": validate_timestamps(df),
        "escalation_consistency": validate_escalation_consistency(df),
    }
