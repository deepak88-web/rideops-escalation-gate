"""
End-to-end integration tests for RideOps pipeline components.
"""

import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np

from src.config import RAW_DATA_PATH
from src.data.loader import load_raw_tickets
from src.data.quality import run_data_quality_audit
from src.features.pipeline import build_feature_pipeline
from src.utils.hypothesis_tests import run_all_hypothesis_tests
from src.models.leakage_guard import prepare_model_dataset


class TestPipelineIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Load sample from actual raw data if present
        if RAW_DATA_PATH.exists():
            cls.raw_df = load_raw_tickets(RAW_DATA_PATH)
        else:
            cls.raw_df = pd.DataFrame()

    def test_end_to_end_data_flow(self):
        if self.raw_df.empty:
            self.skipTest("Raw data file not found.")

        # 1. Quality audit
        audit = run_data_quality_audit(self.raw_df)
        self.assertEqual(audit["duplicate_check"]["duplicate_count"], 0)
        self.assertEqual(audit["timestamp_validation"]["total_violations"], 0)
        self.assertEqual(audit["escalation_consistency"]["inconsistent_rows_count"], 0)

        # 2. Feature pipeline on representative subset for rapid test execution
        subset_df = self.raw_df.head(200).copy()
        df_clean = build_feature_pipeline(subset_df)
        self.assertEqual(len(df_clean), 200)
        self.assertIn("hrs_to_first_response", df_clean.columns)
        self.assertIn("resolution_hrs", df_clean.columns)
        self.assertIn("is_escalated", df_clean.columns)
        self.assertIn("is_avoidable_esc", df_clean.columns)
        self.assertIn("is_repeat_contact", df_clean.columns)

        # 3. Model dataset extraction & leakage guard
        X, y, is_sep = prepare_model_dataset(df_clean)
        self.assertEqual(len(X), len(y))
        self.assertEqual(len(X), df_clean["is_escalated"].sum())


if __name__ == "__main__":
    unittest.main()
