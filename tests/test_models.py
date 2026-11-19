"""
Unit tests for Machine Learning models, leakage guard, baseline, and evaluation (Section J).
"""

import os
import sys
import tempfile
from pathlib import Path

os.environ["LOKY_MAX_CPU_COUNT"] = "1"
os.environ["MPLCONFIGDIR"] = tempfile.gettempdir()
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
import pandas as pd
import numpy as np
import joblib

from src.config import MODEL_PATH, LIVE_MODEL_PATH
from src.models.leakage_guard import check_leakage, prepare_model_dataset, CAT_FEATURES, NUM_FEATURES, TEXT_FEATURE
from src.models.live_gate import build_live_triage_labels, prepare_live_model_dataset, get_live_model_pipelines
from src.models.baseline import CategoryRateBaselineClassifier
from src.models.evaluate import evaluate_probabilities


class TestModels(unittest.TestCase):

    def test_check_leakage_clean(self):
        # Pre-escalation features only
        clean_features = CAT_FEATURES + NUM_FEATURES + [TEXT_FEATURE]
        # Should not raise any error
        check_leakage(clean_features)

    def test_check_leakage_detected(self):
        # Injecting post-escalation leakage columns
        dirty_features = CAT_FEATURES + ["resolution_hrs", "eng_outcome"]
        with self.assertRaises(ValueError):
            check_leakage(dirty_features)

    def test_baseline_classifier(self):
        train_X = pd.DataFrame({"category": ["Billing", "Billing", "App Bug", "App Bug"]})
        train_y = np.array([1, 1, 0, 0])

        clf = CategoryRateBaselineClassifier(threshold=0.5)
        clf.fit(train_X, train_y)

        # Billing rate should be 1.0, App Bug rate should be 0.0, global rate 0.5
        self.assertEqual(clf.category_rates_["Billing"], 1.0)
        self.assertEqual(clf.category_rates_["App Bug"], 0.0)
        self.assertEqual(clf.global_rate_, 0.5)

        test_X = pd.DataFrame({"category": ["Billing", "App Bug", "New Category"]})
        probs = clf.predict_proba(test_X)
        self.assertEqual(probs.shape, (3, 2))
        self.assertAlmostEqual(probs[0, 1], 1.0)
        self.assertAlmostEqual(probs[1, 1], 0.0)
        self.assertAlmostEqual(probs[2, 1], 0.5)  # Fallback to global rate

        preds = clf.predict(test_X)
        self.assertEqual(list(preds), [1, 0, 1])  # 0.5 >= threshold 0.5 -> 1

    def test_evaluate_probabilities(self):
        y_true = np.array([1, 1, 0, 0])
        y_prob = np.array([0.9, 0.8, 0.2, 0.1])
        metrics = evaluate_probabilities(y_true, y_prob, threshold=0.5)

        self.assertEqual(metrics["ROC_AUC"], 1.0)
        self.assertEqual(metrics["PR_AUC"], 1.0)
        self.assertEqual(metrics["Precision"], 1.0)
        self.assertEqual(metrics["Recall"], 1.0)
        self.assertEqual(metrics["F1"], 1.0)

    def test_champion_model_artifact_exists(self):
        self.assertTrue(MODEL_PATH.exists(), f"Model artifact missing at {MODEL_PATH}")

    def test_pipeline_construction_and_prediction(self):
        from src.models.train import get_model_pipelines

        models = get_model_pipelines()
        self.assertIn("Logistic Regression", models)
        self.assertIn("Random Forest", models)

        pipe = models["Logistic Regression"]
        X_mock = pd.DataFrame({
            "category": ["Billing Issue", "App Bug"],
            "priority": ["P2", "P1"],
            "channel": ["Email", "Portal"],
            "client_tier": ["Enterprise", "Mid-Market"],
            "assigned_agent": ["Rahul T", "Karan B"],
            "weekday": ["Monday", "Tuesday"],
            "hrs_to_first_response": [1.5, 0.5],
            "hour_of_day": [11, 14],
            "is_repeat_contact": [1, 0],
            "client_prior_tickets": [5, 2],
            "description": ["Customer reports payment processing timeout.", "App crashes on launch."]
        })
        y_mock = np.array([1, 0])

        pipe.fit(X_mock, y_mock)
        probs = pipe.predict_proba(X_mock)
        self.assertEqual(probs.shape, (2, 2))

    def test_live_model_artifact_exists(self):
        self.assertTrue(LIVE_MODEL_PATH.exists(), f"Live Model artifact missing at {LIVE_MODEL_PATH}")

    def test_build_live_triage_labels(self):
        mock_df = pd.DataFrame({
            "is_open": [0, 0, 0, 1],
            "is_escalated": [1, 1, 0, 0],
            "eng_outcome": ["Fixed", "Duplicate of known issue", None, None],
            "reopen_count": [0, 0, 0, 0],
            "category": ["Report export failing", "Report export failing", "Billing / invoice discrepancy", "App"]
        })
        labeled = build_live_triage_labels(mock_df, regime="strict")
        # is_open == 1 should be excluded
        self.assertEqual(len(labeled), 3)
        # Fixed -> target_avoidable = 0
        self.assertEqual(labeled.iloc[0]["target_avoidable"], 0)
        # Duplicate -> target_avoidable = 1
        self.assertEqual(labeled.iloc[1]["target_avoidable"], 1)
        # 0 reopens non-escalated -> target_avoidable = 1
        self.assertEqual(labeled.iloc[2]["target_avoidable"], 1)

    def test_live_gate_pipeline_prediction(self):
        pipelines = get_live_model_pipelines()
        self.assertIn("Logistic Regression", pipelines)
        pipe = pipelines["Logistic Regression"]
        X_mock = pd.DataFrame({
            "category": ["Billing / invoice discrepancy", "OTP / boarding issue"],
            "priority": ["P2", "P1"],
            "channel": ["Email", "WhatsApp"],
            "client_tier": ["Enterprise", "SMB"],
            "assigned_agent": ["Rahul T", "Karan B"],
            "weekday": ["Monday", "Tuesday"],
            "hrs_to_first_response": [1.5, 0.5],
            "hour_of_day": [11, 14],
            "is_repeat_contact": [1, 0],
            "client_prior_tickets": [5, 2],
            "description": ["Invoice calculation error.", "OTP failed on boarding."]
        })
        y_mock = np.array([1, 0])
        pipe.fit(X_mock, y_mock)
        probs = pipe.predict_proba(X_mock)
        self.assertEqual(probs.shape, (2, 2))
        self.assertTrue((probs >= 0.0).all() and (probs <= 1.0).all())
        self.assertAlmostEqual(probs[0, 0] + probs[0, 1], 1.0, places=4)


if __name__ == "__main__":
    unittest.main()
