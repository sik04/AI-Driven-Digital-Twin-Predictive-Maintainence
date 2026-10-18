"""Executed regression evidence runner and mutation rejection verification.

This module executes empirical regression audits against known verifier defect modes:
1. Verifies unmodified baseline evidence passes verification.
2. Applies 5 isolated mutations to temporary copies of the evidence.
3. Evaluates that each mutated copy fails verification for the intended reason.
4. Cleans all temporary copies after execution.
5. Produces an executed regression report bound into pre-test freeze evidence.
"""

from __future__ import annotations

import math
import shutil
import tempfile
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from intellitwin.data.artifacts import compute_sha256
from intellitwin.evaluation.schema import (
    DECISION_QUANTILES,
    DESCRIPTIVE_QUANTILES,
    PROTOCOL_VERSION,
)
from intellitwin.evaluation.verification import (
    REQUIRED_SMOKE_FILES,
    verify_validation_smoke_matrix,
)
from intellitwin.provenance import (
    capture_environment_metadata,
    get_git_info,
)

REGRESSION_REPORT_SCHEMA_VERSION = "step09-regression-report-v2"


# =============================================================================
# Prescribed Mutation Helpers
# =============================================================================


def apply_mutation_1_altered_point_prediction(smoke_dir: Path) -> dict[str, Any]:
    """Mutation 1: Increase one FD001/GBR/seed-2027 point prediction by 100."""
    pts_p = smoke_dir / "point_predictions.csv"
    df_pts = pd.read_csv(pts_p)
    mask = (
        (df_pts["dataset"] == "FD001")
        & (df_pts["model_family"] == "GBR")
        & (df_pts["seed"] == 2027)
    )
    if not any(mask):
        raise ValueError(
            "Mutation 1 target (FD001, GBR, seed 2027) not found in point_predictions.csv"
        )
    idx = df_pts[mask].index[0]
    orig_val = float(df_pts.at[idx, "prediction"])
    new_val = orig_val + 100.0
    df_pts.at[idx, "prediction"] = new_val
    df_pts.to_csv(pts_p, index=False)
    return {
        "dataset": "FD001",
        "model_family": "GBR",
        "seed": 2027,
        "row_index": int(idx),
        "original_prediction": orig_val,
        "mutated_prediction": new_val,
    }


def apply_mutation_2_deleted_point_prediction(smoke_dir: Path) -> dict[str, Any]:
    """Mutation 2: Delete one FD001/GBR/seed-2026 point-prediction row."""
    pts_p = smoke_dir / "point_predictions.csv"
    df_pts = pd.read_csv(pts_p)
    mask = (
        (df_pts["dataset"] == "FD001")
        & (df_pts["model_family"] == "GBR")
        & (df_pts["seed"] == 2026)
    )
    if not any(mask):
        raise ValueError(
            "Mutation 2 target (FD001, GBR, seed 2026) not found in point_predictions.csv"
        )
    idx = df_pts[mask].index[0]
    dropped_row = df_pts.loc[idx].to_dict()
    df_pts = df_pts.drop(idx)
    df_pts.to_csv(pts_p, index=False)
    return {
        "dataset": "FD001",
        "model_family": "GBR",
        "seed": 2026,
        "dropped_index": int(idx),
        "dropped_unit": int(dropped_row.get("unit", -1)),
    }


def apply_mutation_3_altered_component_evidence(smoke_dir: Path) -> dict[str, Any]:
    """Mutation 3: Increase ci_decision_low by 100 for component
    RQ1_GBR_global_hcp_cost_improvement.
    """
    comp_p = smoke_dir / "component_evidence.csv"
    df_comp = pd.read_csv(comp_p)
    target_cid = "RQ1_GBR_global_hcp_cost_improvement"
    mask = df_comp["component_id"] == target_cid
    if not any(mask):
        raise ValueError(
            f"Mutation 3 target component {target_cid} not found in component_evidence.csv"
        )
    idx = df_comp[mask].index[0]
    orig_val = float(df_comp.at[idx, "ci_decision_low"])
    new_val = orig_val + 100.0
    df_comp.at[idx, "ci_decision_low"] = new_val
    df_comp.to_csv(comp_p, index=False)
    return {
        "component_id": target_cid,
        "row_index": int(idx),
        "original_ci_decision_low": orig_val,
        "mutated_ci_decision_low": new_val,
    }


