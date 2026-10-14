"""Independent verification and reconstruction machinery for Step 8 calibration."""

from __future__ import annotations

import json
import math
import subprocess
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from intellitwin.data.artifacts import compute_sha256
from intellitwin.data.loader import load_cmapss_run_to_failure
from intellitwin.data.schema import EXPECTED_ENGINE_COUNTS, LIFECYCLE_STAGES, get_lifecycle_stage
from intellitwin.data.splits import load_split_manifest
from intellitwin.models.registry import (
    EXPECTED_DATASETS,
    EXPECTED_FAMILIES,
    EXPECTED_SEEDS,
)
from intellitwin.uncertainty.artifacts import (
    INTERVAL_PREDICTION_COLUMNS,
    POINT_PREDICTION_COLUMNS,
    load_calibrator_from_artifact,
    resolve_repo_relative_path,
)
from intellitwin.uncertainty.calibration import (
    DATASET_VOCABULARY,
    get_min_engines_required,
)
from intellitwin.uncertainty.metrics import compute_engine_weighted_interval_metrics
from intellitwin.uncertainty.schema import (
    COVERAGE_FRACTIONS,
    METHOD_DECISION_AWARE,
    NOMINAL_COVERAGES,
    SUPPORTED_METHODS,
    CandidateConfig,
)
from intellitwin.uncertainty.scores import (
    compute_absolute_residual_score,
    compute_decision_aware_score,
)
from intellitwin.uncertainty.selection import (
    run_leave_one_engine_out_evaluation,
    select_winning_candidate,
)


def compute_independent_reference_hierarchical_quantile(
    engine_ids: np.ndarray[Any, Any],
    endpoint_cycles: np.ndarray[Any, Any],
    scores: np.ndarray[Any, Any],
    nominal_coverage: float,
) -> float:
    """Independent reference calculation for hierarchical conformal quantile threshold.

    Computes sorted weighted scores and exact Fraction checks at the selected score
    and its preceding distinct score, strictly avoiding calls to the production quantile.
    """
    eids = np.asarray(engine_ids)
    cycles = np.asarray(endpoint_cycles)
    sc = np.asarray(scores, dtype=np.float64)

    if len(sc) == 0:
        raise ValueError("Cannot compute quantiles on empty input.")
    if not (len(eids) == len(cycles) == len(sc)):
        raise ValueError("Array length mismatch in reference quantile calculation.")

    target_frac = COVERAGE_FRACTIONS.get(nominal_coverage)
    if target_frac is None:
        raise ValueError(f"Unsupported nominal coverage: {nominal_coverage}")

    engine_scores: dict[int, list[float]] = defaultdict(list)
    for eid, score_val in zip(eids, sc, strict=True):
        engine_scores[int(eid)].append(float(score_val))

    m = len(engine_scores)
    if m == 0:
        raise ValueError("Zero contributing engines.")

    n_i = {eid: len(vals) for eid, vals in engine_scores.items()}
    required_sum = Fraction(m + 1) * target_frac

    # Finite support check
    if Fraction(m) < required_sum:
        return float("inf")

    sorted_engine_scores = {
        eid: np.sort(np.asarray(vals, dtype=np.float64)) for eid, vals in engine_scores.items()
    }

    obs_scores = np.asarray(sc, dtype=np.float64)
    obs_weights = np.array([1.0 / n_i[int(eid)] for eid in eids], dtype=np.float64)
    sort_idx = np.argsort(obs_scores)
    sorted_s = obs_scores[sort_idx]
    sorted_w = obs_weights[sort_idx]

    unique_scores, group_indices = np.unique(sorted_s, return_index=True)
    cum_w = np.cumsum(sorted_w)
    last_indices = np.empty_like(group_indices)
    last_indices[:-1] = group_indices[1:] - 1
    last_indices[-1] = len(sorted_s) - 1
    unique_cum_w = cum_w[last_indices]

    def exact_mass(q_val: float) -> Fraction:
        tot = Fraction(0, 1)
        for eid, vals in sorted_engine_scores.items():
            cnt = int(np.searchsorted(vals, q_val, side="right"))
            tot += Fraction(cnt, n_i[eid])
        return tot

    req_float = float(required_sum)
    cand_idx = int(np.searchsorted(unique_cum_w, req_float - 1e-11))
    if cand_idx >= len(unique_scores):
        cand_idx = len(unique_scores) - 1

    while (
        cand_idx < len(unique_scores) and exact_mass(float(unique_scores[cand_idx])) < required_sum
    ):
        cand_idx += 1
    while cand_idx > 0 and exact_mass(float(unique_scores[cand_idx - 1])) >= required_sum:
        cand_idx -= 1

    if cand_idx >= len(unique_scores):
        return float("inf")

    # Verify exact boundary property
    assert exact_mass(float(unique_scores[cand_idx])) >= required_sum, "Reference boundary failed"
    if cand_idx > 0:
        assert exact_mass(float(unique_scores[cand_idx - 1])) < required_sum, (
            "Reference boundary failed"
        )

    return float(unique_scores[cand_idx])


