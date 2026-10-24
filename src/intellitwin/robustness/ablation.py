"""Component ablation definitions, exploratory calibrator fitting, and candidate evaluation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from intellitwin.uncertainty.calibration import (
    Calibrator,
    fit_calibrator_bundle,
)
from intellitwin.uncertainty.schema import (
    CandidateConfig,
    CoverageThresholdBundle,
    RegimeThresholdRecord,
)
from intellitwin.uncertainty.scores import invert_score_to_interval

# Full 2x2x2 Factorial Definition
ABLATION_GAMMA_VALUES: tuple[int, ...] = (0, 2)
ABLATION_BETA_CODES: tuple[int, ...] = (0, -1)
ABLATION_ROUTINGS: tuple[str, ...] = ("global", "regime")


@dataclass(frozen=True)
class AblationVariant:
    """Factorial configuration of scale, asymmetry, and threshold routing."""

    variant_id: str
    gamma: int
    beta_code: int
    routing: str
    is_full_method: bool

    @classmethod
    def from_params(cls, gamma: int, beta_code: int, routing: str) -> AblationVariant:
        if gamma not in ABLATION_GAMMA_VALUES:
            raise ValueError(f"gamma must be in {ABLATION_GAMMA_VALUES}, got {gamma}")
        if beta_code not in ABLATION_BETA_CODES:
            raise ValueError(f"beta_code must be in {ABLATION_BETA_CODES}, got {beta_code}")
        if routing not in ABLATION_ROUTINGS:
            raise ValueError(f"routing must be in {ABLATION_ROUTINGS}, got {routing}")

        beta_str = "0" if beta_code == 0 else "m1"
        vid = f"gamma{gamma}_beta{beta_str}_{routing}"
        is_full = gamma == 2 and beta_code == -1 and routing == "regime"
        return cls(
            variant_id=vid,
            gamma=gamma,
            beta_code=beta_code,
            routing=routing,
            is_full_method=is_full,
        )


ALL_EIGHT_ABLATION_VARIANTS: tuple[AblationVariant, ...] = tuple(
    AblationVariant.from_params(g, b, r)
    for g in ABLATION_GAMMA_VALUES
    for b in ABLATION_BETA_CODES
    for r in ABLATION_ROUTINGS
)

VARIANT_BY_ID: dict[str, AblationVariant] = {v.variant_id: v for v in ALL_EIGHT_ABLATION_VARIANTS}


def get_candidate_for_variant(variant: AblationVariant) -> CandidateConfig:
    """Retrieve CandidateConfig for a given ablation variant."""
    return CandidateConfig.from_params(gamma=variant.gamma, beta_code=variant.beta_code)


def fit_exploratory_ablation_calibrator(
    dataset: str,
    model_family: str,
    seed: int,
    variant: AblationVariant,
    calibration_cache_dir: Path | str = "experiments/calibration/point_predictions/calibration",
    base_dir: Path | str = ".",
) -> Calibrator:
    """Fit exploratory calibrator for an ablation variant on clean calibration prediction caches.

    Enforces that calibration engines alone fit thresholds. Never uses validation or test data.
    """
    base = Path(base_dir).resolve()
    cache_root = (base / calibration_cache_dir).resolve()
    csv_p = cache_root / dataset / model_family / f"seed_{seed}.csv"
    if not csv_p.exists():
        raise FileNotFoundError(f"Calibration prediction cache missing: {csv_p}")

    df_cal = pd.read_csv(csv_p)
    cand = get_candidate_for_variant(variant)

    calibrator = fit_calibrator_bundle(
        method_id="decision_aware_hcp",
        predictions=df_cal["prediction"].to_numpy(),
        labels=df_cal["rul_true"].to_numpy(),
        regimes=df_cal["regime"].to_numpy(),
        engine_ids=df_cal["unit"].to_numpy(),
        endpoint_cycles=df_cal["endpoint_cycle"].to_numpy(),
        dataset_name=dataset,
        model_family=model_family,
        model_seed=seed,
        candidate=cand,
    )
    return calibrator


def predict_ablation_intervals(
    calibrator: Calibrator,
    variant: AblationVariant,
    predictions: np.ndarray[Any, Any],
    regimes: Sequence[str] | np.ndarray[Any, Any],
    nominal_coverage: float = 0.90,
) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any], np.ndarray[Any, Any]]:
    """Predict intervals for an ablation variant adhering to routing and asymmetry rules.

    Rules:
    - If routing == 'global': uses calibrator's global threshold with candidate inversion.
    - If routing == 'regime': uses regime-specific threshold (with fallback) with
      candidate inversion.
    - Fallback flag is True only if routing == 'regime' and the fallback threshold was used.
    """
    p = np.asarray(predictions, dtype=np.float64)
    reg_arr = np.asarray(regimes, dtype=object)
    cand = get_candidate_for_variant(variant)

    bundle: CoverageThresholdBundle | None = calibrator.coverage_bundles.get(nominal_coverage)
    if bundle is None:
        raise ValueError(f"Coverage {nominal_coverage} not found in calibrator bundles.")

    n = len(p)
    thresholds = np.empty(n, dtype=np.float64)
    fallback_used = np.zeros(n, dtype=bool)

    if variant.routing == "global":
        thresholds.fill(bundle.global_threshold)
        fallback_used.fill(False)
    else:
        # regime routing
        for idx, reg_val in enumerate(reg_arr):
            reg_str = str(reg_val)
            reg_rec: RegimeThresholdRecord | None = bundle.regime_thresholds.get(reg_str)
            if reg_rec is None or reg_rec.fallback_used:
                thresholds[idx] = bundle.global_threshold
                fallback_used[idx] = True
            else:
                thresholds[idx] = reg_rec.threshold
                fallback_used[idx] = False

    lower, upper = invert_score_to_interval(
        predictions=p,
        threshold=thresholds,
        candidate=cand,
    )

    return lower, upper, fallback_used
