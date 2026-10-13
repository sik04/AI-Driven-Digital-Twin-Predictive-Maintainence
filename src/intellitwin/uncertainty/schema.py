"""Immutable configuration, constants, and artifact schemas for Step 8 calibration."""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Final

PROTOCOL_VERSION: Final[str] = "step08-v1"
CALIBRATOR_SCHEMA_VERSION: Final[str] = "step08-calibrator-v1"
SELECTION_SCHEMA_VERSION: Final[str] = "step08-selection-v1"
FREEZE_SCHEMA_VERSION: Final[str] = "step08-freeze-v1"

METHOD_GLOBAL: Final[str] = "global_hcp"
METHOD_REGIME: Final[str] = "regime_hcp"
METHOD_DECISION_AWARE: Final[str] = "decision_aware_hcp"
SUPPORTED_METHODS: Final[tuple[str, ...]] = (
    METHOD_GLOBAL,
    METHOD_REGIME,
    METHOD_DECISION_AWARE,
)

NOMINAL_COVERAGES: Final[tuple[float, ...]] = (0.80, 0.90, 0.95)
COVERAGE_FRACTIONS: Final[dict[float, Fraction]] = {
    0.80: Fraction(4, 5),
    0.90: Fraction(9, 10),
    0.95: Fraction(19, 20),
}

GAMMA_GRID: Final[tuple[int, ...]] = (0, 1, 2)
BETA_CODE_GRID: Final[tuple[int, ...]] = (-1, 0, 1)
BETA_CODE_TO_STR: Final[dict[int, str]] = {-1: "m1", 0: "0", 1: "p1"}
STR_TO_BETA_CODE: Final[dict[str, int]] = {"m1": -1, "0": 0, "p1": 1}

LN2: Final[float] = math.log(2.0)
SIGMA_SCALE: Final[float] = 125.0
Z_SCALE: Final[float] = 20.0

IDENTITY_CANDIDATE_ID: Final[str] = "gamma0_beta0"


@dataclass(frozen=True)
class CandidateConfig:
    """Specification of an asymmetric decision-aware candidate configuration."""

    candidate_id: str
    gamma: int
    beta_code: int
    beta: float

    @classmethod
    def from_params(cls, gamma: int, beta_code: int) -> CandidateConfig:
        if gamma not in GAMMA_GRID:
            raise ValueError(f"gamma must be in {GAMMA_GRID}, got {gamma}")
        if beta_code not in BETA_CODE_GRID:
            raise ValueError(f"beta_code must be in {BETA_CODE_GRID}, got {beta_code}")
        cid = f"gamma{gamma}_beta{BETA_CODE_TO_STR[beta_code]}"
        return cls(
            candidate_id=cid,
            gamma=gamma,
            beta_code=beta_code,
            beta=float(beta_code) * LN2,
        )

    @classmethod
    def from_id(cls, candidate_id: str) -> CandidateConfig:
        for g in GAMMA_GRID:
            for b in BETA_CODE_GRID:
                cand = cls.from_params(g, b)
                if cand.candidate_id == candidate_id:
                    return cand
        raise ValueError(f"Unknown candidate_id: {candidate_id}")


ALL_NINE_CANDIDATES: Final[tuple[CandidateConfig, ...]] = tuple(
    CandidateConfig.from_params(g, b) for g in GAMMA_GRID for b in BETA_CODE_GRID
)


@dataclass(frozen=True)
class RegimeThresholdRecord:
    """Threshold record for a specific operating regime."""

    regime: str
    threshold: float
    m_engines: int
    n_endpoints: int
    fallback_used: bool
    fallback_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "regime": self.regime,
            "threshold": self.threshold,
            "m_engines": self.m_engines,
            "n_endpoints": self.n_endpoints,
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
        }


@dataclass(frozen=True)
class CoverageThresholdBundle:
    """Hierarchical conformal thresholds for a single coverage level."""

    nominal_coverage: float
    coverage_fraction: str  # e.g. "9/10"
    global_threshold: float
    global_m_engines: int
    global_n_endpoints: int
    regime_thresholds: dict[str, RegimeThresholdRecord]

    def to_dict(self) -> dict[str, Any]:
        return {
            "nominal_coverage": self.nominal_coverage,
            "coverage_fraction": self.coverage_fraction,
            "global_threshold": self.global_threshold,
            "global_m_engines": self.global_m_engines,
            "global_n_endpoints": self.global_n_endpoints,
            "regime_thresholds": {k: v.to_dict() for k, v in self.regime_thresholds.items()},
        }
