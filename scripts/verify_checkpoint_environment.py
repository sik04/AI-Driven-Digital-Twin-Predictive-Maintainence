"""Portion B: Checkpoint Environment Verification and Prediction Reproduction.

Schema: checkpoint-environment-verification-v1
Official Protocol:
- Enforces clean Git state at entry.
- Verifies version agreement across all 30 base model metadata files.
- Verifies exact runtime Python, numpy, pandas, scikit-learn, and torch CPU versions.
- Executes and validates pip check.
- Hashes protected inputs pre-execution and verifies zero mutation post-execution.
- Traps and forbids sklearn InconsistentVersionWarning.
- Executes full Step 8 reproduction audit across 60 model/partition records.
- Asserts finite predictions, exact key alignment, and max absolute error <= 1e-4.
- Generates 6 official handoff artifacts into target directory:
  1. environment_verification.json
  2. step08_full_audit.json
  3. input_manifest.json
  4. execution.log
  5. pip_freeze.txt
  6. pip_check.txt
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import io
import json
import platform
import subprocess
import sys
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sklearn
import torch
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from intellitwin.provenance import (  # noqa: E402
    capture_environment_metadata,
    get_git_info,
    write_immutable_json,
)
from intellitwin.uncertainty.verification import RAW_TRAIN_HASHES  # noqa: E402
from scripts.audit_step08_calibration import run_step08_audit  # noqa: E402

SCHEMA_VERSION = "checkpoint-environment-verification-v1"
EXPECTED_DATASETS = ("FD001", "FD002", "FD004")
EXPECTED_FAMILIES = ("GBR", "LSTM")
EXPECTED_SEEDS = (2026, 2027, 2028, 2029, 2030)
EXPECTED_PARTITIONS = ("validation", "calibration")

REQUIRED_VERSIONS = {
    "python": "3.14.0",
    "numpy": "2.5.3",
    "pandas": "3.0.6",
    "scikit-learn": "1.9.1",
    "torch": "2.14.1+cpu",
    "pyyaml": "6.0.3",
}


class TeeLogger:
    """Tee stdout/stderr to a string buffer and real stream."""

    def __init__(self, original_stream: Any) -> None:
        self.original_stream = original_stream
        self.buffer = io.StringIO()

    def write(self, data: str) -> int:
        self.original_stream.write(data)
        self.original_stream.flush()
        return self.buffer.write(data)

    def flush(self) -> None:
        self.original_stream.flush()
        self.buffer.flush()

    def get_value(self) -> str:
        return self.buffer.getvalue()


def compute_file_sha256(path: Path) -> str:
    """Compute SHA-256 of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_metadata_agreement(base_dir: Path) -> dict[str, Any]:
    """Verify agreement across all 30 base model metadata files mechanically."""
    metadata_records: list[dict[str, Any]] = []
    mismatches: list[str] = []

    for ds in EXPECTED_DATASETS:
        for fam in EXPECTED_FAMILIES:
            for seed in EXPECTED_SEEDS:
                meta_p = (
                    base_dir
                    / "experiments"
                    / "base_models"
                    / ds
                    / fam
                    / f"seed_{seed}"
                    / "metadata.json"
                )
                if not meta_p.exists():
                    raise FileNotFoundError(f"Missing base model metadata file: {meta_p}")

                with open(meta_p, encoding="utf-8") as f:
                    meta = json.load(f)

                rec = {
                    "dataset": ds,
                    "model_family": fam,
                    "seed": seed,
                    "python_version": meta.get("python_version"),
                    "numpy_version": meta.get("numpy_version"),
                    "pandas_version": meta.get("pandas_version"),
                    "scikit_learn_version": meta.get("scikit_learn_version"),
                    "torch_version": meta.get("torch_version"),
                }
                metadata_records.append(rec)

                # Check against required baseline declarations
                if rec["python_version"] != REQUIRED_VERSIONS["python"]:
                    mismatches.append(
                        f"{meta_p}: python_version={rec['python_version']} "
                        f"!= {REQUIRED_VERSIONS['python']}"
                    )
                if rec["numpy_version"] != REQUIRED_VERSIONS["numpy"]:
                    mismatches.append(
                        f"{meta_p}: numpy_version={rec['numpy_version']} "
                        f"!= {REQUIRED_VERSIONS['numpy']}"
                    )
                if rec["pandas_version"] != REQUIRED_VERSIONS["pandas"]:
                    mismatches.append(
                        f"{meta_p}: pandas_version={rec['pandas_version']} "
                        f"!= {REQUIRED_VERSIONS['pandas']}"
                    )
                if rec["scikit_learn_version"] != REQUIRED_VERSIONS["scikit-learn"]:
                    mismatches.append(
                        f"{meta_p}: scikit_learn_version={rec['scikit_learn_version']} "
                        f"!= {REQUIRED_VERSIONS['scikit-learn']}"
                    )
                if rec["torch_version"] != REQUIRED_VERSIONS["torch"]:
                    mismatches.append(
                        f"{meta_p}: torch_version={rec['torch_version']} "
                        f"!= {REQUIRED_VERSIONS['torch']}"
                    )

    if len(metadata_records) != 30:
        raise ValueError(f"Expected exactly 30 metadata files, found {len(metadata_records)}")

    if mismatches:
        raise ValueError(
            "Conflicting or non-matching metadata declarations detected across 30 records:\n"
            + "\n".join(mismatches)
        )

    return {
        "status": "PASS",
        "record_count": len(metadata_records),
        "declared_versions": {
            "python": REQUIRED_VERSIONS["python"],
            "numpy": REQUIRED_VERSIONS["numpy"],
            "pandas": REQUIRED_VERSIONS["pandas"],
            "scikit-learn": REQUIRED_VERSIONS["scikit-learn"],
            "torch": REQUIRED_VERSIONS["torch"],
        },
    }


