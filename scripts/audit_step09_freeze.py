"""Step 9: Pre-test readiness content verification, protocol freeze, and audit."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from intellitwin.data.artifacts import compute_sha256
from intellitwin.evaluation.schema import PROTOCOL_VERSION
from intellitwin.evaluation.verification import verify_validation_smoke_matrix
from intellitwin.provenance import (
    capture_environment_metadata,
    get_git_info,
    write_immutable_json,
)
from intellitwin.uncertainty.artifacts import resolve_repo_relative_path


def audit_pretest_evidence(
    verification_dir: Path | str = "experiments/pretest_verification_v2",
    base_dir: Path | str = ".",
    allow_dirty: bool = False,
    git_info: tuple[str, bool] | None = None,
    env_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Perform content-level verification of all pre-test readiness evidence.

    Returns PASS only if every mandatory check executes and passes.
    Returns INCOMPLETE if mandatory evidence or execution is missing.
    Returns FAIL if any check executes and fails.
    """
    base = Path(base_dir).resolve()
    v_dir = Path(verification_dir)
    if not v_dir.is_absolute():
        v_dir = (base / v_dir).resolve()

    if git_info is not None:
        git_sha, git_dirty = git_info
    else:
        git_sha, git_dirty = get_git_info(allow_dirty=allow_dirty, repo_root=base)
    if env_meta is None:
        env_meta = capture_environment_metadata(device="cpu")

    checks: dict[str, Any] = {}
    missing_items: list[str] = []

    # 1. Step 8 Full Audit Verification
    s8_audit_p = v_dir / "step08_full_audit.json"
    if not s8_audit_p.exists():
        missing_items.append("step08_full_audit.json")
        checks["step08_full_audit"] = {"status": "MISSING"}
    else:
        with open(s8_audit_p, encoding="utf-8") as f:
            s8_data = json.load(f)
        s8_status = s8_data.get("overall_status")
        raw_repro = s8_data.get("details", {}).get(
            "checkpoint_prediction_reproduction",
            s8_data.get("raw_checkpoint_reproduction", {}),
        )
        checks_count = raw_repro.get("models_verified", raw_repro.get("passing_checks_count", 0))
        max_err = float(raw_repro.get("max_diff_overall", raw_repro.get("max_absolute_error", 1.0)))
        raw_passed = (checks_count == 60) and (max_err <= 1e-4)
        checks["step08_full_audit"] = {
            "status": "PASS" if (s8_status == "PASS" and raw_passed) else "FAIL",
            "overall_status": s8_status,
            "raw_reproduction_checks_passed": checks_count,
            "raw_reproduction_expected": 60,
            "raw_reproduction_max_absolute_error": max_err,
        }

    # 2. Baseline Manifest Verification
    base_man_p = v_dir / "baseline_manifest.json"
    if not base_man_p.exists():
        missing_items.append("baseline_manifest.json")
        checks["baseline_manifest"] = {"status": "MISSING"}
    else:
        with open(base_man_p, encoding="utf-8") as f:
            b_man = json.load(f)
        tracked_info = b_man.get("repository_tracked_protected_artifacts", {})
        tracked_pass = (
            tracked_info.get("expected") == 652
            and tracked_info.get("matched") == 652
            and tracked_info.get("missing") == 0
            and tracked_info.get("changed") == 0
        )
        reg_mig = b_man.get("registry_portability_migration", {})
        reg_pass = reg_mig.get("entries_agreement_pass") is True
        checks["baseline_manifest"] = {
            "status": "PASS" if (tracked_pass and reg_pass) else "FAIL",
            "baseline_commit": b_man.get("baseline_commit"),
            "tracked_expected": tracked_info.get("expected"),
            "tracked_matched": tracked_info.get("matched"),
            "tracked_missing": tracked_info.get("missing"),
            "tracked_changed": tracked_info.get("changed"),
            "registry_migration_pass": reg_pass,
        }

    # 3. Calibration Registry and Calibrators
    cal_reg_p = resolve_repo_relative_path(
        base, "experiments/calibration/calibration_registry.json"
    )
    if not cal_reg_p.exists():
        missing_items.append("experiments/calibration/calibration_registry.json")
        checks["calibration_registry"] = {"status": "MISSING"}
    else:
        with open(cal_reg_p, encoding="utf-8") as f:
            cal_reg_data = json.load(f)
        entries = cal_reg_data.get("entries", {})
        has_90 = len(entries) == 90
        has_backslash = any(
            "\\" in str(e.get("calibrator_artifact_path", "")) for e in entries.values()
        )
        all_cal_files_exist = all(
            (base / e.get("calibrator_artifact_path", "")).exists() for e in entries.values()
        )
        checks["calibration_registry"] = {
            "status": "PASS" if (has_90 and not has_backslash and all_cal_files_exist) else "FAIL",
            "entries_count": len(entries),
            "paths_posix": not has_backslash,
            "all_calibrators_exist": all_cal_files_exist,
        }

    # 4. Prespecified Controls Verification
    ctrl_reconstruct_p = v_dir / "control_reconstruction.json"
    ctrl_gbr_p = v_dir / "controls" / "FD002" / "GBR" / "selection.json"
    ctrl_lstm_p = v_dir / "controls" / "FD002" / "LSTM" / "selection.json"
    if not (ctrl_reconstruct_p.exists() and ctrl_gbr_p.exists() and ctrl_lstm_p.exists()):
        missing_items.append("controls and control_reconstruction.json")
        checks["controls_verification"] = {"status": "MISSING"}
    else:
        with open(ctrl_reconstruct_p, encoding="utf-8") as f:
            ctrl_recon = json.load(f)
        gbr_pass = (
            ctrl_recon.get("models", {}).get("GBR", {}).get("matched_width_readiness_pass") is True
        )
        lstm_pass = (
            ctrl_recon.get("models", {}).get("LSTM", {}).get("matched_width_readiness_pass") is True
        )
        checks["controls_verification"] = {
            "status": "PASS" if (gbr_pass and lstm_pass) else "FAIL",
            "gbr_matched_width_pass": gbr_pass,
            "gbr_matched_width_diff": ctrl_recon.get("models", {})
            .get("GBR", {})
            .get("matched_width_diff"),
            "lstm_matched_width_pass": lstm_pass,
            "lstm_matched_width_diff": ctrl_recon.get("models", {})
            .get("LSTM", {})
            .get("matched_width_diff"),
        }

    # 5. Validation Smoke Content Verification
    smoke_dir = v_dir / "validation_smoke"
    if not (smoke_dir / "execution_manifest.json").exists():
        missing_items.append("validation_smoke/execution_manifest.json")
        checks["validation_smoke_verification"] = {"status": "MISSING"}
    else:
        smoke_res = verify_validation_smoke_matrix(smoke_dir=smoke_dir, base_dir=base)
        checks["validation_smoke_verification"] = smoke_res

    # 6. Anti-Leakage / Zero Held-Out Verification
    test_artifacts = list(base.glob("experiments/**/test_*.csv")) + list(
        base.glob("experiments/**/official_test*.csv")
    )
    checks["zero_held_out_artifacts"] = {
        "status": "PASS" if len(test_artifacts) == 0 else "FAIL",
        "found_test_artifacts_count": len(test_artifacts),
    }

    if missing_items:
        overall_status = "INCOMPLETE"
    elif any(
        c.get("status") == "FAIL" or (isinstance(c, dict) and c.get("overall_match") is False)
        for c in checks.values()
    ):
        overall_status = "FAIL"
    else:
        overall_status = "PASS"

    return {
        "protocol_version": PROTOCOL_VERSION,
        "schema_version": "step09-evidence-audit-v2",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_sha,
        "git_dirty": git_dirty,
        "environment": env_meta,
        "overall_status": overall_status,
        "missing_items": missing_items,
        "checks": checks,
    }


