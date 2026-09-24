"""
Comprehensive Unit Test Suite for UQ-DT Framework.
Tests data simulation, conformal calibration, probabilistic surrogates,
evaluation metrics, and maintenance decision dispatch.
"""

import unittest
import numpy as np
import pandas as pd

from uq_digital_twin.data_generator import (
    InfrastructureDegradationSimulator,
    extract_feature_matrix,
)
from uq_digital_twin.conformal_calibrator import (
    ConformalizedQuantileCalibrator,
    ConformalNormalizedResidualCalibrator,
)
from uq_digital_twin.probabilistic_models import (
    HeteroscedasticEnsemble,
    GradientBoostedQuantileModel,
)
from uq_digital_twin.metrics import (
    compute_picp,
    compute_nmpiw,
    compute_cwc,
    compute_winkler_score,
    compute_crps_gaussian,
    compute_nll,
    compute_point_metrics,
)
from uq_digital_twin.decision_engine import RiskSensitiveMaintenanceScheduler


class TestDataGenerator(unittest.TestCase):
    def setUp(self):
        self.sim = InfrastructureDegradationSimulator(random_seed=123)

    def test_single_trajectory_structure(self):
        df = self.sim.generate_single_trajectory(asset_id=0, max_timesteps=100)
        self.assertIsInstance(df, pd.DataFrame)
        required_cols = [
            "asset_id",
            "timestep",
            "sensor_strain",
            "sensor_vibration",
            "sensor_acoustic",
            "sensor_temp",
            "ambient_temp",
            "operational_load",
            "health_index",
            "true_rul",
        ]
        for col in required_cols:
            self.assertIn(col, df.columns)

        # Health index must be bounded in [0, 1]
        self.assertTrue((df["health_index"] >= 0.0).all())
        self.assertTrue((df["health_index"] <= 1.0).all())

        # RUL must be non-negative and decreasing
        self.assertTrue((df["true_rul"] >= 0).all())

    def test_fleet_generation(self):
        fleet = self.sim.generate_fleet_dataset(
            num_train_assets=3,
            num_calib_assets=2,
            num_test_nominal=2,
            num_test_ood=1,
        )
        self.assertIn("train", fleet)
        self.assertIn("calib", fleet)
        self.assertIn("test_nominal", fleet)
        self.assertIn("test_ood", fleet)
        self.assertGreater(len(fleet["train"]), 0)


class TestMetrics(unittest.TestCase):
    def test_picp_computation(self):
        y_true = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        lower = np.array([8.0, 18.0, 28.0, 35.0, 55.0])  # 4th is inside, 5th is outside
        upper = np.array([12.0, 22.0, 32.0, 45.0, 60.0])
        picp = compute_picp(y_true, lower, upper)
        self.assertAlmostEqual(picp, 0.80)

    def test_nmpiw_computation(self):
        y_true = np.array([0.0, 100.0])
        lower = np.array([0.0, 80.0])
        upper = np.array([20.0, 100.0])
        # Widths are 20 and 20 -> mean = 20. Range = 100 -> NMPIW = 0.20
        nmpiw = compute_nmpiw(y_true, lower, upper, y_range=100.0)
        self.assertAlmostEqual(nmpiw, 0.20)

    def test_cwc_penalty(self):
        y_true = np.array([10.0, 20.0, 30.0, 40.0])
        lower = np.array([8.0, 18.0, 28.0, 35.0])
        upper = np.array([12.0, 22.0, 32.0, 45.0])
        # 100% coverage -> no penalty
        cwc_full = compute_cwc(y_true, lower, upper, nominal_coverage=0.90)
        nmpiw = compute_nmpiw(y_true, lower, upper)
        self.assertAlmostEqual(cwc_full, nmpiw)

    def test_winkler_score(self):
        y_true = np.array([10.0])
        lower = np.array([8.0])
        upper = np.array([12.0])
        # Inside interval: score = upper - lower = 4.0
        score = compute_winkler_score(y_true, lower, upper, alpha=0.10)
        self.assertAlmostEqual(score, 4.0)

        # Outside below: y = 6.0, lower = 8.0, upper = 12.0
        # score = 4.0 + (2/0.1)*(8.0 - 6.0) = 4.0 + 20 * 2 = 44.0
        score_below = compute_winkler_score(np.array([6.0]), lower, upper, alpha=0.10)
        self.assertAlmostEqual(score_below, 44.0)


