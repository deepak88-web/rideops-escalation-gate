"""
Unit tests for operations analysis modules (Sections C through H).
"""

import unittest
import pandas as pd
import numpy as np

from src.analysis.volume_backlog import compute_weekly_volume_and_backlog, compute_monthly_volume_clients
from src.analysis.speed import compute_first_response_speed, compute_first_response_sla, compute_open_backlog_age_bands
from src.analysis.escalation import compute_escalation_by_category, compute_escalation_quality_kpis, compute_duplicate_issues_by_category
from src.analysis.quality_csat import compute_reopen_by_category, compute_first_contact_resolution
from src.analysis.agent_benchmarks import compute_agent_scorecard
from src.analysis.repeat_trends import compute_repeat_contacts_by_month


class TestAnalysis(unittest.TestCase):

    def setUp(self):
        # 6-ticket fixture spanning 2 agents, 2 categories, and various states
        self.df = pd.DataFrame({
            "ticket_id": [1, 2, 3, 4, 5, 6],
            "client_id": ["C1", "C1", "C2", "C2", "C3", "C4"],
            "client_name": ["A", "A", "B", "B", "C", "D"],
            "client_tier": ["Enterprise"] * 6,
            "channel": ["Email"] * 6,
            "category": ["Billing", "Billing", "Billing", "App Bug", "App Bug", "App Bug"],
            "priority": ["P1", "P1", "P2", "P2", "P3", "P4"],
            "assigned_agent": ["Rahul T", "Rahul T", "Karan B", "Karan B", "Karan B", "Sarah M"],
            "status": ["Closed", "Closed", "Closed", "Closed", "Closed", "Open"],
            "created_at": pd.to_datetime([
                "2026-07-06 09:00:00",
                "2026-07-08 10:00:00",
                "2026-07-15 11:00:00",
                "2026-08-01 12:00:00",
                "2026-09-01 13:00:00",
                "2026-09-29 14:00:00"
            ]),
            "first_response_at": pd.to_datetime([
                "2026-07-06 09:30:00",  # 0.5h (P1 SLA target: 1h -> met)
                "2026-07-08 11:30:00",  # 1.5h (P1 SLA target: 1h -> missed)
                "2026-07-15 12:00:00",  # 1.0h
                "2026-08-01 14:00:00",  # 2.0h
                "2026-09-01 16:00:00",  # 3.0h
                np.nan
            ]),
            "final_closed_at": pd.to_datetime([
                "2026-07-06 13:00:00",  # 4h
                "2026-07-08 15:00:00",  # 5h
                "2026-07-15 21:00:00",  # 10h
                "2026-08-01 22:00:00",  # 10h
                "2026-09-01 23:00:00",  # 10h
                np.nan
            ]),
            "hrs_to_first_response": [0.5, 1.5, 1.0, 2.0, 3.0, np.nan],
            "resolution_hrs": [4.0, 5.0, 10.0, 10.0, 10.0, np.nan],
            "escalated_to_eng": ["Yes", "Yes", "No", "No", "No", "No"],
            "is_escalated": [1, 1, 0, 0, 0, 0],
            "eng_handoffs": [1, 2, 0, 0, 0, 0],
            "eng_outcome": ["Fixed", "Duplicate of known issue", np.nan, np.nan, np.nan, np.nan],
            "is_avoidable_esc": [0, 1, 0, 0, 0, 0],
            "is_returned_to_l1": [0, 0, 0, 0, 0, 0],
            "reopen_count": [0, 0, 1, 1, 0, 0],
            "is_reopened": [0, 0, 1, 1, 0, 0],
            "is_fcr": [0, 0, 0, 0, 1, 0],
            "csat_score": [5.0, 3.0, 4.0, 2.0, 5.0, np.nan],
            "month": ["2026-07", "2026-07", "2026-07", "2026-08", "2026-09", "2026-09"],
            "is_open": [0, 0, 0, 0, 0, 1],
            "open_age_hrs": [np.nan, np.nan, np.nan, np.nan, np.nan, 34.0],
            "is_repeat_contact": [0, 1, 0, 0, 0, 0]
        })

    def test_volume_and_backlog(self):
        weekly = compute_weekly_volume_and_backlog(self.df)
        self.assertGreater(len(weekly), 0)
        self.assertIn("created", weekly.columns)
        self.assertIn("closed", weekly.columns)
        self.assertIn("net_backlog", weekly.columns)
        self.assertEqual(weekly["created"].sum(), 6)
        self.assertEqual(weekly["closed"].sum(), 5)

    def test_speed_metrics(self):
        frt = compute_first_response_speed(self.df)
        self.assertIn("Overall", frt.index)
        self.assertIn("median_hrs", frt.columns)

        sla = compute_first_response_sla(self.df)
        # In P1: 2 responded, 1 within 1.0h -> 50%
        self.assertEqual(sla.loc["P1", "sla_attainment_pct"], 50.0)

        age = compute_open_backlog_age_bands(self.df)
        # Ticket 6 is open with age 34h (>24h is 1, >48h is 0)
        self.assertEqual(age.loc[age["age_band"] == "Open > 24 hours", "open_tickets"].values[0], 1)
        self.assertEqual(age.loc[age["age_band"] == "Open > 48 hours", "open_tickets"].values[0], 0)

    def test_escalation_metrics(self):
        kpis = compute_escalation_quality_kpis(self.df)
        self.assertEqual(kpis["total_escalated"], 2)
        # 1 avoidable out of 2 escalated -> 50%
        self.assertEqual(kpis["avoidable_esc_rate_pct"], 50.0)
        # Average handoffs: (1 + 2) / 2 = 1.5
        self.assertEqual(kpis["avg_handoffs_per_escalated"], 1.5)

        dups = compute_duplicate_issues_by_category(self.df)
        self.assertIn("duplicate_count", dups.columns)
        self.assertEqual(dups.loc["Billing", "duplicate_count"], 1)

    def test_agent_scorecard(self):
        card = compute_agent_scorecard(self.df)
        self.assertIn("assigned_agent", card.columns)
        self.assertIn("actual_vs_expected_ratio", card.columns)
        # Rahul T has 2 tickets, both escalated -> 100%
        rahul_row = card[card["assigned_agent"] == "Rahul T"].iloc[0]
        self.assertEqual(rahul_row["actual_esc_rate"], 100.0)
        # Karan B has 3 tickets, 0 escalated -> 0%
        karan_row = card[card["assigned_agent"] == "Karan B"].iloc[0]
        self.assertEqual(karan_row["actual_esc_rate"], 0.0)
        # Karan check: reopen rate is 2/3 = 66.67%
        self.assertAlmostEqual(karan_row["reopen_rate"], 66.67, places=1)


if __name__ == "__main__":
    unittest.main()
