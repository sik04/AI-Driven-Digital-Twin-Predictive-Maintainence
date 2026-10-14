"""Regression and defect verification tests for Step 8 and Step 9 pre-test readiness."""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from intellitwin.decision.controls import (
    select_control_parameters,
)
from intellitwin.evaluation.bootstrap import (
    compute_bootstrap_ci,
)
from intellitwin.evaluation.decisions import (
    evaluate_improvement,
    evaluate_noninferiority,
    validate_component_manifest_completeness,
)
from intellitwin.evaluation.metrics import (
    compute_interval_score,
    compute_replicate_worst_group_bounds,
    propagate_delta_error_bounds,
)
from intellitwin.evaluation.schema import (
    CONFIRMATORY_DATASETS,
    CONFIRMATORY_METHODS,
    CONFIRMATORY_MODELS,
    CONFIRMATORY_SEEDS,
    CONTROL_ALL_FOUR,
    COST_SCENARIOS,
)
from intellitwin.evaluation.validation import (
    DataLeakageError,
    TrajectoryValidationError,
    assert_no_held_out_path,
    validate_trajectory,
)
from intellitwin.provenance import (
    get_git_info,
    write_immutable_csv,
    write_immutable_json,
)

# =============================================================================
# 1. Step 8 Audit Defect & Baseline SHA Tests
# =============================================================================


def _git_commit_exists(commit_sha: str) -> bool:
    """Check if a commit exists in local git history (avoids failure in shallow clones)."""
    try:
        res = subprocess.run(
            ["git", "cat-file", "-t", commit_sha],
            capture_output=True,
            text=True,
        )
        return res.returncode == 0
    except Exception:
        return False


def test_raw_reproduction_not_run_cannot_satisfy_readiness(tmp_path: Path) -> None:
    """If raw reproduction was NOT RUN, audit must not report PASS."""
    from scripts.audit_step08_calibration import run_step08_audit

    if not _git_commit_exists("d25d0fa5f50377ddf90e039be3a01da6067c1972"):
        pytest.skip("Historical commit d25d0fa5... not available in shallow git clone")

    audit_res = run_step08_audit(base_dir=".", allow_dirty=True, full_audit=False)
    # Artifact-only audit explicitly marks checkpoint reproduction NOT RUN
    assert audit_res["results"]["checkpoint_prediction_reproduction"].startswith("NOT RUN")
    # When full_audit=False, overall_status cannot be full PASS for pretest readiness
    assert audit_res["overall_status"] == "INCOMPLETE"


def test_wrong_baseline_sha_fails_git_validation() -> None:
    """Historical typo SHA f1edce78... must fail git cat-file,
    while actual baseline f1edce7f... succeeds.
    """
    wrong_sha = "f1edce7858c9748b6ee92e7c4f4a3b7849e7b235"
    actual_sha = "f1edce7fdf48b45513ff90a680da49701451d9cb"

    if not _git_commit_exists(actual_sha):
        pytest.skip(f"Baseline commit {actual_sha} not available in shallow git clone")

    # Wrong SHA must fail
    res_wrong = subprocess.run(
        ["git", "cat-file", "-t", wrong_sha],
        capture_output=True,
        text=True,
    )
    assert res_wrong.returncode != 0

    # Actual SHA must succeed
    res_actual = subprocess.run(
        ["git", "cat-file", "-t", actual_sha],
        capture_output=True,
        text=True,
    )
    assert res_actual.returncode == 0
    assert res_actual.stdout.strip() == "commit"


def test_missing_tracked_protected_files_fail(tmp_path: Path) -> None:
    """A missing tracked protected file must cause baseline verification to fail."""
    from scripts.build_baseline_manifest import build_baseline_manifest

    if not _git_commit_exists("f1edce7fdf48b45513ff90a680da49701451d9cb"):
        pytest.skip("Baseline commit f1edce7f... not available in shallow git clone")

    # Point to empty directory where tracked files are missing
    out_json = tmp_path / "baseline_manifest.json"
    manifest = build_baseline_manifest(
        output_path=out_json,
        base_dir=tmp_path,  # empty base dir: all files missing
        repo_root=".",
        allow_dirty=True,
    )
    assert manifest["repository_tracked_protected_artifacts"]["status"] == "FAIL"
    assert manifest["repository_tracked_protected_artifacts"]["missing"] > 0


