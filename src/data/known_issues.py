"""
Known Issues Management Module (Section 5)
Maintains a structured registry of active platform defects, workarounds,
and engineering references to intercept duplicate escalations before engineering handoff.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd

from src.config import PROJECT_ROOT

KNOWN_ISSUES_PATH = PROJECT_ROOT / "data" / "known_issues.csv"


def load_known_issues(path: Optional[Path] = None) -> pd.DataFrame:
    """Load known issues registry."""
    csv_file = Path(path) if path else KNOWN_ISSUES_PATH
    if not csv_file.exists():
        return pd.DataFrame(columns=[
            "issue_id", "issue_title", "category", "description",
            "status", "workaround", "eng_reference", "created_at"
        ])
    return pd.read_csv(csv_file)


def search_known_issues(
    query: str = "",
    category: str = "",
    issues_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Search known issues by free-text keywords, category, or issue ID.
    """
    df = issues_df if issues_df is not None else load_known_issues()
    if df.empty:
        return df

    filtered = df.copy()

    if category and category.strip():
        cat_lower = category.strip().lower()
        filtered = filtered[filtered["category"].str.lower() == cat_lower]

    if query and query.strip():
        q = query.strip().lower()
        match_mask = (
            filtered["issue_id"].str.lower().str.contains(q, na=False) |
            filtered["issue_title"].str.lower().str.contains(q, na=False) |
            filtered["description"].str.lower().str.contains(q, na=False) |
            filtered["workaround"].str.lower().str.contains(q, na=False) |
            filtered["eng_reference"].str.lower().str.contains(q, na=False)
        )
        filtered = filtered[match_mask]

    return filtered


def get_known_issue_by_id(
    issue_id: str,
    issues_df: Optional[pd.DataFrame] = None
) -> Optional[Dict[str, Any]]:
    """Fetch single known issue by ID."""
    df = issues_df if issues_df is not None else load_known_issues()
    match = df[df["issue_id"].str.upper() == issue_id.strip().upper()]
    if not match.empty:
        return match.iloc[0].to_dict()
    return None
