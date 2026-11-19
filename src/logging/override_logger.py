"""
Persistent SQLite Override & Decision Logging Module (Phase 7)
Tracks every agent escalation decision, gate recommendation, manager override,
and downstream operational outcome to quantify human agreement and model impact.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
import sqlite3
from datetime import datetime
import pandas as pd

from src.config import OVERRIDE_DB_PATH


def _get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Obtain SQLite connection and ensure parent directory exists."""
    path = Path(db_path) if db_path else OVERRIDE_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_override_db(db_path: Optional[Path] = None) -> None:
    """Initialize SQLite database table for escalation decisions and overrides."""
    conn = _get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS escalation_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    category TEXT,
                    priority TEXT,
                    client_tier TEXT,
                    predicted_probability REAL,
                    model_recommendation TEXT NOT NULL,
                    actual_decision TEXT NOT NULL,
                    is_override INTEGER NOT NULL DEFAULT 0,
                    override_reason TEXT,
                    created_at TEXT NOT NULL,
                    final_outcome TEXT,
                    known_issue_id TEXT
                );
            """)
            try:
                cursor.execute("ALTER TABLE escalation_decisions ADD COLUMN known_issue_id TEXT;")
            except Exception:
                pass
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_agent ON escalation_decisions (agent_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_created ON escalation_decisions (created_at);")
    finally:
        conn.close()


def log_escalation_decision(
    ticket_id: str,
    agent_id: str,
    category: str,
    priority: str,
    client_tier: str,
    predicted_probability: float,
    model_recommendation: str,
    actual_decision: str,
    is_override: bool,
    override_reason: str = "",
    final_outcome: Optional[str] = None,
    known_issue_id: Optional[str] = None,
    created_at: Optional[str] = None,
    db_path: Optional[Path] = None
) -> int:
    """
    Log an agent's escalation decision to SQLite.
    Returns inserted decision record ID.
    """
    init_override_db(db_path)
    if created_at is None:
        created_at = datetime.now().isoformat()

    conn = _get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO escalation_decisions (
                    ticket_id, agent_id, category, priority, client_tier,
                    predicted_probability, model_recommendation, actual_decision,
                    is_override, override_reason, created_at, final_outcome, known_issue_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                str(ticket_id).strip(),
                str(agent_id).strip(),
                str(category).strip(),
                str(priority).strip(),
                str(client_tier).strip(),
                float(predicted_probability),
                str(model_recommendation).strip(),
                str(actual_decision).strip(),
                int(bool(is_override)),
                str(override_reason).strip(),
                str(created_at).strip(),
                str(final_outcome).strip() if final_outcome else None,
                str(known_issue_id).strip() if known_issue_id else None
            ))
            last_id = cursor.lastrowid
    finally:
        conn.close()
    return last_id


def get_logged_decisions(
    db_path: Optional[Path] = None,
    limit: int = 100
) -> pd.DataFrame:
    """Fetch recent escalation decisions and overrides as a DataFrame."""
    init_override_db(db_path)
    conn = _get_connection(db_path)
    try:
        query = "SELECT * FROM escalation_decisions ORDER BY id DESC"
        if limit > 0:
            query += f" LIMIT {int(limit)}"
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    return df


def compute_override_metrics(db_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Compute operational metrics on model recommendation agreement, override rates,
    and agent compliance.
    """
    df = get_logged_decisions(db_path=db_path, limit=0)
    if df.empty:
        return {
            "total_decisions": 0,
            "total_overrides": 0,
            "override_rate": 0.0,
            "agreement_rate": 1.0,
            "overrides_by_agent": pd.DataFrame(),
            "overrides_by_category": pd.DataFrame()
        }

    total = len(df)
    overrides = int((df["is_override"] == 1).sum())
    override_rate = (overrides / total) if total > 0 else 0.0
    agreement_rate = 1.0 - override_rate

    by_agent = df.groupby("agent_id").agg(
        total_decisions=("id", "count"),
        override_count=("is_override", "sum")
    ).reset_index()
    by_agent["override_rate"] = (by_agent["override_count"] / by_agent["total_decisions"]) * 100

    by_cat = df.groupby("category").agg(
        total_decisions=("id", "count"),
        override_count=("is_override", "sum")
    ).reset_index()
    by_cat["override_rate"] = (by_cat["override_count"] / by_cat["total_decisions"]) * 100

    return {
        "total_decisions": total,
        "total_overrides": overrides,
        "override_rate": override_rate,
        "agreement_rate": agreement_rate,
        "overrides_by_agent": by_agent,
        "overrides_by_category": by_cat
    }


