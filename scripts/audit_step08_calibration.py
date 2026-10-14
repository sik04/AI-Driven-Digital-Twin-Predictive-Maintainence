"""Step 8: Independent Calibration Matrix, Content Verification, and Reproduction Audit.

Protocol: step08-v1
Exhaustively verifies:
1. Calibration registry completeness (90 entries, 270 bundles) and dependency integrity.
2. Prediction cache membership, completeness, and non-negative finite validity across seeds.
3. Selection freeze integrity, git commit verification, and LOEO reconstruction from caches.
4. Independent rational quantile and fallback routing reconstruction for all 90 calibrators.
5. Saved interval prediction CSVs and metric numerical reconstruction across coverages.
6. Scoped partition isolation (absence of held-out test predictions/metrics in Step 7/8).
7. Base predictor checkpoint prediction reproduction on validation and calibration partitions.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from intellitwin.provenance import capture_environment_metadata, get_git_info, write_immutable_json
from intellitwin.uncertainty.schema import PROTOCOL_VERSION
from intellitwin.uncertainty.verification import (
    reproduce_checkpoint_predictions,
    verify_all_calibrator_quantiles_and_intervals,
    verify_prediction_cache_membership,
    verify_registry_structure_and_hashes,
    verify_scoped_isolation,
    verify_selection_freeze_reconstruction,
)


def run_step08_audit(
    base_dir: Path | str = ".",
    raw_data_dir: Path | str = "data/raw/cmapss",
    full_audit: bool = True,
    reproduce_predictions_from_raw: bool | None = None,
    allow_dirty: bool = False,
) -> dict[str, Any]:
    """Execute complete independent Step 8 verification audit.

    Official full audit mode executes all mandatory verification checks,
    including raw checkpoint prediction reproduction on validation and
    calibration partitions (60 model/partition checks).
    """
    base = Path(base_dir).resolve()

    # Provenance tracking at entry - strict clean tree enforced
    git_sha, git_dirty = get_git_info(
        allow_dirty=allow_dirty,
        repo_root=base,
    )
    env_meta = capture_environment_metadata(device="cpu")

    should_reproduce = (
        full_audit if reproduce_predictions_from_raw is None else reproduce_predictions_from_raw
    )

    results: dict[str, Any] = {
        "registry_completeness": "PENDING",
        "prediction_cache_integrity": "PENDING",
        "selection_freeze_reconstruction": "PENDING",
        "threshold_and_interval_reconstruction": "PENDING",
        "scoped_isolation": "PENDING",
        "checkpoint_prediction_reproduction": "NOT RUN",
    }
    details: dict[str, Any] = {}

    # A. Registry Completeness & Hashes
    reg_res = verify_registry_structure_and_hashes(
        registry_path="experiments/calibration/calibration_registry.json",
        base_dir=base,
    )
    results["registry_completeness"] = reg_res["status"]
    details["registry"] = reg_res

    # B. Prediction-Cache Membership & Completeness
    cache_res = verify_prediction_cache_membership(
        base_dir=base,
        raw_data_dir=raw_data_dir,
    )
    results["prediction_cache_integrity"] = cache_res["status"]
    details["prediction_caches"] = cache_res["details"]

    # C. Selection-Freeze Integrity & LOEO Candidate Reconstruction
    freeze_res = verify_selection_freeze_reconstruction(base_dir=base)
    results["selection_freeze_reconstruction"] = freeze_res["status"]
    details["selection_freeze"] = freeze_res["details"]

    # D & E & F. Quantiles, Routing, Saved Intervals, and Metrics
    quant_res = verify_all_calibrator_quantiles_and_intervals(base_dir=base)
    results["threshold_and_interval_reconstruction"] = quant_res["status"]
    details["quantiles_and_intervals"] = quant_res

    # H. Scoped Isolation
    iso_res = verify_scoped_isolation(base_dir=base)
    results["scoped_isolation"] = iso_res["status"]
    details["isolation"] = iso_res

    # G. Raw Prediction Reproduction
    if should_reproduce:
        raw_p = base / raw_data_dir
        if not raw_p.exists():
            results["checkpoint_prediction_reproduction"] = "NOT RUN (RAW DATA MISSING)"
            details["checkpoint_prediction_reproduction"] = {
                "status": "NOT RUN",
                "reason": f"Raw data directory not found: {raw_p}",
            }
        else:
            raw_res = reproduce_checkpoint_predictions(
                base_dir=base,
                raw_data_dir=raw_data_dir,
            )
            results["checkpoint_prediction_reproduction"] = raw_res["status"]
            details["checkpoint_prediction_reproduction"] = raw_res

    # Status determination:
    # PASS: every mandatory check executed and passed.
    # INCOMPLETE: mandatory evidence or execution is missing.
    # FAIL: a check executed and failed.
    failures = [k for k, v in results.items() if v == "FAIL"]
    not_runs = [k for k, v in results.items() if str(v).startswith("NOT RUN") or v == "PENDING"]

    if failures:
        overall_status = "FAIL"
    elif not_runs:
        overall_status = "INCOMPLETE"
    elif all(v == "PASS" for v in results.values()):
        overall_status = "PASS"
    else:
        overall_status = "FAIL"

    return {
        "schema_version": "step08-full-audit-v1" if full_audit else "step08-repair-verification-v1",
        "protocol_version": PROTOCOL_VERSION,
        "overall_status": overall_status,
        "historical_provenance_context": {
            "historical_baseline_commit": "f1edce7fdf48b45513ff90a680da49701451d9cb",
            "historical_audit_git_dirty": True,
            "historical_audit_path": "experiments/calibration/audit_report.json",
            "notice": (
                "Current reconstruction cannot retroactively establish that historical dirty "
                "run was clean; historical report preserved unchanged."
            ),
        },
        "current_reconstruction": {
            "git_commit": git_sha,
            "git_dirty": git_dirty,
            "environment": env_meta,
        },
        "checks_actually_run": [k for k, v in results.items() if not str(v).startswith("NOT RUN")],
        "checks_not_run": not_runs,
        "failures": failures,
        "results": results,
        "details": details,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Step 8: Independent Calibration Matrix & Content Verification Audit"
    )
    parser.add_argument(
        "--raw-data-dir",
        type=str,
        default="data/raw/cmapss",
        help="Directory containing raw C-MAPSS training text files",
    )
    parser.add_argument(
        "--skip-raw-reproduction",
        action="store_true",
        help="Explicitly skip raw checkpoint prediction reproduction (produces INCOMPLETE audit)",
    )
    parser.add_argument(
        "--output-audit-json",
        type=str,
        default="experiments/pretest_verification_v2/step08_full_audit.json",
        help="Output path for Step 8 audit report JSON",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Permit execution on a dirty git working tree (ineligible for official completion)",
    )
    args = parser.parse_args()

    full_audit = not args.skip_raw_reproduction

    print("=" * 80)
    print("Step 8: Independent Calibration Matrix & Full Content Verification Audit")
    print(f"Mode: {'FULL OFFICIAL AUDIT' if full_audit else 'ARTIFACT-ONLY (INCOMPLETE)'}")
    print("=" * 80)

    try:
        report = run_step08_audit(
            base_dir=".",
            raw_data_dir=args.raw_data_dir,
            full_audit=full_audit,
            allow_dirty=args.allow_dirty,
        )
    except Exception as exc:
        print(f"\nAUDIT FAILED with exception:\n{exc}")
        sys.exit(1)

    print("\n" + "=" * 80)
    print(f"STEP 8 AUDIT RESULT: {report['overall_status']}")
    for check_name, status in report["results"].items():
        print(f"  {check_name:<40}: {status}")
    print("=" * 80)

    out_p = Path(args.output_audit_json)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    write_immutable_json(out_p, report, overwrite=False)
    print(f"\nWrote Step 8 audit report to: {out_p}")

    if report["overall_status"] != "PASS":
        print(f"\nERROR: Audit overall status is {report['overall_status']} (required: PASS).")
        sys.exit(1)


if __name__ == "__main__":
    main()
