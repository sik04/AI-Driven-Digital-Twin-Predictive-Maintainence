"""
Unit Tests for Evaluation Metrics in IntelliTwin.
Verifies:
- RMSE implementation and numerical precision.
- MAE implementation and numerical precision.
- NASA C-MAPSS scoring function asymmetric behavior and hand-checkable cases.
"""

import unittest
import numpy as np

from intellitwin.metrics import compute_regression_metrics
from intellitwin.models.lstm_rul import nasa_scoring_function


class TestRegressionMetrics(unittest.TestCase):
    """Test suite for RUL regression and NASA scoring function validation."""

    def test_perfect_prediction(self):
        """Case 1: Exact agreement yields zero error across all metrics."""
        y_true = np.array([50.0, 100.0, 20.0])
        y_pred = np.array([50.0, 100.0, 20.0])
        res = compute_regression_metrics(y_true, y_pred)
        
        self.assertAlmostEqual(res["mae"], 0.0, places=6)
        self.assertAlmostEqual(res["rmse"], 0.0, places=6)
        self.assertAlmostEqual(res["nasa_score"], 0.0, places=6)

    def test_small_asymmetric_error(self):
        """Case 2 & 3: Small underprediction vs small overprediction (magnitude = 5 cycles).
        Underprediction (d = -5): exp(5/13) - 1 ≈ 0.469036
        Overprediction  (d = +5): exp(5/10) - 1 ≈ 0.648721
        Asymmetry requirement: overprediction penalty > underprediction penalty.
        """
        y_true = np.array([50.0])
        y_pred_under = np.array([45.0])
        y_pred_over = np.array([55.0])

        res_under = compute_regression_metrics(y_true, y_pred_under)
        res_over = compute_regression_metrics(y_true, y_pred_over)

        # Equal MAE and RMSE
        self.assertAlmostEqual(res_under["mae"], 5.0, places=6)
        self.assertAlmostEqual(res_over["mae"], 5.0, places=6)
        self.assertAlmostEqual(res_under["rmse"], 5.0, places=6)
        self.assertAlmostEqual(res_over["rmse"], 5.0, places=6)

        # Hand-calculated NASA score verification
        expected_under = np.exp(5.0 / 13.0) - 1.0
        expected_over = np.exp(5.0 / 10.0) - 1.0
        self.assertAlmostEqual(res_under["nasa_score"], expected_under, places=5)
        self.assertAlmostEqual(res_over["nasa_score"], expected_over, places=5)

        # Asymmetric check: overprediction penalty must exceed underprediction penalty
        self.assertGreater(res_over["nasa_score"], res_under["nasa_score"])

    def test_large_asymmetric_error(self):
        """Case 4 & 5: Large underprediction vs large overprediction (magnitude = 20 cycles).
        Underprediction (d = -20): exp(20/13) - 1 ≈ 3.65681
        Overprediction  (d = +20): exp(20/10) - 1 ≈ 6.38906
        """
        y_true = np.array([100.0])
        y_pred_under = np.array([80.0])
        y_pred_over = np.array([120.0])

        res_under = compute_regression_metrics(y_true, y_pred_under)
        res_over = compute_regression_metrics(y_true, y_pred_over)

        self.assertAlmostEqual(res_under["mae"], 20.0, places=6)
        self.assertAlmostEqual(res_over["mae"], 20.0, places=6)
        self.assertAlmostEqual(res_under["rmse"], 20.0, places=6)
        self.assertAlmostEqual(res_over["rmse"], 20.0, places=6)

        expected_under = np.exp(20.0 / 13.0) - 1.0
        expected_over = np.exp(20.0 / 10.0) - 1.0
        self.assertAlmostEqual(res_under["nasa_score"], expected_under, places=4)
        self.assertAlmostEqual(res_over["nasa_score"], expected_over, places=4)

        # Late prediction penalty should be almost double the early prediction penalty
        self.assertGreater(res_over["nasa_score"], 1.7 * res_under["nasa_score"])

    def test_composite_aggregation(self):
        """Case 6: Vector aggregation consistency."""
        y_true = np.array([50.0, 50.0, 50.0])
        y_pred = np.array([50.0, 45.0, 55.0])
        res = compute_regression_metrics(y_true, y_pred)

        expected_mae = (0.0 + 5.0 + 5.0) / 3.0
        expected_rmse = np.sqrt((0.0 + 25.0 + 25.0) / 3.0)
        expected_nasa = 0.0 + (np.exp(5.0 / 13.0) - 1.0) + (np.exp(5.0 / 10.0) - 1.0)

        self.assertAlmostEqual(res["mae"], expected_mae, places=5)
        self.assertAlmostEqual(res["rmse"], expected_rmse, places=5)
        self.assertAlmostEqual(res["nasa_score"], expected_nasa, places=4)

    def test_module_nasa_scoring_consistency(self):
        """Verify that intellitwin.models.lstm_rul.nasa_scoring_function produces identical outputs."""
        y_true = np.array([10.0, 20.0, 30.0, 40.0])
        y_pred = np.array([12.0, 18.0, 35.0, 38.0])

        score_1 = compute_regression_metrics(y_true, y_pred)["nasa_score"]
        score_2 = nasa_scoring_function(y_true, y_pred)

        self.assertAlmostEqual(score_1, score_2, places=6)


if __name__ == "__main__":
    unittest.main()
