"""
Unit Tests for Known Issues Registry and Upload Validator (Sections 5 & 6)
"""

import unittest
import io
import pandas as pd

from src.data.known_issues import load_known_issues, search_known_issues, get_known_issue_by_id
from src.data.upload_validator import validate_uploaded_tickets_csv, REQUIRED_COLUMNS


class TestKnownIssuesAndUpload(unittest.TestCase):

    def test_load_known_issues(self):
        df = load_known_issues()
        self.assertFalse(df.empty)
        self.assertIn("issue_id", df.columns)
        self.assertIn("eng_reference", df.columns)

    def test_search_known_issues_by_category(self):
        results = search_known_issues(category="Report export failing")
        self.assertFalse(results.empty)
        self.assertTrue((results["category"] == "Report export failing").all())

    def test_search_known_issues_by_query(self):
        results = search_known_issues(query="ENG-402")
        self.assertEqual(len(results), 1)
        self.assertEqual(results.iloc[0]["issue_id"], "ISS-101")

    def test_get_known_issue_by_id(self):
        issue = get_known_issue_by_id("ISS-101")
        self.assertIsNotNone(issue)
        self.assertEqual(issue["eng_reference"], "ENG-402")

        missing = get_known_issue_by_id("NONEXISTENT")
        self.assertIsNone(missing)

    def test_validate_uploaded_tickets_csv_valid(self):
        # Create a valid minimal dataframe with required columns
        valid_df = pd.DataFrame([{
            "ticket_id": "SUP-TEST-1",
            "created_at": "2026-09-01 10:00:00",
            "channel": "Email",
            "client_id": "CLI-101",
            "client_name": "Test Client",
            "client_tier": "Enterprise",
            "category": "Report export failing",
            "priority": "P2",
            "description": "Test report failure",
            "assigned_agent": "Rahul T",
            "first_response_at": "2026-09-01 10:30:00",
            "first_closed_at": "2026-09-01 12:00:00",
            "final_closed_at": "2026-09-01 12:00:00",
            "escalated_to_eng": 0,
            "status": "Closed",
            "reopen_count": 0,
            "eng_handoffs": 0,
            "csat_score": 4.0
        }])
        is_valid, errors, clean_df = validate_uploaded_tickets_csv(valid_df)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        self.assertIsNotNone(clean_df)
        self.assertIn("resolution_hrs", clean_df.columns)

    def test_validate_uploaded_tickets_csv_missing_column(self):
        # Missing 'status' column
        bad_df = pd.DataFrame([{
            "ticket_id": "SUP-TEST-2",
            "created_at": "2026-09-01 10:00:00",
            "category": "App Bug"
        }])
        is_valid, errors, clean_df = validate_uploaded_tickets_csv(bad_df)
        self.assertFalse(is_valid)
        self.assertTrue(any("Missing required columns" in e for e in errors))
        self.assertIsNone(clean_df)

    def test_validate_uploaded_tickets_csv_duplicate_id(self):
        dup_df = pd.DataFrame([
            {
                "ticket_id": "SUP-DUP", "created_at": "2026-09-01 10:00:00", "channel": "Email",
                "client_id": "CLI-1", "client_name": "Client", "client_tier": "SMB",
                "category": "How-to / feature request", "priority": "P4", "description": "Help",
                "assigned_agent": "Priya D", "first_response_at": "2026-09-01 11:00:00",
                "escalated_to_eng": 0, "status": "Closed"
            },
            {
                "ticket_id": "SUP-DUP", "created_at": "2026-09-01 12:00:00", "channel": "Email",
                "client_id": "CLI-1", "client_name": "Client", "client_tier": "SMB",
                "category": "How-to / feature request", "priority": "P4", "description": "Help again",
                "assigned_agent": "Priya D", "first_response_at": "2026-09-01 12:30:00",
                "escalated_to_eng": 0, "status": "Closed"
            }
        ])
        is_valid, errors, clean_df = validate_uploaded_tickets_csv(dup_df)
        self.assertFalse(is_valid)
        self.assertTrue(any("duplicate ticket_id" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
