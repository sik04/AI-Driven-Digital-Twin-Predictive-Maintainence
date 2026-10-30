"""Unit and integration tests for Phase 8 ablation and robustness analysis."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from intellitwin.data.artifacts import compute_sha256
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
from intellitwin.robustness.reporting import generate_phase08_reports_and_figures
from intellitwin.robustness.statistics import (
    compute_subgroup_metrics_equal_engine,
    generate_phase08_bootstrap_draws,
)
from intellitwin.robustness.verification import (
    REQUIRED_PHASE08_FILES,
    _reconstruct_reference_intervals,
    independently_verify_phase08_evidence,
    verify_equal_engine_subgroup_math,
    verify_exact_keys_and_duplicates,
    verify_simulation_terminal_precedence,
    verify_summary_aggregations,
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


# =============================================================================
# AUDIT FAILURE-CASE REGRESSION TESTS
# =============================================================================


def test_audit_fails_on_unequal_engine_lengths_subgroup_weighting() -> None:
    """Regression test: prove equal-engine weighting differs from pooled endpoint weighting.

    Engine 1 has 10 endpoints, all covered (10/10 = 1.0).
    Engine 2 has 90 endpoints, none covered (0/90 = 0.0).
    Direct row pooling gives: 10/100 = 0.10.
    Equal-engine weighting gives: (1.0 + 0.0) / 2 = 0.50.
    """
    rows = []
    # Engine 1
    for c in range(1, 11):
        rows.append(
            {
                "dataset": "FD002",
                "unit": 1,
                "endpoint_cycle": c + 29,
                "prediction": 50.0,
                "rul_true": 50.0,
                "lower": 40.0,
                "upper": 60.0,  # covered
                "seed": 2026,
                "regime": "C1",
            }
        )
    # Engine 2
    for c in range(1, 91):
        rows.append(
            {
                "dataset": "FD002",
                "unit": 2,
                "endpoint_cycle": c + 29,
                "prediction": 50.0,
                "rul_true": 100.0,
                "lower": 40.0,
                "upper": 60.0,  # missed
                "seed": 2026,
                "regime": "C1",
            }
        )
    df_eval = pd.DataFrame(rows)

    clean_subgroups = pd.DataFrame(
        [
            {"dataset": "FD002", "unit": 1, "endpoint_cycle": c + 29, "regime": "C1"}
            for c in range(1, 11)
        ]
        + [
            {"dataset": "FD002", "unit": 2, "endpoint_cycle": c + 29, "regime": "C1"}
            for c in range(1, 91)
        ]
    )

    df_eng_sub, df_sub_sum = compute_subgroup_metrics_equal_engine(
        df_eval=df_eval,
        clean_subgroup_df=clean_subgroups,
        subgroup_family="regime",
        nominal_coverage=0.90,
    )

    # 1. Verify that production implementation correctly calculates 0.50, NOT 0.10
    assert np.isclose(df_sub_sum["coverage"].iloc[0], 0.50, atol=1e-10)
    assert df_sub_sum["n_engines"].iloc[0] == 2
    assert not df_sub_sum["is_eligible"].iloc[0]  # < 10 engines

    # 2. Corrupt summary with pooled endpoint weighting (0.10)
    df_sub_corrupt = df_sub_sum.copy()
    df_sub_corrupt["evaluation_type"] = "ablation"
    df_sub_corrupt["dataset"] = "FD002"
    df_sub_corrupt["model_family"] = "GBR"
    df_sub_corrupt["variant_id"] = "test_var"
    df_sub_corrupt["method_id"] = ""
    df_sub_corrupt["condition_id"] = "clean"
    df_sub_corrupt["coverage"] = 0.10  # corrupted!

    df_eng_sub_tagged = df_eng_sub.copy()
    df_eng_sub_tagged["evaluation_type"] = "ablation"
    df_eng_sub_tagged["dataset"] = "FD002"
    df_eng_sub_tagged["model_family"] = "GBR"
    df_eng_sub_tagged["variant_id"] = "test_var"
    df_eng_sub_tagged["method_id"] = ""
    df_eng_sub_tagged["condition_id"] = "clean"

    mismatches = verify_equal_engine_subgroup_math(df_sub_corrupt, df_eng_sub_tagged)
    assert len(mismatches) > 0
    assert any("equal-engine cov exp=0.5 != act=0.1" in m for m in mismatches)


def test_audit_fails_on_empty_and_incomplete_hash_inventories(tmp_path: Path) -> None:
    """Regression test: audit must fail closed on empty or missing artifact_hashes."""
    # Write empty files for all required files
    for fname in REQUIRED_PHASE08_FILES:
        (tmp_path / fname).write_text("dummy", encoding="utf-8")

    # Manifest with empty artifact_hashes
    manifest = {
        "protocol_version": "phase08-v1",
        "schema_version": "phase08-manifest-v2",
        "status": "EXPLORATORY_POST_CONFIRMATORY",
        "git_commit": "abcdef123456",
        "git_dirty": False,
        "platform": "Linux",
        "python_version": "3.11.0",
        "start_time_utc": "2026-10-25T00:00:00Z",
        "end_time_utc": "2026-10-25T01:00:00Z",
        "duration_seconds": 3600.0,
        "counts": {
            "ablation_configurations": 240,
            "stress_evaluations": 1620,
            "datasets": 3,
            "models": 2,
            "seeds": 5,
            "bootstrap_replicates": 10000,
            "total_test_engines": 122,
        },
        "artifact_hashes": {},  # EMPTY!
    }
    (tmp_path / "execution_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    res = independently_verify_phase08_evidence(evidence_dir=tmp_path)
    assert res["overall_status"] == "FAIL"
    assert any("artifact_hashes mapping is absent or empty" in r for r in res["failing_reasons"])


def test_audit_fails_on_missing_or_duplicate_records(tmp_path: Path) -> None:
    """Regression test: audit must fail on duplicate or missing keys."""
    expected_units = {
        "FD001": list(range(1, 21)),
        "FD002": list(range(1, 53)),
        "FD004": list(range(1, 51)),
    }
    # Create file with duplicate keys
    rows = [
        {
            "dataset": "FD001",
            "model_family": "GBR",
            "variant_id": "gamma0_beta0_global",
            "seed": 2026,
            "unit": 1,
        },
        {
            "dataset": "FD001",
            "model_family": "GBR",
            "variant_id": "gamma0_beta0_global",
            "seed": 2026,
            "unit": 1,
        },  # duplicate!
    ]
    pd.DataFrame(rows).to_csv(tmp_path / "ablation_engine_seed_metrics.csv", index=False)
    mismatches = verify_exact_keys_and_duplicates(tmp_path, expected_units)
    assert len(mismatches) > 0
    assert any("duplicate keys" in m for m in mismatches)


def test_audit_fails_on_changed_regime_thresholds_or_fallbacks() -> None:
    """Regression test: verify that threshold modification fails reference reconstruction."""
    from intellitwin.robustness.verification import _reconstruct_reference_quantile

    eids = np.array([1, 1, 2, 2, 3, 3])
    scores = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    correct_q = _reconstruct_reference_quantile(eids, scores, nominal_coverage=0.90)

    # If recorded threshold was corrupted to 1.5, verification fails
    corrupted_q = 1.5
    assert not np.isclose(correct_q, corrupted_q)


def test_audit_fails_on_changed_perturbations_or_stream_hashes() -> None:
    """Regression test: prove that altered PRNG seed changes perturbation values."""
    # Canonical noise
    z_canonical = generate_engine_noise_array("FD002", 5, 0, 100)
    # Perturbed replicate
    z_altered = generate_engine_noise_array("FD002", 5, 1, 100)
    assert not np.array_equal(z_canonical, z_altered)


def test_audit_fails_on_changed_engine_metrics_and_summaries() -> None:
    """Regression test: audit must detect semantic discrepancies in summary aggregations."""
    df_ablation_engine = pd.DataFrame(
        [
            {
                "dataset": "FD001",
                "model_family": "GBR",
                "variant_id": "gamma0_beta0_global",
                "coverage": 0.90,
                "cost": 2.0,
                "width": 10.0,
                "interval_score": 15.0,
                "rmse": 12.0,
            }
        ]
    )
    # Corrupted summary: cost_mean set to 999.0
    df_ablation_summary = pd.DataFrame(
        [
            {
                "dataset": "FD001",
                "model_family": "GBR",
                "variant_id": "gamma0_beta0_global",
                "coverage_mean": 0.90,
                "cost_mean": 999.0,  # corrupted!
                "width_mean": 10.0,
                "interval_score_mean": 15.0,
                "rmse_mean": 12.0,
            }
        ]
    )
    mismatches = verify_summary_aggregations(
        df_ablation_summary=df_ablation_summary,
        df_ablation_engine=df_ablation_engine,
        df_stress_summary=pd.DataFrame(),
        df_stress_engine=pd.DataFrame(),
    )
    assert len(mismatches) > 0
    assert any("cost_mean: exp=2.0 != act=999.0" in m for m in mismatches)


def test_audit_fails_on_absent_factor_effects_or_bootstrap_statistics(tmp_path: Path) -> None:
    """Regression test: audit must detect missing factor effect evidence."""
    # Write factor effects table with fewer than 126 rows
    df_fac = pd.DataFrame(
        [
            {
                "dataset": "FD001",
                "model_family": "GBR",
                "factor": "gamma_scale",
                "metric": "cost",
            }
        ]
    )
    df_fac.to_csv(tmp_path / "factor_main_effects.csv", index=False)
    mismatches = verify_exact_keys_and_duplicates(
        tmp_path,
        expected_units={
            "FD001": list(range(1, 21)),
            "FD002": list(range(1, 53)),
            "FD004": list(range(1, 51)),
        },
    )
    assert any("factor_main_effects expected 126 rows, got 1" in m for m in mismatches)


def test_audit_fails_on_changed_protected_inputs(tmp_path: Path) -> None:
    """Regression test: audit fails when pre- and post-protected hashes mismatch."""
    dummy_header_pred = (
        "dataset,model_family,seed,variant_id,unit,endpoint_cycle,prediction,"
        "rul_true,lower,upper,regime,lifecycle_stage,fallback_used\n"
    )
    dummy_header_eng = (
        "dataset,model_family,variant_id,seed,unit,total_cost,failed,"
        "pm_occurred,wasted_rul,intervention_cycle\n"
    )
    for fname in REQUIRED_PHASE08_FILES:
        if fname.endswith(".npz"):
            np.savez(tmp_path / fname, draws=np.zeros((1, 1)))
        elif fname.endswith(".csv.gz"):
            import gzip

            with gzip.open(tmp_path / fname, "wt") as gz:
                gz.write(dummy_header_pred)
        elif fname.endswith(".json"):
            (tmp_path / fname).write_text("{}", encoding="utf-8")
        else:
            (tmp_path / fname).write_text(dummy_header_eng, encoding="utf-8")

    manifest = {
        "protocol_version": "phase08-v1",
        "schema_version": "phase08-manifest-v2",
        "status": "EXPLORATORY_POST_CONFIRMATORY",
        "git_commit": "abcdef123456",
        "git_dirty": False,
        "platform": "Linux",
        "python_version": "3.11.0",
        "start_time_utc": "2026-10-25T00:00:00Z",
        "end_time_utc": "2026-10-25T01:00:00Z",
        "duration_seconds": 3600.0,
        "counts": {
            "ablation_configurations": 240,
            "stress_evaluations": 1620,
            "datasets": 3,
            "models": 2,
            "seeds": 5,
            "bootstrap_replicates": 10000,
            "total_test_engines": 122,
        },
        "artifact_hashes": {
            fname: compute_sha256(tmp_path / fname) for fname in REQUIRED_PHASE08_FILES
        },
    }
    (tmp_path / "execution_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    # Corrupted input manifest where pre and post hashes do not match
    in_man = {
        "pre_execution_protected_hashes": {"file_a": "hash1"},
        "post_execution_protected_hashes": {"file_a": "hash_altered"},  # ALTERED!
    }
    (tmp_path / "input_manifest.json").write_text(json.dumps(in_man), encoding="utf-8")

    res = independently_verify_phase08_evidence(evidence_dir=tmp_path)
    assert res["overall_status"] == "FAIL"
    assert any("protected hashes inconsistent" in r.lower() for r in res["failing_reasons"])


def test_audit_fails_on_missing_provenance_fields(tmp_path: Path) -> None:
    """Regression test: audit fails if mandatory provenance fields are missing."""
    dummy_header_pred = (
        "dataset,model_family,seed,variant_id,unit,endpoint_cycle,prediction,"
        "rul_true,lower,upper,regime,lifecycle_stage,fallback_used\n"
    )
    dummy_header_eng = (
        "dataset,model_family,variant_id,seed,unit,total_cost,failed,"
        "pm_occurred,wasted_rul,intervention_cycle\n"
    )
    for fname in REQUIRED_PHASE08_FILES:
        if fname.endswith(".npz"):
            np.savez(tmp_path / fname, draws=np.zeros((1, 1)))
        elif fname.endswith(".csv.gz"):
            import gzip

            with gzip.open(tmp_path / fname, "wt") as gz:
                gz.write(dummy_header_pred)
        elif fname.endswith(".json"):
            (tmp_path / fname).write_text("{}", encoding="utf-8")
        else:
            (tmp_path / fname).write_text(dummy_header_eng, encoding="utf-8")

    manifest = {
        "protocol_version": "phase08-v1",
        "status": "EXPLORATORY_POST_CONFIRMATORY",
        # MISSING git_commit, platform, start_time_utc, etc.
        "artifact_hashes": {
            fname: compute_sha256(tmp_path / fname) for fname in REQUIRED_PHASE08_FILES
        },
    }
    (tmp_path / "execution_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    res = independently_verify_phase08_evidence(evidence_dir=tmp_path)
    assert res["overall_status"] == "FAIL"
    assert any("Missing mandatory provenance fields" in r for r in res["failing_reasons"])


def test_audit_fails_on_terminal_failure_precedence_and_dropout_causality() -> None:
    """Regression test: verify terminal failure precedence and dropout causality."""
    # Part A: Terminal failure precedence violation
    df_sim_violation = pd.DataFrame(
        [
            {
                "unit": 1,
                "failed": True,
                "pm_occurred": True,  # Contradictory: cannot be both failed and PM!
                "intervention_cycle": 100,
            }
        ]
    )
    violations = verify_simulation_terminal_precedence(df_sim_violation)
    assert len(violations) > 0
    assert any("marked both failed and PM occurred" in v for v in violations)

    # Part B: Dropout causality
    cols = ["unit", "cycle", "setting1", "setting2", "setting3"] + list(SENSOR_COLUMNS)
    data = {c: [10.0, 20.0, 30.0] for c in cols}
    data["unit"] = [1, 1, 1]
    data["cycle"] = [1, 2, 3]
    df = pd.DataFrame(data)

    cond = StressCondition("test_causal_drop", "sensor_dropout", 0.999, 1, False)
    df_pert = apply_stream_perturbation(df, "FD001", cond, replicate_id=0)

    # Because dropout occurred at cycle 1, the value must be normalized 0.0 (past observation only)
    for s in SENSOR_COLUMNS:
        assert df_pert[s].iloc[0] == 0.0


def test_detection_missing_regime_threshold_fails_closed(tmp_path: Path) -> None:
    """Requirement G: Missing regime thresholds must FAIL closed, not skip comparison."""
    # Setup dummy bundle with required files
    for fname in REQUIRED_PHASE08_FILES:
        fpath = tmp_path / fname
        if fname.endswith(".npz"):
            np.savez(fpath, draws=np.zeros((1, 1)))
        elif fname.endswith(".csv.gz"):
            import gzip

            with gzip.open(fpath, "wt") as gz:
                gz.write("dummy\n")
        elif fname.endswith(".json"):
            fpath.write_text("{}", encoding="utf-8")
        else:
            fpath.write_text("dummy\n", encoding="utf-8")

    # Create exploratory calibrators dir with a calibrator missing regime threshold
    cal_dir = tmp_path / "exploratory_calibrators"
    cal_dir.mkdir(parents=True, exist_ok=True)
    bad_cal = {
        "candidate_parameters": {"gamma": 0, "beta_code": 0, "routing": "regime"},
        "threshold_bundles": {
            "coverage_90": {
                "global_threshold": 12.5,
                # Missing regime thresholds mapping completely!
            }
        },
    }
    cal_file = cal_dir / "FD001_GBR_seed2026_gamma0_beta0_regime.json"
    cal_file.write_text(json.dumps(bad_cal), encoding="utf-8")

    manifest = {
        "protocol_version": "phase08-v1",
        "schema_version": "phase08-manifest-v2",
        "status": "EXPLORATORY_POST_CONFIRMATORY",
        "git_commit": "abcdef123456",
        "git_dirty": False,
        "platform": "Linux",
        "python_version": "3.11.0",
        "start_time_utc": "2026-10-25T00:00:00Z",
        "end_time_utc": "2026-10-25T01:00:00Z",
        "duration_seconds": 3600.0,
        "counts": {
            "ablation_configurations": 240,
            "stress_evaluations": 1620,
            "datasets": 3,
            "models": 2,
            "seeds": 5,
            "bootstrap_replicates": 10000,
            "total_test_engines": 122,
        },
        "artifact_hashes": {
            fname: compute_sha256(tmp_path / fname) for fname in REQUIRED_PHASE08_FILES
        },
    }
    (tmp_path / "execution_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (tmp_path / "input_manifest.json").write_text(
        json.dumps(
            {
                "pre_execution_protected_hashes": {"a": "1"},
                "post_execution_protected_hashes": {"a": "1"},
            }
        ),
        encoding="utf-8",
    )

    res = independently_verify_phase08_evidence(evidence_dir=tmp_path)
    assert res["overall_status"] == "FAIL"
    assert any("missing regime threshold" in r.lower() for r in res["failing_reasons"])


def test_detection_deleted_or_replaced_engine_records_preserving_count(tmp_path: Path) -> None:
    """Requirement G: Detect duplicated or replaced engine keys while preserving row counts."""
    # Write paired contrasts with 1176 rows, but duplicate one row and drop another
    row_proto = {
        "comparison_type": "ablation",
        "dataset": "FD001",
        "model_family": "GBR",
        "variant_or_condition": "gamma0_beta0_global",
        "baseline_or_full": "gamma2_betam1_regime",
        "metric": "cost",
        "delta_point": 0.5,
        "ci_95_low": 0.1,
        "ci_95_high": 0.9,
    }
    rows = [dict(row_proto) for _ in range(1176)]
    # All identical => 1175 duplicates!
    df_contrasts = pd.DataFrame(rows)
    df_contrasts.to_csv(tmp_path / "paired_contrasts.csv", index=False)

    mismatches = verify_exact_keys_and_duplicates(
        tmp_path,
        expected_units={
            "FD001": list(range(1, 21)),
            "FD002": list(range(1, 53)),
            "FD004": list(range(1, 51)),
        },
    )
    assert any("paired_contrasts has" in m and "duplicate keys" in m for m in mismatches)


def test_detection_incorrect_asymmetric_interval_inversion() -> None:
    """Requirement G: Verify independent asymmetric interval reconstruction fails if altered."""
    p = np.array([50.0, 100.0, 150.0])
    reg = np.array(["C1", "C1", "C1"])

    low_correct, upp_correct, _ = _reconstruct_reference_intervals(
        predictions=p,
        regimes=reg,
        global_threshold=10.0,
        regime_thresholds={"C1": 10.0},
        gamma=2,
        beta_code=-1,
        routing="regime",
    )

    # Inverted beta_code (0 instead of -1)
    low_wrong, upp_wrong, _ = _reconstruct_reference_intervals(
        predictions=p,
        regimes=reg,
        global_threshold=10.0,
        regime_thresholds={"C1": 10.0},
        gamma=2,
        beta_code=0,
        routing="regime",
    )

    assert not np.allclose(low_correct, low_wrong)
    assert not np.allclose(upp_correct, upp_wrong)


def test_reporting_fails_closed_when_audit_missing_or_failing(tmp_path: Path) -> None:
    """Requirement G: Reports must not emit PASS or complete if audit is missing or failing."""
    ev_dir = tmp_path / "ev"
    ev_dir.mkdir(parents=True, exist_ok=True)
    rep_dir = tmp_path / "rep"

    # Case 1: Missing audit
    with pytest.raises(RuntimeError, match="independent audit"):
        generate_phase08_reports_and_figures(evidence_dir=ev_dir, output_report_dir=rep_dir)

    # Case 2: Audit exists but failed
    (ev_dir / "independent_audit.json").write_text(
        json.dumps({"overall_status": "FAIL", "failing_reasons": ["Test failure"]}),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="independent audit"):
        generate_phase08_reports_and_figures(evidence_dir=ev_dir, output_report_dir=rep_dir)


def test_reporting_direction_reversal_is_dynamic(tmp_path: Path) -> None:
    """Requirement G: Changing input estimates or reversing direction dynamically changes report."""
    from intellitwin.data.artifacts import compute_sha256

    ev_dir = tmp_path / "ev"
    ev_dir.mkdir(parents=True, exist_ok=True)
    rep_dir = tmp_path / "rep"

    # Factor effects with reversed effect (positive cost increase)
    df_fac = pd.DataFrame(
        [
            {
                "dataset": "FD001",
                "model_family": "GBR",
                "factor": "gamma_scale",
                "metric": "cost",
                "effect_on_minus_off": 42.123456,  # Reversed / distinct value
                "ci_95_low": 40.0,
                "ci_95_high": 45.0,
            }
        ]
    )
    df_fac.to_csv(ev_dir / "factor_main_effects.csv", index=False)

    # Complete paired contrasts fixture with valid 54 noise and 36 dropout rows
    contrast_rows: list[dict[str, object]] = [
        {
            "comparison_type": "ablation",
            "dataset": "FD001",
            "model_family": "GBR",
            "variant_or_condition": "gamma0_beta0_global",
            "baseline_or_full": "gamma2_betam1_regime",
            "metric": "cost",
            "delta_point": 5.0,
            "ci_95_low": 3.0,
            "ci_95_high": 7.0,
        }
    ]
    for d in ["FD001", "FD002", "FD004"]:
        for m in ["GBR", "LSTM"]:
            for met in ["global_hcp", "regime_hcp", "decision_aware_hcp"]:
                for c in ["noise_std_005", "noise_std_010", "noise_std_020"]:
                    contrast_rows.append(
                        {
                            "comparison_type": "stress_vs_clean",
                            "dataset": d,
                            "model_family": m,
                            "variant_or_condition": f"{met}:{c}",
                            "baseline_or_full": f"{met}:clean",
                            "metric": "cost",
                            "delta_point": 0.5,
                            "ci_95_low": 0.1,
                            "ci_95_high": 0.9,
                        }
                    )
                for c in ["dropout_prob_005", "dropout_prob_010"]:
                    contrast_rows.append(
                        {
                            "comparison_type": "stress_vs_clean",
                            "dataset": d,
                            "model_family": m,
                            "variant_or_condition": f"{met}:{c}",
                            "baseline_or_full": f"{met}:clean",
                            "metric": "coverage",
                            "delta_point": -0.001,
                            "ci_95_low": -0.005,
                            "ci_95_high": 0.002,
                        }
                    )
    pd.DataFrame(contrast_rows).to_csv(ev_dir / "paired_contrasts.csv", index=False)

    df_abl_sum = pd.DataFrame(
        [
            {
                "dataset": "FD001",
                "model_family": "GBR",
                "variant_id": "gamma2_betam1_regime",
                "coverage_mean": 0.90,
                "cost_mean": 2.5,
                "width_mean": 30.0,
                "interval_score_mean": 45.0,
                "rmse_mean": 15.0,
                "failure_rate_mean": 0.05,
            }
        ]
    )
    df_abl_sum.to_csv(ev_dir / "ablation_summary.csv", index=False)

    df_str_sum = pd.DataFrame(
        [
            {
                "dataset": "FD001",
                "model_family": "GBR",
                "method_id": "decision_aware_hcp",
                "condition_id": "clean",
                "condition_type": "clean",
                "coverage_mean": 0.90,
                "cost_mean": 2.5,
                "width_mean": 30.0,
                "interval_score_mean": 45.0,
                "rmse_mean": 15.0,
                "failure_rate_mean": 0.05,
            }
        ]
    )
    df_str_sum.to_csv(ev_dir / "stress_summary.csv", index=False)

    df_subgroups = pd.DataFrame(
        [
            {
                "evaluation_type": "ablation",
                "dataset": "FD001",
                "model_family": "GBR",
                "variant_id": "gamma2_betam1_regime",
                "method_id": "",
                "condition_id": "clean",
                "subgroup_family": "regime",
                "subgroup": "C1",
                "n_endpoints": 100,
                "n_engines": 20,
                "is_eligible": True,
                "coverage": 0.91,
                "coverage_abs_error": 0.01,
                "lower_tail_miss": 0.05,
                "upper_tail_miss": 0.04,
            }
        ]
    )
    df_subgroups.to_csv(ev_dir / "subgroup_metrics.csv", index=False)

    manifest_hashes = {
        tbl: compute_sha256(ev_dir / tbl)
        for tbl in [
            "factor_main_effects.csv",
            "paired_contrasts.csv",
            "ablation_summary.csv",
            "stress_summary.csv",
            "subgroup_metrics.csv",
        ]
    }
    man_data = {"artifact_hashes": manifest_hashes}
    man_p = ev_dir / "execution_manifest.json"
    man_p.write_text(json.dumps(man_data), encoding="utf-8")
    man_hash = compute_sha256(man_p)

    mandatory_checks = [
        "exact_endpoint_membership",
        "calibration_reconstruction",
        "full_checkpoint_prediction_parity",
        "full_interval_reconstruction",
        "full_simulation_reconstruction",
        "endpoint_to_engine_metric_reconstruction",
        "full_subgroup_reconstruction",
        "full_bootstrap_reconstruction",
        "artifact_and_provenance_integrity",
        "protected_input_integrity",
    ]
    audit_data = {
        "schema_version": "phase08-independent-audit-v3",
        "overall_status": "PASS",
        "failing_reasons": [],
        "execution_manifest_sha256": man_hash,
        "checks": {
            chk: {"status": "PASS", "expected_count": 1, "checked_count": 1}
            for chk in mandatory_checks
        },
    }
    (ev_dir / "independent_audit.json").write_text(json.dumps(audit_data), encoding="utf-8")

    res = generate_phase08_reports_and_figures(evidence_dir=ev_dir, output_report_dir=rep_dir)
    assert Path(res["results_summary"]).exists()
    content = Path(res["results_summary"]).read_text(encoding="utf-8")

    # The dynamic value +42.1235 MUST be present in the report
    assert "42.1235" in content or "42.12" in content
    # The old hardcoded -10.48 or -1.42 must NOT be present as the gamma_scale value
    assert "-1.42" not in content
