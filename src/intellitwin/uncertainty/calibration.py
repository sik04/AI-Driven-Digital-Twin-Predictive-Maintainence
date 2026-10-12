"""Hierarchical conformal calibrator fitting, routing, and prediction."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from intellitwin.data.preprocessing import CANONICAL_REGIMES
from intellitwin.uncertainty.quantiles import compute_engine_weighted_hierarchical_quantile
from intellitwin.uncertainty.schema import (
    METHOD_DECISION_AWARE,
    METHOD_GLOBAL,
    METHOD_REGIME,
    NOMINAL_COVERAGES,
    CandidateConfig,
    CoverageThresholdBundle,
    RegimeThresholdRecord,
)
from intellitwin.uncertainty.scores import (
    compute_absolute_residual_score,
    compute_decision_aware_score,
    invert_score_to_interval,
)

DATASET_VOCABULARY: dict[str, tuple[str, ...]] = {
    "FD001": ("C1",),
    "FD002": CANONICAL_REGIMES,
    "FD004": CANONICAL_REGIMES,
}


class InsufficientCalibrationSupport(Exception):
    """Raised when global calibration pool lacks sufficient support (threshold is infinite)."""


def get_min_engines_required(nominal_coverage: float) -> int:
    """Compute required contributing engines for final regime calibration.

    Rule:
        m_g >= max(10, ceil(1 / alpha) - 1)
    """
    alpha = 1.0 - nominal_coverage
    inv_alpha = 1.0 / alpha
    ceil_inv = math.ceil(inv_alpha)
    return max(10, ceil_inv - 1)


@dataclass
class Calibrator:
    """Fitted conformal calibrator bundle for a specific model-method cell."""

    method_id: str
    dataset_name: str
    model_family: str
    model_seed: int
    candidate: CandidateConfig | None
    coverage_bundles: dict[float, CoverageThresholdBundle]

    def predict_intervals(
        self,
        predictions: np.ndarray,
        regimes: Sequence[str] | np.ndarray,
        nominal_coverage: float,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Predict prediction intervals [lower, upper] and fallback flags.

        Parameters
        ----------
        predictions : np.ndarray
            Array of point predictions p >= 0.
        regimes : Sequence[str] or np.ndarray
            Array of operating regime labels for each point prediction.
        nominal_coverage : float
            Nominal coverage level (must be in 0.80, 0.90, 0.95).

        Returns
        -------
        tuple[np.ndarray, np.ndarray, np.ndarray]
            (lower, upper, fallback_used)
            lower: float64 array of lower bounds (0 <= lower <= p)
            upper: float64 array of upper bounds (p <= upper)
            fallback_used: bool array indicating whether global fallback threshold was used
        """
        p = np.asarray(predictions, dtype=np.float64)
        if not np.all(np.isfinite(p)):
            raise ValueError("Non-finite predictions passed to predict_intervals.")
        if np.any(p < 0.0):
            raise ValueError("Negative predictions passed to predict_intervals.")

        reg_arr = np.asarray(regimes, dtype=object)
        if len(p) != len(reg_arr):
            raise ValueError(f"Length mismatch: predictions {len(p)} != regimes {len(reg_arr)}")

        bundle = self.coverage_bundles.get(nominal_coverage)
        if bundle is None:
            avail = list(self.coverage_bundles.keys())
            raise ValueError(f"Coverage {nominal_coverage} not fitted. Available: {avail}")

        valid_vocab = DATASET_VOCABULARY.get(self.dataset_name, CANONICAL_REGIMES)
        for reg in reg_arr:
            if str(reg) not in valid_vocab:
                raise ValueError(
                    f"Invalid regime {reg!r} for dataset {self.dataset_name}. "
                    f"Valid vocabulary: {valid_vocab}"
                )

        n = len(p)
        thresholds = np.empty(n, dtype=np.float64)
        fallback_used = np.zeros(n, dtype=bool)

        if self.method_id == METHOD_GLOBAL:
            # Global method always uses global threshold
            thresholds.fill(bundle.global_threshold)
            fallback_used.fill(False)
        else:
            # Regime or decision-aware method
            for idx, reg_val in enumerate(reg_arr):
                reg_str = str(reg_val)
                reg_record = bundle.regime_thresholds.get(reg_str)
                if reg_record is None or reg_record.fallback_used:
                    thresholds[idx] = bundle.global_threshold
                    fallback_used[idx] = True
                else:
                    thresholds[idx] = reg_record.threshold
                    fallback_used[idx] = False

        lower, upper = invert_score_to_interval(
            predictions=p,
            threshold=thresholds,
            candidate=self.candidate if self.method_id == METHOD_DECISION_AWARE else None,
        )

        # Validate invariants: 0 <= lower <= p <= upper
        if np.any(lower < 0.0):
            raise RuntimeError("Invariant violation: lower bound < 0")
        if np.any(lower > p + 1e-9):
            raise RuntimeError("Invariant violation: lower bound > prediction")
        if np.any(upper < p - 1e-9):
            raise RuntimeError("Invariant violation: upper bound < prediction")

        return lower, upper, fallback_used


