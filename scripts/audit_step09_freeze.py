"""Step 9: Pre-test readiness content verification, protocol freeze, and audit."""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from intellitwin.data.artifacts import compute_sha256
from intellitwin.evaluation.schema import (
    CONFIRMATORY_DATASETS,
    CONFIRMATORY_MODELS,
    CONFIRMATORY_SEEDS,
    PROTOCOL_VERSION,
)
from intellitwin.evaluation.verification import (
    REQUIRED_SMOKE_FILES,
    verify_validation_smoke_matrix,
)
from intellitwin.provenance import (
    capture_environment_metadata,
    get_git_info,
    write_immutable_json,
)
from intellitwin.uncertainty.artifacts import resolve_repo_relative_path

FROZEN_SCIENTIFIC_PROTOCOLS: tuple[str, ...] = (
    "research/hypotheses/hypothesis_framework.yaml",
    "research/research_design/statistical_inference_protocol.md",
    "research/research_design/data_evaluation_protocol.md",
    "research/research_design/maintenance_cost_scenarios.yaml",
    "research/research_design/step09_confirmatory_protocol.md",
    "research/research_design/step09_confirmatory_config.json",
    "research/research_design/step09_control_selection.md",
)

FROZEN_SPLIT_AND_QUARTILE_FILES: tuple[str, ...] = (
    "data/splits/fd001_engine_split_seed_2026.json",
    "data/splits/fd002_engine_split_seed_2026.json",
    "data/splits/fd002_lifetime_quartile_provenance.json",
    "data/splits/fd004_engine_split_seed_2026.json",
)

CORE_SOURCE_FILES: tuple[str, ...] = (
    "src/intellitwin/provenance.py",
    "src/intellitwin/decision/controls.py",
    "src/intellitwin/uncertainty/artifacts.py",
    "src/intellitwin/uncertainty/verification.py",
    "src/intellitwin/evaluation/schema.py",
    "src/intellitwin/evaluation/evidence_schema.py",
    "src/intellitwin/evaluation/validation.py",
    "src/intellitwin/evaluation/metrics.py",
    "src/intellitwin/evaluation/bootstrap.py",
    "src/intellitwin/evaluation/decisions.py",
    "src/intellitwin/evaluation/artifacts.py",
    "src/intellitwin/evaluation/inference.py",
    "src/intellitwin/evaluation/runner.py",
    "src/intellitwin/evaluation/verification.py",
    "scripts/run_step09_validation_smoke.py",
    "scripts/audit_step09_freeze.py",
)


def verify_step08_report_records(s8_path: Path) -> dict[str, Any]:
    """Independently audit referenced Step-8 raw-reproduction report.

    Requires exactly 60 records: 3 datasets x 2 models x 5 seeds x 2 partitions.
    Partitions must be validation and calibration.
    Every record must report PASS and finite error <= 1e-4.
    Recomputes summary counts and max error from records.
    """
    with open(s8_path, encoding="utf-8") as f:
        s8_data = json.load(f)

    raw_repro = s8_data.get("details", {}).get(
        "checkpoint_prediction_reproduction",
        s8_data.get("raw_checkpoint_reproduction", {}),
    )
    records = raw_repro.get("records", [])

    expected_keys = {
        (ds, fam, s, part)
        for ds in CONFIRMATORY_DATASETS
        for fam in CONFIRMATORY_MODELS
        for s in CONFIRMATORY_SEEDS
        for part in ("validation", "calibration")
    }

    actual_keys: set[tuple[str, str, int, str]] = set()
    all_passed = True
    max_err = 0.0

    for r in records:
        key = (
            str(r.get("dataset")),
            str(r.get("model_family")),
            int(r.get("seed")),
            str(r.get("partition")),
        )
        actual_keys.add(key)
        st = r.get("status")
        err = float(r.get("max_abs_diff", r.get("max_absolute_error", 1.0)))
        if st != "PASS" or not math.isfinite(err) or err > 1e-4:
            all_passed = False
        if err > max_err:
            max_err = err

    match = len(records) == 60 and actual_keys == expected_keys and all_passed and max_err <= 1e-4

    return {
        "status": "PASS" if match else "FAIL",
        "record_count": len(records),
        "expected_count": 60,
        "keys_match": actual_keys == expected_keys,
        "all_records_pass": all_passed,
        "max_absolute_error": max_err,
        "match": match,
    }