def apply_mutation_4_out_of_bounds_engine_metrics(smoke_dir: Path) -> dict[str, Any]:
    """Mutation 4: Set one engine_metrics.csv coverage value to 12345."""
    em_p = smoke_dir / "engine_metrics.csv"
    df_em = pd.read_csv(em_p)
    if len(df_em) == 0:
        raise ValueError("Mutation 4 engine_metrics.csv is empty")
    orig_val = float(df_em.at[0, "coverage"])
    new_val = 12345.0
    df_em.at[0, "coverage"] = new_val
    df_em.to_csv(em_p, index=False)
    return {
        "row_index": 0,
        "original_coverage": orig_val,
        "mutated_coverage": new_val,
    }


def apply_mutation_5_consistent_contrast(smoke_dir: Path) -> dict[str, Any]:
    """Mutation 5: Add 100 to every replicate in FD001_GBR_global_hcp_cost_improvement
    and update corresponding saved contrast summary consistently using linear quantiles.

    Quantiles used:
    - descriptive: 0.025 and 0.975 (DESCRIPTIVE_QUANTILES)
    - decision: 0.00625 and 0.99375 (DECISION_QUANTILES)
    Recomputes mean and median.
    Asserts saved row matches altered array within numerical tolerance.
    """
    npz_p = smoke_dir / "bootstrap_statistics_FD001.npz"
    data = dict(np.load(npz_p))
    target_key = "FD001_GBR_global_hcp_cost_improvement"
    if target_key not in data:
        raise ValueError(f"Mutation 5 target key {target_key} not in {npz_p}")
    altered_arr = data[target_key] + 100.0
    data[target_key] = altered_arr
    np.savez(npz_p, **data)

    c_p = smoke_dir / "contrast_intervals.csv"
    df_c = pd.read_csv(c_p)
    mask = df_c["contrast_id"] == target_key
    if not any(mask):
        raise ValueError(f"Mutation 5 target contrast {target_key} not in {c_p}")
    idx = df_c[mask].index[0]

    new_mean = float(np.mean(altered_arr))
    new_median = float(np.median(altered_arr))
    ci_95_low = float(np.quantile(altered_arr, q=DESCRIPTIVE_QUANTILES[0], method="linear"))
    ci_95_high = float(np.quantile(altered_arr, q=DESCRIPTIVE_QUANTILES[1], method="linear"))
    ci_decision_low = float(np.quantile(altered_arr, q=DECISION_QUANTILES[0], method="linear"))
    ci_decision_high = float(np.quantile(altered_arr, q=DECISION_QUANTILES[1], method="linear"))

    df_c.at[idx, "mean"] = new_mean
    df_c.at[idx, "median"] = new_median
    df_c.at[idx, "ci_95_low"] = ci_95_low
    df_c.at[idx, "ci_95_high"] = ci_95_high
    df_c.at[idx, "ci_decision_low"] = ci_decision_low
    df_c.at[idx, "ci_decision_high"] = ci_decision_high
    df_c.to_csv(c_p, index=False)

    # Verification assertions: saved summary matches altered array within tolerance
    saved_row = df_c.loc[idx]
    assert math.isclose(float(saved_row["mean"]), new_mean, abs_tol=1e-10)
    assert math.isclose(float(saved_row["median"]), new_median, abs_tol=1e-10)
    assert math.isclose(float(saved_row["ci_95_low"]), ci_95_low, abs_tol=1e-10)
    assert math.isclose(float(saved_row["ci_95_high"]), ci_95_high, abs_tol=1e-10)
    assert math.isclose(float(saved_row["ci_decision_low"]), ci_decision_low, abs_tol=1e-10)
    assert math.isclose(float(saved_row["ci_decision_high"]), ci_decision_high, abs_tol=1e-10)
    assert str(saved_row["status"]) == "DEVELOPMENT_SMOKE_ONLY"
    assert str(saved_row["contrast_id"]) == target_key

    return {
        "contrast_id": target_key,
        "shift": 100.0,
        "mean": new_mean,
        "median": new_median,
        "ci_95_low": ci_95_low,
        "ci_95_high": ci_95_high,
        "ci_decision_low": ci_decision_low,
        "ci_decision_high": ci_decision_high,
        "quantiles_used": {
            "descriptive": [DESCRIPTIVE_QUANTILES[0], DESCRIPTIVE_QUANTILES[1]],
            "decision": [DECISION_QUANTILES[0], DECISION_QUANTILES[1]],
        },
    }


