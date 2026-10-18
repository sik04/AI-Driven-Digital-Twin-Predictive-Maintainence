"""Unit tests for independent reference reconstruction and fail-closed pretest verification."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from intellitwin.evaluation.evidence_schema import (
    canonicalize_coverage,
)
from intellitwin.evaluation.reference_verification import (
    _check_finite_and_bounds,
    _reconstruct_bootstrap_draws,
)

# =============================================================================
# 1. Canonical Coverage Parsing Tests
# =============================================================================


def test_canonicalize_coverage_valid_representations() -> None:
    """Canonicalize accepts 80, 90, 95 and fractional 0.80, 0.90, 0.95 in int/float/str."""
    assert canonicalize_coverage(80) == 80
    assert canonicalize_coverage(90) == 90
    assert canonicalize_coverage(95) == 95

    assert canonicalize_coverage("80") == 80
    assert canonicalize_coverage("90") == 90
    assert canonicalize_coverage("95") == 95

    assert canonicalize_coverage(" 90 ") == 90

    assert canonicalize_coverage(0.80) == 80
    assert canonicalize_coverage(0.90) == 90
    assert canonicalize_coverage(0.95) == 95

    assert canonicalize_coverage("0.80") == 80
    assert canonicalize_coverage("0.90") == 90
    assert canonicalize_coverage("0.95") == 95


def test_canonicalize_coverage_rejects_booleans() -> None:
    """Canonicalize must strictly reject booleans (True/False are int subclasses in Python)."""
    with pytest.raises(TypeError, match="Booleans are not valid coverages"):
        canonicalize_coverage(True)

    with pytest.raises(TypeError, match="Booleans are not valid coverages"):
        canonicalize_coverage(False)


def test_canonicalize_coverage_rejects_non_finite() -> None:
    """Canonicalize must reject NaN and infinite values."""
    with pytest.raises(ValueError, match="must be a finite number"):
        canonicalize_coverage(float("nan"))

    with pytest.raises(ValueError, match="must be a finite number"):
        canonicalize_coverage(float("inf"))

    with pytest.raises(ValueError, match="must be a finite number"):
        canonicalize_coverage(float("-inf"))

    with pytest.raises(ValueError, match="must be a finite number"):
        canonicalize_coverage("nan")


def test_canonicalize_coverage_rejects_out_of_tolerance_floats() -> None:
    """Canonicalize strictly enforces 1e-12 absolute tolerance and rejects values like 0.90005."""
    with pytest.raises(ValueError, match="Invalid nominal coverage"):
        canonicalize_coverage(0.90005)

    with pytest.raises(ValueError, match="Invalid nominal coverage"):
        canonicalize_coverage(0.8999)

    with pytest.raises(ValueError, match="Invalid nominal coverage"):
        canonicalize_coverage(75)

    with pytest.raises(ValueError, match="Invalid nominal coverage"):
        canonicalize_coverage(100)

    with pytest.raises(ValueError, match="Invalid nominal coverage"):
        canonicalize_coverage("invalid_str")


# =============================================================================
# 2. Independent Bootstrap Draw Generation Tests
# =============================================================================


def test_reconstruct_independent_bootstrap_draws_reproducibility() -> None:
    """PRNG draw reconstruction produces identical draws for identical unit lists."""
    units = [2, 5, 9, 10, 11]
    base = Path(".")
    draws1 = _reconstruct_bootstrap_draws("FD001", units, base_dir=base, n_replicates=20)
    draws2 = _reconstruct_bootstrap_draws("FD001", units, base_dir=base, n_replicates=20)

    assert draws1.shape == (20, len(units))
    assert np.array_equal(draws1, draws2)
    assert np.all(np.isin(draws1, units))


def test_reconstruct_independent_bootstrap_draws_differs_by_dataset() -> None:
    """Different datasets have different seed sequences and produce distinct draw matrices."""
    units = [2, 5, 9, 10, 11]
    base = Path(".")
    draws1 = _reconstruct_bootstrap_draws("FD001", units, base_dir=base, n_replicates=20)
    draws2 = _reconstruct_bootstrap_draws("FD002", units, base_dir=base, n_replicates=20)

    assert not np.array_equal(draws1, draws2)


# =============================================================================
# 3. Finite Bounds Checking Tests
# =============================================================================


def test_check_finite_and_bounds_valid() -> None:
    """Valid finite lower <= upper arrays produce no errors."""
    lower = np.array([1.0, 2.0, 3.0])
    upper = np.array([1.5, 2.0, 3.5])
    # Should execute without raising
    _check_finite_and_bounds(lower, upper, "test_stat")


def test_check_finite_and_bounds_nan_inf_violations() -> None:
    """Non-finite arrays in lower or upper raise ValueError."""
    lower = np.array([1.0, np.nan, 3.0])
    upper = np.array([1.5, 2.0, 3.5])
    with pytest.raises(ValueError, match="Non-finite values encountered"):
        _check_finite_and_bounds(lower, upper, "nan_test")

    lower_inf = np.array([1.0, 2.0, 3.0])
    upper_inf = np.array([1.5, float("inf"), 3.5])
    with pytest.raises(ValueError, match="Non-finite values encountered"):
        _check_finite_and_bounds(lower_inf, upper_inf, "inf_test")


def test_check_finite_and_bounds_inversion_violations() -> None:
    """Violations where lower > upper raise ValueError."""
    lower = np.array([1.0, 5.0, 3.0])
    upper = np.array([1.5, 4.0, 3.5])  # index 1: lower (5.0) > upper (4.0)
    with pytest.raises(ValueError, match="Inverted bounds detected"):
        _check_finite_and_bounds(lower, upper, "inversion_test")


# =============================================================================
# 4. Confirmed False-PASS Mutation Rejection Tests
# =============================================================================


def _copy_v3_validation_smoke(target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    src_dir = Path("experiments/pretest_verification_v3/validation_smoke")
    for f in src_dir.glob("*"):
        if f.is_file():
            (target_dir / f.name).write_bytes(f.read_bytes())
    return target_dir


def test_mutation_point_prediction_altered_fails_closed(tmp_path: Path) -> None:
    """Mutation 1: Corrupted seed 2027 point prediction (+100.0) is decisively rejected."""
    smoke_dir = _copy_v3_validation_smoke(tmp_path / "smoke_m1")
    pts_p = smoke_dir / "point_predictions.csv"
    df_pts = pd.read_csv(pts_p)
    mask = (
        (df_pts["dataset"] == "FD001")
        & (df_pts["model_family"] == "GBR")
        & (df_pts["seed"] == 2027)
    )
    idx = df_pts[mask].index[0]
    df_pts.at[idx, "prediction"] = df_pts.at[idx, "prediction"] + 100.0
    df_pts.to_csv(pts_p, index=False)

    from intellitwin.evaluation.verification import verify_validation_smoke_matrix

    res = verify_validation_smoke_matrix(smoke_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert any("Point prediction discrepancy" in r for r in res["failing_reasons"])


def test_mutation_point_prediction_row_deleted_fails_closed(tmp_path: Path) -> None:
    """Mutation 2: Deleted seed 2026 point prediction row is decisively rejected."""
    smoke_dir = _copy_v3_validation_smoke(tmp_path / "smoke_m2")
    pts_p = smoke_dir / "point_predictions.csv"
    df_pts = pd.read_csv(pts_p)
    mask = (
        (df_pts["dataset"] == "FD001")
        & (df_pts["model_family"] == "GBR")
        & (df_pts["seed"] == 2026)
    )
    idx = df_pts[mask].index[0]
    df_pts = df_pts.drop(idx)
    df_pts.to_csv(pts_p, index=False)

    from intellitwin.evaluation.verification import verify_validation_smoke_matrix

    res = verify_validation_smoke_matrix(smoke_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert any(
        "count mismatch" in r.lower() or "discrepancy" in r.lower() for r in res["failing_reasons"]
    )


def test_mutation_non_failure_component_evidence_altered_fails_closed(tmp_path: Path) -> None:
    """Mutation 3: Altered non-failure component evidence is decisively rejected."""
    smoke_dir = _copy_v3_validation_smoke(tmp_path / "smoke_m3")
    comp_p = smoke_dir / "component_evidence.csv"
    df_comp = pd.read_csv(comp_p)
    target_cid = "RQ1_GBR_global_hcp_cost_improvement"
    mask = df_comp["component_id"] == target_cid
    idx = df_comp[mask].index[0]
    df_comp.at[idx, "ci_decision_low"] = df_comp.at[idx, "ci_decision_low"] + 100.0
    df_comp.to_csv(comp_p, index=False)

    from intellitwin.evaluation.verification import verify_validation_smoke_matrix

    res = verify_validation_smoke_matrix(smoke_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert any("Component evidence discrepancies" in r for r in res["failing_reasons"])


def test_mutation_engine_metrics_coverage_out_of_bounds_fails_closed(tmp_path: Path) -> None:
    """Mutation 4: engine_metrics.csv coverage = 12345.0 is decisively rejected."""
    smoke_dir = _copy_v3_validation_smoke(tmp_path / "smoke_m4")
    em_p = smoke_dir / "engine_metrics.csv"
    df_em = pd.read_csv(em_p)
    df_em.at[0, "coverage"] = 12345.0
    df_em.to_csv(em_p, index=False)

    from intellitwin.evaluation.verification import verify_validation_smoke_matrix

    res = verify_validation_smoke_matrix(smoke_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert any("Coverage values outside [0, 1]" in r for r in res["failing_reasons"])


def test_mutation_bootstrap_stat_with_consistent_contrast_fails_closed(tmp_path: Path) -> None:
    """Mutation 5: Altered bootstrap replicate with matching contrast is decisively rejected."""
    from intellitwin.evaluation.regression_audit import apply_mutation_5_consistent_contrast
    from intellitwin.evaluation.verification import verify_validation_smoke_matrix

    smoke_dir = _copy_v3_validation_smoke(tmp_path / "smoke_m5")
    mut_info = apply_mutation_5_consistent_contrast(smoke_dir)

    # Verify that the saved contrast summary is internally consistent with altered array
    df_c = pd.read_csv(smoke_dir / "contrast_intervals.csv")
    row = df_c[df_c["contrast_id"] == mut_info["contrast_id"]].iloc[0]
    assert np.isclose(float(row["mean"]), mut_info["mean"], atol=1e-10)
    assert np.isclose(float(row["median"]), mut_info["median"], atol=1e-10)
    assert np.isclose(float(row["ci_95_low"]), mut_info["ci_95_low"], atol=1e-10)
    assert np.isclose(float(row["ci_95_high"]), mut_info["ci_95_high"], atol=1e-10)
    assert np.isclose(float(row["ci_decision_low"]), mut_info["ci_decision_low"], atol=1e-10)
    assert np.isclose(float(row["ci_decision_high"]), mut_info["ci_decision_high"], atol=1e-10)
    assert str(row["status"]) == "DEVELOPMENT_SMOKE_ONLY"

    res = verify_validation_smoke_matrix(smoke_dir, base_dir=".")
    assert res["status"] == "FAIL"
    # ci_verification (internal consistency between NPZ and contrast_intervals.csv) passed
    assert res["checks"]["ci_verification"]["match"] is True
    # Independent reference reconstruction rejected the altered bootstrap values
    boot_res = res["checks"]["reference_verification"]["checks"][
        "bootstrap_statistics_npz_reconstruction"
    ]
    assert boot_res["status"] == "FAIL"
    assert any("Bootstrap statistics NPZ discrepancies" in r for r in res["failing_reasons"])


# =============================================================================
# 5. Freeze Audit CLI Verification Tests
# =============================================================================


def test_audit_step09_freeze_cli_help() -> None:
    """audit_step09_freeze.py --help succeeds with code 0."""
    import subprocess
    import sys

    res = subprocess.run(
        [sys.executable, "scripts/audit_step09_freeze.py", "--help"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "--verify-only" in res.stdout


def test_audit_step09_freeze_cli_verify_only_nonexistent_dir() -> None:
    """audit_step09_freeze.py --verify-only fails with code 1 for missing directory."""
    import subprocess
    import sys

    res = subprocess.run(
        [
            sys.executable,
            "scripts/audit_step09_freeze.py",
            "--verification-dir",
            "nonexistent_verification_dir",
            "--verify-only",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1


def test_audit_step09_freeze_cli_verify_only_v4_historical_source_mismatch() -> None:
    """Historical v4 bundle fails closed (exit code 1) when current source hashes have changed."""
    import subprocess
    import sys

    res = subprocess.run(
        [
            sys.executable,
            "scripts/audit_step09_freeze.py",
            "--verification-dir",
            "experiments/pretest_verification_v4",
            "--verify-only",
            "--allow-dirty",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    assert "Pre-Test Readiness:        BLOCKED" in res.stdout
