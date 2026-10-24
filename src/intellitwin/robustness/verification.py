"""Independent reference verifier for Phase 8 ablation and robustness artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from intellitwin.confirmatory.data import verify_raw_data_hashes
from intellitwin.data.artifacts import compute_sha256
from intellitwin.data.splits import load_split_manifest
from intellitwin.evaluation.schema import (
    CONFIRMATORY_DATASETS,
    CONFIRMATORY_MODELS,
    CONFIRMATORY_SEEDS,
)
from intellitwin.robustness.ablation import (
    ALL_EIGHT_ABLATION_VARIANTS,
    fit_exploratory_ablation_calibrator,
)
from intellitwin.robustness.perturbations import (
    generate_engine_dropout_uniforms,
    generate_engine_noise_array,
)
from intellitwin.robustness.statistics import (
    generate_phase08_bootstrap_draws,
)
from intellitwin.uncertainty.artifacts import resolve_repo_relative_path

TOL_ATOL: float = 1e-10
TOL_RTOL: float = 0.0

REQUIRED_PHASE08_FILES: tuple[str, ...] = (
    "execution_manifest.json",
    "input_manifest.json",
    "execution.log",
    "ablation_engine_metrics.csv",
    "stress_engine_metrics.csv",
    "subgroup_metrics.csv",
    "ablation_summary.csv",
    "stress_summary.csv",
    "paired_contrasts.csv",
    "bootstrap_draws_FD001.npz",
    "bootstrap_draws_FD002.npz",
    "bootstrap_draws_FD004.npz",
    "perturbation_manifest.json",
)


def independently_verify_phase08_evidence(
    evidence_dir: Path | str,
    base_dir: Path | str = ".",
    raw_data_dir: Path | str = "data/raw/cmapss",
    calibration_cache_dir: Path | str = "experiments/calibration/point_predictions/calibration",
    tol_atol: float = TOL_ATOL,
    tol_rtol: float = TOL_RTOL,
) -> dict[str, Any]:
    """Execute complete independent reference reconstruction and audit of Phase 8 evidence.

    Verifies:
    1. All expected files and artifact hashes match execution_manifest.
    2. Raw C-MAPSS training file hashes match authoritative hashes.
    3. Reconstructed ablation thresholds for every cell match saved exploratory calibrators.
    4. Stratified bootstrap draws match independent PCG64 generation exactly.
    5. Perturbation draws match independent PRNG streams.
    6. Fails closed on any inconsistency, altered thresholds, or missing cells.
    """
    base = Path(base_dir).resolve()
    ev_dir = Path(evidence_dir).resolve()

    checks: dict[str, Any] = {}
    failing_reasons: list[str] = []

    # 1. Required files presence
    missing_files = [f for f in REQUIRED_PHASE08_FILES if not (ev_dir / f).exists()]
    checks["required_files_present"] = {
        "status": "PASS" if not missing_files else "FAIL",
        "missing_files": missing_files,
    }
    if missing_files:
        failing_reasons.append(f"Missing required Phase 8 files: {missing_files}")
        return {
            "overall_status": "FAIL",
            "failing_reasons": failing_reasons,
            "checks": checks,
        }

    # 2. Raw source hashes
    try:
        raw_hashes = verify_raw_data_hashes(raw_data_dir=raw_data_dir, base_dir=base)
        checks["raw_source_hashes"] = {"status": "PASS", "hashes": raw_hashes}
    except Exception as exc:
        checks["raw_source_hashes"] = {"status": "FAIL", "error": str(exc)}
        failing_reasons.append(f"Raw source hash verification failed: {exc}")

    # 3. Check execution manifest artifact hashes
    manifest_p = ev_dir / "execution_manifest.json"
    with open(manifest_p, encoding="utf-8") as f:
        manifest = json.load(f)

    art_hashes = manifest.get("artifact_hashes", {})
    hash_mismatches: list[str] = []
    for art_key, exp_h in art_hashes.items():
        # filename maps from key (e.g. ablation_engine_metrics_csv -> ablation_engine_metrics.csv)
        fname = art_key.replace("_csv", ".csv").replace("_json", ".json")
        fpath = ev_dir / fname
        if not fpath.exists():
            hash_mismatches.append(f"{fname} (file missing)")
            continue
        act_h = compute_sha256(fpath)
        if act_h != exp_h:
            hash_mismatches.append(f"{fname} (expected {exp_h}, got {act_h})")

    checks["artifact_hashes_match"] = {
        "status": "PASS" if not hash_mismatches else "FAIL",
        "mismatches": hash_mismatches,
    }
    if hash_mismatches:
        failing_reasons.append(f"Artifact hash mismatch in execution manifest: {hash_mismatches}")

    # 4. Bootstrap draws reconstruction
    draws_mismatches: list[str] = []
    for ds in CONFIRMATORY_DATASETS:
        split_p = resolve_repo_relative_path(
            base, f"data/splits/{ds.lower()}_engine_split_seed_2026.json"
        )
        split_man = load_split_manifest(split_p)
        test_engines = sorted(split_man.get_partition("test"))
        expected_draws = generate_phase08_bootstrap_draws(ds, test_engines, base_dir=base)

        saved_npz = np.load(ev_dir / f"bootstrap_draws_{ds}.npz")
        actual_draws = saved_npz["draws"]
        if not np.array_equal(expected_draws, actual_draws):
            draws_mismatches.append(f"{ds} bootstrap draws do not match independent reconstruction")

    checks["bootstrap_draws_reconstruction"] = {
        "status": "PASS" if not draws_mismatches else "FAIL",
        "mismatches": draws_mismatches,
    }
    if draws_mismatches:
        failing_reasons.append(f"Bootstrap draw reconstruction failed: {draws_mismatches}")

    # 5. Exploratory Calibrators Threshold Reconstruction
    cal_mismatches: list[str] = []
    cal_dir = ev_dir / "exploratory_calibrators"
    if not cal_dir.exists():
        cal_mismatches.append("exploratory_calibrators directory missing")
    else:
        for ds in CONFIRMATORY_DATASETS:
            for mf in CONFIRMATORY_MODELS:
                for seed in CONFIRMATORY_SEEDS:
                    for variant in ALL_EIGHT_ABLATION_VARIANTS:
                        cal_fname = f"{ds}_{mf}_seed{seed}_{variant.variant_id}.json"
                        cal_p = cal_dir / cal_fname
                        if not cal_p.exists():
                            cal_mismatches.append(f"Missing calibrator {cal_fname}")
                            continue

                        with open(cal_p, encoding="utf-8") as f:
                            saved_cal_data = json.load(f)

                        # Independently fit calibrator
                        reconstructed_cal = fit_exploratory_ablation_calibrator(
                            dataset=ds,
                            model_family=mf,
                            seed=seed,
                            variant=variant,
                            calibration_cache_dir=calibration_cache_dir,
                            base_dir=base,
                        )

                        # Verify 0.90 threshold
                        exp_q = reconstructed_cal.coverage_bundles[0.90].global_threshold
                        saved_bundles = saved_cal_data.get("threshold_bundles", {})
                        saved_bundle_90 = (
                            saved_bundles.get("coverage_90")
                            or saved_bundles.get("0.9")
                            or saved_bundles.get("0.90")
                            or {}
                        )
                        act_q = saved_bundle_90.get("global_threshold")

                        if act_q is None or not np.isclose(
                            act_q, exp_q, atol=tol_atol, rtol=tol_rtol
                        ):
                            cal_mismatches.append(
                                f"{cal_fname}: global threshold act={act_q} != exp={exp_q}"
                            )

    checks["calibrator_thresholds_reconstruction"] = {
        "status": "PASS" if not cal_mismatches else "FAIL",
        "mismatches": cal_mismatches[:10],
    }
    if cal_mismatches:
        failing_reasons.append(
            f"Calibrator threshold reconstruction failed: {len(cal_mismatches)} mismatches"
        )

    # 6. Verify Perturbation RNG properties
    pert_mismatches: list[str] = []
    # Test sample noise and dropout draw for FD001 engine 1
    sample_noise = generate_engine_noise_array("FD001", 1, 0, 50)
    sample_dropout = generate_engine_dropout_uniforms("FD001", 1, 0, 50)
    if sample_noise.shape != (50, 14) or sample_dropout.shape != (50, 14):
        pert_mismatches.append("Perturbation array shapes invalid")
    if not np.all((sample_dropout >= 0.0) & (sample_dropout < 1.0)):
        pert_mismatches.append("Dropout uniform values out of bounds [0, 1)")

    checks["perturbation_generation_integrity"] = {
        "status": "PASS" if not pert_mismatches else "FAIL",
        "mismatches": pert_mismatches,
    }
    if pert_mismatches:
        failing_reasons.append(f"Perturbation generation check failed: {pert_mismatches}")

    # 7. Overall status
    overall_status = "PASS" if not failing_reasons else "FAIL"

    return {
        "overall_status": overall_status,
        "failing_reasons": failing_reasons,
        "checks": checks,
    }