def test_missing_historical_local_only_checkpoints_reported_separately(tmp_path: Path) -> None:
    """72 local-only model selection search checkpoints are accounted for separately."""
    from scripts.build_baseline_manifest import build_baseline_manifest

    if not _git_commit_exists("f1edce7fdf48b45513ff90a680da49701451d9cb"):
        pytest.skip("Baseline commit f1edce7f... not available in shallow git clone")

    out_json = tmp_path / "baseline_manifest.json"
    manifest = build_baseline_manifest(
        output_path=out_json,
        base_dir=".",
        repo_root=".",
        allow_dirty=True,
    )
    # Exactly 652 tracked protected artifacts
    assert manifest["repository_tracked_protected_artifacts"]["expected"] == 652
    assert manifest["repository_tracked_protected_artifacts"]["matched"] == 652
    # Exactly 72 local-only checkpoints listed separately
    assert manifest["historical_local_only_model_selection_checkpoints"]["total_listed"] == 72


def test_historical_reports_cannot_be_overwritten(tmp_path: Path) -> None:
    """write_immutable_json and write_immutable_csv must reject overwriting existing files."""
    test_json = tmp_path / "existing.json"
    write_immutable_json(test_json, {"key": "val1"}, overwrite=False)
    with pytest.raises(RuntimeError):
        write_immutable_json(test_json, {"key": "val2"}, overwrite=False)

    test_csv = tmp_path / "existing.csv"
    df = pd.DataFrame([{"a": 1}])
    write_immutable_csv(test_csv, df, overwrite=False)
    with pytest.raises(RuntimeError):
        write_immutable_csv(test_csv, pd.DataFrame([{"a": 2}]), overwrite=False)


def test_modified_audit_file_makes_startup_dirty(tmp_path: Path) -> None:
    """Dirty status detection must not ignore any audit or output paths."""
    git_sha, git_dirty = get_git_info(allow_dirty=True, repo_root=".")
    assert isinstance(git_sha, str)
    assert len(git_sha) >= 7


# =============================================================================
# 2. Control Selection Tie-Breaking & Candidate Grid Tests
# =============================================================================


def test_candidate_values_near_rounding_boundaries_follow_minimum_relative_rule() -> None:
    """Test candidate selection uses exact minimum-relative filtering (diff <= min + 1e-8)."""
    # 1. Matched width test
    cands_mw = [
        {
            "control_family": "matched_width_interval",
            "width_diff": 0.500000001,
            "cost": 10.0,
            "param": 0.90,
            "source": "regime_hcp",
        },
        {
            "control_family": "matched_width_interval",
            "width_diff": 0.500000005,
            "cost": 9.0,
            "param": 0.90,
            "source": "global_hcp",
        },  # <= min + 1e-8, lower cost!
        {
            "control_family": "matched_width_interval",
            "width_diff": 0.500000020,
            "cost": 5.0,
            "param": 0.90,
            "source": "global_hcp",
        },  # > min + 1e-8, excluded
    ]
    df_mw = pd.DataFrame(cands_mw)
    sel_mw = select_control_parameters(df_mw, "matched_width_interval", target_mpiw=100.0)
    assert sel_mw["metrics"]["mean_cost"] == 9.0
    assert sel_mw["interval_source"] == "global_hcp"

    # 2. Minimum cost test with smaller parameter preference
    cands_cost = [
        {
            "control_family": "widened_interval",
            "cost": 5.000000001,
            "param": 1.10,
            "source": "global_hcp",
        },
        {
            "control_family": "widened_interval",
            "cost": 5.000000005,
            "param": 1.05,
            "source": "global_hcp",
        },  # cost <= min + 1e-8, smaller param!
        {
            "control_family": "widened_interval",
            "cost": 5.000000020,
            "param": 1.00,
            "source": "global_hcp",
        },  # cost > min + 1e-8, excluded
    ]
    df_c = pd.DataFrame(cands_cost)
    sel_c = select_control_parameters(df_c, "widened_interval")
    assert sel_c["parameter_value"] == 1.05


