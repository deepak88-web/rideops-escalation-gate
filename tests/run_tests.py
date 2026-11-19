"""
Comprehensive Test Runner for RideOps Escalation Gate
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import unittest

from tests.test_data_quality import TestDataQuality
from tests.test_features import TestFeatures
from tests.test_analysis import TestAnalysis
from tests.test_models import TestModels
from tests.test_override_logger import TestOverrideLogger
from tests.test_known_issues_and_upload import TestKnownIssuesAndUpload
from tests.test_pipeline_integration import TestPipelineIntegration


def run_all_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestDataQuality))
    suite.addTests(loader.loadTestsFromTestCase(TestFeatures))
    suite.addTests(loader.loadTestsFromTestCase(TestAnalysis))
    suite.addTests(loader.loadTestsFromTestCase(TestModels))
    suite.addTests(loader.loadTestsFromTestCase(TestOverrideLogger))
    suite.addTests(loader.loadTestsFromTestCase(TestKnownIssuesAndUpload))
    suite.addTests(loader.loadTestsFromTestCase(TestPipelineIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