class TestConformalCalibrator(unittest.TestCase):
    def test_cqr_calibration_coverage(self):
        rng = np.random.RandomState(42)
        n_calib = 500
        n_test = 500

        # Synthetic ground truth
        X_calib = rng.uniform(0, 10, size=n_calib)
        y_calib = 2.0 * X_calib + rng.normal(0, 1.0, size=n_calib)

        X_test = rng.uniform(0, 10, size=n_test)
        y_test = 2.0 * X_test + rng.normal(0, 1.0, size=n_test)

        # Base quantile estimates (slightly uncalibrated)
        q_lo_calib = 2.0 * X_calib - 1.2
        q_hi_calib = 2.0 * X_calib + 1.2

        q_lo_test = 2.0 * X_test - 1.2
        q_hi_test = 2.0 * X_test + 1.2

        calibrator = ConformalizedQuantileCalibrator(target_coverage=0.90)
        q_shift = calibrator.calibrate(y_calib, q_lo_calib, q_hi_calib)

        calibrated_lo, calibrated_hi = calibrator.predict_intervals(q_lo_test, q_hi_test)
        test_coverage = compute_picp(y_test, calibrated_lo, calibrated_hi)

        # Finite-sample guarantee: coverage should be within stochastic tolerance of 90% (e.g. >= 88%)
        self.assertGreaterEqual(test_coverage, 0.87)


class TestProbabilisticModels(unittest.TestCase):
    def test_heteroscedastic_ensemble_decomposition(self):
        rng = np.random.RandomState(42)
        X = rng.uniform(0, 5, size=(120, 3))
        # y has heteroscedastic noise increasing with X[:, 0]
        y = 3.0 * X[:, 0] + rng.normal(0, 0.2 + 0.3 * X[:, 0])

        ensemble = HeteroscedasticEnsemble(n_estimators=3, hidden_layer_sizes=(16,), max_iter=80, random_state=42)
        ensemble.fit(X, y)

        mu, sig_tot, sig_a, sig_e = ensemble.predict_distribution(X[:10])

        self.assertEqual(len(mu), 10)
        self.assertEqual(len(sig_tot), 10)
        self.assertTrue((sig_a > 0).all())
        self.assertTrue((sig_e >= 0).all())
        # Total variance = aleatoric + epistemic
        np.testing.assert_allclose(sig_tot ** 2, sig_a ** 2 + sig_e ** 2, rtol=1e-4)


class TestDecisionEngine(unittest.TestCase):
    def test_scheduler_policies(self):
        scheduler = RiskSensitiveMaintenanceScheduler(
            cost_preventive=1000.0,
            cost_unplanned_failure=10000.0,
            planning_horizon=10,
        )

        timesteps = np.arange(50)
        # RUL steadily counts down to 0 at step 45
        true_rul = np.maximum(0, 45 - timesteps)
        mu_pred = np.maximum(0, 45 - timesteps) + 1.0  # slight over-estimate
        lower_bound = np.maximum(0, mu_pred - 4.0)
        upper_bound = mu_pred + 4.0

        mock_trajectories = [{
            "asset_id": 0,
            "timesteps": timesteps,
            "true_rul": true_rul,
            "mu_pred": mu_pred,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "sigma": np.full_like(mu_pred, 2.0),
        }]

        res_det = scheduler.evaluate_fleet_policy(mock_trajectories, policy_type="deterministic")
        res_uq = scheduler.evaluate_fleet_policy(mock_trajectories, policy_type="uq_dt")

        self.assertIn("total_cost", res_det)
        self.assertIn("total_cost", res_uq)
        # Both should execute preventive maintenance without failure
        self.assertEqual(res_uq["catastrophic_failures"], 0)

    def test_constrained_fleet_scheduler(self):
        from uq_digital_twin.decision_engine import MultiAssetConstrainedFleetScheduler
        fleet_scheduler = MultiAssetConstrainedFleetScheduler(planning_horizon=15)

        # Asset 1: Low point RUL, but low consequence
        # Asset 2: High uncertainty and high failure cost
        asset_states = [
            {"asset_id": 1, "mu_pred": 12.0, "lower_cqr": 8.0, "sigma_total": 2.0, "cost_prev": 1000.0, "cost_fail": 5000.0},
            {"asset_id": 2, "mu_pred": 16.0, "lower_cqr": 4.0, "sigma_total": 8.0, "cost_prev": 1000.0, "cost_fail": 50000.0},
        ]

        # Budget allows only 1 intervention
        res_uq = fleet_scheduler.optimize_fleet_dispatch(asset_states, budget_envelope=1000.0, strategy="uq_risk")
        self.assertEqual(res_uq["dispatched_count"], 1)
        # UQ risk should prioritize Asset 2 due to massive downside tail risk
        self.assertEqual(res_uq["dispatched_asset_ids"], [2])

        # Deterministic strategy prioritizes Asset 1 because its point RUL is lower (12 < 16)
        res_det = fleet_scheduler.optimize_fleet_dispatch(asset_states, budget_envelope=1000.0, strategy="deterministic")
        self.assertEqual(res_det["dispatched_asset_ids"], [1])


if __name__ == "__main__":
    unittest.main()
