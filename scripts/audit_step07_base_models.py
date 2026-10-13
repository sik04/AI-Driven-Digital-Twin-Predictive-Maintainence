"""Step 7.5: Authoritative Base Predictor Matrix Audit Script.

Performs exhaustive verification of:
1. 30-model registry (experiments/base_models/model_registry.json).
2. Exactly 3 datasets x 2 families x 5 seeds = 30 unique cells.
3. Configuration freeze across seeds for every dataset/family cell.
4. Preprocessing artifact SHA-256 constancy and match with committed preprocessors.
5. Split manifest SHA-256 constancy and match with committed split manifests.
6. Checkpoint loadability and numerical reproduction on CPU.
7. Validation prediction endpoint completeness (cycles 30..T for each engine).
8. Target semantics (capped rul_target 125 for training, uncapped rul_true for validation).
9. Strict isolation of Step 7 development artifacts (no calibration/test leakage in base models).
10. Explicit prediction-reproduction audit mode (`--reproduce-predictions`).
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sklearn
import torch

from intellitwin.data.artifacts import compute_sha256
from intellitwin.models.registry import audit_base_model_registry


def get_git_info() -> tuple[str, bool]:
    """Retrieve git HEAD SHA and dirty status."""
    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
        status = subprocess.check_output(["git", "status", "--porcelain"]).decode("utf-8").strip()
        dirty = len(status) > 0
        return sha, dirty
    except Exception:
        return "unknown", False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Step 7.5: Authoritative Base Predictor Matrix Audit"
    )
    parser.add_argument(
        "--reproduce-predictions",
        action="store_true",
        help=(
            "Re-evaluate raw validation data and verify exact prediction "
            "and metric reproduction for all 30 models"
        ),
    )
    parser.add_argument(
        "--raw-data-dir",
        type=str,
        default="data/raw/cmapss",
        help="Directory containing raw C-MAPSS training text files",
    )
    parser.add_argument(
        "--registry-path",
        type=str,
        default="experiments/base_models/model_registry.json",
        help="Path to model_registry.json",
    )
    parser.add_argument(
        "--output-audit-json",
        type=str,
        default="experiments/audits/step07_prediction_reproduction.json",
        help="Output path for reproduction audit report JSON",
    )
    args = parser.parse_args()

    print("=" * 80)
    print("Step 7.5: Authoritative 30-Model Base Predictor Matrix Audit")
    if args.reproduce_predictions:
        print("Mode: Checkpoint Integrity + Full Raw-Data Prediction Reproduction")
    else:
        print("Mode: Checkpoint Integrity Only (Prediction Reproduction: NOT RUN)")
    print("=" * 80)

    reg_path = Path(args.registry_path)
    if not reg_path.exists():
        print(f"FAILED: Registry file not found: {reg_path}")
        sys.exit(1)

    try:
        audit_res = audit_base_model_registry(
            registry_path=reg_path,
            base_dir=Path("."),
            reload_checkpoints=True,
            reproduce_predictions=args.reproduce_predictions,
            raw_data_dir=Path(args.raw_data_dir),
        )
    except Exception as exc:
        print(f"\nAUDIT FAILED with exception:\n{exc}")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("AUDIT RESULT: ALL CHECKS PASSED (STATUS: PASS)")
    print(f"Total verified models: {audit_res['models_audited']}/30")
    print(f"Checkpoint integrity:  {audit_res['checkpoint_integrity']}")
    print(f"Prediction repro check: {audit_res['prediction_reproduction']}")
    print(f"Datasets: {audit_res['datasets']}")
    print(f"Families: {audit_res['families']}")
    print(f"Seeds: {audit_res['seeds']}")
    print("Configurations:")
    for cell, cfg_id in audit_res["configurations"].items():
        print(f"  {cell:12s}: {cfg_id}")
    print("=" * 80)

    if args.reproduce_predictions and audit_res["reproduction_details"]:
        git_sha, git_dirty = get_git_info()
        audit_time = datetime.now(timezone.utc).isoformat()

        # Gather file hashes
        raw_hashes = {}
        for ds in ("FD001", "FD002", "FD004"):
            p = Path(args.raw_data_dir) / f"train_{ds}.txt"
            raw_hashes[ds] = compute_sha256(p) if p.exists() else "missing"

        manifest_hashes = {}
        for ds in ("FD001", "FD002", "FD004"):
            p = Path(f"data/splits/{ds.lower()}_engine_split_seed_2026.json")
            manifest_hashes[ds] = compute_sha256(p) if p.exists() else "missing"

        preprocessor_hashes = {}
        for ds in ("FD001", "FD002", "FD004"):
            p = Path(f"experiments/preprocessing/{ds}/preprocessor.json")
            preprocessor_hashes[ds] = compute_sha256(p) if p.exists() else "missing"

        report_data: dict[str, Any] = {
            "schema_version": "step07-prediction-reproduction-v1",
            "audit_timestamp_utc": audit_time,
            "status": "PASS",
            "git_commit": git_sha,
            "git_dirty": git_dirty,
            "platform": platform.platform(),
            "package_versions": {
                "python": sys.version,
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "scikit_learn": sklearn.__version__,
                "torch": torch.__version__,
            },
            "source_hashes": {
                "registry_py": compute_sha256(Path("src/intellitwin/models/registry.py")),
                "audit_script": compute_sha256(Path("scripts/audit_step07_base_models.py")),
            },
            "data_hashes": raw_hashes,
            "split_manifest_hashes": manifest_hashes,
            "preprocessor_hashes": preprocessor_hashes,
            "models_audited": audit_res["models_audited"],
            "models": audit_res["reproduction_details"],
        }

        out_path = Path(args.output_audit_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
        print(f"\nWrote reproduction audit report to: {out_path}")


if __name__ == "__main__":
    main()