def verify_registry_structure_and_hashes(
    registry_path: Path | str,
    base_dir: Path | str = ".",
) -> dict[str, Any]:
    """Verify registry completeness (90 entries, 270 bundles) and SHA-256 integrity."""
    base = Path(base_dir).resolve()
    reg_p = (
        resolve_repo_relative_path(base, registry_path)
        if not Path(registry_path).is_absolute()
        else Path(registry_path)
    )
    if not reg_p.exists():
        raise FileNotFoundError(f"Registry not found: {reg_p}")

    with open(reg_p, encoding="utf-8") as f:
        registry_data = json.load(f)

    entries = registry_data.get("entries", {})
    expected_identities = set()
    for ds in EXPECTED_DATASETS:
        for fam in EXPECTED_FAMILIES:
            for seed in EXPECTED_SEEDS:
                for method in SUPPORTED_METHODS:
                    expected_identities.add(f"{ds}_{fam}_seed{seed}_{method}")

    if len(entries) != 90:
        raise ValueError(f"Expected exactly 90 registry entries, got {len(entries)}")
    if set(entries.keys()) != expected_identities:
        raise ValueError("Registry entry keys do not match expected Cartesian product")

    total_bundles = 0
    for bundle_id, entry in entries.items():
        if entry.get("bundle_id") != bundle_id:
            raise ValueError(f"Mismatched bundle_id in entry: {bundle_id}")
        covs = entry.get("coverage_levels", [])
        if sorted(covs) != [0.8, 0.9, 0.95]:
            raise ValueError(f"Invalid coverage levels for {bundle_id}: {covs}")
        total_bundles += len(covs)

        art_p = resolve_repo_relative_path(base, entry["calibrator_artifact_path"])
        if not art_p.exists():
            raise FileNotFoundError(f"Calibrator artifact missing: {art_p}")
        disk_hash = compute_sha256(art_p)
        if disk_hash != entry["artifact_sha256"]:
            raise ValueError(f"Calibrator artifact hash mismatch for {bundle_id}")

        # Check declared dependencies
        ds = entry["dataset"]
        fam = entry["model_family"]
        seed = entry["seed"]
        ckpt_p = resolve_repo_relative_path(
            base, f"experiments/base_models/{ds}/{fam}/seed_{seed}/checkpoint"
        )
        prep_p = resolve_repo_relative_path(
            base, f"experiments/preprocessing/{ds}/preprocessor.json"
        )
        split_p = resolve_repo_relative_path(
            base, f"data/splits/{ds.lower()}_engine_split_seed_2026.json"
        )
        if compute_sha256(ckpt_p) != entry["checkpoint_sha256"]:
            raise ValueError(f"Checkpoint hash mismatch for {bundle_id}")
        if compute_sha256(prep_p) != entry["preprocessor_sha256"]:
            raise ValueError(f"Preprocessor hash mismatch for {bundle_id}")
        if compute_sha256(split_p) != entry["split_manifest_sha256"]:
            raise ValueError(f"Split hash mismatch for {bundle_id}")

    return {
        "status": "PASS",
        "total_entries": len(entries),
        "total_coverage_bundles": total_bundles,
    }