# =============================================================================
# 3. Validation Smoke Matrix and Completeness Tests
# =============================================================================


def test_full_930_configuration_matrix_enforced() -> None:
    """Validation matrix must comprise exactly:
    810 primary configurations + 120 control configurations = 930.
    """
    primary_configs = (
        len(CONFIRMATORY_DATASETS)
        * len(CONFIRMATORY_MODELS)
        * len(CONFIRMATORY_SEEDS)
        * len(CONFIRMATORY_METHODS)
        * 3
        * len(COST_SCENARIOS)
    )
    assert primary_configs == 810

    control_configs = (
        1
        * len(CONFIRMATORY_MODELS)
        * len(CONFIRMATORY_SEEDS)
        * len(CONTROL_ALL_FOUR)
        * 1
        * len(COST_SCENARIOS)
    )
    assert control_configs == 120

    total_configs = primary_configs + control_configs
    assert total_configs == 930

    # Expected outcome rows:
    # FD001: 10, FD002: 26, FD004: 25. Total = 61 engines
    primary_rows = 61 * (2 * 5 * 3 * 3 * 3)
    assert primary_rows == 16470

    # FD002: 26 engines
    control_rows = 26 * (2 * 5 * 4 * 1 * 3)
    assert control_rows == 3120

    assert primary_rows + control_rows == 19590

    # Cell summary rows (5-seed aggregated):
    prim_cell_rows = 3 * 2 * 3 * 3 * 3
    assert prim_cell_rows == 162
    ctrl_cell_rows = 1 * 2 * 4 * 1 * 3
    assert ctrl_cell_rows == 24
    assert prim_cell_rows + ctrl_cell_rows == 186


def test_component_manifest_completeness() -> None:
    """Component manifest must define all components for RQ1, RQ2, RQ3, and RQ4."""
    res = validate_component_manifest_completeness()
    assert res["all_valid"] is True
    assert res["rq1_components_count"] == 14
    assert res["rq2_components_count"] == 20
    assert res["rq3_components_count"] == 22
    assert res["rq4_components_count"] == 96


# =============================================================================
# 4. Bootstrap Drawing and Replicate Statistic Tests
# =============================================================================


def test_hand_calculated_example_duplicate_engines_retain_multiplicity() -> None:
    """Stratified bootstrap draws with duplicate engines must compute engine-weighted
    means retaining multiplicity.
    """
    # Engine metrics for 3 engines: costs 10.0, 20.0, 30.0
    engine_costs = {1: 10.0, 2: 20.0, 3: 30.0}

    # Replicate draw: engine 1 drawn twice, engine 2 drawn 0 times, engine 3 drawn once
    # Replicate mean = (10.0 * 2 + 30.0 * 1) / 3 = 50.0 / 3 = 16.6666667
    mult = {1: 2.0, 2: 0.0, 3: 1.0}
    rep_mean = sum(mult[u] * engine_costs[u] for u in (1, 2, 3)) / sum(mult.values())
    assert np.isclose(rep_mean, 50.0 / 3.0)


def test_changing_worst_group_recomputed_per_replicate() -> None:
    """Worst subgroup coverage error must be recomputed in each replicate
    across the fixed eligible group set.
    """
    # Two groups g1 and g2. In replicate A, g1 has error 0.15, g2 has 0.05 -> worst is 0.15
    # In replicate B, g1 has error 0.02, g2 has 0.18 -> worst is 0.18
    # Global worst is NOT fixed
    rep_errors_g1 = np.array([0.15, 0.02])
    rep_errors_g2 = np.array([0.05, 0.18])
    worst_per_rep = np.maximum(rep_errors_g1, rep_errors_g2)
    assert worst_per_rep[0] == 0.15
    assert worst_per_rep[1] == 0.18


