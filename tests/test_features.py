"""
Unit tests for feature engineering, operational flags, durations, and repeat contacts (Section B).
"""

import unittest
import pandas as pd
import numpy as np

from src.features.durations import compute_durations, compute_duration_metrics
from src.features.flags import compute_operational_flags
from src.features.calendar import compute_calendar_features
from src.features.repeat_contacts import compute_repeat_contacts
from src.features.pipeline import build_feature_pipeline


class TestFeatures(unittest.TestCase):

    def setUp(self):
        self.sample_df = pd.DataFrame({
            "ticket_id": [1, 2, 3, 4],
            "client_id": ["C100", "C100", "C200", "C100"],
            "client_name": ["Acme", "Acme", "Beta", "Acme"],
            "client_tier": ["Enterprise", "Enterprise", "Mid-Market", "Enterprise"],
            "category": ["Billing", "Billing", "App Bug", "Billing"],
            "status": ["Closed", "Closed", "Open", "Closed"],
            "created_at": pd.to_datetime([
                "2026-07-05 10:00:00",
                "2026-07-10 12:00:00",  # 5.08 days after ticket 1 -> Repeat contact!
                "2026-07-12 09:00:00",
                "2026-08-01 14:00:00"   # 22 days after ticket 2 -> NOT a repeat contact
            ]),
            "first_response_at": pd.to_datetime([
                "2026-07-05 11:30:00",  # 1.5h
                "2026-07-10 13:00:00",  # 1.0h
                np.nan,
                "2026-08-01 15:00:00"   # 1.0h
            ]),
            "first_closed_at": pd.to_datetime([
                "2026-07-05 16:00:00",  # 6.0h
                "2026-07-11 12:00:00",  # 24.0h
                np.nan,
                "2026-08-02 14:00:00"   # 24.0h
            ]),
            "final_closed_at": pd.to_datetime([
                "2026-07-05 16:00:00",  # 6.0h
                "2026-07-12 12:00:00",  # 48.0h (reopened!)
                np.nan,
                "2026-08-02 14:00:00"
            ]),
            "reopen_count": [0, 1, 0, 0],
            "escalated_to_eng": ["No", "Yes", "No", "Yes"],
            "eng_handoffs": [0, 2, 0, 1],
            "eng_outcome": [np.nan, "Config issue - returned to L1", np.nan, "Fixed"]
        })

    def test_compute_duration_metrics(self):
        df_dur = compute_duration_metrics(self.sample_df)
        self.assertAlmostEqual(df_dur.loc[0, "hrs_to_first_response"], 1.5, places=2)
        self.assertAlmostEqual(df_dur.loc[0, "hrs_to_first_close"], 6.0, places=2)
        self.assertAlmostEqual(df_dur.loc[0, "hrs_to_final_close"], 6.0, places=2)
        self.assertAlmostEqual(df_dur.loc[0, "resolution_hrs"], 6.0, places=2)

        # Reopened ticket final close is 48.0 hrs
        self.assertAlmostEqual(df_dur.loc[1, "resolution_hrs"], 48.0, places=2)

        # Open ticket has NaN duration metrics
        self.assertTrue(pd.isna(df_dur.loc[2, "resolution_hrs"]))

    def test_compute_operational_flags(self):
        df_flags = compute_operational_flags(self.sample_df)
        self.assertEqual(list(df_flags["is_escalated"]), [0, 1, 0, 1])
        # Ticket 1: non-escalated -> 0
        # Ticket 2: Config issue -> avoidable (1) and returned to L1 (1)
        # Ticket 3: non-escalated -> 0
        # Ticket 4: Fixed -> legitimate fix (0)
        self.assertEqual(list(df_flags["is_avoidable_esc"]), [0, 1, 0, 0])
        self.assertEqual(list(df_flags["is_returned_to_l1"]), [0, 1, 0, 0])
        self.assertEqual(list(df_flags["is_reopened"]), [0, 1, 0, 0])
        # FCR: closed, not escalated, not reopened
        self.assertEqual(list(df_flags["is_fcr"]), [1, 0, 0, 0])

    def test_compute_calendar_features(self):
        df_cal = compute_calendar_features(self.sample_df)
        self.assertIn("week_start", df_cal.columns)
        self.assertIn("month", df_cal.columns)
        self.assertIn("hour_of_day", df_cal.columns)
        self.assertIn("weekday", df_cal.columns)
        self.assertIn("is_open", df_cal.columns)
        self.assertIn("open_age_hrs", df_cal.columns)

        self.assertEqual(df_cal.loc[0, "month"], "2026-07")
        self.assertEqual(df_cal.loc[0, "hour_of_day"], 10)
        self.assertEqual(df_cal.loc[2, "is_open"], 1)
        self.assertEqual(df_cal.loc[0, "is_open"], 0)
        self.assertGreater(df_cal.loc[2, "open_age_hrs"], 0)

    def test_compute_repeat_contacts(self):
        df_rep = compute_repeat_contacts(self.sample_df)
        # Ticket 0: First ticket for C100 Billing -> 0
        # Ticket 1: C100 Billing ~5 days later -> 1 (repeat!)
        # Ticket 2: C200 App Bug -> 0
        # Ticket 3: C100 Billing 22 days later (> 14 days) -> 0
        self.assertEqual(df_rep.loc[0, "is_repeat_contact"], 0)
        self.assertEqual(df_rep.loc[1, "is_repeat_contact"], 1)
        self.assertEqual(df_rep.loc[2, "is_repeat_contact"], 0)
        self.assertEqual(df_rep.loc[3, "is_repeat_contact"], 0)

    def test_build_feature_pipeline(self):
        df_pipe = build_feature_pipeline(self.sample_df)
        expected_cols = [
            "hrs_to_first_response", "resolution_hrs", "is_escalated",
            "is_avoidable_esc", "is_reopened", "is_fcr", "is_repeat_contact"
        ]
        for col in expected_cols:
            self.assertIn(col, df_pipe.columns)


if __name__ == "__main__":
    unittest.main()
