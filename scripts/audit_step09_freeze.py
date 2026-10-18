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
from intellitwin.evaluation.regression_audit import execute_regression_audit
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
    "src/intellitwin/evaluation/reference_verification.py",
    "src/intellitwin/evaluation/verification.py",
    "src/intellitwin/evaluation/regression_audit.py",
    "scripts/run_step09_validation_smoke.py",
    "scripts/audit_step09_freeze.py",
    "tests/test_pretest_reference_verification.py",
)

REQUIRED_PARTNER_CHECKPOINT_FILES: tuple[str, ...] = (
    "environment_verification.json",
    "step08_full_audit.json",
    "input_manifest.json",
    "execution.log",
    "pip_freeze.txt",
    "pip_check.txt",
)


def validate_portable_artifact_path(path_str: str, context: str = "") -> str:
    """Validate and normalize an artifact reference path.

    Rules:
    - Must be a non-empty string using POSIX forward slashes.
    - Rejects absolute paths (starting with /).
    - Rejects Windows drive prefixes (e.g. C:, D:).
    - Rejects traversal outside the repository ('..').
    """
    if not isinstance(path_str, str):
        raise TypeError(
            f"Artifact path must be a string, got {type(path_str)}: {path_str!r} in {context}"
        )
    if not path_str.strip():
        raise ValueError(f"Artifact path cannot be empty in {context}")
    if "\\" in path_str:
        raise ValueError(
            f"Artifact reference path must use POSIX slashes, "
            f"got backslash in '{path_str}' ({context})"
        )
    if len(path_str) >= 2 and path_str[1] == ":" and path_str[0].isalpha():
        raise ValueError(
            f"Drive-prefixed paths are not permitted in artifact references: "
            f"'{path_str}' ({context})"
        )
    if path_str.startswith("/"):
        raise ValueError(
            f"Absolute paths are not permitted in artifact references: '{path_str}' ({context})"
        )
    parts = path_str.split("/")
    if ".." in parts:
        raise ValueError(
            f"Traversal outside repository ('..') is not permitted in artifact references: "
            f"'{path_str}' ({context})"
        )
    return path_str


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


def verify_partner_checkpoint_evidence(
    checkpoint_dir: Path | str = "experiments/checkpoint_verification_v1",
    base_dir: Path | str = ".",
) -> dict[str, Any]:
    """Verify partner checkpoint reproduction evidence in experiments/checkpoint_verification_v1.

    Requires:
    - All 6 required files present
    - environment_verification PASS, clean source execution, compatible environment
    - execution.log free from sklearn InconsistentVersionWarning
    - step08_full_audit.json contains exactly 60 reproduction records, all PASS,
      finite error <= 1e-4
    - input_manifest.json matches frozen input hashes
    """
    base = Path(base_dir).resolve()
    cp_dir = Path(checkpoint_dir)
    if not cp_dir.is_absolute():
        cp_dir = (base / cp_dir).resolve()

    if not cp_dir.exists():
        return {
            "status": "BLOCKED",
            "reason": f"Partner checkpoint verification directory missing: {checkpoint_dir}",
            "directory_exists": False,
            "missing_files": list(REQUIRED_PARTNER_CHECKPOINT_FILES),
            "match": False,
        }

    missing_files = [f for f in REQUIRED_PARTNER_CHECKPOINT_FILES if not (cp_dir / f).exists()]
    if missing_files:
        return {
            "status": "BLOCKED",
            "reason": f"Partner checkpoint evidence missing required files: {missing_files}",
            "directory_exists": True,
            "missing_files": missing_files,
            "match": False,
        }

    checks: dict[str, Any] = {}
    failing_reasons: list[str] = []

    # 1. Environment Verification
    env_p = cp_dir / "environment_verification.json"
    with open(env_p, encoding="utf-8") as f:
        env_data = json.load(f)
    env_pass = env_data.get("status") == "PASS" or env_data.get("overall_status") == "PASS"
    clean_exec = env_data.get("clean_source_execution", not env_data.get("git_dirty", True))
    checks["environment_verification"] = {
        "status": "PASS" if env_pass else "FAIL",
        "clean_source_execution": clean_exec,
        "env_pass": env_pass,
    }
    if not env_pass:
        failing_reasons.append("Partner environment verification did not report PASS")
    if not clean_exec:
        failing_reasons.append(
            "Partner evidence was not executed from clean source (git_dirty=True)"
        )

    # 2. Execution Log for InconsistentVersionWarning
    log_p = cp_dir / "execution.log"
    with open(log_p, encoding="utf-8", errors="replace") as f:
        log_text = f.read()
    has_warning = "InconsistentVersionWarning" in log_text
    checks["no_inconsistent_version_warning"] = not has_warning
    if has_warning:
        failing_reasons.append("sklearn InconsistentVersionWarning detected in execution.log")

    # 3. Step 8 Full Audit (60 records, max diff <= 1e-4)
    s8_p = cp_dir / "step08_full_audit.json"
    s8_res = verify_step08_report_records(s8_p)
    checks["step08_reproduction_records"] = s8_res
    if not s8_res.get("match", False):
        failing_reasons.append(
            f"Partner Step-8 reproduction audit failed: count={s8_res.get('record_count')}, "
            f"max_err={s8_res.get('max_absolute_error')}"
        )

    # 4. Input Manifest Unchanged Frozen Inputs
    input_p = cp_dir / "input_manifest.json"
    with open(input_p, encoding="utf-8") as f:
        in_manifest = json.load(f)

    manifest_match = True
    manifest_mismatches: list[str] = []
    splits_declared = in_manifest.get("protected_inputs", {}).get("splits_and_quartiles", {})
    for split_file, declared_h in splits_declared.items():
        curr_p = resolve_repo_relative_path(base, split_file)
        if not curr_p.exists() or compute_sha256(curr_p) != declared_h:
            manifest_match = False
            manifest_mismatches.append(split_file)

    checks["frozen_inputs_match"] = {
        "match": manifest_match,
        "mismatches": manifest_mismatches,
    }
    if not manifest_match:
        failing_reasons.append(
            f"Partner input manifest has mismatched frozen inputs: {manifest_mismatches}"
        )

    all_ok = (
        len(failing_reasons) == 0
        and env_pass
        and clean_exec
        and not has_warning
        and s8_res.get("match", False)
        and manifest_match
    )

    file_hashes = {f: compute_sha256(cp_dir / f) for f in REQUIRED_PARTNER_CHECKPOINT_FILES}

    return {
        "status": "PASS" if all_ok else "FAIL",
        "match": all_ok,
        "checks": checks,
        "failing_reasons": failing_reasons,
        "file_hashes": file_hashes,
    }


