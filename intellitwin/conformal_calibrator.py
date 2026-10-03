"""
Split Conformal Prediction Calibrator for IntelliTwin.
Provides finite-sample coverage guarantee: P(y in C(x)) >= 1 - alpha.
Computes non-conformity scores and calibrated intervals with variance scaling.
"""

import numpy as np


class ConformalCalibrator:
    """Split Conformal Prediction calibrator for regression intervals."""

    def __init__(self, target_coverage=0.90):
        self.target_coverage = target_coverage
        self.alpha = 1.0 - target_coverage
        self.q_hat = None
        self.calibrated = False

    def calibrate(self, y_cal, mu_cal, sigma_cal=None):
        """Fit conformal quantile on a held-out calibration set.
        Non-conformity score: s_i = |y_i - mu_i| / sigma_i (normalized residual)
        or s_i = |y_i - mu_i| if sigma is not provided.
        """
        y_cal = np.asarray(y_cal).ravel()
        mu_cal = np.asarray(mu_cal).ravel()
        n = len(y_cal)

        if sigma_cal is not None:
            sigma_cal = np.maximum(np.asarray(sigma_cal).ravel(), 1e-4)
            scores = np.abs(y_cal - mu_cal) / sigma_cal
        else:
            scores = np.abs(y_cal - mu_cal)

        # Finite-sample correction quantile: ceil((n + 1) * (1 - alpha)) / n
        level = np.clip(np.ceil((n + 1) * self.target_coverage) / n, 0.0, 1.0)
        self.q_hat = float(np.quantile(scores, level, method="higher"))
        self.calibrated = True
        return self.q_hat

    def predict_intervals(self, mu_test, sigma_test=None):
        """Compute calibrated lower and upper prediction bounds."""
        if not self.calibrated or self.q_hat is None:
            raise RuntimeError("Calibrator has not been fitted. Call calibrate() first.")

        mu_test = np.asarray(mu_test).ravel()
        if sigma_test is not None:
            sigma_test = np.maximum(np.asarray(sigma_test).ravel(), 1e-4)
            margin = self.q_hat * sigma_test
        else:
            margin = self.q_hat

        lower = np.maximum(0.0, mu_test - margin)
        upper = mu_test + margin
        return lower, upper