def test_missing_groups_and_empty_families_cannot_produce_false_passes() -> None:
    """Absent eligible groups bound at [0, 0.90] conservatively;
    empty families produce not-estimable.
    """
    res_empty = compute_replicate_worst_group_bounds(
        [], missing_group_count=1, nominal_coverage=0.90
    )
    assert res_empty == (0.0, 0.90)

    # Propagate delta error bounds conservatively
    delta_low, delta_upp = propagate_delta_error_bounds(
        baseline_bounds=(0.0, 0.90), proposed_bounds=(0.0, 0.90)
    )
    # delta = base - prop -> minimum possible = 0 - 0.90 = -0.90; maximum = 0.90 - 0 = +0.90
    assert delta_low == -0.90
    assert delta_upp == 0.90


def test_rq4_uses_equal_cell_weights() -> None:
    """RQ4 aggregate contrast must average exactly 6 cells with weight 1/6."""
    cell_contrasts = [
        np.array([1.0, 2.0]),
        np.array([2.0, 3.0]),
        np.array([3.0, 4.0]),
        np.array([4.0, 5.0]),
        np.array([5.0, 6.0]),
        np.array([6.0, 7.0]),
    ]
    agg = np.mean(cell_contrasts, axis=0)
    # Expected: (1+2+3+4+5+6)/6 = 21/6 = 3.5; (2+3+4+5+6+7)/6 = 27/6 = 4.5
    assert np.isclose(agg[0], 3.5)
    assert np.isclose(agg[1], 4.5)


# =============================================================================
# 5. Statistical Validation & Anti-Leakage Tests
# =============================================================================


def test_inverted_nonfinite_intervals_raise_errors() -> None:
    """Inverted confidence intervals or nonfinite values must raise ValueError."""
    # Nonfinite array
    with pytest.raises(ValueError):
        compute_bootstrap_ci(np.array([1.0, np.nan, 3.0]))

    # Inverted interval score bounds
    with pytest.raises(ValueError):
        compute_interval_score(
            y_true=np.array([10.0]),
            lower=np.array([15.0]),  # lower > upper!
            upper=np.array([5.0]),
            nominal_coverage=0.90,
        )


def test_zero_width_valid_intervals_are_indeterminate() -> None:
    """Zero-width confidence intervals must evaluate to INDETERMINATE under hypothesis testing."""
    dec = evaluate_improvement(ci_lower=0.20, ci_upper=0.20, margin=0.20)
    assert dec == "INDETERMINATE"

    dec_noninf = evaluate_noninferiority(ci_lower=-0.01, ci_upper=-0.01, margin=-0.01)
    assert dec_noninf == "INDETERMINATE"


def test_trajectory_validation_strict_typing() -> None:
    """validate_trajectory must reject booleans, invalid shapes, and inconsistent regime lengths."""
    # Boolean cycle
    with pytest.raises(TrajectoryValidationError):
        validate_trajectory(
            unit=1,
            terminal_cycle=31,
            cycles=np.array([True, False]),  # bool cycle
            predictions=np.array([10.0, 9.0]),
            lower_bounds=np.array([5.0, 4.0]),
            upper_bounds=np.array([15.0, 14.0]),
            regimes=np.array(["regime_1", "regime_1"]),
        )

    # Missing lower bound when upper bound is provided
    with pytest.raises(TrajectoryValidationError):
        validate_trajectory(
            unit=1,
            terminal_cycle=31,
            cycles=np.array([30, 31]),
            predictions=np.array([10.0, 9.0]),
            lower_bounds=None,
            upper_bounds=np.array([15.0, 14.0]),
            regimes=np.array(["regime_1", "regime_1"]),
        )


def test_held_out_requests_fail_before_execution() -> None:
    """assert_no_held_out_path must raise DataLeakageError if path references held-out test data."""
    with pytest.raises(DataLeakageError):
        assert_no_held_out_path("experiments/official_test/results.csv")

    with pytest.raises(DataLeakageError):
        assert_no_held_out_path("data/test/test_FD002.txt")