def verify_runtime_versions() -> dict[str, Any]:
    """Compare actual runtime versions against required versions before loading checkpoints."""
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    np_ver = np.__version__
    pd_ver = pd.__version__
    sk_ver = sklearn.__version__
    torch_ver = torch.__version__
    yaml_ver = getattr(yaml, "__version__", "unknown")

    actual = {
        "python": py_ver,
        "numpy": np_ver,
        "pandas": pd_ver,
        "scikit-learn": sk_ver,
        "torch": torch_ver,
        "pyyaml": yaml_ver,
    }

    mismatches: list[str] = []
    for pkg, exp in REQUIRED_VERSIONS.items():
        act = actual.get(pkg)
        if act != exp:
            mismatches.append(f"{pkg}: actual={act} != expected={exp}")

    if mismatches:
        msg = "Runtime environment mismatch (stopped before checkpoint loading):\n" + "\n".join(
            mismatches
        )
        raise RuntimeError(msg)

    return {
        "status": "PASS",
        "match": True,
        "expected": REQUIRED_VERSIONS,
        "actual": actual,
    }


def execute_pip_check() -> tuple[int, str]:
    """Execute pip check and return exit code and combined output."""
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            capture_output=True,
            text=True,
            check=False,
        )
        output = (proc.stdout + "\n" + proc.stderr).strip()
        return proc.returncode, output
    except Exception as exc:
        return 1, f"Failed to execute pip check: {exc}"


def execute_pip_freeze() -> str:
    """Execute pip freeze and return captured freeze output."""
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            check=True,
        )
        return proc.stdout.strip()
    except Exception as exc:
        return f"# Error executing pip freeze: {exc}"


