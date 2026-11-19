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
    Seed initial historical calibration records from late September matching
    ground-truth ticket records in tickets_clean.csv if table is empty or contains legacy data.
    Pre-seeds demo audit trail to demonstrate override tracking and audit logging on first launch.
    """
    init_override_db(db_path)
    conn = _get_connection(db_path)
    try:
        # Check if legacy seed data exists and purge to refresh with canonical tickets
        try:
            legacy_check = conn.cursor().execute(
                "SELECT COUNT(*) FROM escalation_decisions WHERE ticket_id = 'SUP-11204' AND agent_id = 'Rahul T'"
            ).fetchone()[0]
            if legacy_check > 0:
                conn.cursor().execute("DELETE FROM escalation_decisions")
                conn.commit()
        except Exception:
            pass

        count = conn.cursor().execute("SELECT COUNT(*) FROM escalation_decisions").fetchone()[0]
        if count > 0:
            return
    finally:
        conn.close()

    # Grounded in actual records from tickets_clean.csv
    samples = [
        ("SUP-11204", "Karan B", "Live tracking / GPS incorrect", "P4", "Enterprise", 0.86,
         "Gate Activated: L1 Troubleshooting Required", "Resolved at L1", 0,
         "", "2026-09-18T15:41:00", "Clean Close"),
        ("SUP-11218", "Ananya R", "Report export failing", "P3", "Mid-market", 0.92,
         "Gate Activated: L1 Troubleshooting Required", "Escalated to Tier 3 Eng", 1,
         "Client insisted on immediate engineering ticket for board pack.", "2026-09-19T11:20:00", "Insufficient info - returned to L1"),
        ("SUP-11225", "Neha P", "OTP / boarding issue", "P4", "Enterprise", 0.90,
         "Gate Activated: L1 Troubleshooting Required", "Resolved at L1", 0,
         "", "2026-09-19T14:15:00", "Clean Close"),
        ("SUP-11240", "Neha P", "Driver / vehicle compliance docs", "P4", "Enterprise", 0.91,
         "Gate Activated: L1 Troubleshooting Required", "Resolved at L1", 0,
         "", "2026-09-20T09:30:00", "Clean Close"),
        ("SUP-11252", "Karan B", "Login / access issue", "P2", "Mid-market", 0.92,
         "Gate Activated: L1 Troubleshooting Required", "Resolved at L1", 0,
         "", "2026-09-21T10:45:00", "Clean Close"),
        ("SUP-11267", "Priya D", "OTP / boarding issue", "P2", "Enterprise", 0.84,
         "Gate Activated: L1 Troubleshooting Required", "Escalated to Tier 3 Eng", 1,
         "Shift supervisor reported multiple drivers unable to generate OTP at hub.", "2026-09-21T16:10:00", "Fixed"),
        ("SUP-11280", "Sneha M", "Login / access issue", "P4", "SMB", 0.93,
         "Gate Activated: L1 Troubleshooting Required", "Resolved at L1", 0,
         "", "2026-09-22T11:00:00", "Clean Close"),
        ("SUP-11295", "Karan B", "Roster / booking not syncing", "P4", "Mid-market", 0.81,
         "Gate Passed: Engineering Escalation Approved", "Resolved at L1", 0,
         "", "2026-09-23T13:20:00", "Clean Close"),
        ("SUP-11308", "Neha P", "Billing / invoice discrepancy", "P4", "Enterprise", 0.94,
         "Gate Activated: L1 Troubleshooting Required", "Resolved at L1", 0,
         "", "2026-09-24T09:15:00", "Clean Close"),
        ("SUP-11322", "Vikram S", "Roster / booking not syncing", "P3", "Enterprise", 0.68,
         "Gate Passed: Engineering Escalation Approved", "Resolved at L1", 0,
         "", "2026-09-24T15:40:00", "Clean Close"),
        ("SUP-11335", "Arjun K", "Report export failing", "P4", "Mid-market", 0.91,
         "Gate Activated: L1 Troubleshooting Required", "Escalated to Tier 3 Eng", 1,
         "Admin reported 504 gateway timeout on monthly export.", "2026-09-25T10:30:00", "Config issue - returned to L1"),
        ("SUP-11350", "Vikram S", "Roster / booking not syncing", "P4", "Enterprise", 0.58,
         "Gate Passed: Engineering Escalation Approved", "Escalated to Tier 3 Eng", 0,
         "", "2026-09-26T14:00:00", "Fixed")
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
