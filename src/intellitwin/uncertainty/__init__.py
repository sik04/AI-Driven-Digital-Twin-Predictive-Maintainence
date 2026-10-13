"""Uncertainty quantification and conformal calibration package for IntelliTwin."""

from intellitwin.uncertainty.artifacts import load_frozen_calibrator
from intellitwin.uncertainty.calibration import (
    Calibrator,
    InsufficientCalibrationSupport,
    fit_calibrator_bundle,
)
from intellitwin.uncertainty.quantiles import (
    compute_engine_weighted_dev_quantile,
    compute_engine_weighted_hierarchical_quantile,
)
from intellitwin.uncertainty.schema import (
    ALL_NINE_CANDIDATES,
    METHOD_DECISION_AWARE,
    METHOD_GLOBAL,
    METHOD_REGIME,
    NOMINAL_COVERAGES,
    CandidateConfig,
)
from intellitwin.uncertainty.scores import (
    compute_absolute_residual_score,
    compute_decision_aware_score,
    invert_score_to_interval,
)

__all__ = [
    "Calibrator",
    "InsufficientCalibrationSupport",
    "fit_calibrator_bundle",
    "load_frozen_calibrator",
    "compute_engine_weighted_dev_quantile",
    "compute_engine_weighted_hierarchical_quantile",
    "compute_absolute_residual_score",
    "compute_decision_aware_score",
    "invert_score_to_interval",
    "CandidateConfig",
    "ALL_NINE_CANDIDATES",
    "METHOD_GLOBAL",
    "METHOD_REGIME",
    "METHOD_DECISION_AWARE",
    "NOMINAL_COVERAGES",
]