def collect_protected_input_paths(base_dir: Path) -> dict[str, list[Path]]:
    """Enumerate all protected input files by category."""
    inputs: dict[str, list[Path]] = {}

    # 1. splits_and_quartiles
    inputs["splits_and_quartiles"] = sorted(
        [p for p in (base_dir / "data" / "splits").glob("*.json") if p.is_file()]
    )

    # 2. model_metadata
    inputs["model_metadata"] = sorted(
        [
            p
            for p in (base_dir / "experiments" / "base_models").glob("*/*/seed_*/metadata.json")
            if p.is_file()
        ]
    )

    # 3. model_registry
    inputs["model_registry"] = [base_dir / "experiments" / "base_models" / "model_registry.json"]

    # 4. checkpoints
    inputs["checkpoints"] = sorted(
        [
            p
            for p in (base_dir / "experiments" / "base_models").glob("*/*/seed_*/checkpoint")
            if p.is_file()
        ]
    )

    # 5. preprocessing
    inputs["preprocessing"] = sorted(
        [p for p in (base_dir / "experiments" / "preprocessing").glob("**/*.json") if p.is_file()]
    )

    # 6. calibrator_registry
    inputs["calibrator_registry"] = [
        base_dir / "experiments" / "calibration" / "calibration_registry.json"
    ]

    # 7. calibrator_bundles
    inputs["calibrator_bundles"] = sorted(
        [
            p
            for p in (base_dir / "experiments" / "calibration" / "fitted").glob(
                "*/*/*/*/calibrator.json"
            )
            if p.is_file()
        ]
    )

    # 8. calibration_selection
    inputs["calibration_selection"] = sorted(
        [
            p
            for p in (base_dir / "experiments" / "calibration" / "selection").glob(
                "*/*/selection.json"
            )
            if p.is_file()
        ]
    )

    # 9. prediction_caches
    inputs["prediction_caches"] = sorted(
        [
            p
            for p in (base_dir / "experiments" / "calibration" / "point_predictions").glob(
                "*/*/*/*.csv"
            )
            if p.is_file()
        ]
    )

    # 10. verification_sources
    inputs["verification_sources"] = [
        base_dir / "scripts" / "audit_step08_calibration.py",
        base_dir / "src" / "intellitwin" / "uncertainty" / "verification.py",
        base_dir / "src" / "intellitwin" / "data" / "calibration_pipeline.py",
        base_dir / "src" / "intellitwin" / "models" / "registry.py",
        base_dir / "src" / "intellitwin" / "provenance.py",
    ]

    # 11. environment_specification
    inputs["environment_specification"] = [
        base_dir / "requirements" / "checkpoint-verification" / "requirements.in",
        base_dir
        / "requirements"
        / "checkpoint-verification"
        / "requirements-windows-py314.lock.txt",
        base_dir / "requirements" / "checkpoint-verification" / "environment_spec.json",
    ]

    return inputs


def hash_protected_inputs(
    base_dir: Path,
) -> dict[str, dict[str, str]]:
    """Compute mapping of repository-relative POSIX path to SHA-256 for all protected inputs."""
    cat_paths = collect_protected_input_paths(base_dir)
    hashed_categories: dict[str, dict[str, str]] = {}

    for cat, paths in cat_paths.items():
        cat_map: dict[str, str] = {}
        for p in paths:
            if not p.exists():
                raise FileNotFoundError(f"Protected input missing: {p}")
            rel = p.relative_to(base_dir).as_posix()
            cat_map[rel] = compute_file_sha256(p)
        if not cat_map:
            raise ValueError(f"Protected input category '{cat}' is unexpectedly empty!")
        hashed_categories[cat] = cat_map

    return hashed_categories


def hash_raw_files(base_dir: Path, raw_data_dir: Path | str) -> dict[str, str]:
    """Verify raw source files exist and compute hashes."""
    raw_map: dict[str, str] = {}
    rel_raw = Path(raw_data_dir)
    if rel_raw.is_absolute():
        rel_raw = rel_raw.relative_to(base_dir)

    for ds in EXPECTED_DATASETS:
        p = base_dir / rel_raw / f"train_{ds}.txt"
        if not p.exists():
            raise FileNotFoundError(f"Raw C-MAPSS dataset missing: {p}")
        h = compute_file_sha256(p)
        if h != RAW_TRAIN_HASHES[ds]:
            raise ValueError(
                f"Raw dataset hash mismatch for {p}: actual={h} != expected={RAW_TRAIN_HASHES[ds]}"
            )
        rel_posix = (rel_raw / f"train_{ds}.txt").as_posix()
        raw_map[rel_posix] = h
    return raw_map


