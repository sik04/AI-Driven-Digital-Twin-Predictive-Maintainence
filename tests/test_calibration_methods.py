"""Unit tests for the three calibration methods, fallback routing, and interval properties."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from intellitwin.uncertainty.calibration import (
    InsufficientCalibrationSupport,
    fit_calibrator_bundle,
)
from intellitwin.uncertainty.schema import (
    METHOD_DECISION_AWARE,
    METHOD_GLOBAL,
    METHOD_REGIME,
    CandidateConfig,
)


def _create_synthetic_calibration_data(
    n_engines: int = 25,
    points_per_engine: int = 20,
    regimes: tuple[str, ...] = ("C1", "C2", "C3", "C4", "C5", "C6"),
) -> tuple[
    np.ndarray[Any, Any],
    np.ndarray[Any, Any],
    np.ndarray[Any, Any],
    np.ndarray[Any, Any],
    np.ndarray[Any, Any],
]:
    """Create synthetic calibration data fixture."""
    rng = np.random.default_rng(2026)
    eids_list: list[int] = []
    cycles_list: list[int] = []
    preds_list: list[float] = []
    labels_list: list[float] = []
    regimes_list: list[str] = []

    for eid in range(1, n_engines + 1):
        for cyc in range(30, 30 + points_per_engine):
            eids_list.append(eid)
            cycles_list.append(cyc)
            p = float(rng.uniform(10.0, 100.0))
            err = float(rng.normal(0.0, 5.0))
            y = max(0.0, p + err)
            preds_list.append(p)
            labels_list.append(y)
            # Assign regime based on engine & cycle
            regimes_list.append(regimes[(eid + cyc) % len(regimes)])

    return (
        np.array(preds_list),
        np.array(labels_list),
        np.array(regimes_list, dtype=object),
        np.array(eids_list),
        np.array(cycles_list),
    )


def test_identity_proposed_calibrator_equals_regime_hcp() -> None:
    """Verify that candidate gamma0_beta0 calibrator produces intervals identical to regime_hcp."""
    preds, labels, regimes, eids, cycles = _create_synthetic_calibration_data(n_engines=25)

    cal_regime = fit_calibrator_bundle(
        method_id=METHOD_REGIME,
        predictions=preds,
        labels=labels,
        regimes=regimes,
        engine_ids=eids,
        endpoint_cycles=cycles,
        dataset_name="FD002",
        model_family="GBR",
        model_seed=2026,
    )

    id_cand = CandidateConfig.from_id("gamma0_beta0")
    cal_proposed = fit_calibrator_bundle(
        method_id=METHOD_DECISION_AWARE,
        predictions=preds,
        labels=labels,
        regimes=regimes,
        engine_ids=eids,
        endpoint_cycles=cycles,
        dataset_name="FD002",
        model_family="GBR",
        model_seed=2026,
        candidate=id_cand,
    )

    for cov in (0.80, 0.90, 0.95):
        l_reg, u_reg, fb_reg = cal_regime.predict_intervals(preds[:50], regimes[:50], cov)
        l_prop, u_prop, fb_prop = cal_proposed.predict_intervals(preds[:50], regimes[:50], cov)

        np.testing.assert_allclose(l_reg, l_prop, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(u_reg, u_prop, rtol=1e-12, atol=1e-12)
        np.testing.assert_array_equal(fb_reg, fb_prop)


def test_fd001_single_regime_baseline_equivalence() -> None:
    """Verify that for FD001 (single regime 'C1'), global_hcp and regime_hcp are identical."""
    preds, labels, _, eids, cycles = _create_synthetic_calibration_data(n_engines=20)
    regimes_c1 = np.full(len(preds), "C1", dtype=object)

    cal_global = fit_calibrator_bundle(
        method_id=METHOD_GLOBAL,
        predictions=preds,
        labels=labels,
        regimes=regimes_c1,
        engine_ids=eids,
        endpoint_cycles=cycles,
        dataset_name="FD001",
        model_family="GBR",
        model_seed=2026,
    )

    cal_regime = fit_calibrator_bundle(
        method_id=METHOD_REGIME,
        predictions=preds,
        labels=labels,
        regimes=regimes_c1,
        engine_ids=eids,
        endpoint_cycles=cycles,
        dataset_name="FD001",
        model_family="GBR",
        model_seed=2026,
    )

    for cov in (0.80, 0.90, 0.95):
        l_glob, u_glob, fb_glob = cal_global.predict_intervals(preds[:30], regimes_c1[:30], cov)
        l_reg, u_reg, fb_reg = cal_regime.predict_intervals(preds[:30], regimes_c1[:30], cov)

        np.testing.assert_allclose(l_glob, l_reg, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(u_glob, u_reg, rtol=1e-12, atol=1e-12)
        assert not np.any(fb_reg)


def test_regime_minimum_support_and_global_fallback() -> None:
    """Verify that a regime with fewer than required engines falls back to global threshold."""
    # Create dataset where regime 'C6' is observed in only 3 engines (< 10)
    preds, labels, regimes, eids, cycles = _create_synthetic_calibration_data(n_engines=25)
    # Overwrite: only engine 1, 2, 3 have C6, others are C1..C5
    c6_mask = regimes == "C6"
    regimes[c6_mask & (eids > 3)] = "C1"

    cal = fit_calibrator_bundle(
        method_id=METHOD_REGIME,
        predictions=preds,
        labels=labels,
        regimes=regimes,
        engine_ids=eids,
        endpoint_cycles=cycles,
        dataset_name="FD002",
        model_family="GBR",
        model_seed=2026,
    )

    # For coverage 0.80, required engines is 10. Engine count for C6 is <= 3.
    b_80 = cal.coverage_bundles[0.80]
    c6_rec = b_80.regime_thresholds["C6"]
    assert c6_rec.fallback_used
    assert c6_rec.threshold == b_80.global_threshold

    # Prediction on C6 uses fallback
    test_p = np.array([50.0])
    test_r = np.array(["C6"])
    lower_fb, upper_fb, fb = cal.predict_intervals(test_p, test_r, 0.80)
    assert bool(fb[0])


def test_invalid_regime_label_rejection() -> None:
    """Verify that an invalid regime label outside dataset vocabulary raises ValueError."""
    preds, labels, regimes, eids, cycles = _create_synthetic_calibration_data(n_engines=25)
    cal = fit_calibrator_bundle(
        method_id=METHOD_GLOBAL,
        predictions=preds,
        labels=labels,
        regimes=regimes,
        engine_ids=eids,
        endpoint_cycles=cycles,
        dataset_name="FD002",
        model_family="GBR",
        model_seed=2026,
    )

    with pytest.raises(ValueError, match="Invalid regime 'UNKNOWN_REGIME'"):
        cal.predict_intervals(np.array([50.0]), np.array(["UNKNOWN_REGIME"]), 0.90)


def test_interval_nesting_for_fixed_calibration_route() -> None:
    """Verify intervals are nested (L_80 >= L_90 >= L_95 and U_80 <= U_90 <= U_95)."""
    preds, labels, regimes, eids, cycles = _create_synthetic_calibration_data(n_engines=25)
    cal = fit_calibrator_bundle(
        method_id=METHOD_GLOBAL,
        predictions=preds,
        labels=labels,
        regimes=regimes,
        engine_ids=eids,
        endpoint_cycles=cycles,
        dataset_name="FD002",
        model_family="GBR",
        model_seed=2026,
    )

    p_test = np.array([20.0, 50.0, 80.0])
    r_test = np.array(["C1", "C2", "C3"])

    l_80, u_80, _ = cal.predict_intervals(p_test, r_test, 0.80)
    l_90, u_90, _ = cal.predict_intervals(p_test, r_test, 0.90)
    l_95, u_95, _ = cal.predict_intervals(p_test, r_test, 0.95)

    assert np.all(l_80 >= l_90 - 1e-9)
    assert np.all(l_90 >= l_95 - 1e-9)
    assert np.all(u_80 <= u_90 + 1e-9)
    assert np.all(u_90 <= u_95 + 1e-9)


def test_insufficient_calibration_support_error() -> None:
    """Verify that infinite global threshold raises InsufficientCalibrationSupport."""
    # Only 3 engines: at 95% coverage, hierarchical threshold is infinite
    preds, labels, regimes, eids, cycles = _create_synthetic_calibration_data(n_engines=3)

    with pytest.raises(InsufficientCalibrationSupport):
        fit_calibrator_bundle(
            method_id=METHOD_GLOBAL,
            predictions=preds,
            labels=labels,
            regimes=regimes,
            engine_ids=eids,
            endpoint_cycles=cycles,
            dataset_name="FD002",
            model_family="GBR",
            model_seed=2026,
        )
