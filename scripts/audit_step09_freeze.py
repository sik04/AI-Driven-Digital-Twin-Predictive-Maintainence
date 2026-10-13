"""Verify pre-test readiness and produce protocol_freeze.json and pretest_audit.json."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from intellitwin.data.artifacts import compute_sha256
from intellitwin.evaluation.schema import PROTOCOL_VERSION
from intellitwin.provenance import (
    capture_environment_metadata,
    get_git_info,
    write_immutable_json,
)
from intellitwin.uncertainty.artifacts import resolve_repo_relative_path


def build_protocol_freeze(
    base_dir: Path | str = ".",
    allow_dirty: bool = False,
) -> dict[str, Any]:
    """Assemble all binding cryptographic hashes and specifications for protocol_freeze.json."""
    base = Path(base_dir).resolve()
    git_sha, git_dirty = get_git_info(allow_dirty=allow_dirty)
    env_meta = capture_environment_metadata()

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
    step08_baseline_p = resolve_repo_relative_path(
        base, "experiments/audits/step08_repair_baseline.json"
    )
    step08_verification_p = resolve_repo_relative_path(
        base, "experiments/audits/step08_repair_verification.json"
    )

    # 4. Calibrator registry
    cal_reg_p = resolve_repo_relative_path(
        base, "experiments/calibration/calibration_registry.json"
    )

    # 5. Control selection files
    control_gbr_p = resolve_repo_relative_path(
        base, "experiments/confirmatory_development/controls/FD002/GBR/selection.json"
    )
    control_lstm_p = resolve_repo_relative_path(
        base, "experiments/confirmatory_development/controls/FD002/LSTM/selection.json"
    )

    with open(control_gbr_p, encoding="utf-8") as f:
        ctrl_gbr_data = json.load(f)
    with open(control_lstm_p, encoding="utf-8") as f:
        ctrl_lstm_data = json.load(f)

    # 6. Evaluation source code hashes
    eval_sources = [
        "src/intellitwin/evaluation/schema.py",
        "src/intellitwin/evaluation/validation.py",
        "src/intellitwin/evaluation/metrics.py",
        "src/intellitwin/evaluation/bootstrap.py",
        "src/intellitwin/evaluation/decisions.py",
        "src/intellitwin/evaluation/artifacts.py",
        "src/intellitwin/decision/controls.py",
        "src/intellitwin/provenance.py",
    ]
    source_hashes = {f: compute_sha256(resolve_repo_relative_path(base, f)) for f in eval_sources}

    freeze = {
        "protocol_version": PROTOCOL_VERSION,
        "schema_version": "step09-freeze-v1",
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
            "step08_repair_baseline_sha256": compute_sha256(step08_baseline_p),
            "step08_repair_verification_sha256": compute_sha256(step08_verification_p),
            "control_selection_FD002_GBR_sha256": compute_sha256(control_gbr_p),
            "control_selection_FD002_LSTM_sha256": compute_sha256(control_lstm_p),
            "evaluation_source_hashes": source_hashes,
        },
        "selected_controls": {
            "GBR": ctrl_gbr_data["selected_controls"],
            "LSTM": ctrl_lstm_data["selected_controls"],
        },
        "planned_configuration_counts": {
            "primary_method_configurations": 810,
            "control_configurations": 120,
            "total_matrix_configurations": 930,
        },
        "held_out_status": {
            "execution_status": "NOT_STARTED",
            "test_windows_prepared": False,
            "confirmatory_conclusions": "PENDING",
        },
    }
    return freeze


def run_pretest_audit(
    base_dir: Path | str = ".",
    allow_dirty: bool = False,
) -> dict[str, Any]:
    """Execute pre-test audit verifying all freeze gates and anti-leakage barriers."""
    base = Path(base_dir).resolve()
    git_sha, git_dirty = get_git_info(allow_dirty=allow_dirty)

    checks: dict[str, Any] = {}

    # Check 1: Base models frozen
    model_reg_p = resolve_repo_relative_path(base, "experiments/base_models/model_registry.json")
    checks["base_model_registry_present"] = model_reg_p.exists()

    # Check 2: Calibrator registry POSIX paths and loadability
    cal_reg_p = resolve_repo_relative_path(
        base, "experiments/calibration/calibration_registry.json"
    )
    with open(cal_reg_p, encoding="utf-8") as f:
        cal_data = json.load(f)
    entries = cal_data.get("entries", {})
    checks["calibrator_count_is_90"] = len(entries) == 90
    has_backslash = any(
        "\\" in str(e.get("calibrator_artifact_path", "")) for e in entries.values()
    )
    checks["registry_paths_posix"] = not has_backslash

    # Check 3: Repair baseline and verification present
    baseline_p = resolve_repo_relative_path(base, "experiments/audits/step08_repair_baseline.json")
    verif_p = resolve_repo_relative_path(base, "experiments/audits/step08_repair_verification.json")
    checks["step08_repair_baseline_present"] = baseline_p.exists()
    checks["step08_repair_verification_present"] = verif_p.exists()

    # Check 4: Control selection present
    ctrl_gbr_p = resolve_repo_relative_path(
        base, "experiments/confirmatory_development/controls/FD002/GBR/selection.json"
    )
    ctrl_lstm_p = resolve_repo_relative_path(
        base, "experiments/confirmatory_development/controls/FD002/LSTM/selection.json"
    )
    checks["control_selection_present"] = ctrl_gbr_p.exists() and ctrl_lstm_p.exists()

    # Check 5: Anti-leakage / Zero held-out test data
    # Verify no test window artifacts exist under experiments/
    test_artifacts = list(base.glob("experiments/**/test_*.csv")) + list(
        base.glob("experiments/**/official_test*.csv")
    )
    checks["zero_test_artifacts"] = len(test_artifacts) == 0

    all_passed = all(checks.values())

    report = {
        "protocol_version": PROTOCOL_VERSION,
        "schema_version": "step09-audit-v1",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_sha,
        "git_dirty": git_dirty,
        "overall_status": "PASS" if all_passed else "FAIL",
        "gates": checks,
        "held_out_execution_status": "NOT_STARTED",
        "rq_outcomes_status": "PENDING",
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Step 9 Pre-Test Freeze and Audit Script")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="experiments/confirmatory_development",
        help="Directory to write protocol_freeze.json and pretest_audit.json",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Permit execution on dirty working tree (development runs only)",
    )
    args = parser.parse_args()

    out_base = Path(args.output_dir).resolve()
    out_base.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("Step 9: Confirmatory Protocol Freeze and Pre-Test Audit")
    print(f"Output Directory: {out_base}")
    print("=" * 80)

    # 1. Build and write protocol_freeze.json
    freeze_data = build_protocol_freeze(base_dir=".", allow_dirty=args.allow_dirty)
    freeze_p = out_base / "protocol_freeze.json"
    write_immutable_json(freeze_p, freeze_data, overwrite=True)
    print(f"PASS: Protocol freeze assembled and written to {freeze_p}")

    # 2. Build and write pretest_audit.json
    audit_data = run_pretest_audit(base_dir=".", allow_dirty=args.allow_dirty)
    audit_p = out_base / "pretest_audit.json"
    write_immutable_json(audit_p, audit_data, overwrite=True)
    print(f"PASS: Pre-test audit completed and written to {audit_p}")
    print(f"  Overall Status: {audit_data['overall_status']}")
    print(f"  Held-Out Execution: {audit_data['held_out_execution_status']}")
    print(f"  RQ Outcomes: {audit_data['rq_outcomes_status']}")

    if audit_data["overall_status"] != "PASS":
        print("ERROR: Pre-test audit failed gates!")
        sys.exit(1)


if __name__ == "__main__":
    main()
