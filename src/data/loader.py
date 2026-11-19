"""
Data Ingestion and Schema Preprocessing Module
"""

from pathlib import Path
from typing import Optional, List
import pandas as pd
from src.config import RAW_DATA_PATH


def load_raw_tickets(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load raw ticket dataset from CSV, parse timestamp columns, and strip strings.
    """
    file_path = path or RAW_DATA_PATH
    if not file_path.exists():
        raise FileNotFoundError(f"Raw ticket dataset not found at: {file_path}")

    df = pd.read_csv(file_path)

    # Parse timestamps
    dt_cols = ["created_at", "first_response_at", "first_closed_at", "final_closed_at"]
    for col in dt_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Strip accidental whitespace on string columns
    str_cols = [
        "ticket_id", "channel", "client_id", "client_name", "client_tier",
        "category", "priority", "description", "assigned_agent",
        "escalated_to_eng", "eng_ticket_id", "eng_outcome", "status"
    ]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].where(df[col].isna(), df[col].astype(str).str.strip())

    return df