def seed_sample_overrides_if_empty(db_path: Optional[Path] = None) -> None:
    """
    Seed initial historical decision records from late September if table is empty.
    Allows operations leads to inspect real-world override distribution on first launch.
    """
    init_override_db(db_path)
    conn = _get_connection(db_path)
    try:
        count = conn.cursor().execute("SELECT COUNT(*) FROM escalation_decisions").fetchone()[0]
        if count > 0:
            return
    finally:
        conn.close()

    samples = [
        ("SUP-11204", "Rahul T", "Report export failing", "P2", "Mid-market", 0.92,
         "Gate Activated: L1 Troubleshooting Required", "Escalated to Tier 3 Eng", 1,
         "Client escalated via Account Manager; insisted on engineering ticket.", "2026-09-24T10:15:00", "Duplicate of known issue"),
        ("SUP-11218", "Karan B", "Live tracking / GPS incorrect", "P1", "Enterprise", 0.88,
         "Gate Activated: L1 Troubleshooting Required", "Escalated to Tier 3 Eng", 1,
         "Driver app GPS stream dropped for VIP airport convoy.", "2026-09-25T08:30:00", "Config issue - returned to L1"),
        ("SUP-11225", "Sneha M", "Login / access issue", "P3", "SMB", 0.94,
         "Gate Activated: L1 Troubleshooting Required", "Resolved at L1", 0,
         "", "2026-09-25T11:45:00", "Clean Close"),
        ("SUP-11240", "Rahul T", "Roster / booking not syncing", "P2", "Enterprise", 0.86,
         "Gate Activated: L1 Troubleshooting Required", "Escalated to Tier 3 Eng", 1,
         "Bulk shift roster failing 500 error on upload.", "2026-09-26T14:20:00", "Fixed"),
        ("SUP-11252", "Vikram S", "OTP / boarding issue", "P1", "Enterprise", 0.35,
         "Gate Passed: Engineering Escalation Approved", "Escalated to Tier 3 Eng", 0,
         "", "2026-09-26T18:10:00", "Fixed"),
        ("SUP-11267", "Ananya R", "Billing / invoice discrepancy", "P2", "Mid-market", 0.91,
         "Gate Activated: L1 Troubleshooting Required", "Resolved at L1", 0,
         "", "2026-09-27T09:40:00", "Clean Close"),
        ("SUP-11280", "Arjun K", "Driver / vehicle compliance docs", "P3", "SMB", 0.95,
         "Gate Activated: L1 Troubleshooting Required", "Resolved at L1", 0,
         "", "2026-09-27T16:00:00", "Clean Close"),
        ("SUP-11295", "Karan B", "Report export failing", "P2", "Enterprise", 0.89,
         "Gate Activated: L1 Troubleshooting Required", "Escalated to Tier 3 Eng", 1,
         "CFO dashboard export required for quarterly board pack.", "2026-09-28T11:05:00", "Duplicate of known issue"),
        ("SUP-11308", "Neha P", "Cab delay / no-show complaint", "P2", "Mid-market", 0.93,
         "Gate Activated: L1 Troubleshooting Required", "Resolved at L1", 0,
         "", "2026-09-28T15:25:00", "Clean Close"),
        ("SUP-11322", "Priya D", "How-to / feature request", "P4", "SMB", 0.97,
         "Gate Activated: L1 Troubleshooting Required", "Resolved at L1", 0,
         "", "2026-09-29T10:50:00", "Clean Close"),
        ("SUP-11335", "Rahul T", "Live tracking / GPS incorrect", "P2", "Enterprise", 0.87,
         "Gate Activated: L1 Troubleshooting Required", "Escalated to Tier 3 Eng", 1,
         "Client ops room unable to view 14 vehicles simultaneously.", "2026-09-29T13:40:00", "Insufficient info - returned to L1"),
        ("SUP-11350", "Sneha M", "Employee address / geocode change", "P3", "Enterprise", 0.96,
         "Gate Activated: L1 Troubleshooting Required", "Resolved at L1", 0,
         "", "2026-09-30T09:15:00", "Clean Close")
    ]

    for item in samples:
        log_escalation_decision(
            ticket_id=item[0],
            agent_id=item[1],
            category=item[2],
            priority=item[3],
            client_tier=item[4],
            predicted_probability=item[5],
            model_recommendation=item[6],
            actual_decision=item[7],
            is_override=bool(item[8]),
            override_reason=item[9],
            created_at=item[10],
            final_outcome=item[11],
            db_path=db_path
        )
