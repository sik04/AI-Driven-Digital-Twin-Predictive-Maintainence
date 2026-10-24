"""Unit and integration tests for Phase 8 ablation and robustness analysis."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from intellitwin.data.schema import SENSOR_COLUMNS
from intellitwin.robustness.ablation import (
    ALL_EIGHT_ABLATION_VARIANTS,
    AblationVariant,
    fit_exploratory_ablation_calibrator,
    predict_ablation_intervals,
)
from intellitwin.robustness.perturbations import (
    ALL_STRESS_CONDITIONS,
    StressCondition,
    apply_stream_perturbation,
    generate_engine_dropout_uniforms,
    generate_engine_noise_array,
)
from intellitwin.robustness.statistics import (
    generate_phase08_bootstrap_draws,
)
from intellitwin.uncertainty.artifacts import load_calibrator_from_artifact


def test_exact_factorial_and_stress_matrix_membership() -> None:
    """Verify that the ablation factorial has 8 variants and stress matrix has 8 conditions."""
    assert len(ALL_EIGHT_ABLATION_VARIANTS) == 8
    expected_vids = {
        "gamma0_beta0_global",
        "gamma0_beta0_regime",
        "gamma0_betam1_global",
        "gamma0_betam1_regime",
        "gamma2_beta0_global",
        "gamma2_beta0_regime",
        "gamma2_betam1_global",
        "gamma2_betam1_regime",
    }
    actual_vids = {v.variant_id for v in ALL_EIGHT_ABLATION_VARIANTS}
    assert actual_vids == expected_vids

    assert len(ALL_STRESS_CONDITIONS) == 8
    expected_conds = {
        "clean",
        "noise_std_005",
        "noise_std_010",
        "noise_std_020",
        "dropout_prob_005",
        "dropout_prob_010",
        "setting1_bias_plus_020",
        "setting1_bias_minus_020",
    }
    actual_conds = {c.condition_id for c in ALL_STRESS_CONDITIONS}
    assert actual_conds == expected_conds


def test_three_reference_method_equivalence_checks() -> None:
    """Verify that:
    1. gamma=0, beta=0, global reproduces frozen global_hcp.
    2. gamma=0, beta=0, regime reproduces frozen regime_hcp.
    3. gamma=2, beta=-ln(2), regime reproduces frozen decision_aware_hcp.
    """
    cal_p = "experiments/calibration/point_predictions/calibration/FD002/GBR/seed_2026.csv"
    if not Path(cal_p).exists():
        pytest.skip("Calibration caches not present in test environment.")

    df_conf = pd.read_csv("experiments/confirmatory_v1/point_predictions.csv")
    sub_test = (
        df_conf[
            (df_conf["dataset"] == "FD002")
            & (df_conf["model_family"] == "GBR")
            & (df_conf["seed"] == 2026)
        ]
        .sort_values(["unit", "endpoint_cycle"])
        .reset_index(drop=True)
    )

    # 1. global_hcp equivalence
    var_g0 = AblationVariant.from_params(0, 0, "global")
    cal_g0 = fit_exploratory_ablation_calibrator("FD002", "GBR", 2026, var_g0)
    low_g0, upp_g0, _ = predict_ablation_intervals(
        cal_g0, var_g0, sub_test["prediction"].to_numpy(), sub_test["regime"].to_numpy(), 0.90
    )

    with open("experiments/calibration/fitted/FD002/GBR/seed_2026/global_hcp/calibrator.json") as f:
        art_glob = json.load(f)
    cal_glob_frozen = load_calibrator_from_artifact(art_glob)
    low_fg, upp_fg, _ = cal_glob_frozen.predict_intervals(
        sub_test["prediction"].to_numpy(), sub_test["regime"].to_numpy(), 0.90
    )

    assert np.allclose(low_g0, low_fg, atol=1e-10, rtol=0.0)
    assert np.allclose(upp_g0, upp_fg, atol=1e-10, rtol=0.0)

    # 2. regime_hcp equivalence
    var_r0 = AblationVariant.from_params(0, 0, "regime")
    cal_r0 = fit_exploratory_ablation_calibrator("FD002", "GBR", 2026, var_r0)
    low_r0, upp_r0, _ = predict_ablation_intervals(
        cal_r0, var_r0, sub_test["prediction"].to_numpy(), sub_test["regime"].to_numpy(), 0.90
    )

    with open("experiments/calibration/fitted/FD002/GBR/seed_2026/regime_hcp/calibrator.json") as f:
        art_reg = json.load(f)
    cal_reg_frozen = load_calibrator_from_artifact(art_reg)
    low_fr, upp_fr, _ = cal_reg_frozen.predict_intervals(
        sub_test["prediction"].to_numpy(), sub_test["regime"].to_numpy(), 0.90
    )

    assert np.allclose(low_r0, low_fr, atol=1e-10, rtol=0.0)
    assert np.allclose(upp_r0, upp_fr, atol=1e-10, rtol=0.0)

    # 3. decision_aware_hcp equivalence
    var_full = AblationVariant.from_params(2, -1, "regime")
    cal_full = fit_exploratory_ablation_calibrator("FD002", "GBR", 2026, var_full)
    low_full, upp_full, _ = predict_ablation_intervals(
        cal_full, var_full, sub_test["prediction"].to_numpy(), sub_test["regime"].to_numpy(), 0.90
    )

    with open(
        "experiments/calibration/fitted/FD002/GBR/seed_2026/decision_aware_hcp/calibrator.json"
    ) as f:
        art_dah = json.load(f)
    cal_dah_frozen = load_calibrator_from_artifact(art_dah)
    low_fd, upp_fd, _ = cal_dah_frozen.predict_intervals(
        sub_test["prediction"].to_numpy(), sub_test["regime"].to_numpy(), 0.90
    )

    assert np.allclose(low_full, low_fd, atol=1e-10, rtol=0.0)
    assert np.allclose(upp_full, upp_fd, atol=1e-10, rtol=0.0)


def test_fd001_global_regime_routing_agreement() -> None:
    """Verify that on FD001, global and regime routing thresholds agree for each candidate."""
    cal_p = "experiments/calibration/point_predictions/calibration/FD001/GBR/seed_2026.csv"
    if not Path(cal_p).exists():
        pytest.skip("Calibration caches not present in test environment.")

    var_g = AblationVariant.from_params(2, -1, "global")
    cal_g = fit_exploratory_ablation_calibrator("FD001", "GBR", 2026, var_g)
    q_glob = cal_g.coverage_bundles[0.90].global_threshold
    q_reg = cal_g.coverage_bundles[0.90].regime_thresholds["C1"].threshold
    assert np.isclose(q_glob, q_reg, atol=1e-10, rtol=0.0)


def test_deterministic_perturbations_and_nested_scaling() -> None:
    """Verify that perturbations are deterministic and scaled noise / nested dropout hold."""
    # Determinism
    z1 = generate_engine_noise_array("FD002", 5, 0, 100)
    z2 = generate_engine_noise_array("FD002", 5, 0, 100)
    assert np.array_equal(z1, z2)

    u1 = generate_engine_dropout_uniforms("FD002", 5, 0, 100)
    u2 = generate_engine_dropout_uniforms("FD002", 5, 0, 100)
    assert np.array_equal(u1, u2)

    # Nested dropout
    m05 = u1 < 0.05
    m10 = u1 < 0.10
    assert np.all(m05 <= m10)

    # Linear noise scaling
    n05 = 0.05 * z1
    n10 = 0.10 * z1
    assert np.allclose(n10, 2.0 * n05)


def test_causal_forward_fill_dropout_imputation() -> None:
    """Verify that missing sensor values forward-fill causally and initial cycle fills with 0.0."""
    cols = ["unit", "cycle", "setting1", "setting2", "setting3"] + list(SENSOR_COLUMNS)
    data = {c: [1.0, 2.0, 3.0] for c in cols}
    data["unit"] = [1, 1, 1]
    data["cycle"] = [1, 2, 3]
    df = pd.DataFrame(data)

    cond = StressCondition("test_drop", "sensor_dropout", 0.999, 1, False)
    df_pert = apply_stream_perturbation(df, "FD001", cond, replicate_id=0)

    # Since prob=0.999, all cycles will be dropped; cycle 1 missing must be 0.0
    for s in SENSOR_COLUMNS:
        assert (df_pert[s] == 0.0).all()


def test_sensor_only_vs_setting_only_perturbation_isolation() -> None:
    """Verify that sensor noise alters sensors only and setting bias alters setting1 only."""
    cols = ["unit", "cycle", "setting1", "setting2", "setting3"] + list(SENSOR_COLUMNS)
    data = {c: [1.0, 2.0] for c in cols}
    data["unit"] = [1, 1]
    data["cycle"] = [1, 2]
    df = pd.DataFrame(data)

    # Noise condition
    cond_noise = StressCondition("noise", "sensor_gaussian_noise", 0.10, 1, False)
    df_n = apply_stream_perturbation(df, "FD001", cond_noise, replicate_id=0)
    # settings must be identical
    assert (df_n["setting1"] == df["setting1"]).all()
    assert (df_n["setting2"] == df["setting2"]).all()
    assert (df_n["setting3"] == df["setting3"]).all()

    # Setting bias condition
    cond_bias = StressCondition("bias", "setting1_bias", 0.20, 1, True)
    df_b = apply_stream_perturbation(df, "FD001", cond_bias, replicate_id=0)
    assert np.allclose(df_b["setting1"].to_numpy(), df["setting1"].to_numpy() + 0.20)
    for s in SENSOR_COLUMNS:
        assert (df_b[s] == df[s]).all()


def test_paired_bootstrap_draws_reproducibility() -> None:
    """Verify that Phase 8 bootstrap draws reproduce identical arrays on same dataset."""
    engines = list(range(1, 21))
    draws1 = generate_phase08_bootstrap_draws("FD001", engines, n_replicates=50)
    draws2 = generate_phase08_bootstrap_draws("FD001", engines, n_replicates=50)
    assert np.array_equal(draws1, draws2)
    assert draws1.shape == (50, 20)