def verify_step08_reproduction_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Mechanically verify exactly 60 reproduction records from Step 8 audit."""
    expected_keys = {
        (ds, fam, s, part)
        for ds in EXPECTED_DATASETS
        for fam in EXPECTED_FAMILIES
        for s in EXPECTED_SEEDS
        for part in EXPECTED_PARTITIONS
    }

    actual_keys: set[tuple[str, str, int, str]] = set()
    all_passed = True
    max_err = 0.0
    errors: list[str] = []

    for r in records:
        key = (
            str(r.get("dataset")),
            str(r.get("model_family")),
            int(r.get("seed", 0)),
            str(r.get("partition")),
        )
        if key in actual_keys:
            errors.append(f"Duplicate reproduction record key: {key}")
        actual_keys.add(key)

        st = r.get("status")
        err = float(r.get("max_abs_diff", 1.0))
        if st != "PASS":
            all_passed = False
            errors.append(f"Record {key} failed with status {st}")
        if not np.isfinite(err):
            all_passed = False
            errors.append(f"Record {key} produced non-finite difference {err}")
        if err > 1e-4:
            all_passed = False
            errors.append(f"Record {key} exceeded error tolerance: {err:.6e} > 1e-4")
        if err > max_err:
            max_err = err

    keys_match = actual_keys == expected_keys
    if not keys_match:
        missing = expected_keys - actual_keys
        extra = actual_keys - expected_keys
        if missing:
            errors.append(f"Missing expected reproduction keys: {missing}")
        if extra:
            errors.append(f"Unexpected reproduction keys: {extra}")

    complete = len(records) == 60 and keys_match and all_passed and max_err <= 1e-4

    return {
        "status": "PASS" if complete else "FAIL",
        "record_count": len(records),
        "expected_count": 60,
        "reproduction_records_complete": complete,
        "keys_match": keys_match,
        "max_absolute_difference": max_err,
        "errors": errors,
    }


def run_checkpoint_verification(
    base_dir: Path | str = ".",
    raw_data_dir: Path | str = "data/raw/cmapss",
    output_dir: Path | str | None = None,
    allow_dirty: bool = False,
    skip_raw_reproduction: bool = False,
) -> dict[str, Any]:
    """Execute complete checkpoint environment verification and prediction reproduction."""
    utc_start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    base = Path(base_dir).resolve()
    raw_rel = Path(raw_data_dir)
    if raw_rel.is_absolute():
        raw_rel = raw_rel.relative_to(base)
    raw_rel_str = raw_rel.as_posix()

    if output_dir is None:
        raise ValueError("An explicit --output-dir is required for checkpoint verification.")

    out_p = Path(output_dir).resolve()
    out_p.mkdir(parents=True, exist_ok=True)

    # 1. Clean Git state check & provenance
    git_sha, git_dirty = get_git_info(allow_dirty=allow_dirty, repo_root=base)
    clean_exec = not git_dirty
    if git_dirty and not allow_dirty:
        raise RuntimeError(
            "Clean git state required for official checkpoint verification execution."
        )

    env_meta = capture_environment_metadata(device="cpu")

    # 2. Mechanically verify metadata across all 30 base models
    metadata_res = verify_metadata_agreement(base)

    # 3. Verify actual runtime versions BEFORE loading models
    runtime_res = verify_runtime_versions()

    # 4. Require successful pip check
    pip_check_code, pip_check_out = execute_pip_check()
    if pip_check_code != 0:
        raise RuntimeError(f"pip check failed with exit code {pip_check_code}:\n{pip_check_out}")

    # 5. Capture pip freeze
    pip_freeze_out = execute_pip_freeze()

    # 6. Hash protected inputs before execution
    pre_protected_hashes = hash_protected_inputs(base)
    raw_hashes = hash_raw_files(base, raw_rel_str)

    # 7. Execute Step 8 Full Audit with raw prediction reproduction enabled while catching warnings
    sklearn_warning_count = 0
    caught_warning_details: list[str] = []

    with warnings.catch_warnings(record=True) as recorded_warnings:
        warnings.simplefilter("always")

        s8_report = run_step08_audit(
            base_dir=base,
            raw_data_dir=raw_rel_str,
            full_audit=not skip_raw_reproduction,
            reproduce_predictions_from_raw=not skip_raw_reproduction,
            allow_dirty=allow_dirty,
        )

        for w in recorded_warnings:
            w_msg = str(w.message)
            w_cat = getattr(w.category, "__name__", str(w.category))
            caught_warning_details.append(f"[{w_cat}] {w_msg}")
            if "InconsistentVersionWarning" in w_cat or "InconsistentVersionWarning" in w_msg:
                sklearn_warning_count += 1

    if sklearn_warning_count > 0:
        raise RuntimeError(
            f"FATAL: {sklearn_warning_count} sklearn.exceptions.InconsistentVersionWarning "
            f"detected during execution: {caught_warning_details}"
        )

    # 8. Hash protected inputs post-execution and verify immutability
    post_protected_hashes = hash_protected_inputs(base)
    mismatches: list[str] = []
    for cat, pre_map in pre_protected_hashes.items():
        post_map = post_protected_hashes.get(cat, {})
        for rel_p, pre_h in pre_map.items():
            post_h = post_map.get(rel_p)
            if post_h != pre_h:
                mismatches.append(f"{cat} file {rel_p}: pre={pre_h} != post={post_h}")

    if mismatches:
        raise RuntimeError(
            "FATAL: Protected inputs were modified during execution:\n" + "\n".join(mismatches)
        )

    # 9. Verify 60 reproduction records from Step 8 report
    raw_repro = s8_report.get("details", {}).get(
        "checkpoint_prediction_reproduction",
        s8_report.get("raw_checkpoint_reproduction", {}),
    )
    records = raw_repro.get("records", [])
    repro_check = verify_step08_reproduction_records(records)

    overall_pass = (
        s8_report.get("overall_status") == "PASS"
        and repro_check["status"] == "PASS"
        and repro_check["reproduction_records_complete"]
        and pip_check_code == 0
        and sklearn_warning_count == 0
        and not mismatches
        and (not git_dirty if not allow_dirty else True)
    )

    status = "PASS" if overall_pass else ("INCOMPLETE" if skip_raw_reproduction else "FAIL")
    utc_end = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Build environment_verification.json structure
    env_verif_data: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "overall_status": status,
        "source_execution_commit": git_sha,
        "git_dirty": git_dirty,
        "clean_source_execution": clean_exec,
        "utc_start_timestamp": utc_start,
        "utc_end_timestamp": utc_end,
        "platform": platform.platform(),
        "cpu": env_meta.get("cpu", platform.processor()),
        "device": "cpu",
        "expected_versions": REQUIRED_VERSIONS,
        "actual_versions": runtime_res["actual"],
        "environment_match": runtime_res["match"],
        "metadata_records_verified": metadata_res["record_count"],
        "pip_check_exit_code": pip_check_code,
        "sklearn_inconsistent_version_warning_count": sklearn_warning_count,
        "warning_details": caught_warning_details,
        "error_details": repro_check["errors"] + mismatches,
        "reproduction_record_count": repro_check["record_count"],
        "reproduction_records_complete": repro_check["reproduction_records_complete"],
        "max_absolute_difference": repro_check["max_absolute_difference"],
        "protected_inputs_unchanged": not mismatches,
        "held_out_execution_status": "NOT_STARTED",
    }

    # Build input_manifest.json structure
    input_manifest_data: dict[str, Any] = {
        "schema_version": "checkpoint-input-manifest-v1",
        "source_execution_commit": git_sha,
        "git_dirty": git_dirty,
        "clean_source_execution": clean_exec,
        "protected_inputs": pre_protected_hashes,
        "raw_files": raw_hashes,
        "pre_post_comparison": {
            "protected_inputs_unchanged": not mismatches,
            "mismatches": mismatches,
        },
    }

    # Save handoff files to output_dir
    write_immutable_json(out_p / "environment_verification.json", env_verif_data, overwrite=True)
    write_immutable_json(out_p / "step08_full_audit.json", s8_report, overwrite=True)
    write_immutable_json(out_p / "input_manifest.json", input_manifest_data, overwrite=True)

    with open(out_p / "pip_freeze.txt", "w", encoding="utf-8") as f:
        f.write(pip_freeze_out + "\n")

    with open(out_p / "pip_check.txt", "w", encoding="utf-8") as f:
        f.write(pip_check_out + "\n")

    return {
        "status": status,
        "env_verification": env_verif_data,
        "step08_report": s8_report,
        "input_manifest": input_manifest_data,
        "pip_freeze": pip_freeze_out,
        "pip_check": pip_check_out,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Portion B: Independent Verification Wrapper for Checkpoint Environment"
    )
    parser.add_argument(
        "--raw-data-dir",
        type=str,
        default="data/raw/cmapss",
        help="Directory containing raw C-MAPSS training text files",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Required target directory for official verification handoff files",
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Repository root directory",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Permit execution on a dirty git working tree (ineligible for official completion)",
    )
    parser.add_argument(
        "--skip-raw-reproduction",
        action="store_true",
        help="Skip prediction reproduction from raw files (for test/failure isolation only)",
    )
    args = parser.parse_args()

    # Capture execution output in real time and in log buffer
    tee_out = TeeLogger(sys.stdout)
    tee_err = TeeLogger(sys.stderr)
    sys.stdout = tee_out
    sys.stderr = tee_err

    print("=" * 80)
    print("IntelliTwin Checkpoint Environment Verification & Prediction Reproduction")
    print(f"Base Directory:     {args.base_dir}")
    print(f"Raw Data Directory: {args.raw_data_dir}")
    print(f"Output Directory:   {args.output_dir}")
    print(f"Allow Dirty:        {args.allow_dirty}")
    print(f"Skip Reproduction:  {args.skip_raw_reproduction}")
    print("=" * 80)

    try:
        res = run_checkpoint_verification(
            base_dir=args.base_dir,
            raw_data_dir=args.raw_data_dir,
            output_dir=args.output_dir,
            allow_dirty=args.allow_dirty,
            skip_raw_reproduction=args.skip_raw_reproduction,
        )
    except Exception as exc:
        print(f"\nFATAL EXECUTION FAILURE:\n{exc}")
        out_p = Path(args.output_dir).resolve()
        out_p.mkdir(parents=True, exist_ok=True)
        # Flush log before exiting
        with open(out_p / "execution.log", "w", encoding="utf-8") as f:
            f.write(tee_out.get_value())
            if tee_err.get_value():
                f.write("\nSTDERR:\n" + tee_err.get_value())
        sys.exit(1)

    print("\n" + "=" * 80)
    print(f"CHECKPOINT VERIFICATION RESULT: {res['status']}")
    print(f"  Records Verified:        {res['env_verification']['reproduction_record_count']}/60")
    print(f"  All Records Complete:    {res['env_verification']['reproduction_records_complete']}")
    print(f"  Max Absolute Difference: {res['env_verification']['max_absolute_difference']:.6e}")
    warn_cnt = res["env_verification"]["sklearn_inconsistent_version_warning_count"]
    print(f"  Inconsistent Warnings:   {warn_cnt}")
    print(f"  Protected Inputs Preserved: {res['env_verification']['protected_inputs_unchanged']}")
    print(f"  Held-Out Execution:      {res['env_verification']['held_out_execution_status']}")
    print("=" * 80)

    # Write execution log
    out_p = Path(args.output_dir).resolve()
    with open(out_p / "execution.log", "w", encoding="utf-8") as f:
        f.write(tee_out.get_value())
        if tee_err.get_value():
            f.write("\nSTDERR:\n" + tee_err.get_value())

    if res["status"] != "PASS":
        print(f"\nERROR: Verification ended with non-PASS status: {res['status']}")
        sys.exit(1)

    print("\nVerification succeeded! All handoff files generated.")


if __name__ == "__main__":
    main()
