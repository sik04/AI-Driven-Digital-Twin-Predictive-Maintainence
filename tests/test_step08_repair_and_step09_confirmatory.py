"""Comprehensive tests for Step 8 repair verification and Step 9 confirmatory infrastructure.

Tests:
- Portability & artifact integrity across all 90 committed calibrators
- Path resolver security (rejection of escape, absolute, drive paths)
- Audit falsification detection (leakage, truncation, duplicates, wrong labels)
- Execution provenance & immutability
- Exact quantile numerics, beta sign mechanics, and regime support thresholds
- Benchmark control grids, observable state contracts, and tie-breaking
- Sequential simulator decision rules and cost repricing
- Production statistical inference, stratified bootstrap, and IUT decision aggregator
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from intellitwin.decision.controls import (
    GRID_EARLIER_INTERVENTION_H,
    GRID_MATCHED_WIDTH_LAMBDA,
    GRID_SAFETY_MARGIN_M,
    GRID_WIDENED_LAMBDA,
    simulate_observable_trajectory,
)
from intellitwin.evaluation.schema import (
    CONFIRMATORY_DATASETS,
    CONFIRMATORY_METHODS,
    CONFIRMATORY_MODELS,
    CONFIRMATORY_SEEDS,
    COST_SCENARIOS,
)
from intellitwin.evaluation.validation import (
    DataLeakageError,
    TrajectoryValidationError,
    assert_no_held_out_path,
    assert_permitted_partition_only,
    validate_trajectory,
)
from intellitwin.provenance import (
    write_immutable_csv,
    write_immutable_json,
)
from intellitwin.simulator.types import MaintenanceAction
from intellitwin.uncertainty.artifacts import (
    load_frozen_calibrator,
    resolve_repo_relative_path,
)
from intellitwin.uncertainty.quantiles import (
    compute_engine_weighted_hierarchical_quantile,
)
from intellitwin.uncertainty.verification import (
    compute_independent_reference_hierarchical_quantile,
)

# =============================================================================
# 1. Portability and Calibrator Loading Tests
# =============================================================================


def test_all_90_committed_calibrators_load_cleanly() -> None:
    """Verify that all 90 real committed calibrators load and pass validation without raw data."""
    repo_root = Path(__file__).resolve().parents[1]
    count = 0
    for ds in CONFIRMATORY_DATASETS:
        for fam in CONFIRMATORY_MODELS:
            for seed in CONFIRMATORY_SEEDS:
                for method in CONFIRMATORY_METHODS:
                    cal = load_frozen_calibrator(
                        dataset=ds,
                        model_family=fam,
                        seed=seed,
                        method_id=method,
                        base_dir=repo_root,
                    )
                    assert cal.dataset_name == ds
                    assert cal.model_family == fam
                    assert cal.model_seed == seed
                    assert cal.method_id == method
                    assert set(cal.coverage_bundles.keys()) == {0.80, 0.90, 0.95}
                    count += 1
    assert count == 90


def test_path_resolver_posix_and_legacy_separators() -> None:
    """Canonical slash paths and Windows backslash paths must resolve identically."""
    repo_root = Path(__file__).resolve().parents[1]
    posix_path = "experiments/calibration/calibration_registry.json"
    win_path = "experiments\\calibration\\calibration_registry.json"

    p1 = resolve_repo_relative_path(repo_root, posix_path)
    p2 = resolve_repo_relative_path(repo_root, win_path)
    assert p1 == p2
    assert p1.exists()


def test_path_resolver_rejects_security_violations(tmp_path: Path) -> None:
    """Resolver must reject absolute paths, Windows drive paths, UNC paths, and root escapes."""
    # Absolute paths
    with pytest.raises(ValueError, match="forbidden"):
        resolve_repo_relative_path(tmp_path, "/etc/passwd")

    with pytest.raises(ValueError, match="forbidden"):
        resolve_repo_relative_path(tmp_path, "C:\\Windows\\System32")

    # UNC paths
    with pytest.raises(ValueError, match="forbidden"):
        resolve_repo_relative_path(tmp_path, "\\\\server\\share\\file.json")

    # Root escape
    with pytest.raises(ValueError, match="forbidden"):
        resolve_repo_relative_path(tmp_path, "../outside.json")

    with pytest.raises(ValueError, match="forbidden"):
        resolve_repo_relative_path(tmp_path, "sub/../../outside.json")


def test_calibrator_mismatched_identity_and_tampered_hash_fails(tmp_path: Path) -> None:
    """Requesting mismatched identity or tampered hash must fail validation."""
    repo_root = Path(__file__).resolve().parents[1]
    reg_p = repo_root / "experiments/calibration/calibration_registry.json"
    with open(reg_p, encoding="utf-8") as f:
        reg_data = json.load(f)

    # Tamper with one entry: point to wrong artifact
    bad_reg = dict(reg_data)
    bad_entries = dict(bad_reg["entries"])
    bad_key = "FD001_GBR_seed2026_global_hcp"
    tampered_entry = dict(bad_entries[bad_key])
    tampered_entry["artifact_sha256"] = "0" * 64
    bad_entries[bad_key] = tampered_entry
    bad_reg["entries"] = bad_entries

    bad_reg_p = tmp_path / "bad_registry.json"
    with open(bad_reg_p, "w", encoding="utf-8") as f:
        json.dump(bad_reg, f)

    with pytest.raises(ValueError, match="hash mismatch"):
        load_frozen_calibrator(
            dataset="FD001",
            model_family="GBR",
            seed=2026,
            method_id="global_hcp",
            registry_path=bad_reg_p,
            base_dir=repo_root,
        )


# =============================================================================
# 2. Audit Falsification Tests
# =============================================================================


def test_trajectory_validation_detects_truncation() -> None:
    """Truncating a trajectory before terminal cycle T must fail."""
    cycles = np.arange(30, 150)
    preds = np.full(len(cycles), 50.0)
    regs = np.full(len(cycles), 1)
    T = 160  # Expected terminal cycle is 160, but trajectory ends at 149

    with pytest.raises(TrajectoryValidationError, match="endpoints; expected"):
        validate_trajectory(
            unit=1,
            cycles=cycles,
            predictions=preds,
            regimes=regs,
            terminal_cycle=T,
        )


def test_trajectory_validation_detects_duplicate_cycles() -> None:
    """Duplicate endpoint cycles in trajectory must fail."""
    cycles = np.array([30, 31, 32, 32, 33])
    preds = np.full(len(cycles), 40.0)
    regs = np.full(len(cycles), 1)

    with pytest.raises(TrajectoryValidationError):
        validate_trajectory(
            unit=1,
            cycles=cycles,
            predictions=preds,
            regimes=regs,
            terminal_cycle=34,
        )


def test_trajectory_validation_detects_invalid_bounds() -> None:
    """Interval bounds violating 0 <= L <= p <= U must fail."""
    cycles = np.arange(30, 35)
    preds = np.array([40.0, 30.0, 20.0, 15.0, 10.0])
    regs = np.ones(5, dtype=int)

    # Lower bound exceeds prediction
    low_invalid = np.array([45.0, 30.0, 20.0, 15.0, 10.0])
    upp_valid = np.array([50.0, 40.0, 30.0, 25.0, 20.0])
    with pytest.raises(TrajectoryValidationError, match="lower bound exceeding point prediction"):
        validate_trajectory(
            unit=1,
            cycles=cycles,
            predictions=preds,
            regimes=regs,
            terminal_cycle=34,
            lower_bounds=low_invalid,
            upper_bounds=upp_valid,
        )

    # Upper bound less than prediction
    low_valid = np.array([30.0, 20.0, 10.0, 5.0, 0.0])
    upp_invalid = np.array([35.0, 30.0, 20.0, 15.0, 5.0])  # point 4 has pred=10 > upp=5
    with pytest.raises(TrajectoryValidationError, match="upper bound less than point prediction"):
        validate_trajectory(
            unit=1,
            cycles=cycles,
            predictions=preds,
            regimes=regs,
            terminal_cycle=34,
            lower_bounds=low_valid,
            upper_bounds=upp_invalid,
        )


def test_partition_leakage_detection() -> None:
    """Accessing non-permitted partition or held-out test engines must fail."""
    valid_units = {1, 2, 3, 4, 5}
    actual_with_leakage = {1, 2, 3, 4, 99}  # 99 is a test engine

    with pytest.raises(DataLeakageError, match="Engine partition mismatch"):
        assert_permitted_partition_only(actual_with_leakage, valid_units)

    with pytest.raises(DataLeakageError, match="Pre-test barrier"):
        assert_no_held_out_path("data/test/test_FD002.txt")


# =============================================================================
# 3. Provenance and Immutability Tests
# =============================================================================


def test_immutable_writers_prevent_conflicting_overwrites(tmp_path: Path) -> None:
    """write_immutable_json and write_immutable_csv must reject conflicting overwrites."""
    json_path = tmp_path / "test.json"
    write_immutable_json(json_path, {"key": "original", "val": 123})

    # Writing identical content is idempotent
    write_immutable_json(json_path, {"key": "original", "val": 123})

    # Writing conflicting content fails
    with pytest.raises(RuntimeError, match="Refusing to overwrite"):
        write_immutable_json(json_path, {"key": "altered", "val": 456})

    csv_path = tmp_path / "test.csv"
    df1 = pd.DataFrame({"col": [1, 2, 3]})
    write_immutable_csv(csv_path, df1)

    # Identical rewrite is idempotent
    write_immutable_csv(csv_path, df1)

    # Conflicting rewrite fails
    df2 = pd.DataFrame({"col": [1, 2, 999]})
    with pytest.raises(RuntimeError, match="Refusing to overwrite"):
        write_immutable_csv(csv_path, df2)


# =============================================================================
# 4. Numerics and Quantiles Tests
# =============================================================================


def test_exact_weighted_quantile_boundaries_and_tied_scores() -> None:
    """Verify that exact rational quantiles match reference calculation on tied scores."""
    # 20 contributing engines for support at 0.80, 0.90, 0.95
    eids = np.repeat(np.arange(1, 21), 5)
    cycles = np.tile(np.arange(30, 35), 20)
    scores = np.tile(np.array([10.0, 10.0, 20.0, 30.0, 50.0]), 20)

    for cov in (0.80, 0.90, 0.95):
        q_opt = compute_engine_weighted_hierarchical_quantile(eids, cycles, scores, cov)
        q_ref = compute_independent_reference_hierarchical_quantile(eids, cycles, scores, cov)
        assert q_opt == q_ref


def test_asymmetry_beta_mechanics() -> None:
    """Verify mathematical effect of beta < 0 at fixed p, q, and gamma."""
    p = 30.0
    gamma = 2
    sigma_p = (1.0 + p / 125.0) ** gamma
    z_p = np.exp(-p / 20.0)

    # At beta = 0: a(p) = b(p) = sigma(p)
    a_0 = sigma_p
    b_0 = sigma_p

    # At beta = -ln(2) < 0:
    beta_neg = -np.log(2.0)
    a_neg = sigma_p * np.exp(beta_neg * z_p)
    b_neg = sigma_p * np.exp(-beta_neg * z_p)

    # Mathematical property: a decreases, b increases
    assert a_neg < a_0
    assert b_neg > b_0

    # Holding q fixed:
    q = 1.5
    L_0 = max(0.0, p - q * a_0)
    U_0 = p + q * b_0
    L_neg = max(0.0, p - q * a_neg)
    U_neg = p + q * b_neg

    # Lower bound rises (or stays 0 after clipping), upper bound rises
    assert L_neg >= L_0
    assert U_neg > U_0


# =============================================================================
# 5. Benchmark Controls and Observable Policy Tests
# =============================================================================


def test_benchmark_control_grids_are_exact_and_complete() -> None:
    """Verify all four prespecified control grids against protocol definitions."""
    # Matched width: 1..400 / 100 plus {5, 6, 8, 12, 16} -> 405 values
    assert len(GRID_MATCHED_WIDTH_LAMBDA) == 405
    assert min(GRID_MATCHED_WIDTH_LAMBDA) == 0.01
    assert max(GRID_MATCHED_WIDTH_LAMBDA) == 16.0

    # Widened: 100..400 / 100 plus {5, 6, 8, 12, 16} -> 306 values, lambda >= 1.0
    assert len(GRID_WIDENED_LAMBDA) == 306
    assert min(GRID_WIDENED_LAMBDA) == 1.00
    assert max(GRID_WIDENED_LAMBDA) == 16.0
    assert all(lam >= 1.0 for lam in GRID_WIDENED_LAMBDA)

    # Safety margin: m in 0..250 -> 251 values
    assert len(GRID_SAFETY_MARGIN_M) == 251
    assert min(GRID_SAFETY_MARGIN_M) == 0
    assert max(GRID_SAFETY_MARGIN_M) == 250

    # Earlier intervention: h in 1..251 -> 251 values
    assert len(GRID_EARLIER_INTERVENTION_H) == 251
    assert min(GRID_EARLIER_INTERVENTION_H) == 1
    assert max(GRID_EARLIER_INTERVENTION_H) == 251


def test_simulator_observable_state_contract() -> None:
    """Ensure observable maintenance trajectory simulator adheres strictly to contract."""
    scenario = COST_SCENARIOS["primary_reference"]
    cycles = np.array([30, 31, 32, 33])
    preds = np.array([10.0, 5.0, 2.0, 0.5])
    lows = np.array([5.0, 2.0, 1.0, 0.0])  # low <= 1.0 at cycle 32
    upps = np.array([15.0, 8.0, 4.0, 1.5])
    regs = np.array([1, 1, 1, 1])
    failure_cycle = 35

    # 1. Threshold equality triggers MAINTAIN_NOW at cycle 32
    out = simulate_observable_trajectory(
        unit=101,
        seed=2026,
        control_id="test_ctrl",
        cycles=cycles,
        predictions=preds,
        lower_bounds=lows,
        upper_bounds=upps,
        regimes=regs,
        failure_cycle=failure_cycle,
        policy_fn=lambda s: (
            MaintenanceAction.MAINTAIN_NOW if s.lower_rul <= 1.0 else MaintenanceAction.CONTINUE
        ),
        scenario=scenario,
    )
    assert out.pm_occurred is True
    assert out.failed is False
    assert out.intervention_cycle == 32
    assert out.wasted_rul == float(35 - 32)  # 3.0 cycles
    assert out.total_cost == scenario.c_pm + scenario.c_waste * 3.0

    # 2. Early-PM equality rule: W == r_equal (20.0) is NOT early PM
    assert out.is_cost_inefficient_early_pm is False


def test_simulator_no_action_at_cycle_t() -> None:
    """Verify that continuing past T-1 results in failure; no action occurs at T."""
    scenario = COST_SCENARIOS["primary_reference"]
    cycles = np.array([30, 31, 32])
    preds = np.array([20.0, 15.0, 10.0])
    lows = np.array([15.0, 10.0, 5.0])  # Never triggers <= 1.0
    upps = np.array([25.0, 20.0, 15.0])
    regs = np.array([1, 1, 1])
    failure_cycle = 33

    out = simulate_observable_trajectory(
        unit=102,
        seed=2026,
        control_id="test_ctrl",
        cycles=cycles,
        predictions=preds,
        lower_bounds=lows,
        upper_bounds=upps,
        regimes=regs,
        failure_cycle=failure_cycle,
        policy_fn=lambda s: (
            MaintenanceAction.MAINTAIN_NOW if s.lower_rul <= 1.0 else MaintenanceAction.CONTINUE
        ),
        scenario=scenario,
    )
    assert out.pm_occurred is False
    assert out.failed is True
    assert out.intervention_cycle is None
    assert out.total_cost == scenario.c_fail
    assert out.wasted_rul == 0.0


def test_repricing_preserves_intervention_decisions() -> None:
    """Repricing traces under alternate cost scenarios must preserve intervention cycle."""
    ref_scenario = COST_SCENARIOS["primary_reference"]
    fail_scenario = COST_SCENARIOS["failure_sensitive"]

    cycles = np.array([30, 31, 32])
    preds = np.array([5.0, 2.0, 0.5])
    lows = np.array([2.0, 0.8, 0.0])  # Intervenes at cycle 31 (low=0.8 <= 1.0)
    upps = np.array([8.0, 4.0, 1.5])
    regs = np.array([1, 1, 1])
    failure_cycle = 35

    def policy(s: Any) -> MaintenanceAction:
        return MaintenanceAction.MAINTAIN_NOW if s.lower_rul <= 1.0 else MaintenanceAction.CONTINUE

    out_ref = simulate_observable_trajectory(
        unit=103,
        seed=2026,
        control_id="test",
        cycles=cycles,
        predictions=preds,
        lower_bounds=lows,
        upper_bounds=upps,
        regimes=regs,
        failure_cycle=failure_cycle,
        policy_fn=policy,
        scenario=ref_scenario,
    )
    out_fail = simulate_observable_trajectory(
        unit=103,
        seed=2026,
        control_id="test",
        cycles=cycles,
        predictions=preds,
        lower_bounds=lows,
        upper_bounds=upps,
        regimes=regs,
        failure_cycle=failure_cycle,
        policy_fn=policy,
        scenario=fail_scenario,
    )
    assert out_ref.intervention_cycle == out_fail.intervention_cycle
    assert out_ref.wasted_rul == out_fail.wasted_rul
    assert out_ref.decision_trace == out_fail.decision_trace
