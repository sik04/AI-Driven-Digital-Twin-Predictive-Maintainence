"""
Unit Test Suite for IntelliTwin AI-Driven Digital Twin Framework.
Tests:
  1. Data Loader & Preprocessing
  2. Conformal Prediction Calibrator (Coverage bounds)
  3. Uncertainty & Regression Metrics
  4. Environmental Condition Handler & Residuals
  5. Masking Problem Fault Discriminator
  6. Catastrophic Failure Evaluator
"""

import unittest
import numpy as np

from intellitwin.data_loader import CMAPSSDataLoader
from intellitwin.conformal_calibrator import ConformalCalibrator
from intellitwin.metrics import compute_regression_metrics, compute_uq_metrics
from intellitwin.environmental_handler import EnvironmentalConditionHandler
from intellitwin.fault_discriminator import FaultDiscriminator
from intellitwin.catastrophic_evaluator import CatastrophicFailureEvaluator


class TestIntelliTwinFramework(unittest.TestCase):

    def test_data_loader(self):
        loader = CMAPSSDataLoader(data_dir="data/cmapss", sub_dataset="FD001", max_rul=125)
        train_df, test_df, feature_cols = loader.prepare_data()
        self.assertGreater(len(train_df), 1000)
        self.assertIn("rul", train_df.columns)
        self.assertIn("health_state", train_df.columns)
        self.assertEqual(len(feature_cols), 54)

    def test_conformal_calibrator(self):
        calibrator = ConformalCalibrator(target_coverage=0.90)
        np.random.seed(42)
        y_cal = np.random.uniform(20, 100, 100)
        mu_cal = y_cal + np.random.normal(0, 5, 100)
        sigma_cal = np.abs(np.random.normal(5, 1, 100))

        q_hat = calibrator.calibrate(y_cal, mu_cal, sigma_cal)
        self.assertGreater(q_hat, 0.0)

        lower, upper = calibrator.predict_intervals(mu_cal, sigma_cal)
        coverage = np.mean((y_cal >= lower) & (y_cal <= upper))
        self.assertGreaterEqual(coverage, 0.85)

    def test_uq_metrics(self):
        y_true = np.array([50, 40, 30, 20, 10])
        lower = np.array([45, 35, 25, 15, 5])
        upper = np.array([55, 45, 35, 25, 15])
        metrics = compute_uq_metrics(y_true, lower, upper, alpha=0.10)
        self.assertEqual(metrics["picp"], 1.0)
        self.assertTrue(metrics["coverage_met"])

    def test_environmental_handler(self):
        handler = EnvironmentalConditionHandler(n_regimes=3)
        settings = np.random.uniform(0, 1, (50, 3))
        sensors = settings @ np.array([[10, 2], [5, 3], [1, 4]]) + np.random.normal(0, 0.1, (50, 2))
        handler.fit(settings, sensors)

        residuals = handler.compute_condition_residuals(settings, sensors)
        self.assertEqual(residuals.shape, (50, 2))
        self.assertLess(np.mean(np.abs(residuals)), 1.0)

    def test_fault_discriminator(self):
        discriminator = FaultDiscriminator(residual_threshold=2.0, epistemic_threshold=15.0)
        residuals = np.array([[0.5, 0.5], [5.0, 5.0], [5.0, 5.0], [0.1, 0.1]])
        settings_shift = np.array([0.1, 0.1, 2.5, 0.1])
        epistemic = np.array([2.0, 2.0, 2.0, 25.0])

        cases, counts = discriminator.discriminate(residuals, settings_shift, epistemic)
        self.assertEqual(cases[0], FaultDiscriminator.CASE_NORMAL_VARIATION)
        self.assertEqual(cases[1], FaultDiscriminator.CASE_GENUINE_DEGRADATION)
        self.assertEqual(cases[2], FaultDiscriminator.CASE_COMBINED)
        self.assertEqual(cases[3], FaultDiscriminator.CASE_UNFAMILIAR)

    def test_catastrophic_evaluator(self):
        evaluator = CatastrophicFailureEvaluator(critical_threshold_cycles=20, warning_threshold_cycles=45)
        trajectories = [{
            "unit": 1,
            "cycles": np.arange(1, 101),
            "rul_true": np.maximum(0, 100 - np.arange(1, 101)),
            "rul_pred": np.maximum(0, 100 - np.arange(1, 101)) + 1.0
        }]
        res = evaluator.evaluate_trajectories(trajectories)
        self.assertEqual(res["missed_catastrophic_failures"], 0)
        self.assertEqual(res["catastrophic_prevention_success_rate"], 1.0)
        self.assertGreater(res["mean_warning_lead_time_cycles"], 20.0)


if __name__ == "__main__":
    unittest.main()