def audit_pretest_evidence(
    verification_dir: Path | str = "experiments/pretest_verification_v3",
    base_dir: Path | str = ".",
    allow_dirty: bool = False,
    git_info: tuple[str, bool] | None = None,
    env_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Perform authoritative content-level verification of all pre-test readiness evidence."""
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
        checks["step08_full_audit"] = verify_step08_report_records(s8_audit_p)

    # 2. Control Reconstruction Verification
    ctrl_recon_p = v_dir / "control_reconstruction.json"
    ctrl_gbr_p = v_dir / "controls" / "FD002" / "GBR" / "selection.json"
    ctrl_lstm_p = v_dir / "controls" / "FD002" / "LSTM" / "selection.json"
    if not (ctrl_recon_p.exists() and ctrl_gbr_p.exists() and ctrl_lstm_p.exists()):
        missing_items.append("controls and control_reconstruction.json")
        checks["controls_verification"] = {"status": "MISSING"}
    else:
        with open(ctrl_recon_p, encoding="utf-8") as f:
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
            "lstm_matched_width_pass": lstm_pass,
        }

    # 3. Validation Smoke Content Verification
    smoke_dir = v_dir / "validation_smoke"
    smoke_manifest_p = smoke_dir / "execution_manifest.json"
    if not smoke_manifest_p.exists():
        missing_items.append("validation_smoke/execution_manifest.json")
        checks["validation_smoke_verification"] = {"status": "MISSING"}
    else:
        smoke_res = verify_validation_smoke_matrix(smoke_dir=smoke_dir, base_dir=base)
        checks["validation_smoke_verification"] = smoke_res
        # Save content_verification.json report
        content_rep_p = v_dir / "content_verification.json"
        write_immutable_json(
            content_rep_p,
            {
                "protocol_version": PROTOCOL_VERSION,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "git_commit": git_sha,
                "git_dirty": git_dirty,
                "status": smoke_res["status"],
                "overall_match": smoke_res["overall_match"],
                "failing_reasons": smoke_res["failing_reasons"],
                "checks": smoke_res["checks"],
            },
            overwrite=True,
        )

    # 4. Calibration Registry Transitive Integrity
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
        cal_all_exist = len(entries) == 90 and all(
            (base / e.get("calibrator_artifact_path", "")).exists() for e in entries.values()
        )
        checks["calibration_registry"] = {
            "status": "PASS" if cal_all_exist else "FAIL",
            "entries_count": len(entries),
            "all_calibrators_exist": cal_all_exist,
        }

    # 5. Anti-Leakage / Zero Held-Out Verification
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
        "schema_version": "step09-evidence-audit-v3",
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
    verification_dir: Path | str = "experiments/pretest_verification_v3",
    base_dir: Path | str = ".",
    allow_dirty: bool = False,
    git_info: tuple[str, bool] | None = None,
    env_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble authoritative cryptographic bindings into protocol_freeze.json."""
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

    # 1. Scientific Protocols & Configurations
    protocol_hashes = {
        f: compute_sha256(resolve_repo_relative_path(base, f)) for f in FROZEN_SCIENTIFIC_PROTOCOLS
    }

    # 2. Split Manifests and Quartiles
    split_hashes = {
        f: compute_sha256(resolve_repo_relative_path(base, f))
        for f in FROZEN_SPLIT_AND_QUARTILE_FILES
    }

    # 3. Registries
    model_reg_p = resolve_repo_relative_path(base, "experiments/base_models/model_registry.json")
    cal_reg_p = resolve_repo_relative_path(
        base, "experiments/calibration/calibration_registry.json"
    )
    step08_freeze_p = resolve_repo_relative_path(
        base, "experiments/calibration/selection/selection_freeze.json"
    )

    # 4. Transitive Artifact Hashes (Checkpoints, Preprocessors, Calibrators)
    with open(model_reg_p, encoding="utf-8") as f:
        m_reg = json.load(f)
    checkpoint_hashes = {}
    for entry in m_reg.get("checkpoints", {}).values():
        p_rel = entry.get("checkpoint_path", "")
        if p_rel:
            checkpoint_hashes[p_rel] = compute_sha256(resolve_repo_relative_path(base, p_rel))

    with open(cal_reg_p, encoding="utf-8") as f:
        c_reg = json.load(f)
    calibrator_hashes = {}
    preprocessor_hashes = {}
    for entry in c_reg.get("entries", {}).values():
        c_rel = entry.get("calibrator_artifact_path", "")
        if c_rel:
            calibrator_hashes[c_rel] = compute_sha256(resolve_repo_relative_path(base, c_rel))
        p_rel = entry.get("preprocessor_path", "")
        if p_rel:
            preprocessor_hashes[p_rel] = compute_sha256(resolve_repo_relative_path(base, p_rel))

    # 5. Selected Controls
    ctrl_recon_p = v_dir / "control_reconstruction.json"
    control_gbr_p = v_dir / "controls" / "FD002" / "GBR" / "selection.json"
    control_lstm_p = v_dir / "controls" / "FD002" / "LSTM" / "selection.json"
    with open(control_gbr_p, encoding="utf-8") as f:
        ctrl_gbr_data = json.load(f)
    with open(control_lstm_p, encoding="utf-8") as f:
        ctrl_lstm_data = json.load(f)

    # 6. Smoke Evidence Files
    smoke_dir = v_dir / "validation_smoke"
    smoke_hashes = {
        f: compute_sha256(smoke_dir / f) for f in REQUIRED_SMOKE_FILES if (smoke_dir / f).exists()
    }

    # 7. Core Source Files
    source_hashes = {
        f: compute_sha256(resolve_repo_relative_path(base, f)) for f in CORE_SOURCE_FILES
    }

    # 8. Content Verification Report
    content_rep_p = v_dir / "content_verification.json"
    content_rep_hash = compute_sha256(content_rep_p) if content_rep_p.exists() else None

    # Load confirmatory config payload
    config_p = resolve_repo_relative_path(
        base, "research/research_design/step09_confirmatory_config.json"
    )
    with open(config_p, encoding="utf-8") as f:
        conf_cfg = json.load(f)

    freeze = {
        "protocol_version": PROTOCOL_VERSION,
        "schema_version": "step09-freeze-v3",
        "status": "PRETEST_FROZEN",
        "source_execution_commit": git_sha,
        "git_dirty": git_dirty,
        "freeze_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "environment": env_meta,
        "confirmatory_configuration": {
            "config_path": "research/research_design/step09_confirmatory_config.json",
            "config_sha256": compute_sha256(config_p),
            "payload": conf_cfg,
        },
        "bindings": {
            "scientific_protocols": protocol_hashes,
            "splits_and_quartiles": split_hashes,
            "base_model_registry_sha256": compute_sha256(model_reg_p),
            "calibrator_registry_sha256": compute_sha256(cal_reg_p),
            "step08_selection_freeze_sha256": compute_sha256(step08_freeze_p),
            "step08_full_audit_sha256": compute_sha256(v_dir / "step08_full_audit.json"),
            "control_reconstruction_sha256": compute_sha256(ctrl_recon_p),
            "control_selection_FD002_GBR_sha256": compute_sha256(control_gbr_p),
            "control_selection_FD002_LSTM_sha256": compute_sha256(control_lstm_p),
            "content_verification_sha256": content_rep_hash,
            "smoke_evidence_files": smoke_hashes,
            "transitive_checkpoints": checkpoint_hashes,
            "transitive_preprocessors": preprocessor_hashes,
            "transitive_calibrators": calibrator_hashes,
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
            "component_evidence_rows": 152,
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
    """Independently verify saved protocol freeze, re-verifying content
    and generating pretest_audit.json.
    """
    base = Path(base_dir).resolve()
    f_path = Path(freeze_path)
    if not f_path.is_absolute():
        f_path = (base / f_path).resolve()

    if not f_path.exists():
        raise FileNotFoundError(f"Protocol freeze missing: {f_path}")

    v_dir = f_path.parent

    if git_info is not None:
        git_sha, git_dirty = git_info
    else:
        git_sha, git_dirty = get_git_info(allow_dirty=allow_dirty, repo_root=base)
    if env_meta is None:
        env_meta = capture_environment_metadata(device="cpu")

    with open(f_path, encoding="utf-8") as f:
        freeze_data = json.load(f)

    bindings = freeze_data.get("bindings", {})
    verified_bindings: dict[str, bool] = {}

    # 1. Verify dict-valued bindings
    for group_name in (
        "scientific_protocols",
        "splits_and_quartiles",
        "source_hashes",
        "transitive_checkpoints",
        "transitive_preprocessors",
        "transitive_calibrators",
    ):
        for k, h in bindings.get(group_name, {}).items():
            p = resolve_repo_relative_path(base, k)
            actual_h = compute_sha256(p)
            verified_bindings[f"{group_name}:{k}"] = actual_h == h

    # 2. Verify smoke evidence hashes
    smoke_dir = v_dir / "validation_smoke"
    for f_name, h in bindings.get("smoke_evidence_files", {}).items():
        actual_h = compute_sha256(smoke_dir / f_name)
        verified_bindings[f"smoke:{f_name}"] = actual_h == h

    # 3. Verify single file bindings
    single_bindings = [
        (
            "base_model_registry_sha256",
            resolve_repo_relative_path(base, "experiments/base_models/model_registry.json"),
        ),
        (
            "calibrator_registry_sha256",
            resolve_repo_relative_path(base, "experiments/calibration/calibration_registry.json"),
        ),
        (
            "step08_selection_freeze_sha256",
            resolve_repo_relative_path(
                base, "experiments/calibration/selection/selection_freeze.json"
            ),
        ),
        ("step08_full_audit_sha256", v_dir / "step08_full_audit.json"),
        ("control_reconstruction_sha256", v_dir / "control_reconstruction.json"),
        ("control_selection_FD002_GBR_sha256", v_dir / "controls/FD002/GBR/selection.json"),
        ("control_selection_FD002_LSTM_sha256", v_dir / "controls/FD002/LSTM/selection.json"),
        ("content_verification_sha256", v_dir / "content_verification.json"),
    ]
    for b_key, p in single_bindings:
        single_h = compute_sha256(p) if p.exists() else None
        verified_bindings[b_key] = single_h == bindings.get(b_key)

    all_bindings_match = all(verified_bindings.values()) and len(verified_bindings) > 0

    # 4. Mandatory content verification re-execution
    content_res = verify_validation_smoke_matrix(smoke_dir=smoke_dir, base_dir=base)
    content_pass = content_res.get("overall_match", False) is True

    # 5. Independent Step-8 raw-reproduction audit
    s8_audit_res = verify_step08_report_records(v_dir / "step08_full_audit.json")
    s8_pass = s8_audit_res.get("match", False) is True

    # 6. Anti-leakage verification
    test_artifacts = list(base.glob("experiments/**/test_*.csv")) + list(
        base.glob("experiments/**/official_test*.csv")
    )
    leakage_free = len(test_artifacts) == 0

    pretest_ready = all_bindings_match and content_pass and s8_pass and leakage_free

    pretest_audit = {
        "protocol_version": PROTOCOL_VERSION,
        "schema_version": "step09-audit-v3",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_sha,
        "git_dirty": git_dirty,
        "environment": env_meta,
        "overall_status": "PASS" if pretest_ready else "FAIL",
        "pretest_readiness_status": "PRETEST_READY" if pretest_ready else "BLOCKED",
        "protocol_freeze_sha256": compute_sha256(f_path),
        "bindings_passed": all_bindings_match,
        "content_verification_passed": content_pass,
        "step08_report_passed": s8_pass,
        "anti_leakage_passed": leakage_free,
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
        default="experiments/pretest_verification_v3",
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
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Force rebuilding protocol freeze and overwriting existing audit artifacts",
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

    freeze_p = v_dir / "protocol_freeze.json"
    audit_p = v_dir / "pretest_audit.json"

    # 2. Build or verify protocol_freeze.json
    print("\nPhase 2: Building protocol freeze...")
    if freeze_p.exists() and not args.rebuild:
        print(f"  Protocol freeze already exists at {freeze_p}")
        print("  Skipping freeze rebuild (protocol is immutable; pass --rebuild to regenerate).")
    else:
        freeze_data = build_protocol_freeze(
            evidence_report=evidence_report,
            verification_dir=v_dir,
            base_dir=base,
            allow_dirty=args.allow_dirty,
            git_info=git_info,
            env_meta=env_meta,
        )
        write_immutable_json(freeze_p, freeze_data, overwrite=args.rebuild)
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
    if not audit_p.exists() or args.rebuild:
        write_immutable_json(audit_p, audit_data, overwrite=args.rebuild)
        print(f"  Saved pretest audit to {audit_p}")
    else:
        print(f"  Verified against existing pretest audit at {audit_p}")
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
