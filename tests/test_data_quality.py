"""
Unit tests for data quality and ingestion validation (Section A).
"""

import unittest
import pandas as pd
import numpy as np

from src.data.quality import (
    check_duplicate_tickets,
    check_null_counts,
    validate_timestamps,
    validate_escalation_consistency,
    flag_partial_weeks,
)


class TestDataQuality(unittest.TestCase):

    def setUp(self):
        # Create a clean synthetic dataset fixture
        self.clean_df = pd.DataFrame({
            "ticket_id": [101, 102, 103],
            "client_id": ["C1", "C2", "C3"],
            "created_at": pd.to_datetime(["2026-07-10 10:00:00", "2026-07-11 11:00:00", "2026-07-12 12:00:00"]),
            "first_response_at": pd.to_datetime(["2026-07-10 10:30:00", "2026-07-11 11:15:00", "2026-07-12 12:45:00"]),
            "first_closed_at": pd.to_datetime(["2026-07-10 14:00:00", "2026-07-11 15:00:00", "2026-07-12 16:00:00"]),
            "final_closed_at": pd.to_datetime(["2026-07-10 14:00:00", "2026-07-11 15:00:00", "2026-07-12 16:00:00"]),
            "escalated_to_eng": ["No", "Yes", "No"],
            "eng_handoffs": [0, 1, 0],
            "eng_outcome": [np.nan, "Fixed", np.nan]
        })

    def test_duplicate_check_clean(self):
        result = check_duplicate_tickets(self.clean_df)
        self.assertEqual(result["status"], "PASSED")
        self.assertEqual(result["duplicate_count"], 0)

    def test_duplicate_check_detected(self):
        dirty_df = pd.concat([self.clean_df, self.clean_df.iloc[[0]]], ignore_index=True)
        result = check_duplicate_tickets(dirty_df)
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["duplicate_count"], 1)

    def test_check_null_counts(self):
        expected = {"first_response_at": 0, "eng_outcome": 2}
        report = check_null_counts(self.clean_df, expected_nulls=expected)
        self.assertEqual(report.loc["first_response_at", "null_count"], 0)
        self.assertEqual(report.loc["eng_outcome", "null_count"], 2)
        self.assertTrue(report.loc["eng_outcome", "matches_expected"])

    def test_validate_timestamps_clean(self):
        result = validate_timestamps(self.clean_df)
        self.assertEqual(result["status"], "PASSED")
        self.assertEqual(result["total_violations"], 0)

    def test_validate_timestamps_impossible(self):
        # Case 1: First response before creation
        bad_df = self.clean_df.copy()
        bad_df.loc[0, "first_response_at"] = pd.Timestamp("2026-07-10 09:00:00")
        result = validate_timestamps(bad_df)
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["details"]["response_before_creation"], 1)

        # Case 2: Final close before first close
        bad_df2 = self.clean_df.copy()
        bad_df2.loc[1, "final_closed_at"] = pd.Timestamp("2026-07-11 13:00:00")
        result2 = validate_timestamps(bad_df2)
        self.assertEqual(result2["status"], "FAILED")
        self.assertEqual(result2["details"]["final_close_before_first_close"], 1)

    def test_validate_escalation_consistency_clean(self):
        result = validate_escalation_consistency(self.clean_df)
        self.assertEqual(result["status"], "PASSED")
        self.assertEqual(result["inconsistent_rows_count"], 0)
        self.assertEqual(result["escalated_count"], 1)
        self.assertEqual(result["non_escalated_count"], 2)

    def test_validate_escalation_consistency_violation(self):
        # Escalated Yes but 0 handoffs and missing outcome
        bad_df = self.clean_df.copy()
        bad_df.loc[0, "escalated_to_eng"] = "Yes"
        result = validate_escalation_consistency(bad_df)
        self.assertEqual(result["status"], "WARNING")
        self.assertGreater(result["inconsistent_rows_count"], 0)

    def test_flag_partial_weeks(self):
        test_df = pd.DataFrame({
            "created_at": pd.to_datetime(["2026-07-02 10:00:00", "2026-07-15 10:00:00", "2026-09-29 10:00:00"])
        })
        flagged = flag_partial_weeks(test_df)
        self.assertIn("is_partial_week", flagged.columns)
        # 2026-07-02 is in partial week 2026-06-29; 2026-09-29 is in partial week 2026-09-28
        self.assertEqual(flagged.loc[0, "is_partial_week"], 1)
        self.assertEqual(flagged.loc[1, "is_partial_week"], 0)
        self.assertEqual(flagged.loc[2, "is_partial_week"], 1)


if __name__ == "__main__":
    unittest.main()