def build_protocol_freeze(
    evidence_report: dict[str, Any],
    verification_dir: Path | str = "experiments/pretest_verification_v2",
    base_dir: Path | str = ".",
    allow_dirty: bool = False,
    git_info: tuple[str, bool] | None = None,
    env_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble all cryptographic bindings into protocol_freeze.json after evidence passes."""
    if evidence_report.get("overall_status") != "PASS":
        raise RuntimeError(
            f"Cannot build protocol freeze: pre-test evidence status is "
            f"{evidence_report.get('overall_status')}; must be PASS."
        )

    base = Path(base_dir).resolve()
    v_dir = Path(verification_dir)
    if not v_dir.is_absolute():
        v_dir = (base / v_dir).resolve()

    if git_info is not None:
        git_sha, git_dirty = git_info
    else:
        git_sha, git_dirty = get_git_info(allow_dirty=allow_dirty, repo_root=base)
    if env_meta is None:
        env_meta = capture_environment_metadata(device="cpu")

    # 1. Confirmatory protocol config
    config_p = resolve_repo_relative_path(
        base, "research/research_design/step09_confirmatory_config.json"
    )
    with open(config_p, encoding="utf-8") as f:
        confirmatory_config = json.load(f)

    # 2. Split manifests and quartile provenance
    split_files = [
        "data/splits/fd001_engine_split_seed_2026.json",
        "data/splits/fd002_engine_split_seed_2026.json",
        "data/splits/fd002_lifetime_quartile_provenance.json",
        "data/splits/fd004_engine_split_seed_2026.json",
    ]
    split_hashes = {f: compute_sha256(resolve_repo_relative_path(base, f)) for f in split_files}

    # 3. Base model registry and selection freeze
    model_reg_p = resolve_repo_relative_path(base, "experiments/base_models/model_registry.json")
    step08_freeze_p = resolve_repo_relative_path(
        base, "experiments/calibration/selection/selection_freeze.json"
    )
    cal_reg_p = resolve_repo_relative_path(
        base, "experiments/calibration/calibration_registry.json"
    )

    # 4. Verified pre-test evidence artifacts
    base_man_p = v_dir / "baseline_manifest.json"
    s8_full_audit_p = v_dir / "step08_full_audit.json"
    ctrl_recon_p = v_dir / "control_reconstruction.json"
    smoke_manifest_p = v_dir / "validation_smoke" / "execution_manifest.json"

    # 5. Control selection files
    control_gbr_p = v_dir / "controls" / "FD002" / "GBR" / "selection.json"
    control_lstm_p = v_dir / "controls" / "FD002" / "LSTM" / "selection.json"
    with open(control_gbr_p, encoding="utf-8") as f:
        ctrl_gbr_data = json.load(f)
    with open(control_lstm_p, encoding="utf-8") as f:
        ctrl_lstm_data = json.load(f)

    # 6. Evaluation and verification source files
    source_files = [
        "src/intellitwin/provenance.py",
        "src/intellitwin/decision/controls.py",
        "src/intellitwin/uncertainty/verification.py",
        "src/intellitwin/evaluation/schema.py",
        "src/intellitwin/evaluation/validation.py",
        "src/intellitwin/evaluation/metrics.py",
        "src/intellitwin/evaluation/bootstrap.py",
        "src/intellitwin/evaluation/decisions.py",
        "src/intellitwin/evaluation/artifacts.py",
        "src/intellitwin/evaluation/inference.py",
        "src/intellitwin/evaluation/runner.py",
        "src/intellitwin/evaluation/verification.py",
    ]
    source_hashes = {f: compute_sha256(resolve_repo_relative_path(base, f)) for f in source_files}

    freeze = {
        "protocol_version": PROTOCOL_VERSION,
        "schema_version": "step09-freeze-v2",
        "status": "PRETEST_FROZEN",
        "source_execution_commit": git_sha,
        "git_dirty": git_dirty,
        "freeze_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "environment": env_meta,
        "confirmatory_configuration": {
            "config_path": "research/research_design/step09_confirmatory_config.json",
            "config_sha256": compute_sha256(config_p),
            "payload": confirmatory_config,
        },
        "bindings": {
            "splits_and_quartiles": split_hashes,
            "base_model_registry_sha256": compute_sha256(model_reg_p),
            "calibrator_registry_sha256": compute_sha256(cal_reg_p),
            "step08_selection_freeze_sha256": compute_sha256(step08_freeze_p),
            "baseline_manifest_sha256": compute_sha256(base_man_p),
            "step08_full_audit_sha256": compute_sha256(s8_full_audit_p),
            "control_reconstruction_sha256": compute_sha256(ctrl_recon_p),
            "control_selection_FD002_GBR_sha256": compute_sha256(control_gbr_p),
            "control_selection_FD002_LSTM_sha256": compute_sha256(control_lstm_p),
            "validation_smoke_execution_manifest_sha256": compute_sha256(smoke_manifest_p),
            "source_hashes": source_hashes,
        },
        "selected_controls": {
            "GBR": ctrl_gbr_data["selected_controls"],
            "LSTM": ctrl_lstm_data["selected_controls"],
        },
        "matrix_counts": {
            "primary_configurations": 810,
            "control_configurations": 120,
            "total_configurations": 930,
            "outcome_rows": 19590,
            "cell_summary_rows": 186,
            "bootstrap_replicates": 10000,
        },
        "held_out_status": {
            "execution_status": "NOT_STARTED",
            "test_windows_prepared": False,
            "confirmatory_conclusions": "PENDING",
        },
    }
    return freeze


def verify_saved_freeze(
    freeze_path: Path | str,
    base_dir: Path | str = ".",
    allow_dirty: bool = False,
    git_info: tuple[str, bool] | None = None,
    env_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Independently verify saved protocol freeze and generate pretest_audit.json."""
    base = Path(base_dir).resolve()
    f_path = Path(freeze_path)
    if not f_path.is_absolute():
        f_path = (base / f_path).resolve()

    if not f_path.exists():
        raise FileNotFoundError(f"Protocol freeze missing: {f_path}")

    if git_info is not None:
        git_sha, git_dirty = git_info
    else:
        git_sha, git_dirty = get_git_info(allow_dirty=allow_dirty, repo_root=base)
    if env_meta is None:
        env_meta = capture_environment_metadata(device="cpu")

    with open(f_path, encoding="utf-8") as f:
        freeze_data = json.load(f)

    # Verify bound hashes against disk
    bindings = freeze_data.get("bindings", {})
    verified_bindings: dict[str, bool] = {}

    for k, h in bindings.get("splits_and_quartiles", {}).items():
        actual_h = compute_sha256(resolve_repo_relative_path(base, k))
        verified_bindings[k] = actual_h == h

    for k, h in bindings.get("source_hashes", {}).items():
        actual_h = compute_sha256(resolve_repo_relative_path(base, k))
        verified_bindings[k] = actual_h == h

    single_bindings = [
        ("base_model_registry_sha256", "experiments/base_models/model_registry.json"),
        ("calibrator_registry_sha256", "experiments/calibration/calibration_registry.json"),
        (
            "step08_selection_freeze_sha256",
            "experiments/calibration/selection/selection_freeze.json",
        ),
        ("baseline_manifest_sha256", f_path.parent / "baseline_manifest.json"),
        ("step08_full_audit_sha256", f_path.parent / "step08_full_audit.json"),
        ("control_reconstruction_sha256", f_path.parent / "control_reconstruction.json"),
        ("control_selection_FD002_GBR_sha256", f_path.parent / "controls/FD002/GBR/selection.json"),
        (
            "control_selection_FD002_LSTM_sha256",
            f_path.parent / "controls/FD002/LSTM/selection.json",
        ),
        (
            "validation_smoke_execution_manifest_sha256",
            f_path.parent / "validation_smoke/execution_manifest.json",
        ),
    ]
    for b_key, b_rel in single_bindings:
        p = b_rel if isinstance(b_rel, Path) else resolve_repo_relative_path(base, b_rel)
        actual_h = compute_sha256(p)
        verified_bindings[b_key] = actual_h == bindings.get(b_key)

    all_bindings_match = all(verified_bindings.values())

    pretest_audit = {
        "protocol_version": PROTOCOL_VERSION,
        "schema_version": "step09-audit-v2",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_sha,
        "git_dirty": git_dirty,
        "environment": env_meta,
        "overall_status": "PASS" if all_bindings_match else "FAIL",
        "pretest_readiness_status": "PRETEST_READY" if all_bindings_match else "BLOCKED",
        "protocol_freeze_sha256": compute_sha256(f_path),
        "verified_bindings": verified_bindings,
        "matrix_counts": freeze_data.get("matrix_counts"),
        "held_out_execution_status": "NOT_STARTED",
        "rq_outcomes_status": "PENDING",
    }
    return pretest_audit


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Step 9 Pre-Test Verification, Protocol Freeze, and Audit"
    )
    parser.add_argument(
        "--verification-dir",
        type=str,
        default="experiments/pretest_verification_v2",
        help="Directory containing pretest verification artifacts",
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Repository root base directory",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Permit execution on dirty working tree (development runs only)",
    )
    args = parser.parse_args()

    v_dir = Path(args.verification_dir).resolve()
    base = Path(args.base_dir).resolve()

    print("=" * 80)
    print("Step 9: Confirmatory Protocol Freeze and Pre-Test Readiness Audit")
    print(f"Verification Directory: {v_dir}")
    print("=" * 80)

    # Capture provenance once at process entry
    git_sha, git_dirty = get_git_info(allow_dirty=args.allow_dirty, repo_root=base)
    env_meta = capture_environment_metadata(device="cpu")
    git_info = (git_sha, git_dirty)

    # 1. Audit evidence
    print("\nPhase 1: Auditing pre-test evidence...")
    evidence_report = audit_pretest_evidence(
        verification_dir=v_dir,
        base_dir=base,
        allow_dirty=args.allow_dirty,
        git_info=git_info,
        env_meta=env_meta,
    )
    print(f"  Evidence Audit Status: {evidence_report['overall_status']}")
    if evidence_report["overall_status"] != "PASS":
        print(f"  Missing items: {evidence_report['missing_items']}")
        st = evidence_report["overall_status"]
        print(f"ERROR: Cannot proceed with freeze. Overall status is {st}.")
        sys.exit(1)

    # 2. Build protocol_freeze.json
    print("\nPhase 2: Building protocol freeze...")
    freeze_data = build_protocol_freeze(
        evidence_report=evidence_report,
        verification_dir=v_dir,
        base_dir=base,
        allow_dirty=args.allow_dirty,
        git_info=git_info,
        env_meta=env_meta,
    )
    freeze_p = v_dir / "protocol_freeze.json"
    write_immutable_json(freeze_p, freeze_data, overwrite=False)
    print(f"  Saved protocol freeze to {freeze_p}")

    # 3. Verify saved freeze and produce pretest_audit.json
    print("\nPhase 3: Verifying saved freeze and producing pretest audit...")
    audit_data = verify_saved_freeze(
        freeze_path=freeze_p,
        base_dir=base,
        allow_dirty=args.allow_dirty,
        git_info=git_info,
        env_meta=env_meta,
    )
    audit_p = v_dir / "pretest_audit.json"
    write_immutable_json(audit_p, audit_data, overwrite=False)
    print(f"  Saved pretest audit to {audit_p}")
    print(f"  Overall Status: {audit_data['overall_status']}")
    print(f"  Pre-Test Readiness: {audit_data['pretest_readiness_status']}")
    print(f"  Held-Out Execution: {audit_data['held_out_execution_status']}")
    print(f"  RQ Outcomes: {audit_data['rq_outcomes_status']}")

    if audit_data["overall_status"] != "PASS":
        print("ERROR: Pre-test audit failed verification gates!")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("PRE-TEST READINESS VERIFICATION COMPLETE (STATUS: PRETEST_READY)")
    print("=" * 80)


if __name__ == "__main__":
    main()
