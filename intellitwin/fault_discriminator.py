"""
Masking Problem and Fault Discrimination Engine for IntelliTwin.
Differentiates between:
  Case 1: Normal environmental / operating variation
  Case 2: Genuine mechanical degradation
  Case 3: Combined operating change + genuine mechanical deterioration
  Case 4: Unfamiliar / out-of-distribution condition (high epistemic uncertainty)
"""

import numpy as np


class FaultDiscriminator:
    """Solves the masking problem by analyzing condition-normalized residuals,
    temporal persistence, and epistemic uncertainty.
    """

    CASE_NORMAL_VARIATION = 1
    CASE_GENUINE_DEGRADATION = 2
    CASE_COMBINED = 3
    CASE_UNFAMILIAR = 4

    CASE_DESCRIPTIONS = {
        1: "Normal Operational Variation (No Fault)",
        2: "Genuine Mechanical Degradation",
        3: "Combined Operational Shift + Mechanical Degradation",
        4: "Unfamiliar Operating Condition (High Uncertainty)",
    }

    def __init__(self, residual_threshold=2.0, epistemic_threshold=15.0, persistence_window=3):
        self.residual_threshold = residual_threshold
        self.epistemic_threshold = epistemic_threshold
        self.persistence_window = persistence_window

    def discriminate(self, condition_residuals, setting_deltas, epistemic_uncertainties):
        """Classify each observation into one of the 4 cases.
        Args:
            condition_residuals: (N, S) array of condition-normalized residuals
            setting_deltas: (N,) magnitude of shift in operational settings relative to baseline
            epistemic_uncertainties: (N,) model disagreement / epistemic std
        Returns:
            case_labels: (N,) array of integer case codes (1, 2, 3, or 4)
            diagnostics: dict with breakdown statistics
        """
        condition_residuals = np.asarray(condition_residuals)
        setting_deltas = np.asarray(setting_deltas).ravel()
        epistemic = np.asarray(epistemic_uncertainties).ravel()

        n = len(epistemic)
        # Compute RMS residual across sensors
        residual_norm = np.sqrt(np.mean(condition_residuals ** 2, axis=1))

        # Classify
        case_labels = np.zeros(n, dtype=int)
        for i in range(n):
            is_unfamiliar = epistemic[i] > self.epistemic_threshold
            has_fault_residual = residual_norm[i] > self.residual_threshold
            has_setting_shift = setting_deltas[i] > 1.0

            if is_unfamiliar:
                case_labels[i] = self.CASE_UNFAMILIAR
            elif has_fault_residual and has_setting_shift:
                case_labels[i] = self.CASE_COMBINED
            elif has_fault_residual:
                case_labels[i] = self.CASE_GENUINE_DEGRADATION
            else:
                case_labels[i] = self.CASE_NORMAL_VARIATION

        # Summary statistics
        counts = {
            "normal_variation": int(np.sum(case_labels == self.CASE_NORMAL_VARIATION)),
            "genuine_degradation": int(np.sum(case_labels == self.CASE_GENUINE_DEGRADATION)),
            "combined": int(np.sum(case_labels == self.CASE_COMBINED)),
            "unfamiliar": int(np.sum(case_labels == self.CASE_UNFAMILIAR)),
        }
        return case_labels, counts