def verify_prediction_cache_membership(
    base_dir: Path | str = ".",
    raw_data_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Verify validation and calibration prediction caches for membership and completeness."""
    base = Path(base_dir).resolve()
    cal_base = base / "experiments" / "calibration" / "point_predictions"

    cache_details: dict[str, Any] = {}

    for partition in ("validation", "calibration"):
        for ds in EXPECTED_DATASETS:
            split_p = resolve_repo_relative_path(
                base, f"data/splits/{ds.lower()}_engine_split_seed_2026.json"
            )
            split_data = load_split_manifest(split_p)
            expected_engines = set(split_data.get_partition(partition))
            train_engines = set(split_data.get_partition("train"))
            test_engines = set(split_data.get_partition("test"))
            allowed_regimes = set(DATASET_VOCABULARY[ds])

            raw_trajectories: dict[int, int] = {}
            if raw_data_dir is not None:
                raw_txt = resolve_repo_relative_path(base, Path(raw_data_dir) / f"train_{ds}.txt")
                if raw_txt.exists():
                    raw_df = load_cmapss_run_to_failure(
                        path=raw_txt,
                        dataset_name=ds,
                        expected_engine_count=EXPECTED_ENGINE_COUNTS[ds],
                    )
                    for uid, grp in raw_df.groupby("unit"):
                        raw_trajectories[int(uid)] = int(grp["cycle"].max())

            baseline_keys: list[tuple[int, int]] | None = None
            baseline_regimes: list[str] | None = None
            baseline_stages: list[str] | None = None

            for fam in EXPECTED_FAMILIES:
                for seed in EXPECTED_SEEDS:
                    cache_p = cal_base / partition / ds / fam / f"seed_{seed}.csv"
                    if not cache_p.exists():
                        raise FileNotFoundError(f"Missing prediction cache: {cache_p}")

                    df = pd.read_csv(cache_p)
                    for col in POINT_PREDICTION_COLUMNS:
                        if col not in df.columns:
                            raise ValueError(f"Missing column '{col}' in {cache_p}")

                    cache_units = set(df["unit"].astype(int))
                    if cache_units != expected_engines:
                        raise ValueError(f"Engine set mismatch in {cache_p}")
                    if cache_units.intersection(train_engines):
                        raise ValueError(f"Train engines leaked into {cache_p}")
                    if cache_units.intersection(test_engines):
                        raise ValueError(f"Test engines leaked into {cache_p}")

                    preds = df["prediction"].to_numpy()
                    if not np.all(np.isfinite(preds)):
                        raise ValueError(f"Non-finite predictions in {cache_p}")
                    if np.any(preds < 0.0):
                        raise ValueError(f"Negative predictions in {cache_p}")

                    for reg in df["regime"]:
                        if str(reg) not in allowed_regimes:
                            raise ValueError(f"Invalid regime '{reg}' in {cache_p}")
                    for stg in df["lifecycle_stage"]:
                        if str(stg) not in LIFECYCLE_STAGES:
                            raise ValueError(f"Invalid lifecycle stage '{stg}' in {cache_p}")

                    # Verify trajectory completeness per engine
                    for uid, grp in df.groupby("unit"):
                        u_int = int(uid)
                        cycles = grp["endpoint_cycle"].to_numpy()
                        if len(cycles) != len(set(cycles)):
                            raise ValueError(f"Duplicate cycles for unit {u_int} in {cache_p}")
                        min_c = int(np.min(cycles))
                        max_c = int(np.max(cycles))
                        if min_c != 30:
                            raise ValueError(
                                f"Unit {u_int} does not start at cycle 30 in {cache_p}"
                            )

                        T = raw_trajectories.get(u_int, max_c)
                        if max_c != T:
                            raise ValueError(
                                f"Unit {u_int} terminal cycle {max_c} != expected {T} in {cache_p}"
                            )
                        expected_c = set(range(30, T + 1))
                        if set(cycles) != expected_c:
                            raise ValueError(
                                f"Missing or extra cycles for unit {u_int} in {cache_p}"
                            )

                        # Check labels
                        rul_true = grp["rul_true"].to_numpy()
                        rul_target = grp["rul_target"].to_numpy()
                        expected_true = T - cycles
                        expected_target = np.minimum(expected_true, 125)
                        if not np.array_equal(rul_true, expected_true):
                            raise ValueError(f"rul_true mismatch for unit {u_int} in {cache_p}")
                        if not np.array_equal(rul_target, expected_target):
                            raise ValueError(f"rul_target mismatch for unit {u_int} in {cache_p}")

                        # Check stages
                        stages = grp["lifecycle_stage"].to_numpy()
                        for c, stg in zip(cycles, stages, strict=True):
                            exp_stg = get_lifecycle_stage(int(c), T)
                            if stg != exp_stg:
                                raise ValueError(
                                    f"Lifecycle stage mismatch for unit {u_int} at cycle {c}"
                                )

                    keys = list(zip(df["unit"], df["endpoint_cycle"], strict=True))
                    reg_list = list(df["regime"])
                    stg_list = list(df["lifecycle_stage"])
                    if baseline_keys is None:
                        baseline_keys = keys
                        baseline_regimes = reg_list
                        baseline_stages = stg_list
                    else:
                        if keys != baseline_keys:
                            raise ValueError(f"Endpoint keys mismatch across seeds in {cache_p}")
                        if reg_list != baseline_regimes:
                            raise ValueError(f"Regimes mismatch across seeds in {cache_p}")
                        if stg_list != baseline_stages:
                            raise ValueError(f"Stages mismatch across seeds in {cache_p}")

            cache_details[f"{partition}_{ds}"] = {
                "engine_count": len(expected_engines),
                "total_rows": len(baseline_keys) if baseline_keys else 0,
                "status": "PASS",
            }

    return {"status": "PASS", "details": cache_details}


def verify_selection_freeze_reconstruction(
    base_dir: Path | str = ".",
) -> dict[str, Any]:
    """Verify selection freeze manifest and reconstruct selection from validation caches."""
    base = Path(base_dir).resolve()
    freeze_p = resolve_repo_relative_path(
        base, "experiments/calibration/selection/selection_freeze.json"
    )
    if not freeze_p.exists():
        raise FileNotFoundError(f"Selection freeze manifest missing: {freeze_p}")

    with open(freeze_p, encoding="utf-8") as f:
        freeze_data = json.load(f)

    # 1. Verify freeze commit exists in git
    freeze_commit = freeze_data.get("git_commit")
    if not freeze_commit:
        raise ValueError("Selection freeze manifest missing git_commit")
    try:
        subprocess.run(
            ["git", "cat-file", "-e", freeze_commit],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"Selection freeze commit {freeze_commit} not found in Git: {exc}"
        ) from exc

    # 2. Verify model registry and config hashes
    model_reg_p = resolve_repo_relative_path(base, "experiments/base_models/model_registry.json")
    if compute_sha256(model_reg_p) != freeze_data.get("model_registry_sha256"):
        raise ValueError("Model registry hash mismatch against selection freeze manifest")

    # 3. Verify selection record hashes and reconstruct leave-one-engine-out selection
    selected_cells = freeze_data.get("selected_cells", {})
    reconstruction_log: dict[str, Any] = {}

    for ds in EXPECTED_DATASETS:
        for fam in EXPECTED_FAMILIES:
            cell_key = f"{ds}_{fam}"
            cell_info = selected_cells.get(cell_key)
            if cell_info is None:
                raise KeyError(f"Cell {cell_key} missing in selection freeze")

            sel_dir = resolve_repo_relative_path(
                base, f"experiments/calibration/selection/{ds}/{fam}"
            )
            sel_json_p = sel_dir / "selection.json"
            if compute_sha256(sel_json_p) != cell_info["selection_json_sha256"]:
                raise ValueError(f"selection.json hash mismatch for {cell_key}")

            with open(sel_json_p, encoding="utf-8") as f:
                saved_sel = json.load(f)

            if saved_sel["selected_candidate_id"] != cell_info["selected_candidate_id"]:
                raise ValueError(f"Candidate ID mismatch for {cell_key}")
            if saved_sel["selection_status"] != cell_info["selection_status"]:
                raise ValueError(f"Selection status mismatch for {cell_key}")

            # Reconstruct selection from 5-seed validation caches
            dfs = []
            for seed in EXPECTED_SEEDS:
                p_cache = (
                    base
                    / "experiments"
                    / "calibration"
                    / "point_predictions"
                    / "validation"
                    / ds
                    / fam
                    / f"seed_{seed}.csv"
                )
                df_s = pd.read_csv(p_cache)
                df_s["seed"] = seed
                dfs.append(df_s)

            df_cell = pd.concat(dfs, ignore_index=True)
            re_aggs, re_records, re_regime, re_folds = run_leave_one_engine_out_evaluation(df_cell)
            re_winner, re_status, re_log = select_winning_candidate(re_aggs)

            if re_winner.candidate_id != cell_info["selected_candidate_id"]:
                raise ValueError(
                    f"Selection reconstruction mismatch for {cell_key}: "
                    f"reconstructed {re_winner.candidate_id} "
                    f"!= frozen {cell_info['selected_candidate_id']}"
                )
            if re_status != cell_info["selection_status"]:
                raise ValueError(
                    f"Selection status mismatch for {cell_key}: "
                    f"reconstructed {re_status} != frozen {cell_info['selection_status']}"
                )

            # Compare saved candidate summary metrics
            cand_summary_p = sel_dir / "candidate_summary.csv"
            df_saved_summary = pd.read_csv(cand_summary_p)
            for _, row in df_saved_summary.iterrows():
                cid = row["candidate_id"]
                re_c = re_aggs[cid]
                if abs(float(row["mean_cost"]) - re_c.mean_cost) > 1e-10:
                    raise ValueError(f"Mean cost mismatch for {cell_key} candidate {cid}")
                if abs(float(row["marginal_picp"]) - re_c.marginal_picp) > 1e-10:
                    raise ValueError(f"Marginal PICP mismatch for {cell_key} candidate {cid}")
                if abs(float(row["mpiw"]) - re_c.mpiw) > 1e-10:
                    raise ValueError(f"MPIW mismatch for {cell_key} candidate {cid}")
                if abs(float(row["interval_score"]) - re_c.interval_score) > 1e-10:
                    raise ValueError(f"Interval score mismatch for {cell_key} candidate {cid}")
                if bool(row["is_feasible"]) != re_c.is_feasible:
                    raise ValueError(f"Feasibility mismatch for {cell_key} candidate {cid}")

            re_winner_agg = re_aggs[re_winner.candidate_id]
            reconstruction_log[cell_key] = {
                "selected_candidate_id": re_winner.candidate_id,
                "selection_status": re_status,
                "mean_cost": re_winner_agg.mean_cost,
                "marginal_picp": re_winner_agg.marginal_picp,
                "mpiw": re_winner_agg.mpiw,
                "status": "EXACT_MATCH",
            }

    return {"status": "PASS", "details": reconstruction_log}


def verify_all_calibrator_quantiles_and_intervals(
    base_dir: Path | str = ".",
) -> dict[str, Any]:
    """Verify all 90 calibrator thresholds with reference calculation, intervals, metrics."""
    base = Path(base_dir).resolve()
    reg_p = resolve_repo_relative_path(base, "experiments/calibration/calibration_registry.json")

    with open(reg_p, encoding="utf-8") as f:
        registry_data = json.load(f)

    entries = registry_data.get("entries", {})
    val_summary_p = resolve_repo_relative_path(
        base, "experiments/calibration/validation_summary.csv"
    )
    if not val_summary_p.exists():
        raise FileNotFoundError(f"Missing validation summary artifact: {val_summary_p}")

    threshold_diffs: list[float] = []
    metric_diffs: list[float] = []

    for bundle_id, entry in entries.items():
        ds = entry["dataset"]
        fam = entry["model_family"]
        seed = entry["seed"]
        method_id = entry["method_id"]

        cal_cache_p = (
            base
            / "experiments"
            / "calibration"
            / "point_predictions"
            / "calibration"
            / ds
            / fam
            / f"seed_{seed}.csv"
        )
        df_cal = pd.read_csv(cal_cache_p)

        art_p = resolve_repo_relative_path(base, entry["calibrator_artifact_path"])
        with open(art_p, encoding="utf-8") as f:
            art_data = json.load(f)
        saved_cal = load_calibrator_from_artifact(art_data)

        # 1. Independent threshold reconstruction
        cand_obj = (
            CandidateConfig.from_id(entry["selected_candidate_id"])
            if entry.get("selected_candidate_id")
            else None
        )

        preds_cal = df_cal["prediction"].to_numpy()
        labels_cal = df_cal["rul_true"].to_numpy()
        regimes_cal = df_cal["regime"].to_numpy()
        eids_cal = df_cal["unit"].to_numpy()
        cycles_cal = df_cal["endpoint_cycle"].to_numpy()

        if method_id == METHOD_DECISION_AWARE:
            assert cand_obj is not None
            scores_cal = compute_decision_aware_score(
                predictions=preds_cal,
                labels=labels_cal,
                candidate=cand_obj,
            )
        else:
            scores_cal = compute_absolute_residual_score(preds_cal, labels_cal)

        for cov in NOMINAL_COVERAGES:
            saved_bundle = saved_cal.coverage_bundles[cov]

            # Reconstruct global threshold with independent reference function
            ref_global_q = compute_independent_reference_hierarchical_quantile(
                engine_ids=eids_cal,
                endpoint_cycles=cycles_cal,
                scores=scores_cal,
                nominal_coverage=cov,
            )
            diff_glob = abs(ref_global_q - saved_bundle.global_threshold)
            threshold_diffs.append(diff_glob)
            if diff_glob > 1e-10:
                raise ValueError(
                    f"Global threshold mismatch in {bundle_id} at coverage {cov}: "
                    f"{diff_glob:.6e} > 1e-10"
                )

            # Reconstruct regime thresholds
            min_engines = get_min_engines_required(cov)
            for reg, r_rec in saved_bundle.regime_thresholds.items():
                reg_mask = regimes_cal == reg
                m_reg = len(np.unique(eids_cal[reg_mask])) if np.any(reg_mask) else 0

                if m_reg < min_engines:
                    ref_reg_q = ref_global_q
                    expected_fallback = True
                    expected_reason = f"Insufficient contributing engines ({m_reg} < {min_engines})"
                else:
                    ref_reg_q = compute_independent_reference_hierarchical_quantile(
                        engine_ids=eids_cal[reg_mask],
                        endpoint_cycles=cycles_cal[reg_mask],
                        scores=scores_cal[reg_mask],
                        nominal_coverage=cov,
                    )
                    if math.isinf(ref_reg_q):
                        ref_reg_q = ref_global_q
                        expected_fallback = True
                        expected_reason = "Hierarchical finite mass exceeded; threshold infinite"
                    else:
                        expected_fallback = False
                        expected_reason = None

                if r_rec.fallback_used != expected_fallback:
                    raise ValueError(
                        f"Fallback flag mismatch for regime {reg} in {bundle_id} at {cov}: "
                        f"saved {r_rec.fallback_used} != expected {expected_fallback}"
                    )
                if r_rec.fallback_reason != expected_reason:
                    raise ValueError(
                        f"Fallback reason mismatch for regime {reg} in {bundle_id} at {cov}: "
                        f"saved '{r_rec.fallback_reason}' != expected '{expected_reason}'"
                    )
                diff_reg = abs(ref_reg_q - r_rec.threshold)
                threshold_diffs.append(diff_reg)
                if diff_reg > 1e-10:
                    raise ValueError(
                        f"Regime {reg} threshold mismatch in {bundle_id} at coverage {cov}: "
                        f"{diff_reg:.6e} > 1e-10"
                    )

        # 2. Saved interval predictions reconstruction & comparison
        val_cache_p = (
            base
            / "experiments"
            / "calibration"
            / "point_predictions"
            / "validation"
            / ds
            / fam
            / f"seed_{seed}.csv"
        )
        df_val = pd.read_csv(val_cache_p)

        saved_interval_p = (
            base
            / "experiments"
            / "calibration"
            / "validation"
            / ds
            / fam
            / f"seed_{seed}"
            / method_id
            / "interval_predictions.csv"
        )
        df_saved_intervals = pd.read_csv(saved_interval_p)
        for col in INTERVAL_PREDICTION_COLUMNS:
            if col not in df_saved_intervals.columns:
                raise ValueError(f"Missing column '{col}' in {saved_interval_p}")

        saved_metrics_p = (
            base
            / "experiments"
            / "calibration"
            / "validation"
            / ds
            / fam
            / f"seed_{seed}"
            / method_id
            / "metrics.json"
        )
        with open(saved_metrics_p, encoding="utf-8") as f:
            saved_metrics_data = json.load(f)["metrics"]

        for cov in NOMINAL_COVERAGES:
            cov_key = f"coverage_{int(cov * 100)}"
            saved_cov_m = saved_metrics_data[cov_key]

            lower_re, upper_re, fb_re = saved_cal.predict_intervals(
                predictions=df_val["prediction"].to_numpy(),
                regimes=df_val["regime"].to_numpy(),
                nominal_coverage=cov,
            )

            # Compare against saved interval CSV for this coverage level
            sub_csv = df_saved_intervals[
                np.isclose(df_saved_intervals["nominal_coverage"], cov)
            ].copy()
            if len(sub_csv) != len(df_val):
                raise ValueError(f"Interval count mismatch in {saved_interval_p} at {cov}")

            # Verify alignment
            if not np.array_equal(sub_csv["unit"].to_numpy(), df_val["unit"].to_numpy()):
                raise ValueError("Unit alignment mismatch in interval predictions")
            if not np.array_equal(
                sub_csv["endpoint_cycle"].to_numpy(), df_val["endpoint_cycle"].to_numpy()
            ):
                raise ValueError("Endpoint cycle alignment mismatch in interval predictions")

            diff_l = np.max(np.abs(sub_csv["lower"].to_numpy() - lower_re))
            diff_u = np.max(np.abs(sub_csv["upper"].to_numpy() - upper_re))
            threshold_diffs.extend([float(diff_l), float(diff_u)])
            if max(diff_l, diff_u) > 1e-10:
                raise ValueError(f"Interval prediction bound mismatch in {bundle_id} at {cov_key}")

            # Reconstruct metrics
            re_m = compute_engine_weighted_interval_metrics(
                engine_ids=df_val["unit"].to_numpy(),
                endpoint_cycles=df_val["endpoint_cycle"].to_numpy(),
                labels=df_val["rul_true"].to_numpy(),
                lower=lower_re,
                upper=upper_re,
                regimes=df_val["regime"].to_numpy(),
                alpha=1.0 - cov,
            )

            diff_picp = abs(re_m["marginal_picp"] - saved_cov_m["marginal_picp"])
            diff_mpiw = abs(re_m["mpiw"] - saved_cov_m["mpiw"])
            diff_is = abs(re_m["interval_score"] - saved_cov_m["interval_score"])
            metric_diffs.extend([diff_picp, diff_mpiw, diff_is])

            if max(diff_picp, diff_mpiw, diff_is) > 1e-10:
                raise ValueError(
                    f"Validation metric mismatch in {bundle_id} at {cov_key}: "
                    f"picp_diff={diff_picp:.4e}, mpiw_diff={diff_mpiw:.4e}, is_diff={diff_is:.4e}"
                )

    return {
        "status": "PASS",
        "max_threshold_diff": float(max(threshold_diffs)) if threshold_diffs else 0.0,
        "max_metric_diff": float(max(metric_diffs)) if metric_diffs else 0.0,
    }


def reproduce_checkpoint_predictions(
    base_dir: Path | str = ".",
    raw_data_dir: Path | str = "data/raw/cmapss",
) -> dict[str, Any]:
    """Reproduce all 30 base model predictions on validation and calibration partitions."""
    base = Path(base_dir).resolve()
    from intellitwin.data.calibration_pipeline import prepare_partition_windows
    from intellitwin.models.registry import load_frozen_base_model

    diff_records: list[dict[str, Any]] = []

    for ds in EXPECTED_DATASETS:
        for partition in ("validation", "calibration"):
            windows = prepare_partition_windows(
                dataset_name=ds,
                partition_name=partition,
                raw_data_dir=raw_data_dir,
            )
            w_flat = windows.flatten_for_gbr()
            w_seq = windows.X_sequence

            for fam in EXPECTED_FAMILIES:
                for seed in EXPECTED_SEEDS:
                    model = load_frozen_base_model(
                        dataset=ds,
                        model_family=fam,
                        seed=seed,
                        base_dir=base,
                    )
                    X_in = w_flat if fam == "GBR" else w_seq

                    # Batch size 256 CPU inference
                    preds_list = []
                    batch_size = 256
                    n_samples = len(X_in)
                    for i in range(0, n_samples, batch_size):
                        batch = X_in[i : i + batch_size]
                        preds_list.append(model.predict(batch))
                    re_preds = np.concatenate(preds_list)

                    cache_p = (
                        base
                        / "experiments"
                        / "calibration"
                        / "point_predictions"
                        / partition
                        / ds
                        / fam
                        / f"seed_{seed}.csv"
                    )
                    df_saved = pd.read_csv(cache_p)
                    saved_preds = df_saved["prediction"].to_numpy()

                    max_abs_diff = float(np.max(np.abs(re_preds - saved_preds)))
                    diff_records.append(
                        {
                            "dataset": ds,
                            "partition": partition,
                            "model_family": fam,
                            "seed": seed,
                            "max_abs_diff": max_abs_diff,
                            "status": "PASS" if max_abs_diff <= 1e-4 else "FAIL",
                        }
                    )
                    if max_abs_diff > 1e-4:
                        raise ValueError(
                            f"Prediction reproduction difference {max_abs_diff:.6e} > 1e-4 "
                            f"for {ds}_{fam}_seed{seed} on {partition}"
                        )

    return {
        "status": "PASS",
        "models_verified": len(diff_records),
        "max_diff_overall": max(r["max_abs_diff"] for r in diff_records),
        "records": diff_records,
    }


def verify_scoped_isolation(
    base_dir: Path | str = ".",
) -> dict[str, Any]:
    """Verify data isolation scoped strictly to Step 7 and Step 8 directories."""
    base = Path(base_dir).resolve()
    target_dirs = [
        base / "experiments" / "base_models",
        base / "experiments" / "calibration",
        base / "experiments" / "model_selection",
    ]

    leaked_files: list[str] = []
    # Scoped forbidden patterns in Step 7 / Step 8 outputs
    forbidden_terms = ["test_pred", "test_metric", "held_out_pred", "confirmatory_test_results"]

    for d in target_dirs:
        if d.exists():
            for p in d.rglob("*"):
                if p.is_file():
                    name_l = p.name.lower()
                    if any(term in name_l for term in forbidden_terms):
                        leaked_files.append(p.as_posix())

    if leaked_files:
        raise RuntimeError(
            f"Forbidden held-out artifacts detected in Step 7/8 directories: {leaked_files}"
        )

    return {"status": "PASS", "scoped_dirs_audited": [d.as_posix() for d in target_dirs]}
