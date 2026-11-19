"""
Data Upload and Schema Validation Module (Section 6)
Validates newly uploaded ticket CSV datasets against schema dictionaries,
timestamp rules, data types, and duplicate constraints before dashboard ingestion.
"""

from typing import Tuple, List, Optional
import io
import pandas as pd

from src.features.pipeline import build_feature_pipeline

REQUIRED_COLUMNS = [
    "ticket_id",
    "created_at",
    "channel",
    "client_id",
    "client_name",
    "client_tier",
    "category",
    "priority",
    "description",
    "assigned_agent",
    "first_response_at",
    "escalated_to_eng",
    "status"
]


def validate_uploaded_tickets_csv(
    file_or_df
) -> Tuple[bool, List[str], Optional[pd.DataFrame]]:
    """
    Validate an uploaded CSV file buffer or DataFrame.
    Returns (is_valid, error_messages, processed_df).
    """
    errors: List[str] = []

    # 1. Read input
    try:
        if isinstance(file_or_df, pd.DataFrame):
            df = file_or_df.copy()
        elif hasattr(file_or_df, "read"):
            file_or_df.seek(0)
            df = pd.read_csv(file_or_df)
        else:
            df = pd.read_csv(str(file_or_df))
    except Exception as e:
        return False, [f"Failed to read CSV file: {str(e)}"], None

    if df.empty:
        return False, ["Uploaded CSV is empty."], None

    # 2. Required columns check
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        return False, errors, None

    # 3. Duplicate ticket ID check
    dup_count = int(df["ticket_id"].duplicated().sum())
    if dup_count > 0:
        errors.append(f"Detected {dup_count} duplicate ticket_id values. Ticket IDs must be unique.")

    # 4. Timestamp validity check & datetime conversion
    for ts_col in ["created_at", "first_response_at", "first_closed_at", "final_closed_at"]:
        if ts_col in df.columns:
            non_null = df[ts_col].dropna()
            parsed = pd.to_datetime(non_null, errors="coerce")
            unparseable = int(parsed.isna().sum())
            if unparseable > 0:
                errors.append(f"Column '{ts_col}' contains {unparseable} unparseable timestamp values.")
            else:
                df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")

    # 5. Escalation flag validity check
    valid_esc = df["escalated_to_eng"].dropna().isin([0, 1, "0", "1", "Yes", "No", True, False]).all()
    if not valid_esc:
        errors.append("Column 'escalated_to_eng' must contain binary values (0 or 1, Yes or No).")

    if errors:
        return False, errors, None

    # Populate optional standard columns if omitted from upload
    optional_defaults = {
        "eng_ticket_id": None,
        "eng_handoffs": 0,
        "eng_outcome": None,
        "first_closed_at": None,
        "final_closed_at": None,
        "reopen_count": 0,
        "csat_score": None
    }
    for col, default_val in optional_defaults.items():
        if col not in df.columns:
            df[col] = default_val

    # Standardize escalated_to_eng to Yes/No if numeric
    if df["escalated_to_eng"].dtype in [int, float, bool]:
        df["escalated_to_eng"] = df["escalated_to_eng"].map({1: "Yes", 0: "No", True: "Yes", False: "No"})

    # 6. Apply feature engineering pipeline to derive operational flags and duration metrics
    try:
        clean_df = build_feature_pipeline(df)
        return True, [], clean_df
    except Exception as e:
        return False, [f"Error processing feature pipeline: {str(e)}"], None
