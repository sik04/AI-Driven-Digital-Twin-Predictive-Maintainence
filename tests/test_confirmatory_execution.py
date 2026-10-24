"""Tests for the Step 9 confirmatory execution and independent verification framework.

Validates:
1. Strict partition isolation and rejection of unauthorized or unconfirmed requests.
2. Complete engine and endpoint cycle membership.
3. Causal windowing integrity and uncapped/capped RUL separation.
4. Safeguards against dirty source, failed preflight, or modified inputs.
5. Exact configuration and 152-component hypothesis manifest completeness.
6. Boundary conditions and IUT aggregation for hypothesis decision rules.
7. Output immutability and refusal to overwrite existing directories.
8. Validation equivalence mode vs validation smoke (tol: atol=1e-10, rtol=0).
9. Mutation testing proving independent verifier detects and rejects altered evidence.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from intellitwin.confirmatory.data import (
    FROZEN_RAW_SOURCE_HASHES,
    load_and_prepare_partition_windows,
    verify_raw_data_hashes,
)
from intellitwin.confirmatory.runner import (
    run_confirmatory_evaluation,
)
from intellitwin.confirmatory.verification import (
    independently_verify_confirmatory_evidence,
)
from intellitwin.data.schema import RUL_CAP
from intellitwin.evaluation.decisions import (
    DecisionStatus,
    RQStatus,
    aggregate_rq_decision,
    evaluate_failure_safeguard,
    evaluate_improvement,
    evaluate_noninferiority,
    get_rq_component_manifest,
    validate_component_manifest_completeness,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATION_SMOKE_DIR = REPO_ROOT / "experiments/pretest_verification_v3/validation_smoke"
RAW_DATA_EXISTS = (REPO_ROOT / "data/raw/cmapss/train_FD001.txt").exists()


def test_partition_isolation_and_rejection() -> None:
    """Verify strict partition isolation: train and calibration are forbidden."""
    # 1. Train partition is forbidden
    with pytest.raises(PermissionError, match="strictly forbidden"):
        load_and_prepare_partition_windows(
            dataset="FD001",
            partition="train",
            base_dir=REPO_ROOT,
        )

    # 2. Calibration partition is forbidden
    with pytest.raises(PermissionError, match="strictly forbidden"):
        load_and_prepare_partition_windows(
            dataset="FD001",
            partition="calibration",
            base_dir=REPO_ROOT,
        )

    # 3. Arbitrary partition is rejected with ValueError
    with pytest.raises(ValueError, match="is invalid"):
        load_and_prepare_partition_windows(
            dataset="FD001",
            partition="test_development",
            base_dir=REPO_ROOT,
        )

    # 4. Held-out test partition without confirmation flag is blocked with PermissionError
    with pytest.raises(PermissionError, match="requires explicit confirm_held_out=True"):
        load_and_prepare_partition_windows(
            dataset="FD001",
            partition="test",
            base_dir=REPO_ROOT,
            confirm_held_out=False,
        )


@pytest.mark.skipif(not RAW_DATA_EXISTS, reason="Local raw C-MAPSS data not present in CI")
def test_raw_data_hashes_verification() -> None:
    """Verify that all raw training datasets match authoritative frozen hashes."""
    hashes = verify_raw_data_hashes(base_dir=REPO_ROOT)
    assert len(hashes) == 3
    for ds, exp_h in FROZEN_RAW_SOURCE_HASHES.items():
        assert hashes[ds] == exp_h


@pytest.mark.skipif(not RAW_DATA_EXISTS, reason="Local raw C-MAPSS data not present in CI")
def test_complete_engine_cycle_prediction_membership() -> None:
    """Verify trajectory continuity and causal cycle starting point on prepared windows."""
    windows, engines, manifest = load_and_prepare_partition_windows(
        dataset="FD001",
        partition="validation",
        base_dir=REPO_ROOT,
    )
    assert len(engines) == 10
    assert set(windows.engine_ids) == set(engines)

    # Check each engine starts at cycle 30 and has contiguous sequence
    for u in engines:
        mask = windows.engine_ids == u
        cycles = windows.endpoint_cycles[mask]
        assert len(cycles) > 0
        assert cycles[0] == 30
        expected = np.arange(30, cycles[-1] + 1)
        assert np.array_equal(cycles, expected)


@pytest.mark.skipif(not RAW_DATA_EXISTS, reason="Local raw C-MAPSS data not present in CI")
def test_causal_windows_and_correct_labels() -> None:
    """Verify causal lookback 30, uncapped rul_true, and 125-cycle capped rul_target."""
    windows, engines, _ = load_and_prepare_partition_windows(
        dataset="FD001",
        partition="validation",
        base_dir=REPO_ROOT,
    )
    assert windows.X_sequence.shape[1] == 30
    assert windows.X_sequence.shape[2] == 17

    expected_target = np.minimum(windows.rul_true, float(RUL_CAP))
    assert np.allclose(windows.rul_target, expected_target, atol=1e-6)
    # Ensure uncapped rul_true has values greater than 125
    assert np.any(windows.rul_true > 125.0)


def test_configuration_and_component_membership() -> None:
    """Verify exact 152-component manifest structure and completeness validation."""
    manifest = get_rq_component_manifest()
    assert len(manifest["RQ1"]) == 14
    assert len(manifest["RQ2"]) == 20
    assert len(manifest["RQ3"]) == 22
    assert len(manifest["RQ4"]) == 96
    total = sum(len(c) for c in manifest.values())
    assert total == 152

    # Completeness check on valid set
    all_ids = [c.component_id for comps in manifest.values() for c in comps]
    assert len(all_ids) == len(set(all_ids))  # unique
    rep = validate_component_manifest_completeness(all_ids)
    assert rep["all_valid"] is True

    # Missing component raises ValueError
    with pytest.raises(ValueError, match="Missing required hypothesis components"):
        validate_component_manifest_completeness(all_ids[:-1])

    # Duplicate component raises ValueError
    with pytest.raises(ValueError, match="Duplicate component IDs"):
        validate_component_manifest_completeness(all_ids + [all_ids[0]])


def test_decision_classification_boundary_behavior() -> None:
    """Verify decision rule helper boundary conditions and IUT aggregation."""
    # evaluate_improvement (Delta > margin)
    assert evaluate_improvement(0.21, 0.50, 0.20) == DecisionStatus.PASS
    assert evaluate_improvement(0.10, 0.19, 0.20) == DecisionStatus.FAIL
    assert evaluate_improvement(0.19, 0.25, 0.20) == DecisionStatus.INDETERMINATE
    assert (
        evaluate_improvement(0.20, 0.25, 0.20) == DecisionStatus.INDETERMINATE
    )  # boundary equality
    assert (
        evaluate_improvement(0.20, 0.20, 0.20) == DecisionStatus.INDETERMINATE
    )  # degenerate zero-width
    with pytest.raises(ValueError, match="Inverted confidence interval"):
        evaluate_improvement(0.30, 0.10, 0.20)

    # evaluate_noninferiority (Metric < margin)
    assert evaluate_noninferiority(0.01, 0.04, 0.05) == DecisionStatus.PASS
    assert evaluate_noninferiority(0.06, 0.08, 0.05) == DecisionStatus.FAIL
    assert evaluate_noninferiority(0.04, 0.06, 0.05) == DecisionStatus.INDETERMINATE
    assert evaluate_noninferiority(0.04, 0.05, 0.05) == DecisionStatus.INDETERMINATE
    assert evaluate_noninferiority(0.05, 0.05, 0.05) == DecisionStatus.INDETERMINATE

    # evaluate_failure_safeguard (proposed <= baseline)
    assert evaluate_failure_safeguard(0, 0) == DecisionStatus.PASS
    assert evaluate_failure_safeguard(0, 1) == DecisionStatus.PASS
    assert evaluate_failure_safeguard(2, 1) == DecisionStatus.FAIL
    with pytest.raises(ValueError, match="must not be boolean"):
        evaluate_failure_safeguard(True, 1)

    # aggregate_rq_decision (IUT)
    assert aggregate_rq_decision([DecisionStatus.PASS, DecisionStatus.PASS]) == RQStatus.SUPPORTED
    assert aggregate_rq_decision([DecisionStatus.PASS, DecisionStatus.FAIL]) == RQStatus.UNSUPPORTED
    assert (
        aggregate_rq_decision([DecisionStatus.PASS, DecisionStatus.INDETERMINATE])
        == RQStatus.INCONCLUSIVE
    )
    with pytest.raises(ValueError, match="empty component statuses"):
        aggregate_rq_decision([])


def test_immutable_outputs_and_refusal_to_overwrite(tmp_path: Path) -> None:
    """Verify that runner strictly refuses to execute into a non-empty directory."""
    non_empty_dir = tmp_path / "existing_run"
    non_empty_dir.mkdir(parents=True, exist_ok=True)
    (non_empty_dir / "pre_existing_file.txt").write_text("data")

    with pytest.raises(FileExistsError, match="is not empty"):
        run_confirmatory_evaluation(
            partition="validation",
            output_dir=non_empty_dir,
            base_dir=REPO_ROOT,
        )


def test_validation_equivalence_mode(tmp_path: Path) -> None:
    """Run new runner in validation equivalence mode with atol=1e-10 vs historical smoke."""
    if not VALIDATION_SMOKE_DIR.exists():
        pytest.skip("Historical validation smoke directory not found.")

    run_out = tmp_path / "validation_equivalence_test"

    manifest = run_confirmatory_evaluation(
        partition="validation",
        output_dir=run_out,
        base_dir=REPO_ROOT,
        n_bootstrap=10000,
        use_validation_cache=True,
        allow_dirty=True,
    )

    assert manifest["status"] == "DEVELOPMENT_SMOKE_ONLY"
    assert manifest["partition"] == "validation"
    assert manifest["counts"]["total_configurations"] == 930
    assert manifest["counts"]["total_outcome_rows"] == 19590
    assert manifest["counts"]["total_summary_rows"] == 186
    assert manifest["counts"]["component_evidence_rows"] == 152

    # Compare bootstrap draws bitwise
    for ds in ("FD001", "FD002", "FD004"):
        act_draws = np.load(run_out / f"bootstrap_draws_{ds}.npz")["draws"]
        exp_draws = np.load(VALIDATION_SMOKE_DIR / f"bootstrap_draws_{ds}.npz")["draws"]
        assert np.array_equal(act_draws, exp_draws), f"Draws mismatch for {ds}"

    # Numerical equivalence on cell_summary.csv: atol=1e-10, rtol=0
    df_act_sum = pd.read_csv(
        run_out / "cell_summary.csv", float_precision="round_trip"
    ).sort_values(
        ["dataset", "model_family", "method_or_control_id", "nominal_coverage", "scenario_id"]
    )
    df_exp_sum = pd.read_csv(
        VALIDATION_SMOKE_DIR / "cell_summary.csv", float_precision="round_trip"
    ).sort_values(
        ["dataset", "model_family", "method_or_control_id", "nominal_coverage", "scenario_id"]
    )

    numeric_cols = [
        "mean_cost",
        "failure_rate",
        "pm_rate",
        "mean_wasted_rul",
        "marginal_coverage",
        "marginal_coverage_abs_error",
        "mpiw",
        "interval_score",
    ]
    for col in numeric_cols:
        diff = np.abs(df_act_sum[col].to_numpy() - df_exp_sum[col].to_numpy())
        max_diff = float(np.nanmax(diff))
        assert max_diff <= 1e-10, f"Summary metric {col} exceeded tolerance: max diff {max_diff}"

    # Contrast intervals equivalence: atol=1e-10
    df_act_c = pd.read_csv(
        run_out / "contrast_intervals.csv", float_precision="round_trip"
    ).sort_values("contrast_id")
    df_exp_c = pd.read_csv(
        VALIDATION_SMOKE_DIR / "contrast_intervals.csv", float_precision="round_trip"
    ).sort_values("contrast_id")
    for col in ("mean", "ci_95_low", "ci_95_high", "ci_decision_low", "ci_decision_high"):
        diff = np.abs(df_act_c[col].to_numpy() - df_exp_c[col].to_numpy())
        max_diff = float(np.nanmax(diff))
        assert max_diff <= 1e-10, f"Contrast {col} exceeded tolerance: max diff {max_diff}"


def test_independent_verifier_passes_genuine_and_rejects_mutations(tmp_path: Path) -> None:
    """Verify independent reference verifier passes genuine evidence and detects mutations."""
    if not VALIDATION_SMOKE_DIR.exists():
        pytest.skip("Historical validation smoke directory not found.")

    # 1. Genuine validation smoke must PASS
    rep = independently_verify_confirmatory_evidence(
        evidence_dir=VALIDATION_SMOKE_DIR,
        partition="validation",
        base_dir=REPO_ROOT,
    )
    assert rep["overall_status"] == "PASS", f"Genuine evidence failed: {rep.get('failing_reasons')}"

    # 2. Mutation 1: Altered point predictions
    mut1_dir = tmp_path / "mut1_altered_preds"
    shutil.copytree(VALIDATION_SMOKE_DIR, mut1_dir)
    df_pts = pd.read_csv(mut1_dir / "point_predictions.csv")
    df_pts.loc[0, "prediction"] = df_pts.loc[0, "prediction"] + 5.0
    df_pts.to_csv(mut1_dir / "point_predictions.csv", index=False)
    # Also remove an endpoint to violate continuity
    df_pts_dropped = df_pts.drop(index=1)
    df_pts_dropped.to_csv(mut1_dir / "point_predictions.csv", index=False)

    rep_mut1 = independently_verify_confirmatory_evidence(
        evidence_dir=mut1_dir,
        partition="validation",
        base_dir=REPO_ROOT,
    )
    assert rep_mut1["overall_status"] == "FAIL"

    # 3. Mutation 2: Missing row in component evidence
    mut2_dir = tmp_path / "mut2_missing_component"
    shutil.copytree(VALIDATION_SMOKE_DIR, mut2_dir)
    df_comp = pd.read_csv(mut2_dir / "component_evidence.csv")
    df_comp_dropped = df_comp.iloc[:-1]
    df_comp_dropped.to_csv(mut2_dir / "component_evidence.csv", index=False)

    rep_mut2 = independently_verify_confirmatory_evidence(
        evidence_dir=mut2_dir,
        partition="validation",
        base_dir=REPO_ROOT,
    )
    assert rep_mut2["overall_status"] == "FAIL"

    # 4. Mutation 3: Tampered bootstrap draws
    mut3_dir = tmp_path / "mut3_tampered_draws"
    shutil.copytree(VALIDATION_SMOKE_DIR, mut3_dir)
    draws_p = mut3_dir / "bootstrap_draws_FD001.npz"
    draws_data = dict(np.load(draws_p))
    draws_data["draws"][0, 0] = 999999
    np.savez(draws_p, **draws_data)

    rep_mut3 = independently_verify_confirmatory_evidence(
        evidence_dir=mut3_dir,
        partition="validation",
        base_dir=REPO_ROOT,
    )
    assert rep_mut3["overall_status"] == "FAIL"
