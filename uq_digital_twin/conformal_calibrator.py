"""
Conformal Prediction and Conformalized Quantile Regression (CQR) Calibrator.

Provides distribution-free, finite-sample coverage guarantees P(y in C(x)) >= 1 - alpha
for Digital Twin prognostic streams, directly resolving the uncalibrated point prediction
flaws identified in Paper 14 (GA-Ensemble) and Paper 6 (ALSTM-FCN/Tree models).
"""

import numpy as np
from typing import Tuple, Optional


class ConformalizedQuantileCalibrator:
    """
    Implements Split Conformalized Quantile Regression (CQR) per Romano et al. (NeurIPS 2019).
    Guarantees finite-sample coverage 1 - alpha under exchangeability.
    """

    def __init__(self, target_coverage: float = 0.90):
        self.target_coverage = target_coverage
        self.alpha = 1.0 - target_coverage
        self.q_correction: Optional[float] = None
        self.is_calibrated = False

    def calibrate(
        self,
        y_calib: np.ndarray,
        q_lower_calib: np.ndarray,
        q_upper_calib: np.ndarray,
    ) -> float:
        """
        Computes non-conformity scores on calibration fleet:
        E_i = max( q_lower(x_i) - y_i, y_i - q_upper(x_i) )
        and extracts the (1 - alpha)(1 + 1/n)-th empirical quantile.
        """
        y_calib = np.asarray(y_calib).ravel()
        q_lower_calib = np.asarray(q_lower_calib).ravel()
        q_upper_calib = np.asarray(q_upper_calib).ravel()

        n = len(y_calib)
        if n == 0:
            raise ValueError("Calibration set cannot be empty.")

        # Non-conformity score: signed distance outside the uncalibrated interval
        scores = np.maximum(q_lower_calib - y_calib, y_calib - q_upper_calib)

        # Finite-sample quantile level: ceil((n + 1) * (1 - alpha)) / n
        quantile_level = np.ceil((n + 1) * (1.0 - self.alpha)) / n
        quantile_level = min(1.0, max(0.0, quantile_level))

        # Empirical quantile with linear interpolation
        self.q_correction = float(np.quantile(scores, quantile_level, method="higher"))
        self.is_calibrated = True

        return self.q_correction

    def predict_intervals(
        self,
        q_lower: np.ndarray,
        q_upper: np.ndarray,
        clip_min: Optional[float] = 0.0,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Applies conformal shift to generate calibrated prediction intervals:
        C(x) = [ q_lower(x) - Q_hat,  q_upper(x) + Q_hat ]
        """
        if not self.is_calibrated or self.q_correction is None:
            raise RuntimeError("Calibrator must be fitted using .calibrate() before prediction.")

        q_lower = np.asarray(q_lower).ravel()
        q_upper = np.asarray(q_upper).ravel()

        calibrated_lower = q_lower - self.q_correction
        calibrated_upper = q_upper + self.q_correction

        if clip_min is not None:
            calibrated_lower = np.maximum(clip_min, calibrated_lower)
            calibrated_upper = np.maximum(clip_min, calibrated_upper)

        # Ensure upper is strictly greater than or equal to lower
        calibrated_upper = np.maximum(calibrated_lower, calibrated_upper)

        return calibrated_lower, calibrated_upper


class ConformalNormalizedResidualCalibrator:
    """
    Implements Split Conformal Prediction with variance-normalized residuals:
    S_i = |y_i - mu(x_i)| / sigma(x_i)
    Interval: [ mu(x) - c_hat * sigma(x),  mu(x) + c_hat * sigma(x) ]
    """

    def __init__(self, target_coverage: float = 0.90):
        self.target_coverage = target_coverage
        self.alpha = 1.0 - target_coverage
        self.c_multiplier: Optional[float] = None
        self.is_calibrated = False

    def calibrate(
        self,
        y_calib: np.ndarray,
        mu_calib: np.ndarray,
        sigma_calib: np.ndarray,
    ) -> float:
        """
        Calibrates the scaling multiplier c_hat on the calibration dataset.
        """
        y_calib = np.asarray(y_calib).ravel()
        mu_calib = np.asarray(mu_calib).ravel()
        sigma_calib = np.maximum(np.asarray(sigma_calib).ravel(), 1e-6)

        n = len(y_calib)
        scores = np.abs(y_calib - mu_calib) / sigma_calib

        quantile_level = np.ceil((n + 1) * (1.0 - self.alpha)) / n
        quantile_level = min(1.0, max(0.0, quantile_level))

        self.c_multiplier = float(np.quantile(scores, quantile_level, method="higher"))
        self.is_calibrated = True

        return self.c_multiplier

    def predict_intervals(
        self,
        mu: np.ndarray,
        sigma: np.ndarray,
        clip_min: Optional[float] = 0.0,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Produces variance-adapted calibrated intervals:
        [ mu - c_hat * sigma,  mu + c_hat * sigma ]
        """
        if not self.is_calibrated or self.c_multiplier is None:
            raise RuntimeError("Calibrator must be fitted using .calibrate() before prediction.")

        mu = np.asarray(mu).ravel()
        sigma = np.maximum(np.asarray(sigma).ravel(), 1e-6)

        calibrated_lower = mu - self.c_multiplier * sigma
        calibrated_upper = mu + self.c_multiplier * sigma

        if clip_min is not None:
            calibrated_lower = np.maximum(clip_min, calibrated_lower)
            calibrated_upper = np.maximum(clip_min, calibrated_upper)

        return calibrated_lower, calibrated_upper
