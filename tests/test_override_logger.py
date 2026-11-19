"""
Unit Tests for Persistent Override Logger (Phase 7)
"""

import unittest
import tempfile
from pathlib import Path
import sqlite3
import pandas as pd

from src.logging.override_logger import (
    init_override_db,
    log_escalation_decision,
    get_logged_decisions,
    compute_override_metrics,
    seed_sample_overrides_if_empty
)


class TestOverrideLogger(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_overrides.db"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_init_override_db(self):
        init_override_db(self.db_path)
        self.assertTrue(self.db_path.exists())
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='escalation_decisions';")
            self.assertIsNotNone(cursor.fetchone())
        finally:
            conn.close()

    def test_log_and_retrieve_decision(self):
        rec_id = log_escalation_decision(
            ticket_id="SUP-99999",
            agent_id="Rahul T",
            category="Report export failing",
            priority="P2",
            client_tier="Enterprise",
            predicted_probability=0.88,
            model_recommendation="Gate Activated: L1 Guidance Required",
            actual_decision="Escalated to Tier 3 Eng (Manager Override)",
            is_override=True,
            override_reason="Client VP requested immediate investigation",
            db_path=self.db_path
        )
        self.assertGreater(rec_id, 0)

        df = get_logged_decisions(db_path=self.db_path)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["ticket_id"], "SUP-99999")
        self.assertEqual(df.iloc[0]["is_override"], 1)
        self.assertEqual(df.iloc[0]["override_reason"], "Client VP requested immediate investigation")

    def test_compute_override_metrics(self):
        # 1 standard agree decision
        log_escalation_decision(
            ticket_id="SUP-1", agent_id="Sneha M", category="Login / access issue",
            priority="P3", client_tier="SMB", predicted_probability=0.95,
            model_recommendation="Gate Activated", actual_decision="Resolved at L1",
            is_override=False, db_path=self.db_path
        )
        # 1 override decision
        log_escalation_decision(
            ticket_id="SUP-2", agent_id="Rahul T", category="Report export failing",
            priority="P2", client_tier="Enterprise", predicted_probability=0.85,
            model_recommendation="Gate Activated", actual_decision="Escalated to Eng",
            is_override=True, override_reason="Customer VIP", db_path=self.db_path
        )

        metrics = compute_override_metrics(self.db_path)
        self.assertEqual(metrics["total_decisions"], 2)
        self.assertEqual(metrics["total_overrides"], 1)
        self.assertAlmostEqual(metrics["override_rate"], 0.5)
        self.assertAlmostEqual(metrics["agreement_rate"], 0.5)

    def test_seed_sample_overrides(self):
        seed_sample_overrides_if_empty(self.db_path)
        df = get_logged_decisions(db_path=self.db_path)
        self.assertGreaterEqual(len(df), 10)
        rec_11204 = df[df["ticket_id"] == "SUP-11204"]
        self.assertEqual(len(rec_11204), 1)
        self.assertEqual(rec_11204.iloc[0]["agent_id"], "Karan B")
        self.assertEqual(rec_11204.iloc[0]["category"], "Live tracking / GPS incorrect")


if __name__ == "__main__":
    unittest.main()