def fit_calibrator_bundle(
    method_id: str,
    predictions: np.ndarray,
    labels: np.ndarray,
    regimes: np.ndarray,
    engine_ids: np.ndarray,
    endpoint_cycles: np.ndarray,
    dataset_name: str,
    model_family: str,
    model_seed: int,
    candidate: CandidateConfig | None = None,
) -> Calibrator:
    """Fit a complete conformal calibrator bundle for all nominal coverage levels.

    Parameters
    ----------
    method_id : str
        One of "global_hcp", "regime_hcp", "decision_aware_hcp".
    predictions : np.ndarray
        Calibration point predictions p >= 0.
    labels : np.ndarray
        Calibration true RUL targets y >= 0 (uncapped).
    regimes : np.ndarray
        Operating regime labels for each calibration endpoint.
    engine_ids : np.ndarray
        Contributing calibration engine IDs.
    endpoint_cycles : np.ndarray
        Endpoint cycle numbers for calibration windows.
    dataset_name : str
        Dataset name ("FD001", "FD002", "FD004").
    model_family : str
        Model family ("GBR", "LSTM").
    model_seed : int
        Predictor random seed.
    candidate : CandidateConfig, optional
        Required when method_id == "decision_aware_hcp".

    Returns
    -------
    Calibrator
        Fitted calibrator container.
    """
    if method_id == METHOD_DECISION_AWARE and candidate is None:
        raise ValueError("candidate must be provided for decision_aware_hcp.")

    p = np.asarray(predictions, dtype=np.float64)
    y = np.asarray(labels, dtype=np.float64)
    reg_arr = np.asarray(regimes, dtype=object)
    eids = np.asarray(engine_ids)
    cycles = np.asarray(endpoint_cycles)

    # 1. Compute nonconformity scores
    if method_id in (METHOD_GLOBAL, METHOD_REGIME):
        scores = compute_absolute_residual_score(p, y)
    elif method_id == METHOD_DECISION_AWARE:
        assert candidate is not None
        scores = compute_decision_aware_score(p, y, candidate)
    else:
        raise ValueError(f"Unsupported method_id: {method_id}")

    # Vocabulary check
    valid_vocab = DATASET_VOCABULARY.get(dataset_name, CANONICAL_REGIMES)
    for reg in reg_arr:
        if str(reg) not in valid_vocab:
            raise ValueError(f"Unrecognized regime {reg!r} in calibration data for {dataset_name}")

    coverage_bundles: dict[float, CoverageThresholdBundle] = {}

    for cov in NOMINAL_COVERAGES:
        cov_str = (
            "4/5" if abs(cov - 0.80) < 1e-4 else ("9/10" if abs(cov - 0.90) < 1e-4 else "19/20")
        )
        min_engines_req = get_min_engines_required(cov)

        # Global hierarchical threshold
        global_q = compute_engine_weighted_hierarchical_quantile(
            engine_ids=eids,
            endpoint_cycles=cycles,
            scores=scores,
            nominal_coverage=cov,
        )
        if math.isinf(global_q):
            cell_id = f"{dataset_name}_{model_family}_seed{model_seed}"
            raise InsufficientCalibrationSupport(
                f"Global hierarchical threshold is infinite at coverage {cov} for {cell_id}"
            )

        unique_global_eids = len(set(eids))
        regime_threshold_records: dict[str, RegimeThresholdRecord] = {}

        for reg in valid_vocab:
            mask = reg_arr == reg
            reg_eids = eids[mask]
            reg_cycles = cycles[mask]
            reg_scores = scores[mask]
            m_g = len(set(reg_eids))
            n_g = len(reg_scores)

            if m_g < min_engines_req:
                # Insufficient contributing engines -> global fallback
                regime_threshold_records[reg] = RegimeThresholdRecord(
                    regime=reg,
                    threshold=global_q,
                    m_engines=m_g,
                    n_endpoints=n_g,
                    fallback_used=True,
                    fallback_reason=(
                        f"Insufficient contributing engines ({m_g} < {min_engines_req})"
                    ),
                )
            else:
                # Sufficient engines -> fit regime hierarchical threshold
                reg_q = compute_engine_weighted_hierarchical_quantile(
                    engine_ids=reg_eids,
                    endpoint_cycles=reg_cycles,
                    scores=reg_scores,
                    nominal_coverage=cov,
                )
                if math.isinf(reg_q):
                    regime_threshold_records[reg] = RegimeThresholdRecord(
                        regime=reg,
                        threshold=global_q,
                        m_engines=m_g,
                        n_endpoints=n_g,
                        fallback_used=True,
                        fallback_reason="Hierarchical finite mass exceeded; threshold infinite",
                    )
                else:
                    regime_threshold_records[reg] = RegimeThresholdRecord(
                        regime=reg,
                        threshold=reg_q,
                        m_engines=m_g,
                        n_endpoints=n_g,
                        fallback_used=False,
                        fallback_reason=None,
                    )

        # FD001 exact equality assertion between global and condition-aware
        if dataset_name == "FD001" and "C1" in regime_threshold_records:
            c1_rec = regime_threshold_records["C1"]
            if not c1_rec.fallback_used:
                assert abs(c1_rec.threshold - global_q) < 1e-9, (
                    f"FD001 C1 threshold {c1_rec.threshold} != global {global_q}"
                )

        bundle = CoverageThresholdBundle(
            nominal_coverage=cov,
            coverage_fraction=cov_str,
            global_threshold=global_q,
            global_m_engines=unique_global_eids,
            global_n_endpoints=len(scores),
            regime_thresholds=regime_threshold_records,
        )
        coverage_bundles[cov] = bundle

    return Calibrator(
        method_id=method_id,
        dataset_name=dataset_name,
        model_family=model_family,
        model_seed=model_seed,
        candidate=candidate,
        coverage_bundles=coverage_bundles,
    )