def audit_pretest_evidence(
    source_evidence_dir: Path | str = "experiments/pretest_verification_v3",
    output_dir: Path | str | None = None,
    logical_output_dir: str = "experiments/pretest_verification_v5",
    checkpoint_evidence_dir: Path | str = "experiments/checkpoint_verification_v1",
    base_dir: Path | str = ".",
    allow_dirty: bool = False,
    git_info: tuple[str, bool] | None = None,
    env_meta: dict[str, Any] | None = None,
    overwrite: bool = False,
    verify_only: bool = False,
) -> dict[str, Any]:
    """Perform authoritative content-level verification of all pre-test readiness evidence."""
    base = Path(base_dir).resolve()
    s_dir = Path(source_evidence_dir)
    if not s_dir.is_absolute():
        s_dir = (base / s_dir).resolve()

    validate_portable_artifact_path(logical_output_dir, "audit_pretest_evidence.logical_output_dir")

    if git_info is not None:
        git_sha, git_dirty = git_info
    else:
        git_sha, git_dirty = get_git_info(allow_dirty=allow_dirty, repo_root=base)
    if env_meta is None:
        env_meta = capture_environment_metadata(device="cpu")

    checks: dict[str, Any] = {}
    missing_items: list[str] = []

    # 1. Step 8 Historical Audit Verification (from source_evidence_dir)
    s8_audit_p = s_dir / "step08_full_audit.json"
    if not s8_audit_p.exists():
        missing_items.append("step08_full_audit.json")
        checks["step08_full_audit"] = {"status": "MISSING"}
    else:
        checks["step08_full_audit"] = verify_step08_report_records(s8_audit_p)

    # 2. Control Reconstruction Verification
    ctrl_recon_p = s_dir / "control_reconstruction.json"
    ctrl_gbr_p = s_dir / "controls" / "FD002" / "GBR" / "selection.json"
    ctrl_lstm_p = s_dir / "controls" / "FD002" / "LSTM" / "selection.json"
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
    smoke_dir = s_dir / "validation_smoke"
    smoke_manifest_p = smoke_dir / "execution_manifest.json"
    if not smoke_manifest_p.exists():
        missing_items.append("validation_smoke/execution_manifest.json")
        checks["validation_smoke_verification"] = {"status": "MISSING"}
    else:
        smoke_res = verify_validation_smoke_matrix(smoke_dir=smoke_dir, base_dir=base)
        checks["validation_smoke_verification"] = smoke_res

        # Save content_verification.json report if output_dir specified and not verify_only
        if output_dir is not None and not verify_only:
            out_p = Path(output_dir)
            if not out_p.is_absolute():
                out_p = (base / out_p).resolve()
            content_rep_p = out_p / "content_verification.json"
            if not content_rep_p.exists() or overwrite:
                source_rel = (
                    s_dir.relative_to(base).as_posix() if s_dir.is_relative_to(base) else str(s_dir)
                )
                source_rel = validate_portable_artifact_path(
                    source_rel, "content_verification.source_evidence_dir"
                )
                write_immutable_json(
                    content_rep_p,
                    {
                        "protocol_version": PROTOCOL_VERSION,
                        "schema_version": "step09-content-verification-v5",
                        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                        "git_commit": git_sha,
                        "git_dirty": git_dirty,
                        "source_evidence_dir": source_rel,
                        "logical_bundle_path": logical_output_dir,
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

    # 6. Partner Checkpoint Verification
    cp_res = verify_partner_checkpoint_evidence(checkpoint_evidence_dir, base_dir=base)
    checks["partner_checkpoint_verification"] = cp_res
    if cp_res["status"] == "BLOCKED":
        missing_items.append(
            "partner checkpoint verification (experiments/checkpoint_verification_v1)"
        )

    if missing_items:
        overall_status = "BLOCKED"
    elif any(
        c.get("status") == "FAIL" or (isinstance(c, dict) and c.get("overall_match") is False)
        for c in checks.values()
    ):
        overall_status = "FAIL"
    else:
        overall_status = "PASS"

    return {
        "protocol_version": PROTOCOL_VERSION,
        "schema_version": "step09-evidence-audit-v5",
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
    source_evidence_dir: Path | str = "experiments/pretest_verification_v3",
    output_dir: Path | str = "experiments/pretest_verification_v5",
    logical_output_dir: str = "experiments/pretest_verification_v5",
    checkpoint_evidence_dir: Path | str = "experiments/checkpoint_verification_v1",
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
    s_dir = Path(source_evidence_dir)
    if not s_dir.is_absolute():
        s_dir = (base / s_dir).resolve()

    out_p = Path(output_dir)
    if not out_p.is_absolute():
        out_p = (base / out_p).resolve()

    validate_portable_artifact_path(logical_output_dir, "build_protocol_freeze.logical_output_dir")

    if git_info is not None:
        git_sha, git_dirty = git_info
    else:
        git_sha, git_dirty = get_git_info(allow_dirty=allow_dirty, repo_root=base)
    if env_meta is None:
        env_meta = capture_environment_metadata(device="cpu")

    # 1. Scientific Protocols & Configurations
    protocol_hashes = {
        validate_portable_artifact_path(f, "protocols"): compute_sha256(
            resolve_repo_relative_path(base, f)
        )
        for f in FROZEN_SCIENTIFIC_PROTOCOLS
    }

    # 2. Split Manifests and Quartiles
    split_hashes = {
        validate_portable_artifact_path(f, "splits"): compute_sha256(
            resolve_repo_relative_path(base, f)
        )
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

    with open(model_reg_p, encoding="utf-8") as f:
        m_reg = json.load(f)
    checkpoint_hashes = {}
    if isinstance(m_reg, list):
        for entry in m_reg:
            p_rel = entry.get("checkpoint_path", "")
            if p_rel:
                validate_portable_artifact_path(p_rel, "checkpoint_path")
                checkpoint_hashes[p_rel] = compute_sha256(resolve_repo_relative_path(base, p_rel))
    elif isinstance(m_reg, dict):
        for entry in m_reg.get("checkpoints", {}).values():
            p_rel = entry.get("checkpoint_path", "")
            if p_rel:
                validate_portable_artifact_path(p_rel, "checkpoint_path")
                checkpoint_hashes[p_rel] = compute_sha256(resolve_repo_relative_path(base, p_rel))

    with open(cal_reg_p, encoding="utf-8") as f:
        c_reg = json.load(f)
    calibrator_hashes = {}
    for entry in c_reg.get("entries", {}).values():
        c_rel = entry.get("calibrator_artifact_path", "")
        if c_rel:
            validate_portable_artifact_path(c_rel, "calibrator_artifact_path")
            calibrator_hashes[c_rel] = compute_sha256(resolve_repo_relative_path(base, c_rel))

    preprocessor_hashes = {}
    for ds in CONFIRMATORY_DATASETS:
        p_rel = f"experiments/preprocessing/{ds}/preprocessor.json"
        p_full = resolve_repo_relative_path(base, p_rel)
        if p_full.exists():
            validate_portable_artifact_path(p_rel, "preprocessor_path")
            preprocessor_hashes[p_rel] = compute_sha256(p_full)

    # 4. Selected Controls from source_evidence_dir
    ctrl_recon_p = s_dir / "control_reconstruction.json"
    control_gbr_p = s_dir / "controls" / "FD002" / "GBR" / "selection.json"
    control_lstm_p = s_dir / "controls" / "FD002" / "LSTM" / "selection.json"
    with open(control_gbr_p, encoding="utf-8") as f:
        ctrl_gbr_data = json.load(f)
    with open(control_lstm_p, encoding="utf-8") as f:
        ctrl_lstm_data = json.load(f)

    # 5. Smoke Evidence Files from source_evidence_dir
    smoke_dir = s_dir / "validation_smoke"
    smoke_hashes = {
        validate_portable_artifact_path(f, "smoke_files"): compute_sha256(smoke_dir / f)
        for f in REQUIRED_SMOKE_FILES
        if (smoke_dir / f).exists()
    }

    # 6. Core Source Files (including new regression runner and corrected tests)
    source_hashes = {
        validate_portable_artifact_path(f, "core_source"): compute_sha256(
            resolve_repo_relative_path(base, f)
        )
        for f in CORE_SOURCE_FILES
    }

    # 7. Content Verification Report from output_dir
    content_rep_p = out_p / "content_verification.json"
    content_rep_hash = compute_sha256(content_rep_p) if content_rep_p.exists() else None

    # 8. Executed Regression Test Report from output_dir
    regression_rep_p = out_p / "regression_test_report.json"
    regression_rep_hash = compute_sha256(regression_rep_p) if regression_rep_p.exists() else None

    # 9. Partner Checkpoint Verification Evidence
    partner_cp = evidence_report.get("checks", {}).get("partner_checkpoint_verification", {})
    partner_hashes = partner_cp.get("file_hashes", {})

    # Load confirmatory config payload
    config_p = resolve_repo_relative_path(
        base, "research/research_design/step09_confirmatory_config.json"
    )
    with open(config_p, encoding="utf-8") as f:
        conf_cfg = json.load(f)

    source_rel = s_dir.relative_to(base).as_posix() if s_dir.is_relative_to(base) else str(s_dir)
    source_rel = validate_portable_artifact_path(source_rel, "source_evidence_dir")

    freeze = {
        "protocol_version": PROTOCOL_VERSION,
        "schema_version": "step09-freeze-v5",
        "status": "PRETEST_FROZEN",
        "source_execution_commit": git_sha,
        "git_dirty": git_dirty,
        "freeze_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "environment": env_meta,
        "source_evidence_dir": source_rel,
        "logical_bundle_path": logical_output_dir,
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
            "step08_full_audit_sha256": compute_sha256(s_dir / "step08_full_audit.json"),
            "control_reconstruction_sha256": compute_sha256(ctrl_recon_p),
            "control_selection_FD002_GBR_sha256": compute_sha256(control_gbr_p),
            "control_selection_FD002_LSTM_sha256": compute_sha256(control_lstm_p),
            "content_verification_sha256": content_rep_hash,
            "regression_test_report_sha256": regression_rep_hash,
            "smoke_evidence_files": smoke_hashes,
            "transitive_checkpoints": checkpoint_hashes,
            "transitive_preprocessors": preprocessor_hashes,
            "transitive_calibrators": calibrator_hashes,
            "source_hashes": source_hashes,
            "partner_checkpoint_verification_hashes": partner_hashes,
        },
        "selected_controls": {
            "GBR": ctrl_gbr_data.get("selected_controls", ctrl_gbr_data),
            "LSTM": ctrl_lstm_data.get("selected_controls", ctrl_lstm_data),
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


def build_input_manifest(
    source_evidence_dir: Path | str = "experiments/pretest_verification_v3",
    logical_output_dir: str = "experiments/pretest_verification_v5",
    base_dir: Path | str = ".",
    git_sha: str = "",
) -> dict[str, Any]:
    """Generate input_manifest.json pointing to frozen inputs and source evidence."""
    base = Path(base_dir).resolve()
    s_dir = Path(source_evidence_dir)
    if not s_dir.is_absolute():
        s_dir = (base / s_dir).resolve()

    source_rel = s_dir.relative_to(base).as_posix() if s_dir.is_relative_to(base) else str(s_dir)
    source_rel = validate_portable_artifact_path(source_rel, "input_manifest.source_evidence_dir")
    validate_portable_artifact_path(logical_output_dir, "input_manifest.logical_output_dir")

    splits_quartiles = {
        validate_portable_artifact_path(f, "splits"): compute_sha256(
            resolve_repo_relative_path(base, f)
        )
        for f in FROZEN_SPLIT_AND_QUARTILE_FILES
    }

    preproc_hashes = {}
    for ds in CONFIRMATORY_DATASETS:
        p_rel = f"experiments/preprocessing/{ds}/preprocessor.json"
        p_full = resolve_repo_relative_path(base, p_rel)
        if p_full.exists():
            validate_portable_artifact_path(p_rel, "preproc")
            preproc_hashes[p_rel] = compute_sha256(p_full)

    model_reg_p = resolve_repo_relative_path(base, "experiments/base_models/model_registry.json")
    with open(model_reg_p, encoding="utf-8") as f:
        m_reg = json.load(f)
    ckpt_hashes = {}
    if isinstance(m_reg, list):
        for entry in m_reg:
            p_rel = entry.get("checkpoint_path", "")
            if p_rel:
                validate_portable_artifact_path(p_rel, "ckpt")
                ckpt_hashes[p_rel] = compute_sha256(resolve_repo_relative_path(base, p_rel))
    elif isinstance(m_reg, dict):
        for entry in m_reg.get("checkpoints", {}).values():
            p_rel = entry.get("checkpoint_path", "")
            if p_rel:
                validate_portable_artifact_path(p_rel, "ckpt")
                ckpt_hashes[p_rel] = compute_sha256(resolve_repo_relative_path(base, p_rel))

    cal_reg_p = resolve_repo_relative_path(
        base, "experiments/calibration/calibration_registry.json"
    )
    with open(cal_reg_p, encoding="utf-8") as f:
        c_reg = json.load(f)
    cal_hashes = {}
    for entry in c_reg.get("entries", {}).values():
        c_rel = entry.get("calibrator_artifact_path", "")
        if c_rel:
            validate_portable_artifact_path(c_rel, "calibrator")
            cal_hashes[c_rel] = compute_sha256(resolve_repo_relative_path(base, c_rel))

    # Source evidence files in v3
    smoke_dir = s_dir / "validation_smoke"
    smoke_hashes = {
        validate_portable_artifact_path(
            f"{source_rel}/validation_smoke/{f}", "smoke"
        ): compute_sha256(smoke_dir / f)
        for f in REQUIRED_SMOKE_FILES
        if (smoke_dir / f).exists()
    }
    controls_hashes = {
        validate_portable_artifact_path(
            f"{source_rel}/controls/FD002/GBR/selection.json", "ctrl_gbr"
        ): compute_sha256(s_dir / "controls/FD002/GBR/selection.json"),
        validate_portable_artifact_path(
            f"{source_rel}/controls/FD002/LSTM/selection.json", "ctrl_lstm"
        ): compute_sha256(s_dir / "controls/FD002/LSTM/selection.json"),
    }

    manifest = {
        "schema_version": "step09-input-manifest-v3",
        "starting_commit": git_sha,
        "source_evidence_dir": source_rel,
        "logical_bundle_path": logical_output_dir,
        "protected_inputs": {
            "splits_and_quartiles": splits_quartiles,
            "preprocessing_artifacts": preproc_hashes,
            "base_model_registry": {
                "path": "experiments/base_models/model_registry.json",
                "sha256": compute_sha256(model_reg_p),
            },
            "base_model_checkpoints": ckpt_hashes,
            "calibration_registry": {
                "path": "experiments/calibration/calibration_registry.json",
                "sha256": compute_sha256(cal_reg_p),
            },
            "calibrator_bundles": cal_hashes,
            "source_evidence": {
                "step08_full_audit": {
                    "path": f"{source_rel}/step08_full_audit.json",
                    "sha256": compute_sha256(s_dir / "step08_full_audit.json"),
                },
                "control_reconstruction": {
                    "path": f"{source_rel}/control_reconstruction.json",
                    "sha256": compute_sha256(s_dir / "control_reconstruction.json"),
                },
                "control_selections": controls_hashes,
                "smoke_evidence_files": smoke_hashes,
            },
        },
    }
    return manifest


def build_reused_evidence(
    source_evidence_dir: Path | str = "experiments/pretest_verification_v3",
    logical_output_dir: str = "experiments/pretest_verification_v5",
    base_dir: Path | str = ".",
) -> dict[str, Any]:
    """Generate reused_evidence.json specifying reused numerical evidence from v3."""
    base = Path(base_dir).resolve()
    s_dir = Path(source_evidence_dir)
    if not s_dir.is_absolute():
        s_dir = (base / s_dir).resolve()

    source_rel = s_dir.relative_to(base).as_posix() if s_dir.is_relative_to(base) else str(s_dir)
    source_rel = validate_portable_artifact_path(source_rel, "reused.source_evidence_dir")
    validate_portable_artifact_path(logical_output_dir, "reused.logical_output_dir")

    smoke_dir = s_dir / "validation_smoke"
    smoke_hashes = {
        f: {
            "source_path": validate_portable_artifact_path(
                f"{source_rel}/validation_smoke/{f}", "reused_smoke"
            ),
            "sha256": compute_sha256(smoke_dir / f),
        }
        for f in REQUIRED_SMOKE_FILES
        if (smoke_dir / f).exists()
    }

    reused = {
        "schema_version": "step09-reused-evidence-v3",
        "description": (
            "Explicit references to preserved numerical evidence in Step 9 v3, "
            "verified by repaired independent reference verifier"
        ),
        "source_evidence_dir": source_rel,
        "logical_bundle_path": logical_output_dir,
        "preserved_historical_bundles": [
            "experiments/pretest_verification_v2",
            "experiments/pretest_verification_v3",
            "experiments/pretest_verification_v4",
        ],
        "step08_full_audit": {
            "source_path": f"{source_rel}/step08_full_audit.json",
            "sha256": compute_sha256(s_dir / "step08_full_audit.json"),
            "verification_rules": {
                "unique_records_count": 60,
                "partitions_permitted": ["validation", "calibration"],
                "max_abs_error_allowed": 0.0001,
                "all_records_pass": True,
            },
        },
        "step08_selection_freeze": {
            "source_path": "experiments/calibration/selection/selection_freeze.json",
            "sha256": compute_sha256(
                resolve_repo_relative_path(
                    base, "experiments/calibration/selection/selection_freeze.json"
                )
            ),
        },
        "control_selections": {
            "control_reconstruction": {
                "source_path": f"{source_rel}/control_reconstruction.json",
                "sha256": compute_sha256(s_dir / "control_reconstruction.json"),
            },
            "FD002_GBR": {
                "selection_json": {
                    "source_path": f"{source_rel}/controls/FD002/GBR/selection.json",
                    "sha256": compute_sha256(s_dir / "controls/FD002/GBR/selection.json"),
                },
                "candidate_metrics_csv": {
                    "source_path": f"{source_rel}/controls/FD002/GBR/candidate_metrics.csv",
                    "sha256": compute_sha256(s_dir / "controls/FD002/GBR/candidate_metrics.csv"),
                },
                "engine_seed_outcomes_csv": {
                    "source_path": f"{source_rel}/controls/FD002/GBR/engine_seed_outcomes.csv",
                    "sha256": compute_sha256(s_dir / "controls/FD002/GBR/engine_seed_outcomes.csv"),
                },
            },
            "FD002_LSTM": {
                "selection_json": {
                    "source_path": f"{source_rel}/controls/FD002/LSTM/selection.json",
                    "sha256": compute_sha256(s_dir / "controls/FD002/LSTM/selection.json"),
                },
                "candidate_metrics_csv": {
                    "source_path": f"{source_rel}/controls/FD002/LSTM/candidate_metrics.csv",
                    "sha256": compute_sha256(s_dir / "controls/FD002/LSTM/candidate_metrics.csv"),
                },
                "engine_seed_outcomes_csv": {
                    "source_path": f"{source_rel}/controls/FD002/LSTM/engine_seed_outcomes.csv",
                    "sha256": compute_sha256(
                        s_dir / "controls/FD002/LSTM/engine_seed_outcomes.csv"
                    ),
                },
            },
        },
        "validation_smoke": smoke_hashes,
    }
    return reused


def build_supersession(
    logical_output_dir: str = "experiments/pretest_verification_v5",
    prior_bundle_dir: Path | str = "experiments/pretest_verification_v4",
    base_dir: Path | str = ".",
    git_sha: str = "",
    git_dirty: bool = False,
    env_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate supersession.json recording supersession of v4 audit artifacts by v5."""
    base = Path(base_dir).resolve()
    prior_dir = Path(prior_bundle_dir)
    if not prior_dir.is_absolute():
        prior_dir = (base / prior_dir).resolve()

    prior_rel = (
        prior_dir.relative_to(base).as_posix() if prior_dir.is_relative_to(base) else str(prior_dir)
    )
    prior_rel = validate_portable_artifact_path(prior_rel, "prior_bundle_dir")
    validate_portable_artifact_path(logical_output_dir, "logical_output_dir")

    # Load prior supersession records to preserve full history chain
    historical_chain: list[dict[str, Any]] = []
    prior_supersession_p = prior_dir / "supersession.json"
    if prior_supersession_p.exists():
        with open(prior_supersession_p, encoding="utf-8") as f:
            prior_s_data = json.load(f)
        historical_chain = prior_s_data.get("superseded_records", [])

    current_records = [
        {
            "historical_path": validate_portable_artifact_path(
                f"{prior_rel}/protocol_freeze.json", "supersession.historical_path"
            ),
            "historical_sha256": compute_sha256(prior_dir / "protocol_freeze.json")
            if (prior_dir / "protocol_freeze.json").exists()
            else None,
            "reason_superseded": (
                "v4 pre-test readiness verification contained mock regression test records, "
                "used non-portable external staging paths, and lacked fresh checkpoint "
                "verification. Superseded by v5 which binds actual executed regression evidence, "
                "corrected linear quantiles for Mutation 5, portable normalized "
                "repository-relative paths, and fresh environment-compatible checkpoint audit. "
                "Scientific protocols, models, calibrators, and control selections remain "
                "unchanged."
            ),
            "replacement_evidence_path": validate_portable_artifact_path(
                f"{logical_output_dir}/protocol_freeze.json", "supersession.replacement_path"
            ),
        },
        {
            "historical_path": validate_portable_artifact_path(
                f"{prior_rel}/pretest_audit.json", "supersession.historical_path"
            ),
            "historical_sha256": compute_sha256(prior_dir / "pretest_audit.json")
            if (prior_dir / "pretest_audit.json").exists()
            else None,
            "reason_superseded": (
                "Superseded by v5 audit incorporating executed regression audit verification and "
                "environment-compatible checkpoint audit reproduction."
            ),
            "replacement_evidence_path": validate_portable_artifact_path(
                f"{logical_output_dir}/pretest_audit.json", "supersession.replacement_path"
            ),
        },
        {
            "historical_path": validate_portable_artifact_path(
                f"{prior_rel}/content_verification.json", "supersession.historical_path"
            ),
            "historical_sha256": compute_sha256(prior_dir / "content_verification.json")
            if (prior_dir / "content_verification.json").exists()
            else None,
            "reason_superseded": (
                "Superseded by v5 authoritative independent reference reconstruction report with "
                "portable repository-relative provenance."
            ),
            "replacement_evidence_path": validate_portable_artifact_path(
                f"{logical_output_dir}/content_verification.json", "supersession.replacement_path"
            ),
        },
        {
            "historical_path": validate_portable_artifact_path(
                f"{prior_rel}/regression_test_report.json", "supersession.historical_path"
            ),
            "historical_sha256": compute_sha256(prior_dir / "regression_test_report.json")
            if (prior_dir / "regression_test_report.json").exists()
            else None,
            "reason_superseded": (
                "v4 regression report contained static mock records; superseded by v5 executed "
                "regression evidence verifying baseline pass and empirical rejection of all 5 "
                "isolated mutations."
            ),
            "replacement_evidence_path": validate_portable_artifact_path(
                f"{logical_output_dir}/regression_test_report.json", "supersession.replacement_path"
            ),
        },
        {
            "historical_path": validate_portable_artifact_path(
                f"{prior_rel}/input_manifest.json", "supersession.historical_path"
            ),
            "historical_sha256": compute_sha256(prior_dir / "input_manifest.json")
            if (prior_dir / "input_manifest.json").exists()
            else None,
            "reason_superseded": (
                "Superseded by v5 input manifest binding updated core verification sources."
            ),
            "replacement_evidence_path": validate_portable_artifact_path(
                f"{logical_output_dir}/input_manifest.json", "supersession.replacement_path"
            ),
        },
        {
            "historical_path": validate_portable_artifact_path(
                f"{prior_rel}/reused_evidence.json", "supersession.historical_path"
            ),
            "historical_sha256": compute_sha256(prior_dir / "reused_evidence.json")
            if (prior_dir / "reused_evidence.json").exists()
            else None,
            "reason_superseded": (
                "Superseded by v5 reused evidence catalog with portable normalized references."
            ),
            "replacement_evidence_path": validate_portable_artifact_path(
                f"{logical_output_dir}/reused_evidence.json", "supersession.replacement_path"
            ),
        },
        {
            "historical_path": validate_portable_artifact_path(
                f"{prior_rel}/supersession.json", "supersession.historical_path"
            ),
            "historical_sha256": compute_sha256(prior_dir / "supersession.json")
            if (prior_dir / "supersession.json").exists()
            else None,
            "reason_superseded": (
                "Superseded by v5 supersession chain preserving full multi-version history."
            ),
            "replacement_evidence_path": validate_portable_artifact_path(
                f"{logical_output_dir}/supersession.json", "supersession.replacement_path"
            ),
        },
    ]

    supersession = {
        "protocol_version": PROTOCOL_VERSION,
        "schema_version": "step09-supersession-v4",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source_execution_commit": git_sha,
        "git_dirty": git_dirty,
        "environment": env_meta,
        "logical_bundle_path": logical_output_dir,
        "superseded_count": len(current_records),
        "superseded_records": current_records,
        "prior_supersession_history": historical_chain,
    }
    return supersession


def verify_saved_freeze(
    freeze_path: Path | str,
    source_evidence_dir: Path | str | None = None,
    checkpoint_evidence_dir: Path | str = "experiments/checkpoint_verification_v1",
    base_dir: Path | str = ".",
    allow_dirty: bool = False,
    git_info: tuple[str, bool] | None = None,
    env_meta: dict[str, Any] | None = None,
    rerun_regression: bool = True,
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

    is_v5 = freeze_data.get("schema_version") == "step09-freeze-v5"
    bindings = freeze_data.get("bindings", {})
    verified_bindings: dict[str, bool] = {}

    # Determine source evidence directory
    if source_evidence_dir is not None:
        s_dir = Path(source_evidence_dir)
    else:
        s_rel = freeze_data.get("source_evidence_dir")
        if s_rel:
            s_dir = (base / s_rel).resolve()
        else:
            s_dir = v_dir

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

    # 2. Verify smoke evidence hashes from source_evidence_dir
    smoke_dir = s_dir / "validation_smoke"
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
        ("step08_full_audit_sha256", s_dir / "step08_full_audit.json"),
        ("control_reconstruction_sha256", s_dir / "control_reconstruction.json"),
        ("control_selection_FD002_GBR_sha256", s_dir / "controls/FD002/GBR/selection.json"),
        ("control_selection_FD002_LSTM_sha256", s_dir / "controls/FD002/LSTM/selection.json"),
        ("content_verification_sha256", v_dir / "content_verification.json"),
    ]
    if "regression_test_report_sha256" in bindings:
        single_bindings.append(
            ("regression_test_report_sha256", v_dir / "regression_test_report.json")
        )

    for b_key, p in single_bindings:
        single_h = compute_sha256(p) if p.exists() else None
        verified_bindings[b_key] = single_h == bindings.get(b_key)

    # 4. Mandatory content verification re-execution
    content_res = verify_validation_smoke_matrix(smoke_dir=smoke_dir, base_dir=base)
    content_pass = content_res.get("overall_match", False) is True

    # 5. Independent Step-8 raw-reproduction audit (historical)
    s8_audit_res = verify_step08_report_records(s_dir / "step08_full_audit.json")
    s8_pass = s8_audit_res.get("match", False) is True

    # 6. Executed Regression Report Verification
    regression_pass = True
    reg_rep_p = v_dir / "regression_test_report.json"
    if not reg_rep_p.exists():
        regression_pass = False
        verified_bindings["regression_report_exists"] = False
    else:
        with open(reg_rep_p, encoding="utf-8") as f:
            reg_data = json.load(f)

        mut_records = reg_data.get("records", reg_data.get("mutations", []))
        mut_ids = [m.get("mutation_id") for m in mut_records]
        has_5_unique = len(mut_ids) == 5 and len(set(mut_ids)) == 5
        all_rejected = all(m.get("rejection_confirmed") is True for m in mut_records)
        all_failed = all(
            m.get("verifier_status") == "FAIL" or m.get("repaired_status") == "FAIL"
            for m in mut_records
        )
        base_pass = reg_data.get("baseline_verification", {}).get("status") == "PASS" or not is_v5
        overall_reg_st = reg_data.get("overall_status", reg_data.get("status")) == "PASS"

        if not (has_5_unique and all_rejected and all_failed and base_pass and overall_reg_st):
            regression_pass = False

        # For v5 verify-only, rerun the mutation runner in temporary storage
        # and compare logical outcomes
        if is_v5 and rerun_regression and regression_pass:
            rerun_report = execute_regression_audit(
                source_smoke_dir=smoke_dir,
                base_dir=base,
                allow_dirty=allow_dirty,
                git_info=git_info,
                env_meta=env_meta,
            )
            # Compare logical outcomes
            rerun_records = rerun_report.get("records", [])
            rerun_pass = (
                rerun_report.get("overall_status") == "PASS"
                and rerun_report.get("baseline_verification", {}).get("status") == "PASS"
                and len(rerun_records) == 5
                and all(r.get("rejection_confirmed") is True for r in rerun_records)
                and {r["mutation_id"] for r in rerun_records} == set(mut_ids)
            )
            if not rerun_pass:
                regression_pass = False

    # 7. Partner Checkpoint Reproduction Evidence (v5 fresh audit)
    partner_pass = True
    if is_v5:
        partner_audit = verify_partner_checkpoint_evidence(checkpoint_evidence_dir, base_dir=base)
        partner_pass = partner_audit.get("match", False) is True
        verified_bindings["partner_checkpoint_verification"] = partner_pass
        if partner_pass and "partner_checkpoint_verification_hashes" in bindings:
            # Check bound partner hashes
            for pf, ph in bindings["partner_checkpoint_verification_hashes"].items():
                actual_ph = partner_audit.get("file_hashes", {}).get(pf)
                verified_bindings[f"partner:{pf}"] = actual_ph == ph

    # 8. Anti-leakage verification
    test_artifacts = list(base.glob("experiments/**/test_*.csv")) + list(
        base.glob("experiments/**/official_test*.csv")
    )
    leakage_free = len(test_artifacts) == 0

    all_bindings_match = all(verified_bindings.values()) and len(verified_bindings) > 0

    pretest_ready = (
        all_bindings_match
        and content_pass
        and s8_pass
        and regression_pass
        and (partner_pass if is_v5 else True)
        and leakage_free
    )

    pretest_audit = {
        "protocol_version": PROTOCOL_VERSION,
        "schema_version": "step09-audit-v5" if is_v5 else "step09-audit-v4",
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
        "regression_evidence_passed": regression_pass,
        "partner_checkpoint_passed": partner_pass if is_v5 else True,
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
        "--source-evidence-dir",
        type=str,
        default="experiments/pretest_verification_v3",
        help="Directory containing source validation evidence",
    )
    parser.add_argument(
        "--verification-dir",
        type=str,
        default="experiments/pretest_verification_v5",
        help="Directory containing pretest verification artifacts",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Optional destination physical output directory for generated artifacts",
    )
    parser.add_argument(
        "--logical-output-dir",
        type=str,
        default="experiments/pretest_verification_v5",
        help="Committed repository-relative logical bundle path for artifact references",
    )
    parser.add_argument(
        "--checkpoint-evidence-dir",
        type=str,
        default="experiments/checkpoint_verification_v1",
        help="Directory containing partner checkpoint reproduction evidence",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify existing bundle without writing or rebuilding any artifacts",
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

    base = Path(args.base_dir).resolve()
    s_dir = Path(args.source_evidence_dir)
    if not s_dir.is_absolute():
        s_dir = (base / s_dir).resolve()

    v_dir = Path(args.verification_dir)
    if not v_dir.is_absolute():
        v_dir = (base / v_dir).resolve()

    logical_out = validate_portable_artifact_path(
        args.logical_output_dir, "CLI --logical-output-dir"
    )
    out_dir = Path(args.output_dir).resolve() if args.output_dir else (base / logical_out).resolve()

    print("=" * 80)
    print("Step 9: Confirmatory Protocol Freeze and Pre-Test Readiness Audit")
    print(f"Source Evidence Directory: {s_dir}")
    print(f"Verification Directory:    {v_dir}")
    print(f"Output Directory (Physical): {out_dir}")
    print(f"Logical Output Directory:    {logical_out}")
    print(f"Verify Only:                 {args.verify_only}")
    print("=" * 80)

    # Capture provenance once at process entry
    git_sha, git_dirty = get_git_info(allow_dirty=args.allow_dirty, repo_root=base)
    env_meta = capture_environment_metadata(device="cpu")
    git_info = (git_sha, git_dirty)

    freeze_p = (
        v_dir / "protocol_freeze.json" if args.verify_only else out_dir / "protocol_freeze.json"
    )
    audit_p = v_dir / "pretest_audit.json" if args.verify_only else out_dir / "pretest_audit.json"

    if args.verify_only:
        print("\nMode: Verify-Only")
        if not freeze_p.exists():
            print(f"ERROR: protocol_freeze.json not found at {freeze_p}")
            sys.exit(1)

        required_bundle_files = [
            "protocol_freeze.json",
            "content_verification.json",
            "pretest_audit.json",
            "input_manifest.json",
            "reused_evidence.json",
            "supersession.json",
            "regression_test_report.json",
        ]
        missing = [f for f in required_bundle_files if not (v_dir / f).exists()]
        if missing:
            print(f"ERROR: Missing bundle files in {v_dir}: {missing}")
            sys.exit(1)

        audit_data = verify_saved_freeze(
            freeze_path=freeze_p,
            source_evidence_dir=s_dir,
            checkpoint_evidence_dir=args.checkpoint_evidence_dir,
            base_dir=base,
            allow_dirty=args.allow_dirty,
            git_info=git_info,
            env_meta=env_meta,
            rerun_regression=True,
        )

        print(f"  Overall Status:            {audit_data['overall_status']}")
        print(f"  Pre-Test Readiness:        {audit_data['pretest_readiness_status']}")
        print(f"  Held-Out Execution:        {audit_data['held_out_execution_status']}")
        print(f"  RQ Outcomes:               {audit_data['rq_outcomes_status']}")

        if audit_data["overall_status"] != "PASS":
            print("ERROR: Pre-test audit failed verification gates!")
            sys.exit(1)

        print("\n" + "=" * 80)
        print("PRE-TEST READINESS VERIFICATION COMPLETE (STATUS: PRETEST_READY)")
        print("=" * 80)
        return

    # Generation Mode
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Audit evidence
    print("\nPhase 1: Auditing pre-test evidence...")
    evidence_report = audit_pretest_evidence(
        source_evidence_dir=s_dir,
        output_dir=out_dir,
        logical_output_dir=logical_out,
        checkpoint_evidence_dir=args.checkpoint_evidence_dir,
        base_dir=base,
        allow_dirty=args.allow_dirty,
        git_info=git_info,
        env_meta=env_meta,
        overwrite=args.rebuild,
        verify_only=False,
    )
    print(f"  Evidence Audit Status: {evidence_report['overall_status']}")
    if evidence_report["overall_status"] != "PASS":
        print(f"  Missing items: {evidence_report['missing_items']}")
        st = evidence_report["overall_status"]
        print(f"ERROR: Cannot proceed with freeze. Overall status is {st}.")
        sys.exit(1)

    # 2. Build protocol freeze and supporting artifacts
    print("\nPhase 2: Building protocol freeze and audit bundle artifacts...")
    if freeze_p.exists() and not args.rebuild:
        print(f"  Protocol freeze already exists at {freeze_p}")
        print("  Skipping freeze rebuild (protocol is immutable; pass --rebuild to regenerate).")
    else:
        # Generate Executed Regression Evidence First before binding
        print("  Executing empirical regression test suite across 5 mutations...")
        reg_report_p = out_dir / "regression_test_report.json"
        regression_data = execute_regression_audit(
            source_smoke_dir=s_dir / "validation_smoke",
            base_dir=base,
            allow_dirty=args.allow_dirty,
            git_info=git_info,
            env_meta=env_meta,
        )
        write_immutable_json(reg_report_p, regression_data, overwrite=args.rebuild)
        print(f"  Saved executed regression test report to {reg_report_p}")

        freeze_data = build_protocol_freeze(
            evidence_report=evidence_report,
            source_evidence_dir=s_dir,
            output_dir=out_dir,
            logical_output_dir=logical_out,
            checkpoint_evidence_dir=args.checkpoint_evidence_dir,
            base_dir=base,
            allow_dirty=args.allow_dirty,
            git_info=git_info,
            env_meta=env_meta,
        )
        write_immutable_json(freeze_p, freeze_data, overwrite=args.rebuild)
        print(f"  Saved protocol freeze to {freeze_p}")

        # Input manifest
        input_manifest_data = build_input_manifest(
            source_evidence_dir=s_dir,
            logical_output_dir=logical_out,
            base_dir=base,
            git_sha=git_sha,
        )
        write_immutable_json(
            out_dir / "input_manifest.json", input_manifest_data, overwrite=args.rebuild
        )
        print(f"  Saved input manifest to {out_dir / 'input_manifest.json'}")

        # Reused evidence
        reused_data = build_reused_evidence(
            source_evidence_dir=s_dir,
            logical_output_dir=logical_out,
            base_dir=base,
        )
        write_immutable_json(out_dir / "reused_evidence.json", reused_data, overwrite=args.rebuild)
        print(f"  Saved reused evidence to {out_dir / 'reused_evidence.json'}")

        # Supersession
        supersession_data = build_supersession(
            logical_output_dir=logical_out,
            prior_bundle_dir="experiments/pretest_verification_v4",
            base_dir=base,
            git_sha=git_sha,
            git_dirty=git_dirty,
            env_meta=env_meta,
        )
        write_immutable_json(
            out_dir / "supersession.json", supersession_data, overwrite=args.rebuild
        )
        print(f"  Saved supersession to {out_dir / 'supersession.json'}")

    # 3. Verify saved freeze and produce pretest_audit.json
    print("\nPhase 3: Verifying saved freeze and producing pretest audit...")
    audit_data = verify_saved_freeze(
        freeze_path=freeze_p,
        source_evidence_dir=s_dir,
        checkpoint_evidence_dir=args.checkpoint_evidence_dir,
        base_dir=base,
        allow_dirty=args.allow_dirty,
        git_info=git_info,
        env_meta=env_meta,
        rerun_regression=True,
    )
    if not audit_p.exists() or args.rebuild:
        write_immutable_json(audit_p, audit_data, overwrite=args.rebuild)
        print(f"  Saved pretest audit to {audit_p}")
    else:
        print(f"  Verified against existing pretest audit at {audit_p}")
    print(f"  Overall Status:            {audit_data['overall_status']}")
    print(f"  Pre-Test Readiness:        {audit_data['pretest_readiness_status']}")
    print(f"  Held-Out Execution:        {audit_data['held_out_execution_status']}")
    print(f"  RQ Outcomes:               {audit_data['rq_outcomes_status']}")

    if audit_data["overall_status"] != "PASS":
        print("ERROR: Pre-test audit failed verification gates!")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("PRE-TEST READINESS VERIFICATION COMPLETE (STATUS: PRETEST_READY)")
    print("=" * 80)


if __name__ == "__main__":
    main()
