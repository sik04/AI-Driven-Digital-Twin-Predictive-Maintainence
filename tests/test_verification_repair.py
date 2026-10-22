"""Tests for Portion A verification repairs: executed regression, portable provenance,
and final integration.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from intellitwin.data.artifacts import compute_sha256
from intellitwin.evaluation.regression_audit import (
    apply_mutation_5_consistent_contrast,
    evaluate_mutation_rejection,
    execute_regression_audit,
)
from intellitwin.evaluation.schema import (
    DECISION_QUANTILES,
    DESCRIPTIVE_QUANTILES,
)
from scripts.audit_step09_freeze import (
    REQUIRED_PARTNER_CHECKPOINT_FILES,
    build_input_manifest,
    build_reused_evidence,
    build_supersession,
    validate_portable_artifact_path,
    verify_partner_checkpoint_evidence,
    verify_saved_freeze,
)


def _copy_v3_smoke_fixture(target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    src_dir = Path("experiments/pretest_verification_v3/validation_smoke")
    for f in src_dir.glob("*"):
        if f.is_file():
            shutil.copy2(f, target_dir / f.name)
    return target_dir


# =============================================================================
# 1. Baseline Failure Preventing Regression-Report PASS
# =============================================================================


def test_baseline_failure_prevents_regression_report_pass(tmp_path: Path) -> None:
    """When unmodified baseline evidence fails verification, regression suite fails closed."""
    corrupt_smoke = _copy_v3_smoke_fixture(tmp_path / "corrupt_smoke")
    # Corrupt baseline point prediction
    pts_p = corrupt_smoke / "point_predictions.csv"
    df = pd.read_csv(pts_p)
    df.at[0, "prediction"] = float(df.at[0, "prediction"]) + 999.0
    df.to_csv(pts_p, index=False)

    report = execute_regression_audit(
        source_smoke_dir=corrupt_smoke,
        base_dir=".",
        allow_dirty=True,
    )
    assert report["overall_status"] == "FAIL"
    assert report["status"] == "FAIL"
    assert report["baseline_verification"]["status"] == "FAIL"
    assert report["mutations_evaluated"] == 0
    assert report["mutations_rejected"] == 0
    assert "baseline evidence verification failed" in report["failure_summary"].lower()


# =============================================================================
# 2. Omitted or Duplicate Mutation Records
# =============================================================================


def test_omitted_mutation_records_rejected(tmp_path: Path) -> None:
    """Regression report with fewer than 5 mutation records must be rejected."""
    # Synthetic bundle directory
    bundle_dir = tmp_path / "bundle_omitted"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    fake_reg_report = {
        "status": "PASS",
        "overall_status": "PASS",
        "baseline_verification": {"status": "PASS"},
        "mutations_evaluated": 4,
        "mutations_rejected": 4,
        "records": [
            {
                "mutation_id": f"mutation_{i}",
                "verifier_status": "FAIL",
                "rejection_confirmed": True,
            }
            for i in range(1, 5)
        ],
    }
    (bundle_dir / "regression_test_report.json").write_text(
        json.dumps(fake_reg_report), encoding="utf-8"
    )

    fake_freeze = {
        "schema_version": "step09-freeze-v5",
        "source_evidence_dir": "experiments/pretest_verification_v3",
        "bindings": {
            "regression_test_report_sha256": compute_sha256(
                bundle_dir / "regression_test_report.json"
            ),
        },
    }
    (bundle_dir / "protocol_freeze.json").write_text(json.dumps(fake_freeze), encoding="utf-8")

    audit = verify_saved_freeze(
        freeze_path=bundle_dir / "protocol_freeze.json",
        source_evidence_dir="experiments/pretest_verification_v3",
        base_dir=".",
        allow_dirty=True,
        rerun_regression=False,
    )
    assert audit["regression_evidence_passed"] is False
    assert audit["overall_status"] == "FAIL"


def test_duplicate_mutation_records_rejected(tmp_path: Path) -> None:
    """Regression report with duplicate mutation IDs must be rejected."""
    bundle_dir = tmp_path / "bundle_dup"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    fake_reg_report = {
        "status": "PASS",
        "overall_status": "PASS",
        "baseline_verification": {"status": "PASS"},
        "mutations_evaluated": 5,
        "mutations_rejected": 5,
        "records": [
            {"mutation_id": "mutation_1", "verifier_status": "FAIL", "rejection_confirmed": True},
            {"mutation_id": "mutation_1", "verifier_status": "FAIL", "rejection_confirmed": True},
            {"mutation_id": "mutation_2", "verifier_status": "FAIL", "rejection_confirmed": True},
            {"mutation_id": "mutation_3", "verifier_status": "FAIL", "rejection_confirmed": True},
            {"mutation_id": "mutation_4", "verifier_status": "FAIL", "rejection_confirmed": True},
        ],
    }
    (bundle_dir / "regression_test_report.json").write_text(
        json.dumps(fake_reg_report), encoding="utf-8"
    )

    fake_freeze = {
        "schema_version": "step09-freeze-v5",
        "source_evidence_dir": "experiments/pretest_verification_v3",
        "bindings": {
            "regression_test_report_sha256": compute_sha256(
                bundle_dir / "regression_test_report.json"
            ),
        },
    }
    (bundle_dir / "protocol_freeze.json").write_text(json.dumps(fake_freeze), encoding="utf-8")

    audit = verify_saved_freeze(
        freeze_path=bundle_dir / "protocol_freeze.json",
        source_evidence_dir="experiments/pretest_verification_v3",
        base_dir=".",
        allow_dirty=True,
        rerun_regression=False,
    )
    assert audit["regression_evidence_passed"] is False
    assert audit["overall_status"] == "FAIL"


# =============================================================================
# 3. Intended-Check Failure Despite Unrelated Verifier Failure
# =============================================================================


def test_intended_check_failure_despite_unrelated_verifier_failure() -> None:
    """If verifier fails due to unrelated reasons, rejection is not confirmed."""
    unrelated_failure_res = {
        "status": "FAIL",
        "overall_match": False,
        "failing_reasons": ["Unrelated file missing: non_existent.csv"],
        "checks": {
            "required_files_present": False,
            "reference_verification": {
                "overall_match": False,
                "checks": {
                    "component_evidence_reconstruction": {"status": "SKIPPED"},
                },
            },
        },
    }

    rejected, check_id, details = evaluate_mutation_rejection("mutation_3", unrelated_failure_res)
    assert rejected is False
    assert check_id == "component_evidence_reconstruction"
    assert details.get("comp_reconstruction_status") == "SKIPPED"


def test_intended_check_success_for_mutation_3() -> None:
    """Mutation 3 confirms rejection when component reconstruction fails with discrepancy."""
    valid_rejection_res = {
        "status": "FAIL",
        "overall_match": False,
        "failing_reasons": [
            "Component evidence discrepancies: "
            "['RQ1_GBR_global_hcp_cost_improvement: discrepancy 100.0 > 1e-10']"
        ],
        "checks": {
            "reference_verification": {
                "overall_match": False,
                "checks": {
                    "component_evidence_reconstruction": {"status": "FAIL"},
                },
            },
        },
    }

    rejected, check_id, details = evaluate_mutation_rejection("mutation_3", valid_rejection_res)
    assert rejected is True
    assert check_id == "component_evidence_reconstruction"
    assert details["has_component_discrepancy_reason"] is True


# =============================================================================
# 4. Correct Mutation-5 Quantiles and Internally Consistent Contrast Summary
# =============================================================================


def test_mutation_5_quantiles_and_consistent_contrast_summary(tmp_path: Path) -> None:
    """Mutation 5 uses linear quantiles [0.025, 0.975] and [0.00625, 0.99375], not 5th/95th."""
    smoke_dir = _copy_v3_smoke_fixture(tmp_path / "smoke_m5")
    mut_info = apply_mutation_5_consistent_contrast(smoke_dir)

    target_key = "FD001_GBR_global_hcp_cost_improvement"
    assert mut_info["contrast_id"] == target_key
    assert mut_info["shift"] == 100.0

    # Read modified array and CSV
    npz_data = dict(np.load(smoke_dir / "bootstrap_statistics_FD001.npz"))
    altered_arr = npz_data[target_key]
    df_c = pd.read_csv(smoke_dir / "contrast_intervals.csv")
    row = df_c[df_c["contrast_id"] == target_key].iloc[0]

    # Verify exact formulas
    expected_mean = float(np.mean(altered_arr))
    expected_median = float(np.median(altered_arr))
    expected_ci_95_l = float(np.quantile(altered_arr, DESCRIPTIVE_QUANTILES[0], method="linear"))
    expected_ci_95_h = float(np.quantile(altered_arr, DESCRIPTIVE_QUANTILES[1], method="linear"))
    expected_ci_dec_l = float(np.quantile(altered_arr, DECISION_QUANTILES[0], method="linear"))
    expected_ci_dec_h = float(np.quantile(altered_arr, DECISION_QUANTILES[1], method="linear"))

    # Assert CSV matches computed linear quantiles within tolerance
    assert math.isclose(float(row["mean"]), expected_mean, abs_tol=1e-10)
    assert math.isclose(float(row["median"]), expected_median, abs_tol=1e-10)
    assert math.isclose(float(row["ci_95_low"]), expected_ci_95_l, abs_tol=1e-10)
    assert math.isclose(float(row["ci_95_high"]), expected_ci_95_h, abs_tol=1e-10)
    assert math.isclose(float(row["ci_decision_low"]), expected_ci_dec_l, abs_tol=1e-10)
    assert math.isclose(float(row["ci_decision_high"]), expected_ci_dec_h, abs_tol=1e-10)

    # Prove that 5th and 95th percentiles are DIFFERENT from decision quantiles
    p5 = float(np.quantile(altered_arr, 0.05, method="linear"))
    p95 = float(np.quantile(altered_arr, 0.95, method="linear"))
    assert not math.isclose(float(row["ci_decision_low"]), p5, abs_tol=1e-3)
    assert not math.isclose(float(row["ci_decision_high"]), p95, abs_tol=1e-3)

    # Assert identifying fields and development status preserved
    assert row["status"] == "DEVELOPMENT_SMOKE_ONLY"
    assert row["dataset"] == "FD001"
    assert row["model_family"] == "GBR"


# =============================================================================
# 5. Portable Logical Paths with External Staging Directory
# =============================================================================


def test_portable_logical_paths_with_external_staging(tmp_path: Path) -> None:
    """Physical generation into external staging uses logical bundle paths in all records."""
    external_staging = tmp_path / "staging_dir_outside_repo"
    logical_dir = "experiments/pretest_verification_v5"

    supersession = build_supersession(
        logical_output_dir=logical_dir,
        prior_bundle_dir="experiments/pretest_verification_v4",
        base_dir=".",
        git_sha="test_commit_sha",
    )

    # Check that replacement paths use logical_dir, not external staging
    assert supersession["logical_bundle_path"] == logical_dir
    for rec in supersession["superseded_records"]:
        rep_p = rec["replacement_evidence_path"]
        assert rep_p.startswith(logical_dir)
        assert str(external_staging) not in rep_p
        assert "\\" not in rep_p
        validate_portable_artifact_path(rep_p)

    reused = build_reused_evidence(
        source_evidence_dir="experiments/pretest_verification_v3",
        logical_output_dir=logical_dir,
        base_dir=".",
    )
    assert reused["logical_bundle_path"] == logical_dir
    assert "\\" not in reused["source_evidence_dir"]
    validate_portable_artifact_path(reused["source_evidence_dir"])

    manifest = build_input_manifest(
        source_evidence_dir="experiments/pretest_verification_v3",
        logical_output_dir=logical_dir,
        base_dir=".",
        git_sha="test_sha",
    )
    assert manifest["logical_bundle_path"] == logical_dir
    validate_portable_artifact_path(manifest["source_evidence_dir"])


# =============================================================================
# 6. Rejection of Absolute / Traversal Artifact Locators
# =============================================================================


def test_validate_portable_artifact_path_accepts_valid() -> None:
    """Valid POSIX repository-relative paths pass validation."""
    assert (
        validate_portable_artifact_path("experiments/pretest_verification_v5/protocol_freeze.json")
        == "experiments/pretest_verification_v5/protocol_freeze.json"
    )
    assert (
        validate_portable_artifact_path("research/hypotheses/hypothesis_framework.yaml")
        == "research/hypotheses/hypothesis_framework.yaml"
    )


def test_validate_portable_artifact_path_rejects_invalid() -> None:
    """Rejects absolute paths, Windows drive prefixes, backslashes, and directory traversal."""
    # Absolute path
    with pytest.raises(ValueError, match="Absolute paths are not permitted"):
        validate_portable_artifact_path("/experiments/pretest_verification_v5")

    # Windows drive prefix
    with pytest.raises(ValueError, match="Drive-prefixed paths are not permitted"):
        validate_portable_artifact_path("C:/experiments/pretest_verification_v5")

    # Backslashes
    with pytest.raises(ValueError, match="must use POSIX slashes"):
        validate_portable_artifact_path("experiments\\pretest_verification_v5")

    # Directory traversal
    with pytest.raises(ValueError, match="Traversal outside repository"):
        validate_portable_artifact_path("experiments/../outside/protocol_freeze.json")

    with pytest.raises(ValueError, match="Traversal outside repository"):
        validate_portable_artifact_path("../secret_file.json")

    # Empty string
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_portable_artifact_path("   ")


# =============================================================================
# 7. Tampered Regression Report
# =============================================================================


def test_tampered_regression_report_rejected(tmp_path: Path) -> None:
    """Altered regression report (falsified rejection or changed status) fails verification."""
    bundle_dir = tmp_path / "bundle_tampered"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    tampered_report = {
        "status": "PASS",
        "overall_status": "PASS",
        "baseline_verification": {"status": "PASS"},
        "mutations_evaluated": 5,
        "mutations_rejected": 5,
        "records": [
            {
                "mutation_id": f"mutation_{i}",
                "verifier_status": "PASS",  # Tampered: should be FAIL
                "rejection_confirmed": True,
            }
            for i in range(1, 6)
        ],
    }
    (bundle_dir / "regression_test_report.json").write_text(
        json.dumps(tampered_report), encoding="utf-8"
    )

    fake_freeze = {
        "schema_version": "step09-freeze-v5",
        "source_evidence_dir": "experiments/pretest_verification_v3",
        "bindings": {
            "regression_test_report_sha256": compute_sha256(
                bundle_dir / "regression_test_report.json"
            ),
        },
    }
    (bundle_dir / "protocol_freeze.json").write_text(json.dumps(fake_freeze), encoding="utf-8")

    audit = verify_saved_freeze(
        freeze_path=bundle_dir / "protocol_freeze.json",
        source_evidence_dir="experiments/pretest_verification_v3",
        base_dir=".",
        allow_dirty=True,
        rerun_regression=False,
    )
    assert audit["regression_evidence_passed"] is False
    assert audit["overall_status"] == "FAIL"


# =============================================================================
# 8. Missing or Failed Partner Checkpoint Evidence
# =============================================================================


def test_missing_partner_checkpoint_evidence_blocked(tmp_path: Path) -> None:
    """Missing partner checkpoint verification directory reports status BLOCKED."""
    res = verify_partner_checkpoint_evidence(
        checkpoint_dir=tmp_path / "nonexistent_partner_dir",
        base_dir=".",
    )
    assert res["status"] == "BLOCKED"
    assert res["match"] is False
    assert res["directory_exists"] is False
    assert set(res["missing_files"]) == set(REQUIRED_PARTNER_CHECKPOINT_FILES)


def test_partner_checkpoint_evidence_missing_files_blocked(tmp_path: Path) -> None:
    """Partner checkpoint directory missing required files reports BLOCKED."""
    cp_dir = tmp_path / "incomplete_partner"
    cp_dir.mkdir(parents=True, exist_ok=True)
    # Only create 1 file
    (cp_dir / "environment_verification.json").write_text("{}", encoding="utf-8")

    res = verify_partner_checkpoint_evidence(
        checkpoint_dir=cp_dir,
        base_dir=".",
    )
    assert res["status"] == "BLOCKED"
    assert res["match"] is False
    assert "step08_full_audit.json" in res["missing_files"]


def test_partner_checkpoint_inconsistent_version_warning_fails(tmp_path: Path) -> None:
    """sklearn InconsistentVersionWarning in execution.log causes FAIL."""
    cp_dir = tmp_path / "warning_partner"
    cp_dir.mkdir(parents=True, exist_ok=True)

    (cp_dir / "environment_verification.json").write_text(
        json.dumps({"status": "PASS", "clean_source_execution": True}), encoding="utf-8"
    )
    (cp_dir / "execution.log").write_text(
        "UserWarning: Trying to unpickle estimator GBR from version 1.2 when using version 1.9\n"
        "InconsistentVersionWarning: estimator version mismatch",
        encoding="utf-8",
    )
    (cp_dir / "pip_freeze.txt").write_text("scikit-learn==1.9.1\n", encoding="utf-8")
    (cp_dir / "pip_check.txt").write_text("No broken requirements found.\n", encoding="utf-8")
    (cp_dir / "input_manifest.json").write_text(
        json.dumps({"protected_inputs": {}}), encoding="utf-8"
    )

    # 60 records for step08
    records = []
    for ds in ("FD001", "FD002", "FD004"):
        for m in ("GBR", "LSTM"):
            for s in (2026, 2027, 2028, 2029, 2030):
                for p in ("validation", "calibration"):
                    records.append(
                        {
                            "dataset": ds,
                            "model_family": m,
                            "seed": s,
                            "partition": p,
                            "status": "PASS",
                            "max_abs_diff": 0.0,
                        }
                    )
    (cp_dir / "step08_full_audit.json").write_text(
        json.dumps({"details": {"checkpoint_prediction_reproduction": {"records": records}}}),
        encoding="utf-8",
    )

    res = verify_partner_checkpoint_evidence(checkpoint_dir=cp_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert res["match"] is False
    assert any("InconsistentVersionWarning" in r for r in res["failing_reasons"])


def test_partner_checkpoint_fewer_than_60_records_fails(tmp_path: Path) -> None:
    """Partner Step-8 reproduction with fewer than 60 records fails verification."""
    cp_dir = tmp_path / "few_records_partner"
    cp_dir.mkdir(parents=True, exist_ok=True)

    (cp_dir / "environment_verification.json").write_text(
        json.dumps({"status": "PASS", "clean_source_execution": True}), encoding="utf-8"
    )
    (cp_dir / "execution.log").write_text("Clean execution without warnings\n", encoding="utf-8")
    (cp_dir / "pip_freeze.txt").write_text("scikit-learn==1.9.1\n", encoding="utf-8")
    (cp_dir / "pip_check.txt").write_text("No broken requirements found.\n", encoding="utf-8")
    (cp_dir / "input_manifest.json").write_text(
        json.dumps({"protected_inputs": {}}), encoding="utf-8"
    )
    (cp_dir / "step08_full_audit.json").write_text(
        json.dumps({"details": {"checkpoint_prediction_reproduction": {"records": []}}}),
        encoding="utf-8",
    )

    res = verify_partner_checkpoint_evidence(checkpoint_dir=cp_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert res["match"] is False
    assert any("Step-8 reproduction audit failed" in r for r in res["failing_reasons"])


# =============================================================================
# 9. Verify-Only Leaves Tracked Files Unchanged
# =============================================================================


def test_verify_only_leaves_tracked_files_unchanged() -> None:
    """Running verify-only CLI must leave git working tree byte-for-byte unchanged."""
    git_diff_before = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
    ).stdout

    # Run verify-only against historical v4
    subprocess.run(
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

    git_diff_after = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
    ).stdout

    assert git_diff_before == git_diff_after


# =============================================================================
# 10. Genuine Partner Checkpoint Evidence and Mutation Suite
# =============================================================================


def _copy_partner_fixture(target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    src_dir = Path("experiments/checkpoint_verification_v1")
    for f in src_dir.glob("*"):
        if f.is_file():
            shutil.copy2(f, target_dir / f.name)
    return target_dir


def test_genuine_merged_checkpoint_evidence_passes() -> None:
    """Genuine merged checkpoint evidence passes without mutations."""
    res = verify_partner_checkpoint_evidence(
        checkpoint_dir="experiments/checkpoint_verification_v1",
        base_dir=".",
    )
    assert res["status"] == "PASS"
    assert res["match"] is True
    assert len(res["failing_reasons"]) == 0
    assert len(res["file_hashes"]) == 6
    assert res["checks"]["environment_verification"]["status"] == "PASS"
    assert res["checks"]["frozen_inputs_match"]["match"] is True
    assert res["checks"]["frozen_inputs_match"]["total_files_checked"] == 233


def test_partner_checkpoint_empty_manifest_fails(tmp_path: Path) -> None:
    """Empty manifest in partner checkpoint evidence is rejected."""
    cp_dir = _copy_partner_fixture(tmp_path / "partner_empty_manifest")
    (cp_dir / "input_manifest.json").write_text(
        json.dumps(
            {
                "clean_source_execution": True,
                "git_dirty": False,
                "pre_post_comparison": {"protected_inputs_unchanged": True, "mismatches": []},
                "protected_inputs": {},
            }
        ),
        encoding="utf-8",
    )
    res = verify_partner_checkpoint_evidence(checkpoint_dir=cp_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert res["match"] is False
    assert any("missing or empty" in r or "category mismatch" in r for r in res["failing_reasons"])


def test_partner_checkpoint_omitted_category_fails(tmp_path: Path) -> None:
    """Omitted category in input manifest causes verification failure."""
    cp_dir = _copy_partner_fixture(tmp_path / "partner_omitted_cat")
    with open(cp_dir / "input_manifest.json", encoding="utf-8") as f:
        data = json.load(f)
    del data["protected_inputs"]["verification_sources"]
    (cp_dir / "input_manifest.json").write_text(json.dumps(data), encoding="utf-8")

    res = verify_partner_checkpoint_evidence(checkpoint_dir=cp_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert res["match"] is False
    assert any("category mismatch" in r for r in res["failing_reasons"])


def test_partner_checkpoint_omitted_file_fails(tmp_path: Path) -> None:
    """Omitted file within a category in input manifest causes verification failure."""
    cp_dir = _copy_partner_fixture(tmp_path / "partner_omitted_file")
    with open(cp_dir / "input_manifest.json", encoding="utf-8") as f:
        data = json.load(f)
    # Remove one checkpoint file
    cp_dict = data["protected_inputs"]["checkpoints"]
    first_k = next(iter(cp_dict.keys()))
    del cp_dict[first_k]
    (cp_dir / "input_manifest.json").write_text(json.dumps(data), encoding="utf-8")

    res = verify_partner_checkpoint_evidence(checkpoint_dir=cp_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert res["match"] is False
    assert any(
        "path membership mismatch" in r or "mismatched or incomplete" in r
        for r in res["failing_reasons"]
    )


def test_partner_checkpoint_changed_hash_outside_splits_fails(tmp_path: Path) -> None:
    """Changed hash in a non-splits category (e.g. checkpoints) causes verification failure."""
    cp_dir = _copy_partner_fixture(tmp_path / "partner_changed_hash")
    with open(cp_dir / "input_manifest.json", encoding="utf-8") as f:
        data = json.load(f)
    # Mutate a hash in checkpoints
    cp_dict = data["protected_inputs"]["checkpoints"]
    first_k = next(iter(cp_dict.keys()))
    cp_dict[first_k] = "0" * 64
    (cp_dir / "input_manifest.json").write_text(json.dumps(data), encoding="utf-8")

    res = verify_partner_checkpoint_evidence(checkpoint_dir=cp_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert res["match"] is False
    assert any(
        "Hash mismatch" in r or "mismatched or incomplete" in r for r in res["failing_reasons"]
    )


def test_partner_checkpoint_conflicting_environment_status_fails(tmp_path: Path) -> None:
    """Conflicting status (e.g. status=PASS, overall_status=FAIL) causes verification failure."""
    cp_dir = _copy_partner_fixture(tmp_path / "partner_conflict_status")
    with open(cp_dir / "environment_verification.json", encoding="utf-8") as f:
        data = json.load(f)
    data["overall_status"] = "FAIL"
    (cp_dir / "environment_verification.json").write_text(json.dumps(data), encoding="utf-8")

    res = verify_partner_checkpoint_evidence(checkpoint_dir=cp_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert res["match"] is False
    assert any("both status" in r for r in res["failing_reasons"])


def test_partner_checkpoint_dirty_source_fails(tmp_path: Path) -> None:
    """Dirty source (clean_source_execution=true but git_dirty=true) causes verification failure."""
    cp_dir = _copy_partner_fixture(tmp_path / "partner_dirty_src")
    with open(cp_dir / "environment_verification.json", encoding="utf-8") as f:
        data = json.load(f)
    data["git_dirty"] = True
    (cp_dir / "environment_verification.json").write_text(json.dumps(data), encoding="utf-8")

    res = verify_partner_checkpoint_evidence(checkpoint_dir=cp_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert res["match"] is False
    assert any("git_dirty must be false" in r for r in res["failing_reasons"])


def test_partner_checkpoint_incompatible_versions_fails(tmp_path: Path) -> None:
    """Incompatible runtime package versions cause verification failure."""
    cp_dir = _copy_partner_fixture(tmp_path / "partner_incompat_vers")
    with open(cp_dir / "environment_verification.json", encoding="utf-8") as f:
        data = json.load(f)
    data["actual_versions"]["scikit-learn"] = "1.2.0"
    (cp_dir / "environment_verification.json").write_text(json.dumps(data), encoding="utf-8")

    res = verify_partner_checkpoint_evidence(checkpoint_dir=cp_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert res["match"] is False
    assert any("expected_versions must equal actual_versions" in r for r in res["failing_reasons"])


def test_partner_checkpoint_failed_pip_check_fails(tmp_path: Path) -> None:
    """Failed pip check (pip_check_exit_code != 0) causes verification failure."""
    cp_dir = _copy_partner_fixture(tmp_path / "partner_pip_fail")
    with open(cp_dir / "environment_verification.json", encoding="utf-8") as f:
        data = json.load(f)
    data["pip_check_exit_code"] = 1
    (cp_dir / "environment_verification.json").write_text(json.dumps(data), encoding="utf-8")

    res = verify_partner_checkpoint_evidence(checkpoint_dir=cp_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert res["match"] is False
    assert any("pip_check_exit_code must be 0" in r for r in res["failing_reasons"])


def test_partner_checkpoint_nonzero_warning_count_fails(tmp_path: Path) -> None:
    """Nonzero sklearn warning count causes verification failure."""
    cp_dir = _copy_partner_fixture(tmp_path / "partner_nonzero_warn")
    with open(cp_dir / "environment_verification.json", encoding="utf-8") as f:
        data = json.load(f)
    data["sklearn_inconsistent_version_warning_count"] = 2
    (cp_dir / "environment_verification.json").write_text(json.dumps(data), encoding="utf-8")

    res = verify_partner_checkpoint_evidence(checkpoint_dir=cp_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert res["match"] is False
    assert any(
        "sklearn_inconsistent_version_warning_count must be 0" in r for r in res["failing_reasons"]
    )


def test_partner_checkpoint_failed_full_audit_or_skipped_check_fails(tmp_path: Path) -> None:
    """Failed full audit overall status or skipped mandatory checks causes failure."""
    cp_dir = _copy_partner_fixture(tmp_path / "partner_audit_skipped")
    with open(cp_dir / "step08_full_audit.json", encoding="utf-8") as f:
        data = json.load(f)
    data["checks_not_run"] = ["checkpoint_prediction_reproduction"]
    (cp_dir / "step08_full_audit.json").write_text(json.dumps(data), encoding="utf-8")

    res = verify_partner_checkpoint_evidence(checkpoint_dir=cp_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert res["match"] is False
    assert any("checks_not_run must be empty" in r for r in res["failing_reasons"])


def test_partner_checkpoint_inconsistent_source_shas_fails(tmp_path: Path) -> None:
    """Inconsistent source-execution SHA between environment and full audit causes failure."""
    cp_dir = _copy_partner_fixture(tmp_path / "partner_inconsistent_sha")
    with open(cp_dir / "step08_full_audit.json", encoding="utf-8") as f:
        data = json.load(f)
    data["current_reconstruction"]["git_commit"] = "0" * 40
    (cp_dir / "step08_full_audit.json").write_text(json.dumps(data), encoding="utf-8")

    res = verify_partner_checkpoint_evidence(checkpoint_dir=cp_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert res["match"] is False
    assert any("Partner source-execution SHA mismatch" in r for r in res["failing_reasons"])


def test_saved_freeze_v5_missing_or_empty_bindings_fails(tmp_path: Path) -> None:
    """Missing or empty v5 partner, regression, or source bindings must FAIL."""
    bundle_dir = tmp_path / "bundle_v5_missing_bindings"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    fake_freeze = {
        "schema_version": "step09-freeze-v5",
        "source_evidence_dir": "experiments/pretest_verification_v3",
        "bindings": {
            # Omit partner hashes, regression report, and source hashes
        },
    }
    (bundle_dir / "protocol_freeze.json").write_text(json.dumps(fake_freeze), encoding="utf-8")

    audit = verify_saved_freeze(
        freeze_path=bundle_dir / "protocol_freeze.json",
        source_evidence_dir="experiments/pretest_verification_v3",
        base_dir=".",
        allow_dirty=True,
        rerun_regression=False,
    )
    assert audit["overall_status"] == "FAIL"
    assert audit["bindings_passed"] is False