MUTATION_REGISTRY: list[dict[str, Any]] = [
    {
        "mutation_id": "mutation_1",
        "description": "Increase one FD001/GBR/seed-2027 point prediction by 100",
        "target_artifact": "point_predictions.csv",
        "historical_defect": (
            "Historical evidence: Permissive cache check only evaluated seed 2026, "
            "ignoring seeds 2027-2030."
        ),
        "apply_fn": apply_mutation_1_altered_point_prediction,
    },
    {
        "mutation_id": "mutation_2",
        "description": "Delete one FD001/GBR/seed-2026 point-prediction row",
        "target_artifact": "point_predictions.csv",
        "historical_defect": (
            "Historical evidence: Cache check did not fail closed on row count "
            "mismatch across confirmatory seeds."
        ),
        "apply_fn": apply_mutation_2_deleted_point_prediction,
    },
    {
        "mutation_id": "mutation_3",
        "description": (
            "Increase ci_decision_low by 100 for component: RQ1_GBR_global_hcp_cost_improvement"
        ),
        "target_artifact": "component_evidence.csv",
        "historical_defect": (
            "Historical evidence: Verifier only checked schema, nullability, and "
            "failure count safeguards without reference numerical reconstruction."
        ),
        "apply_fn": apply_mutation_3_altered_component_evidence,
    },
    {
        "mutation_id": "mutation_4",
        "description": "Set one engine_metrics.csv coverage value to 12345",
        "target_artifact": "engine_metrics.csv",
        "historical_defect": (
            "Historical evidence: Verifier lacked finite bounds, range, and CSV "
            "schema validation on engine_metrics.csv coverage."
        ),
        "apply_fn": apply_mutation_4_out_of_bounds_engine_metrics,
    },
    {
        "mutation_id": "mutation_5",
        "description": (
            "Add 100 to every replicate in FD001_GBR_global_hcp_cost_improvement "
            "and update contrast intervals accordingly"
        ),
        "target_artifact": "bootstrap_statistics_FD001.npz and contrast_intervals.csv",
        "historical_defect": (
            "Historical evidence: Verifier only checked internal consistency between saved NPZ "
            "and contrast_intervals.csv, accepting arbitrary forged arrays without independent "
            "draw/stat reconstruction."
        ),
        "apply_fn": apply_mutation_5_consistent_contrast,
    },
]


# =============================================================================
# Intended Rejection Check Evaluator
# =============================================================================


def evaluate_mutation_rejection(
    mutation_id: str,
    verifier_result: dict[str, Any],
) -> tuple[bool, str, dict[str, Any]]:
    """Determine whether the verifier's FAIL status was caused by the intended independent check.

    Returns:
        (intended_check_rejected, intended_check_id, check_details)
    """
    if verifier_result.get("status") != "FAIL":
        return (
            False,
            "overall_status",
            {"status": verifier_result.get("status"), "reason": "Expected FAIL"},
        )

    checks = verifier_result.get("checks", {})
    reasons = verifier_result.get("failing_reasons", [])

    if mutation_id == "mutation_1":
        cache_match = checks.get("point_predictions_cache_match", {}).get("match") is False
        ref_recon = (
            checks.get("reference_verification", {})
            .get("checks", {})
            .get("point_prediction_reconstruction", {})
            .get("status")
            == "FAIL"
        )
        has_reason = any("point prediction discrepancy" in r.lower() for r in reasons)
        rejected = (cache_match or ref_recon) and has_reason
        return (
            rejected,
            "point_predictions_cache_match",
            {
                "cache_match_failed": cache_match,
                "ref_recon_failed": ref_recon,
                "has_point_discrepancy_reason": has_reason,
            },
        )

    elif mutation_id == "mutation_2":
        unique_keys = checks.get("point_predictions_unique_keys") is False
        cache_match = checks.get("point_predictions_cache_match", {}).get("match") is False
        ref_recon = (
            checks.get("reference_verification", {})
            .get("checks", {})
            .get("point_prediction_reconstruction", {})
            .get("status")
            == "FAIL"
        )
        has_reason = any(
            "count mismatch" in r.lower() or "mismatches" in r.lower() or "discrepancy" in r.lower()
            for r in reasons
        )
        rejected = (unique_keys or cache_match or ref_recon) and has_reason
        return (
            rejected,
            "point_predictions_count_and_keys",
            {
                "unique_keys_failed": unique_keys,
                "cache_match_failed": cache_match,
                "ref_recon_failed": ref_recon,
                "has_mismatch_reason": has_reason,
            },
        )

    elif mutation_id == "mutation_3":
        comp_recon = (
            checks.get("reference_verification", {})
            .get("checks", {})
            .get("component_evidence_reconstruction", {})
        )
        comp_failed = comp_recon.get("status") == "FAIL"
        has_reason = any("component evidence discrepancies" in r.lower() for r in reasons)
        rejected = comp_failed and has_reason
        return (
            rejected,
            "component_evidence_reconstruction",
            {
                "comp_reconstruction_status": comp_recon.get("status"),
                "has_component_discrepancy_reason": has_reason,
            },
        )

    elif mutation_id == "mutation_4":
        finite_status = checks.get("finite_values_and_bounds", {}).get("status") == "FAIL"
        eng_recon = (
            checks.get("reference_verification", {})
            .get("checks", {})
            .get("engine_metrics_reconstruction", {})
            .get("status")
            == "FAIL"
        )
        has_reason = any(
            "coverage values outside [0, 1]" in r.lower()
            or "engine metrics discrepancies" in r.lower()
            for r in reasons
        )
        rejected = (finite_status or eng_recon) and has_reason
        return (
            rejected,
            "finite_values_and_bounds",
            {
                "finite_check_failed": finite_status,
                "eng_recon_failed": eng_recon,
                "has_bounds_reason": has_reason,
            },
        )

    elif mutation_id == "mutation_5":
        boot_recon = (
            checks.get("reference_verification", {})
            .get("checks", {})
            .get("bootstrap_statistics_npz_reconstruction", {})
        )
        boot_failed = boot_recon.get("status") == "FAIL"
        has_reason = any("bootstrap statistics npz discrepancies" in r.lower() for r in reasons)
        ci_consistent = checks.get("ci_verification", {}).get("match") is True
        rejected = boot_failed and has_reason
        return (
            rejected,
            "bootstrap_statistics_npz_reconstruction",
            {
                "boot_reconstruction_status": boot_recon.get("status"),
                "ci_internal_consistency_passed": ci_consistent,
                "has_boot_discrepancy_reason": has_reason,
            },
        )

    return False, "unknown_mutation", {"reason": f"Unrecognized mutation_id: {mutation_id}"}


# =============================================================================
# Executed Regression Audit Runner
# =============================================================================


def copy_smoke_evidence(src_dir: Path, dst_dir: Path) -> dict[str, str]:
    """Copy all smoke evidence files to destination directory and return file hashes."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for f_name in REQUIRED_SMOKE_FILES:
        src_f = src_dir / f_name
        if not src_f.exists():
            raise FileNotFoundError(f"Required smoke file missing from source: {src_f}")
        dst_f = dst_dir / f_name
        shutil.copy2(src_f, dst_f)
        hashes[f_name] = compute_sha256(dst_f)
    return hashes


def execute_regression_audit(
    source_smoke_dir: Path | str = "experiments/pretest_verification_v3/validation_smoke",
    base_dir: Path | str = ".",
    allow_dirty: bool = False,
    git_info: tuple[str, bool] | None = None,
    env_meta: dict[str, Any] | None = None,
    mutations_to_run: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Execute complete regression audit with baseline verification and isolated mutations.

    1. Verifies unmodified baseline evidence first (must PASS).
    2. Runs each mutation in an isolated temporary directory.
    3. Requires that every mutation fails verification for the intended reason.
    4. Cleans all temporary copies after execution.
    5. Returns structured report containing timestamps, hashes, and mutation details.
    """
    t_start = time.perf_counter()
    time_start_iso = datetime.now(timezone.utc).isoformat()

    base = Path(base_dir).resolve()
    smoke_src = Path(source_smoke_dir)
    if not smoke_src.is_absolute():
        smoke_src = (base / smoke_src).resolve()

    if not smoke_src.exists():
        raise FileNotFoundError(f"Source smoke evidence directory missing: {smoke_src}")

    if git_info is not None:
        git_sha, git_dirty = git_info
    else:
        git_sha, git_dirty = get_git_info(allow_dirty=allow_dirty, repo_root=base)
    if env_meta is None:
        env_meta = capture_environment_metadata(device="cpu")

    # Record source evidence hashes
    source_hashes = {
        f_name: compute_sha256(smoke_src / f_name)
        for f_name in REQUIRED_SMOKE_FILES
        if (smoke_src / f_name).exists()
    }

    # Step 1: Baseline Verification on unmodified evidence
    t0_base = time.perf_counter()
    baseline_verifier_result = verify_validation_smoke_matrix(smoke_dir=smoke_src, base_dir=base)
    t1_base = time.perf_counter()
    baseline_status = baseline_verifier_result.get("status")
    baseline_match = baseline_verifier_result.get("overall_match") is True
    baseline_elapsed = round(t1_base - t0_base, 3)

    baseline_record = {
        "status": baseline_status,
        "overall_match": baseline_match,
        "elapsed_seconds": baseline_elapsed,
        "failing_reasons": baseline_verifier_result.get("failing_reasons", []),
    }

    if baseline_status != "PASS" or not baseline_match:
        time_end_iso = datetime.now(timezone.utc).isoformat()
        return {
            "protocol_version": PROTOCOL_VERSION,
            "schema_version": REGRESSION_REPORT_SCHEMA_VERSION,
            "timestamp_start_utc": time_start_iso,
            "timestamp_end_utc": time_end_iso,
            "elapsed_seconds": round(time.perf_counter() - t_start, 3),
            "git_commit": git_sha,
            "git_dirty": git_dirty,
            "environment": env_meta,
            "source_evidence_hashes": source_hashes,
            "baseline_verification": baseline_record,
            "mutations": [],
            "mutations_evaluated": 0,
            "mutations_rejected": 0,
            "overall_status": "FAIL",
            "status": "FAIL",
            "failure_summary": (
                "Unmodified baseline evidence verification failed; regression suite aborted."
            ),
        }

    # Step 2: Isolated Mutation Execution
    mutations_spec = mutations_to_run if mutations_to_run is not None else MUTATION_REGISTRY
    mutation_records: list[dict[str, Any]] = []

    for mut in mutations_spec:
        m_id = mut["mutation_id"]
        m_desc = mut["description"]
        m_target = mut["target_artifact"]
        m_defect = mut.get("historical_defect", "Historical defect")
        apply_fn: Callable[[Path], dict[str, Any]] = mut["apply_fn"]

        t0_m = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix=f"regression_{m_id}_") as tmp_dir:
            tmp_smoke = Path(tmp_dir) / "validation_smoke"
            copy_smoke_evidence(smoke_src, tmp_smoke)

            # Apply mutation
            mut_info = apply_fn(tmp_smoke)

            # Run verifier on mutated copy
            ver_res = verify_validation_smoke_matrix(smoke_dir=tmp_smoke, base_dir=base)
            t1_m = time.perf_counter()

            # Evaluate intended check rejection
            rejected, check_id, check_details = evaluate_mutation_rejection(m_id, ver_res)

            mutation_records.append(
                {
                    "mutation_id": m_id,
                    "description": m_desc,
                    "target_artifact": m_target,
                    "historical_defect": m_defect,
                    "verifier_status": ver_res.get("status"),
                    "repaired_status": ver_res.get("status"),
                    "rejection_confirmed": rejected,
                    "intended_check_id": check_id,
                    "intended_check_rejected": rejected,
                    "intended_check_details": check_details,
                    "failing_reasons": ver_res.get("failing_reasons", []),
                    "mutation_applied_details": mut_info,
                    "elapsed_seconds": round(t1_m - t0_m, 3),
                }
            )

    time_end_iso = datetime.now(timezone.utc).isoformat()
    total_elapsed = round(time.perf_counter() - t_start, 3)

    evaluated_count = len(mutation_records)
    rejected_count = sum(1 for m in mutation_records if m.get("rejection_confirmed") is True)

    overall_pass = (
        baseline_record["status"] == "PASS"
        and evaluated_count == 5
        and rejected_count == 5
        and len({m["mutation_id"] for m in mutation_records}) == 5
    )

    report = {
        "protocol_version": PROTOCOL_VERSION,
        "schema_version": REGRESSION_REPORT_SCHEMA_VERSION,
        "timestamp_start_utc": time_start_iso,
        "timestamp_end_utc": time_end_iso,
        "elapsed_seconds": total_elapsed,
        "git_commit": git_sha,
        "git_dirty": git_dirty,
        "environment": env_meta,
        "source_evidence_hashes": source_hashes,
        "baseline_verification": baseline_record,
        "mutations_evaluated": evaluated_count,
        "mutations_rejected": rejected_count,
        "records": mutation_records,
        "mutations": mutation_records,
        "overall_status": "PASS" if overall_pass else "FAIL",
        "status": "PASS" if overall_pass else "FAIL",
    }
    return report
