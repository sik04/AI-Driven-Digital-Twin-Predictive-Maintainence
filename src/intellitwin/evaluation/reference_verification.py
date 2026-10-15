"""Independent reference verification of pre-test validation smoke evidence.

This module independently reconstructs expected evaluation artifacts directly from:
- Frozen validation prediction caches (experiments/calibration/point_predictions/validation)
- Frozen calibrator JSON parameter and threshold bundles (experiments/calibration/fitted)
- Frozen selected control specifications (experiments/pretest_verification_v3/controls)
- Split manifests and quartile definitions (data/splits)

Strict boundaries:
- Does NOT import or reuse the production runner (runner.py)
- Does NOT import or reuse the production simulator or inference policies (inference.py)
- Does NOT use saved bootstrap statistic arrays as ground truth
- Reconstructs all mathematical, decision, and bootstrap quantities independently
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from intellitwin.data.splits import load_split_manifest
from intellitwin.evaluation.bootstrap import (
    DATASET_NUMBERS,
    load_partition_quartile_strata,
)
from intellitwin.evaluation.decisions import (
    get_rq_component_manifest,
)
from intellitwin.evaluation.evidence_schema import (
    CANONICAL_NOMINAL_COVERAGES,
    EXPECTED_TOTAL_CELL_SUMMARIES_COUNT,
    EXPECTED_TOTAL_COMPONENTS_COUNT,
    EXPECTED_TOTAL_OUTCOMES_COUNT,
    PRIMARY_CANONICAL_COVERAGE,
    PRIMARY_COST_SCENARIO,
    canonicalize_coverage,
    coverage_to_float,
    generate_expected_configurations,
    get_expected_contrast_statistic_specs,
    map_component_to_evidence_spec,
)
from intellitwin.evaluation.schema import (
    CONFIRMATORY_DATASETS,
    CONFIRMATORY_METHODS,
    CONFIRMATORY_MODELS,
    CONFIRMATORY_SEEDS,
    CONTROL_ALL_FOUR,
    CONTROL_EARLIER_INTERVENTION,
    CONTROL_MATCHED_WIDTH,
    CONTROL_SAFETY_MARGIN,
    CONTROL_WIDENED,
    SUBGROUP_MIN_ENGINES,
)
from intellitwin.uncertainty.artifacts import resolve_repo_relative_path

TOL_ATOL: float = 1e-10
TOL_RTOL: float = 1e-12


def _check_finite_and_bounds(
    lower: np.ndarray[Any, Any] | Sequence[float],
    upper: np.ndarray[Any, Any] | Sequence[float],
    context: str,
) -> None:
    """Validate that lower and upper bounds are finite and lower <= upper."""
    l_arr = np.asarray(lower, dtype=float)
    u_arr = np.asarray(upper, dtype=float)
    if not (np.all(np.isfinite(l_arr)) and np.all(np.isfinite(u_arr))):
        raise ValueError(f"Non-finite values encountered in {context}")
    if np.any(l_arr > u_arr + 1e-12):
        bad_idx = int(np.where(l_arr > u_arr + 1e-12)[0][0])
        raise ValueError(
            f"Inverted bounds detected in {context} at index {bad_idx}: "
            f"lower={l_arr[bad_idx]} > upper={u_arr[bad_idx]}"
        )


def _reconstruct_bootstrap_draws(
    dataset: str,
    partition_engines: list[int],
    base_dir: Path,
    n_replicates: int = 10000,
) -> np.ndarray[Any, Any]:
    """Independently generate draw sequence according to frozen PCG64 specification."""
    ds_num = DATASET_NUMBERS[dataset]
    seed_seq = np.random.SeedSequence([2026, 6, ds_num])
    rng = np.random.Generator(np.random.PCG64(seed_seq))

    strata = load_partition_quartile_strata(dataset, partition_engines, base_dir=base_dir)
    total_engines = sum(len(engs) for engs in strata.values())
    draws = np.zeros((n_replicates, total_engines), dtype=int)

    for b in range(n_replicates):
        row_engs: list[int] = []
        for q_name in ("Q1", "Q2", "Q3", "Q4"):
            engs = strata[q_name]
            n_q = len(engs)
            if n_q > 0:
                idx_draws = rng.integers(0, n_q, size=n_q)
                for idx in idx_draws:
                    row_engs.append(engs[idx])
        draws[b, :] = row_engs

    return draws


def independently_verify_all_validation_evidence(
    smoke_dir: Path | str,
    base_dir: Path | str = ".",
) -> dict[str, Any]:
    """Execute complete reference reconstruction of pre-test validation smoke evidence.

    Returns structured audit report with status, failure reasons, and detailed check metrics.
    Fails closed if any check is skipped, incomplete, or numerically inconsistent.
    """
    base = Path(base_dir).resolve()
    s_dir = Path(smoke_dir).resolve()

    checks: dict[str, Any] = {}
    failing_reasons: list[str] = []

    # -------------------------------------------------------------------------
    # 1. Validation Split Engines & Lifetime Extraction
    # -------------------------------------------------------------------------
    expected_units: dict[str, list[int]] = {}
    engine_lifetimes: dict[str, dict[int, int]] = {}

    for ds in CONFIRMATORY_DATASETS:
        split_p = resolve_repo_relative_path(
            base, f"data/splits/{ds.lower()}_engine_split_seed_2026.json"
        )
        s_man = load_split_manifest(split_p)
        expected_units[ds] = sorted(s_man.get_partition("validation"))
        engine_lifetimes[ds] = {}

    expected_engine_counts = {"FD001": 10, "FD002": 26, "FD004": 25}
    actual_engine_counts = {ds: len(expected_units[ds]) for ds in CONFIRMATORY_DATASETS}
    counts_match = actual_engine_counts == expected_engine_counts
    checks["validation_engine_counts"] = {
        "status": "PASS" if counts_match else "FAIL",
        "expected": expected_engine_counts,
        "actual": actual_engine_counts,
    }
    if not counts_match:
        failing_reasons.append(
            f"Validation engine count mismatch: expected {expected_engine_counts}, "
            f"got {actual_engine_counts}"
        )

    # -------------------------------------------------------------------------
    # 2. Prediction Caches Integrity & Trajectory Continuity (30 combinations)
    # -------------------------------------------------------------------------
    # Load point_predictions.csv from smoke directory
    smoke_pts_path = s_dir / "point_predictions.csv"
    if not smoke_pts_path.exists():
        failing_reasons.append(f"Missing required smoke file: {smoke_pts_path}")
        return {
            "status": "FAIL",
            "overall_match": False,
            "failing_reasons": failing_reasons,
            "checks": checks,
        }

    df_smoke_pts = pd.read_csv(smoke_pts_path, float_precision="round_trip")

    # Index smoke point predictions by (dataset, model_family, seed, unit, endpoint_cycle)
    smoke_pts_indexed: dict[tuple[str, str, int, int, int], tuple[float, float, str, str]] = {}
    duplicate_smoke_keys: list[tuple[str, str, int, int, int]] = []
    for r in df_smoke_pts.itertuples():
        k = (str(r.dataset), str(r.model_family), int(r.seed), int(r.unit), int(r.endpoint_cycle))
        if k in smoke_pts_indexed:
            duplicate_smoke_keys.append(k)
        smoke_pts_indexed[k] = (
            float(r.prediction),
            float(r.rul_true),
            str(r.regime),
            str(r.lifecycle_stage),
        )

    if duplicate_smoke_keys:
        failing_reasons.append(
            f"Duplicate trajectory keys in point_predictions.csv: {duplicate_smoke_keys[:5]}"
        )

    cached_trajectories: dict[tuple[str, str, int], pd.DataFrame] = {}
    max_pred_discrepancy = 0.0
    pred_key_mismatches: list[str] = []
    trajectory_continuity_clean = True
    total_trajectory_points = 0

    for ds in CONFIRMATORY_DATASETS:
        for fam in CONFIRMATORY_MODELS:
            for s in CONFIRMATORY_SEEDS:
                cell_key = (ds, fam, s)
                cache_rel = (
                    f"experiments/calibration/point_predictions/validation/{ds}/{fam}/seed_{s}.csv"
                )
                cache_path = resolve_repo_relative_path(base, cache_rel)
                if not cache_path.exists():
                    failing_reasons.append(f"Frozen validation cache missing: {cache_rel}")
                    continue

                df_c = pd.read_csv(cache_path, float_precision="round_trip")
                cached_trajectories[cell_key] = df_c

                # Check membership: exactly the expected units
                cache_units = sorted(df_c["unit"].unique())
                if cache_units != expected_units[ds]:
                    failing_reasons.append(
                        f"Cache {cache_rel} units {cache_units} != expected {expected_units[ds]}"
                    )
                    trajectory_continuity_clean = False

                # Validate causal endpoint sequences: cycle 30 through terminal cycle
                for u in expected_units[ds]:
                    df_u = df_c[df_c["unit"] == u].sort_values("endpoint_cycle")
                    cycles = df_u["endpoint_cycle"].to_numpy(dtype=int)
                    if len(cycles) == 0:
                        failing_reasons.append(f"Engine {u} has 0 endpoints in {cache_rel}")
                        trajectory_continuity_clean = False
                        continue
                    if cycles[0] != 30:
                        failing_reasons.append(
                            f"Engine {u} starting cycle {cycles[0]} != 30 in {cache_rel}"
                        )
                        trajectory_continuity_clean = False
                    term_cycle = int(cycles[-1])
                    engine_lifetimes[ds][u] = term_cycle

                    # Check continuity: no gaps, no duplicates
                    expected_seq = np.arange(30, term_cycle + 1, dtype=int)
                    if not np.array_equal(cycles, expected_seq):
                        failing_reasons.append(
                            f"Engine {u} endpoint sequence non-contiguous in {cache_rel}"
                        )
                        trajectory_continuity_clean = False

                    # Check non-negative finite predictions
                    preds = df_u["prediction"].to_numpy(dtype=float)
                    if not np.all(np.isfinite(preds)):
                        failing_reasons.append(
                            f"Non-finite prediction in {cache_rel} for engine {u}"
                        )
                    if np.any(preds < 0.0):
                        failing_reasons.append(f"Negative prediction in {cache_rel} for engine {u}")

                    # Compare against smoke_pts_indexed
                    for row in df_u.itertuples():
                        total_trajectory_points += 1
                        pt_key = (ds, fam, s, int(u), int(row.endpoint_cycle))
                        if pt_key not in smoke_pts_indexed:
                            pred_key_mismatches.append(str(pt_key))
                            continue
                        smk_pred, smk_rul, smk_reg, smk_stg = smoke_pts_indexed[pt_key]
                        p_diff = abs(smk_pred - float(row.prediction))
                        r_diff = abs(smk_rul - float(row.rul_true))
                        if p_diff > max_pred_discrepancy:
                            max_pred_discrepancy = p_diff
                        if r_diff > max_pred_discrepancy:
                            max_pred_discrepancy = r_diff
                        if smk_reg != str(row.regime) or smk_stg != str(row.lifecycle_stage):
                            pred_key_mismatches.append(
                                f"{pt_key}: regime/stage mismatch "
                                f"({smk_reg}/{smk_stg} vs {row.regime}/{row.lifecycle_stage})"
                            )

    checks["point_predictions_complete_reconstruction"] = {
        "status": "PASS"
        if (len(pred_key_mismatches) == 0 and max_pred_discrepancy <= TOL_ATOL)
        else "FAIL",
        "combinations_checked": len(cached_trajectories),
        "total_endpoints_compared": total_trajectory_points,
        "max_numerical_discrepancy": max_pred_discrepancy,
        "trajectory_continuity_clean": trajectory_continuity_clean,
        "mismatches_count": len(pred_key_mismatches),
    }
    if len(pred_key_mismatches) > 0:
        failing_reasons.append(
            f"Point prediction key/attribute mismatches: {pred_key_mismatches[:5]}"
        )
    if max_pred_discrepancy > TOL_ATOL:
        failing_reasons.append(f"Point prediction discrepancy {max_pred_discrepancy} > {TOL_ATOL}")

    # -------------------------------------------------------------------------
    # 3. Independent Interval Reconstruction (all 30 combinations x 3 methods x 3 coverages)
    # -------------------------------------------------------------------------
    # In-memory storage for reconstructed endpoints:
    # Key: (ds, fam, s, method, cov) -> DataFrame with columns:
    # [unit, endpoint_cycle, prediction, rul_true, regime, lifecycle_stage,
    #  lower, upper, covered, width, interval_score]
    reconstructed_cell_intervals: dict[tuple[str, str, int, str, int], pd.DataFrame] = {}
    cell_unit_dict: dict[tuple[tuple[str, str, int, str, int], int], dict[str, Any]] = {}

    def _index_cell_units(cell_k: tuple[str, str, int, str, int], df_cell: pd.DataFrame) -> None:
        for u_val, df_u in df_cell.groupby("unit", sort=False):
            u_int = int(u_val)
            cyc = df_u["endpoint_cycle"].to_numpy(dtype=int)
            p = df_u["prediction"].to_numpy(dtype=float)
            r_true = df_u["rul_true"].to_numpy(dtype=float)
            low = df_u["lower"].to_numpy(dtype=float)
            up = df_u["upper"].to_numpy(dtype=float)
            cov = df_u["covered"].to_numpy(dtype=float)
            w = df_u["width"].to_numpy(dtype=float)
            i_score = df_u["interval_score"].to_numpy(dtype=float)
            cell_unit_dict[(cell_k, u_int)] = {
                "cycles": cyc,
                "prediction": p,
                "rul_true": r_true,
                "lower": low,
                "upper": up,
                "covered": cov,
                "width": w,
                "interval_score": i_score,
                "regime": df_u["regime"].to_numpy(dtype=str),
                "lifecycle_stage": df_u["lifecycle_stage"].to_numpy(dtype=str),
                "cov_mean": float(cov.mean()) if not np.all(np.isnan(cov)) else np.nan,
                "width_mean": float(w.mean()) if not np.all(np.isnan(w)) else np.nan,
                "is_mean": float(i_score.mean()) if not np.all(np.isnan(i_score)) else np.nan,
                "rmse": float(np.sqrt(np.mean((p - r_true) ** 2))),
            }

    max_interval_export_discrepancy = 0.0
    exported_interval_mismatches: list[str] = []

    smoke_interval_path = s_dir / "interval_predictions.csv"
    df_smoke_intervals = (
        pd.read_csv(smoke_interval_path, float_precision="round_trip")
        if smoke_interval_path.exists()
        else pd.DataFrame()
    )

    smoke_interval_map: dict[
        tuple[str, str, int, str, int, int, int], tuple[float, float, float, float, float]
    ] = {}
    for r in df_smoke_intervals.itertuples():
        c_cov = canonicalize_coverage(r.nominal_coverage)
        k_inv = (
            str(r.dataset),
            str(r.model_family),
            int(r.seed),
            str(r.method_or_control_id),
            c_cov,
            int(r.unit),
            int(r.endpoint_cycle),
        )
        smoke_interval_map[k_inv] = (
            float(r.lower),
            float(r.upper),
            float(r.covered),
            float(r.width),
            float(r.interval_score),
        )

    for ds in CONFIRMATORY_DATASETS:
        for fam in CONFIRMATORY_MODELS:
            for s in CONFIRMATORY_SEEDS:
                df_traj = cached_trajectories[(ds, fam, s)]
                preds = np.maximum(0.0, df_traj["prediction"].to_numpy(dtype=float))
                rul_trues = df_traj["rul_true"].to_numpy(dtype=float)
                regimes = df_traj["regime"].to_numpy(dtype=str)

                for method in CONFIRMATORY_METHODS:
                    cal_rel = (
                        f"experiments/calibration/fitted/{ds}/{fam}/"
                        f"seed_{s}/{method}/calibrator.json"
                    )
                    cal_p = resolve_repo_relative_path(base, cal_rel)
                    if not cal_p.exists():
                        failing_reasons.append(f"Calibrator JSON missing: {cal_rel}")
                        continue
                    with open(cal_p, encoding="utf-8") as f:
                        cal_data = json.load(f)

                    cand_params = cal_data.get("candidate_parameters", {})
                    gamma = (
                        float(cand_params.get("gamma", 0.0))
                        if method == "decision_aware_hcp"
                        else 0.0
                    )
                    beta = (
                        float(cand_params.get("beta", 0.0))
                        if method == "decision_aware_hcp"
                        else 0.0
                    )

                    threshold_bundles = cal_data.get("threshold_bundles", {})

                    for cov_int in CANONICAL_NOMINAL_COVERAGES:
                        cov_key = f"coverage_{cov_int}"
                        bundle = threshold_bundles[cov_key]
                        global_th = float(bundle["global_threshold"])
                        reg_thresholds = bundle.get("regime_thresholds", {})

                        # Compute thresholds per point
                        q_vec = np.zeros(len(preds), dtype=float)
                        if method == "global_hcp":
                            q_vec[:] = global_th
                        else:
                            for idx, reg in enumerate(regimes):
                                r_rec = reg_thresholds.get(reg)
                                if r_rec is not None and not r_rec.get("fallback_used", False):
                                    q_vec[idx] = float(r_rec["threshold"])
                                else:
                                    q_vec[idx] = global_th

                        # Compute scale factors
                        if method == "decision_aware_hcp":
                            sigma = (1.0 + preds / 125.0) ** gamma
                            z = np.exp(-preds / 20.0)
                            a = sigma * np.exp(beta * z)
                            b = sigma * np.exp(-beta * z)
                            lower = np.maximum(0.0, preds - q_vec * a)
                            upper = preds + q_vec * b
                        else:
                            lower = np.maximum(0.0, preds - q_vec)
                            upper = preds + q_vec

                        # Validate finite and bounds
                        _check_finite_and_bounds(
                            lower, upper, f"{ds}/{fam}/seed_{s}/{method}/{cov_int}"
                        )

                        covered = ((rul_trues >= lower) & (rul_trues <= upper)).astype(float)
                        width = upper - lower

                        alpha = 1.0 - coverage_to_float(cov_int)
                        penalty_l = np.maximum(0.0, lower - rul_trues) * (2.0 / alpha)
                        penalty_u = np.maximum(0.0, rul_trues - upper) * (2.0 / alpha)
                        int_score = width + penalty_l + penalty_u

                        df_rec = pd.DataFrame(
                            {
                                "dataset": ds,
                                "model_family": fam,
                                "seed": s,
                                "method_or_control_id": method,
                                "nominal_coverage": cov_int,
                                "unit": df_traj["unit"].to_numpy(dtype=int),
                                "endpoint_cycle": df_traj["endpoint_cycle"].to_numpy(dtype=int),
                                "prediction": preds,
                                "rul_true": rul_trues,
                                "regime": regimes,
                                "lifecycle_stage": df_traj["lifecycle_stage"].to_numpy(dtype=str),
                                "lower": lower,
                                "upper": upper,
                                "covered": covered,
                                "width": width,
                                "interval_score": int_score,
                            }
                        )
                        reconstructed_cell_intervals[(ds, fam, s, method, cov_int)] = df_rec
                        _index_cell_units((ds, fam, s, method, cov_int), df_rec)

                        # Documented scope of interval_predictions.csv: seed 2026, 90% cov
                        if s == 2026 and cov_int == PRIMARY_CANONICAL_COVERAGE:
                            for row in df_rec.itertuples():
                                k_inv = (
                                    ds,
                                    fam,
                                    s,
                                    method,
                                    cov_int,
                                    int(row.unit),
                                    int(row.endpoint_cycle),
                                )
                                if k_inv not in smoke_interval_map:
                                    exported_interval_mismatches.append(
                                        f"Missing in interval CSV: {k_inv}"
                                    )
                                    continue
                                smk_l, smk_u, smk_cov, smk_w, smk_is = smoke_interval_map[k_inv]
                                d_l = abs(smk_l - float(row.lower))
                                d_u = abs(smk_u - float(row.upper))
                                d_c = abs(smk_cov - float(row.covered))
                                d_w = abs(smk_w - float(row.width))
                                d_s = abs(smk_is - float(row.interval_score))
                                max_d = max(d_l, d_u, d_c, d_w, d_s)
                                if max_d > max_interval_export_discrepancy:
                                    max_interval_export_discrepancy = max_d
                                if max_d > TOL_ATOL:
                                    exported_interval_mismatches.append(
                                        f"{k_inv}: diff={max_d} (low={d_l}, up={d_u}, is={d_s})"
                                    )

    checks["interval_reconstruction"] = {
        "status": "PASS"
        if (len(exported_interval_mismatches) == 0 and max_interval_export_discrepancy <= TOL_ATOL)
        else "FAIL",
        "bundles_reconstructed": len(reconstructed_cell_intervals),
        "exported_interval_points_verified": len(smoke_interval_map),
        "max_numerical_discrepancy": max_interval_export_discrepancy,
        "mismatches_count": len(exported_interval_mismatches),
    }
    if exported_interval_mismatches:
        failing_reasons.append(
            f"Interval predictions export discrepancy: {exported_interval_mismatches[:5]}"
        )

    # -------------------------------------------------------------------------
    # 4. Controls Reconstruction (FD002 Only, 4 controls x 2 models x 5 seeds)
    # -------------------------------------------------------------------------
    selected_controls: dict[str, dict[str, Any]] = {}
    for fam in CONFIRMATORY_MODELS:
        sel_p = resolve_repo_relative_path(
            base, f"experiments/pretest_verification_v3/controls/FD002/{fam}/selection.json"
        )
        if not sel_p.exists():
            failing_reasons.append(f"Controls selection.json missing for {fam}")
            continue
        with open(sel_p, encoding="utf-8") as f:
            sel_data = json.load(f)
            selected_controls[fam] = sel_data.get("selected_controls", sel_data)

    for fam in CONFIRMATORY_MODELS:
        for s in CONFIRMATORY_SEEDS:
            ctrl_specs = selected_controls[fam]

            # 1. Matched width
            mw_spec = ctrl_specs[CONTROL_MATCHED_WIDTH]
            src_mw = mw_spec.get("interval_source", "global_hcp")
            df_src_mw = reconstructed_cell_intervals[
                ("FD002", fam, s, src_mw, PRIMARY_CANONICAL_COVERAGE)
            ]
            preds_mw = df_src_mw["prediction"].to_numpy(dtype=float)
            uppers_mw = df_src_mw["upper"].to_numpy(dtype=float)
            rul_trues_mw = df_src_mw["rul_true"].to_numpy(dtype=float)

            lam_mw = float(mw_spec["parameter_value"])
            q_half_mw = uppers_mw - preds_mw
            mw_low = np.maximum(0.0, preds_mw - lam_mw * q_half_mw)
            mw_up = preds_mw + lam_mw * q_half_mw
            _check_finite_and_bounds(mw_low, mw_up, f"FD002/{fam}/seed_{s}/{CONTROL_MATCHED_WIDTH}")
            mw_cov = ((rul_trues_mw >= mw_low) & (rul_trues_mw <= mw_up)).astype(float)
            mw_w = mw_up - mw_low
            alpha_90 = 0.10
            mw_is = (
                mw_w
                + np.maximum(0.0, mw_low - rul_trues_mw) * (2.0 / alpha_90)
                + np.maximum(0.0, rul_trues_mw - mw_up) * (2.0 / alpha_90)
            )

            df_mw = df_src_mw.copy()
            df_mw["method_or_control_id"] = CONTROL_MATCHED_WIDTH
            df_mw["lower"] = mw_low
            df_mw["upper"] = mw_up
            df_mw["covered"] = mw_cov
            df_mw["width"] = mw_w
            df_mw["interval_score"] = mw_is
            reconstructed_cell_intervals[
                ("FD002", fam, s, CONTROL_MATCHED_WIDTH, PRIMARY_CANONICAL_COVERAGE)
            ] = df_mw
            _index_cell_units(
                ("FD002", fam, s, CONTROL_MATCHED_WIDTH, PRIMARY_CANONICAL_COVERAGE), df_mw
            )

            # 2. Widened
            wid_spec = ctrl_specs[CONTROL_WIDENED]
            src_wid = wid_spec.get("interval_source", "regime_hcp")
            df_src_wid = reconstructed_cell_intervals[
                ("FD002", fam, s, src_wid, PRIMARY_CANONICAL_COVERAGE)
            ]
            preds_wid = df_src_wid["prediction"].to_numpy(dtype=float)
            uppers_wid = df_src_wid["upper"].to_numpy(dtype=float)
            rul_trues_wid = df_src_wid["rul_true"].to_numpy(dtype=float)

            lam_wid = float(wid_spec["parameter_value"])
            q_half_wid = uppers_wid - preds_wid
            wid_low = np.maximum(0.0, preds_wid - lam_wid * q_half_wid)
            wid_up = preds_wid + lam_wid * q_half_wid
            _check_finite_and_bounds(wid_low, wid_up, f"FD002/{fam}/seed_{s}/{CONTROL_WIDENED}")
            wid_cov = ((rul_trues_wid >= wid_low) & (rul_trues_wid <= wid_up)).astype(float)
            wid_w = wid_up - wid_low
            wid_is = (
                wid_w
                + np.maximum(0.0, wid_low - rul_trues_wid) * (2.0 / alpha_90)
                + np.maximum(0.0, rul_trues_wid - wid_up) * (2.0 / alpha_90)
            )

            df_wid = df_src_wid.copy()
            df_wid["method_or_control_id"] = CONTROL_WIDENED
            df_wid["lower"] = wid_low
            df_wid["upper"] = wid_up
            df_wid["covered"] = wid_cov
            df_wid["width"] = wid_w
            df_wid["interval_score"] = wid_is
            reconstructed_cell_intervals[
                ("FD002", fam, s, CONTROL_WIDENED, PRIMARY_CANONICAL_COVERAGE)
            ] = df_wid
            _index_cell_units(
                ("FD002", fam, s, CONTROL_WIDENED, PRIMARY_CANONICAL_COVERAGE), df_wid
            )

            # 3. Earlier intervention (keeps source intervals)
            ei_spec = ctrl_specs[CONTROL_EARLIER_INTERVENTION]
            src_ei = ei_spec.get("interval_source", "regime_hcp")
            df_src_ei = reconstructed_cell_intervals[
                ("FD002", fam, s, src_ei, PRIMARY_CANONICAL_COVERAGE)
            ]
            df_ei = df_src_ei.copy()
            df_ei["method_or_control_id"] = CONTROL_EARLIER_INTERVENTION
            reconstructed_cell_intervals[
                ("FD002", fam, s, CONTROL_EARLIER_INTERVENTION, PRIMARY_CANONICAL_COVERAGE)
            ] = df_ei
            _index_cell_units(
                ("FD002", fam, s, CONTROL_EARLIER_INTERVENTION, PRIMARY_CANONICAL_COVERAGE), df_ei
            )

            # 4. Point safety margin (policy-only, interval metrics null)
            sm_spec = ctrl_specs[CONTROL_SAFETY_MARGIN]
            src_sm = sm_spec.get("interval_source", "regime_hcp")
            df_src_sm = reconstructed_cell_intervals[
                ("FD002", fam, s, src_sm, PRIMARY_CANONICAL_COVERAGE)
            ]
            df_sm = df_src_sm.copy()
            df_sm["method_or_control_id"] = CONTROL_SAFETY_MARGIN
            df_sm["lower"] = np.nan
            df_sm["upper"] = np.nan
            df_sm["covered"] = np.nan
            df_sm["width"] = np.nan
            df_sm["interval_score"] = np.nan
            reconstructed_cell_intervals[
                ("FD002", fam, s, CONTROL_SAFETY_MARGIN, PRIMARY_CANONICAL_COVERAGE)
            ] = df_sm
            _index_cell_units(
                ("FD002", fam, s, CONTROL_SAFETY_MARGIN, PRIMARY_CANONICAL_COVERAGE), df_sm
            )

    # -------------------------------------------------------------------------
    # 5. Independent Maintenance Policy Simulation & Cost Evaluation
    # -------------------------------------------------------------------------
    # Scenarios specifications
    scenario_params = {
        "primary_reference": {"Cpm": 1.0, "Cfail": 5.0, "Cwaste": 0.2},
        "failure_sensitive": {"Cpm": 1.0, "Cfail": 10.0, "Cwaste": 0.2},
        "waste_sensitive": {"Cpm": 1.0, "Cfail": 5.0, "Cwaste": 0.4},
    }

    # Outcomes storage:
    # Key: (ds, fam, s, method_or_ctrl, cov, scen, unit) -> dict with fields:
    # terminal_event, intervention_cycle, failed, pm, wasted_rul, total_cost,
    # is_cost_inefficient_early_pm
    reconstructed_outcomes: dict[tuple[str, str, int, str, int, str, int], dict[str, Any]] = {}
    reconstructed_traces: dict[tuple[str, str, int, str, int, str, int], list[tuple[int, str]]] = {}

    expected_prim_cfgs, expected_ctrl_cfgs = generate_expected_configurations()
    all_expected_cfgs = expected_prim_cfgs | expected_ctrl_cfgs

    for ds, fam, s, m_id, cov, scen in all_expected_cfgs:
        scen_p = scenario_params[scen]
        c_pm = scen_p["Cpm"]
        c_fail = scen_p["Cfail"]
        c_waste = scen_p["Cwaste"]

        cell_k = (ds, fam, s, m_id, cov)

        # Loop through engine units using fast dictionary lookup
        for u in expected_units[ds]:
            u_data = cell_unit_dict[(cell_k, u)]
            cycles = u_data["cycles"]
            T_u = engine_lifetimes[ds][u]

            # Determine maintain condition function
            intervened = False
            interv_cycle: int | None = None
            trace_actions: list[tuple[int, str]] = []

            if m_id == CONTROL_SAFETY_MARGIN:
                m_val = float(selected_controls[fam][CONTROL_SAFETY_MARGIN]["parameter_value"])
                pts = u_data["prediction"]
                for cyc, p_val in zip(cycles, pts, strict=True):
                    if cyc >= T_u:
                        break
                    should_maintain = p_val <= (1.0 + m_val)
                    if should_maintain:
                        intervened = True
                        interv_cycle = int(cyc)
                        trace_actions.append((int(cyc), "MAINTAIN_NOW"))
                        break
                    else:
                        trace_actions.append((int(cyc), "CONTINUE"))
            elif m_id == CONTROL_EARLIER_INTERVENTION:
                h_val = float(
                    selected_controls[fam][CONTROL_EARLIER_INTERVENTION]["parameter_value"]
                )
                lows = u_data["lower"]
                for cyc, l_val in zip(cycles, lows, strict=True):
                    if cyc >= T_u:
                        break
                    should_maintain = l_val <= h_val
                    if should_maintain:
                        intervened = True
                        interv_cycle = int(cyc)
                        trace_actions.append((int(cyc), "MAINTAIN_NOW"))
                        break
                    else:
                        trace_actions.append((int(cyc), "CONTINUE"))
            else:
                lows = u_data["lower"]
                for cyc, l_val in zip(cycles, lows, strict=True):
                    if cyc >= T_u:
                        break
                    should_maintain = l_val <= 1.0
                    if should_maintain:
                        intervened = True
                        interv_cycle = int(cyc)
                        trace_actions.append((int(cyc), "MAINTAIN_NOW"))
                        break
                    else:
                        trace_actions.append((int(cyc), "CONTINUE"))

            if intervened:
                assert interv_cycle is not None
                term_event = "PM"
                failed = False
                pm = True
                wasted = float(T_u - interv_cycle)
                cost = c_pm + c_waste * wasted
                early_pm = wasted > ((c_fail - c_pm) / c_waste)
            else:
                term_event = "FAILURE"
                interv_cycle = None
                failed = True
                pm = False
                wasted = 0.0
                cost = c_fail
                early_pm = False

            outcome_key = (ds, fam, s, m_id, cov, scen, u)
            reconstructed_outcomes[outcome_key] = {
                "terminal_event": term_event,
                "intervention_cycle": interv_cycle,
                "failed": failed,
                "pm": pm,
                "wasted_rul": wasted,
                "total_cost": cost,
                "is_cost_inefficient_early_pm": early_pm,
            }
            if (
                s == 2026
                and cov == PRIMARY_CANONICAL_COVERAGE
                and scen == PRIMARY_COST_SCENARIO
                and m_id in CONFIRMATORY_METHODS
            ):
                reconstructed_traces[outcome_key] = trace_actions

    # Compare against engine_seed_outcomes.csv
    smoke_outcomes_path = s_dir / "engine_seed_outcomes.csv"
    df_smoke_outcomes = pd.read_csv(smoke_outcomes_path, float_precision="round_trip")

    outcome_mismatches: list[str] = []
    max_cost_discrepancy = 0.0

    for r in df_smoke_outcomes.itertuples():
        cov_c = canonicalize_coverage(r.nominal_coverage)
        k_out = (
            str(r.dataset),
            str(r.model_family),
            int(r.seed),
            str(r.method_or_control_id),
            cov_c,
            str(r.scenario_id),
            int(r.unit),
        )
        if k_out not in reconstructed_outcomes:
            outcome_mismatches.append(f"Unexpected outcome key in smoke: {k_out}")
            continue

        exp = reconstructed_outcomes[k_out]
        # Check discrete fields
        if str(r.terminal_event) != exp["terminal_event"]:
            outcome_mismatches.append(
                f"{k_out}: terminal_event mismatch ({r.terminal_event} != {exp['terminal_event']})"
            )
        if bool(r.failed) != exp["failed"]:
            outcome_mismatches.append(f"{k_out}: failed mismatch ({r.failed} != {exp['failed']})")
        if bool(r.pm) != exp["pm"]:
            outcome_mismatches.append(f"{k_out}: pm mismatch ({r.pm} != {exp['pm']})")
        if bool(r.is_cost_inefficient_early_pm) != exp["is_cost_inefficient_early_pm"]:
            outcome_mismatches.append(
                f"{k_out}: early_pm mismatch "
                f"({r.is_cost_inefficient_early_pm} != {exp['is_cost_inefficient_early_pm']})"
            )

        # Check intervention_cycle
        if exp["intervention_cycle"] is None:
            if pd.notna(r.intervention_cycle):
                outcome_mismatches.append(
                    f"{k_out}: expected null intervention_cycle, got {r.intervention_cycle}"
                )
        else:
            if (
                pd.isna(r.intervention_cycle)
                or int(r.intervention_cycle) != exp["intervention_cycle"]
            ):
                outcome_mismatches.append(
                    f"{k_out}: intervention_cycle "
                    f"({r.intervention_cycle} != {exp['intervention_cycle']})"
                )

        # Check numerical fields
        cost_diff = abs(float(r.total_cost) - exp["total_cost"])
        waste_diff = abs(float(r.wasted_rul) - exp["wasted_rul"])
        if cost_diff > max_cost_discrepancy:
            max_cost_discrepancy = cost_diff
        if cost_diff > TOL_ATOL or waste_diff > TOL_ATOL:
            outcome_mismatches.append(f"{k_out}: cost_diff={cost_diff}, waste_diff={waste_diff}")

    checks["engine_seed_outcomes_reconstruction"] = {
        "status": "PASS"
        if (
            len(outcome_mismatches) == 0 and len(df_smoke_outcomes) == EXPECTED_TOTAL_OUTCOMES_COUNT
        )
        else "FAIL",
        "expected_count": EXPECTED_TOTAL_OUTCOMES_COUNT,
        "actual_count": len(df_smoke_outcomes),
        "reconstructed_count": len(reconstructed_outcomes),
        "max_cost_discrepancy": max_cost_discrepancy,
        "mismatches_count": len(outcome_mismatches),
    }
    if outcome_mismatches:
        failing_reasons.append(f"Engine seed outcomes discrepancies: {outcome_mismatches[:5]}")

    # Compare decision_traces.csv
    smoke_traces_path = s_dir / "decision_traces.csv"
    df_smoke_traces = pd.read_csv(smoke_traces_path)
    trace_mismatches: list[str] = []

    smoke_trace_actions: dict[tuple[str, str, int, str, int, str, int], list[tuple[int, str]]] = (
        defaultdict(list)
    )
    for r in df_smoke_traces.itertuples():
        c_cov = canonicalize_coverage(r.nominal_coverage)
        k_tr = (
            str(r.dataset),
            str(r.model_family),
            int(r.seed),
            str(r.method_or_control_id),
            c_cov,
            str(r.scenario_id),
            int(r.unit),
        )
        smoke_trace_actions[k_tr].append((int(r.cycle), str(r.action)))

    for k_tr, exp_actions in reconstructed_traces.items():
        if k_tr not in smoke_trace_actions:
            trace_mismatches.append(f"Missing trace for {k_tr}")
            continue
        smk_actions = smoke_trace_actions[k_tr]
        if smk_actions != exp_actions:
            trace_mismatches.append(
                f"{k_tr}: action sequence mismatch ({len(smk_actions)} != {len(exp_actions)})"
            )

    checks["decision_traces_reconstruction"] = {
        "status": "PASS" if len(trace_mismatches) == 0 else "FAIL",
        "traces_verified": len(reconstructed_traces),
        "mismatches_count": len(trace_mismatches),
    }
    if trace_mismatches:
        failing_reasons.append(f"Decision traces discrepancies: {trace_mismatches[:5]}")

    # -------------------------------------------------------------------------
    # 6. Reconstruct engine_metrics.csv & cell_summary.csv & subgroup_metrics.csv
    # -------------------------------------------------------------------------
    # A. engine_metrics.csv
    smoke_eng_metrics_path = s_dir / "engine_metrics.csv"
    df_smoke_eng_metrics = pd.read_csv(smoke_eng_metrics_path, float_precision="round_trip")
    eng_metric_mismatches: list[str] = []
    max_eng_metric_discrepancy = 0.0

    for r in df_smoke_eng_metrics.itertuples():
        cov_c = canonicalize_coverage(r.nominal_coverage)
        k_met = (
            str(r.dataset),
            str(r.model_family),
            int(r.seed),
            str(r.method_or_control_id),
            cov_c,
            str(r.scenario_id),
            int(r.unit),
        )
        if k_met not in reconstructed_outcomes:
            eng_metric_mismatches.append(f"Missing expected metric key: {k_met}")
            continue

        exp_o = reconstructed_outcomes[k_met]
        u_data = cell_unit_dict[((k_met[0], k_met[1], k_met[2], k_met[3], k_met[4]), k_met[6])]

        # Compare outcomes fields
        d_cost = abs(float(r.total_cost) - exp_o["total_cost"])
        d_fail = abs(float(r.failed) - (1.0 if exp_o["failed"] else 0.0))
        d_pm = abs(float(r.pm) - (1.0 if exp_o["pm"] else 0.0))
        d_waste = abs(float(r.wasted_rul) - exp_o["wasted_rul"])

        # Compare interval fields
        if k_met[3] == CONTROL_SAFETY_MARGIN:
            if pd.notna(r.coverage) or pd.notna(r.mpiw) or pd.notna(r.mean_interval_score):
                eng_metric_mismatches.append(
                    f"{k_met}: expected NaN for interval metrics in safety margin"
                )
            d_cov, d_mpiw, d_is = 0.0, 0.0, 0.0
        else:
            exp_cov = u_data["cov_mean"]
            exp_mpiw = u_data["width_mean"]
            exp_is = u_data["is_mean"]
            d_cov = abs(float(r.coverage) - exp_cov)
            d_mpiw = abs(float(r.mpiw) - exp_mpiw)
            d_is = abs(float(r.mean_interval_score) - exp_is)

        exp_rmse = u_data["rmse"]
        d_rmse = abs(float(r.rmse) - exp_rmse)

        cur_max = max(d_cost, d_fail, d_pm, d_waste, d_cov, d_mpiw, d_is, d_rmse)
        if cur_max > max_eng_metric_discrepancy:
            max_eng_metric_discrepancy = cur_max
        if cur_max > TOL_ATOL:
            eng_metric_mismatches.append(f"{k_met}: max discrepancy {cur_max} > {TOL_ATOL}")

    checks["engine_metrics_reconstruction"] = {
        "status": "PASS"
        if (
            len(eng_metric_mismatches) == 0
            and len(df_smoke_eng_metrics) == EXPECTED_TOTAL_OUTCOMES_COUNT
        )
        else "FAIL",
        "expected_count": EXPECTED_TOTAL_OUTCOMES_COUNT,
        "actual_count": len(df_smoke_eng_metrics),
        "max_discrepancy": max_eng_metric_discrepancy,
        "mismatches_count": len(eng_metric_mismatches),
    }
    if eng_metric_mismatches:
        failing_reasons.append(f"Engine metrics discrepancies: {eng_metric_mismatches[:5]}")

    # B. cell_summary.csv
    smoke_cell_path = s_dir / "cell_summary.csv"
    df_smoke_cell = pd.read_csv(smoke_cell_path, float_precision="round_trip")
    cell_summary_mismatches: list[str] = []
    max_cell_summary_discrepancy = 0.0

    # Build cell summary keys:
    # (dataset, model_family, method_or_ctrl, nominal_coverage, scenario_id)
    cell_summary_cfgs: set[tuple[str, str, str, int, str]] = {
        (ds, fam, m_id, cov, scen) for (ds, fam, _, m_id, cov, scen) in all_expected_cfgs
    }

    for cfg in cell_summary_cfgs:
        ds, fam, m_id, cov, scen = cfg

        # Filter outcomes for this cell across all seeds and engines
        cell_outcomes = [
            reconstructed_outcomes[(ds, fam, s, m_id, cov, scen, u)]
            for s in CONFIRMATORY_SEEDS
            for u in expected_units[ds]
        ]
        # Equal-engine mean cost: average seeds within engine, then average across engines
        cost_by_unit = defaultdict(list)
        fail_by_unit = defaultdict(list)
        pm_by_unit = defaultdict(list)
        waste_by_unit = defaultdict(list)
        early_by_unit = defaultdict(list)

        for s in CONFIRMATORY_SEEDS:
            for u in expected_units[ds]:
                o = reconstructed_outcomes[(ds, fam, s, m_id, cov, scen, u)]
                cost_by_unit[u].append(o["total_cost"])
                fail_by_unit[u].append(1.0 if o["failed"] else 0.0)
                pm_by_unit[u].append(1.0 if o["pm"] else 0.0)
                waste_by_unit[u].append(o["wasted_rul"])
                early_by_unit[u].append(1.0 if o["is_cost_inefficient_early_pm"] else 0.0)

        exp_mean_cost = float(np.mean([np.mean(cost_by_unit[u]) for u in expected_units[ds]]))
        exp_fail_rate = float(np.mean([np.mean(fail_by_unit[u]) for u in expected_units[ds]]))
        exp_pm_rate = float(np.mean([np.mean(pm_by_unit[u]) for u in expected_units[ds]]))
        exp_mean_waste = float(np.mean([np.mean(waste_by_unit[u]) for u in expected_units[ds]]))
        exp_early_rate = float(np.mean([np.mean(early_by_unit[u]) for u in expected_units[ds]]))

        pm_only_outcomes = [o for o in cell_outcomes if o["pm"]]
        if pm_only_outcomes:
            exp_pm_only_early = float(
                np.mean(
                    [1.0 if o["is_cost_inefficient_early_pm"] else 0.0 for o in pm_only_outcomes]
                )
            )
        else:
            exp_pm_only_early = np.nan

        if m_id == CONTROL_SAFETY_MARGIN:
            exp_marg_cov = np.nan
            exp_marg_err = np.nan
            exp_mpiw = np.nan
            exp_is = np.nan
        else:
            cov_by_u_list = [
                float(
                    np.mean(
                        [
                            cell_unit_dict[((ds, fam, s, m_id, cov), u)]["cov_mean"]
                            for s in CONFIRMATORY_SEEDS
                        ]
                    )
                )
                for u in expected_units[ds]
            ]
            mpiw_by_u_list = [
                float(
                    np.mean(
                        [
                            cell_unit_dict[((ds, fam, s, m_id, cov), u)]["width_mean"]
                            for s in CONFIRMATORY_SEEDS
                        ]
                    )
                )
                for u in expected_units[ds]
            ]
            is_by_u_list = [
                float(
                    np.mean(
                        [
                            cell_unit_dict[((ds, fam, s, m_id, cov), u)]["is_mean"]
                            for s in CONFIRMATORY_SEEDS
                        ]
                    )
                )
                for u in expected_units[ds]
            ]

            exp_marg_cov = float(np.mean(cov_by_u_list))
            exp_marg_err = abs(exp_marg_cov - coverage_to_float(cov))
            exp_mpiw = float(np.mean(mpiw_by_u_list))
            exp_is = float(np.mean(is_by_u_list))

        # Find row in df_smoke_cell
        cov_val = coverage_to_float(cov)
        sub_cell = df_smoke_cell[
            (df_smoke_cell["dataset"] == ds)
            & (df_smoke_cell["model_family"] == fam)
            & (df_smoke_cell["method_or_control_id"] == m_id)
            & (np.isclose(df_smoke_cell["nominal_coverage"], cov_val, atol=1e-12, rtol=0.0))
            & (df_smoke_cell["scenario_id"] == scen)
        ]
        if len(sub_cell) != 1:
            cell_summary_mismatches.append(
                f"Expected exactly 1 row in cell_summary for {cfg}, got {len(sub_cell)}"
            )
            continue

        c_row = sub_cell.iloc[0]
        d_c = abs(float(c_row["mean_cost"]) - exp_mean_cost)
        d_f = abs(float(c_row["failure_rate"]) - exp_fail_rate)
        d_p = abs(float(c_row["pm_rate"]) - exp_pm_rate)
        d_w = abs(float(c_row["mean_wasted_rul"]) - exp_mean_waste)
        d_e = abs(float(c_row["fleet_early_pm_rate"]) - exp_early_rate)

        if np.isnan(exp_pm_only_early):
            if pd.notna(c_row["pm_only_early_pm_rate"]):
                cell_summary_mismatches.append(f"{cfg}: expected NaN for pm_only_early_pm_rate")
        else:
            d_pe = abs(float(c_row["pm_only_early_pm_rate"]) - exp_pm_only_early)
            if d_pe > max_cell_summary_discrepancy:
                max_cell_summary_discrepancy = d_pe

        if m_id != CONTROL_SAFETY_MARGIN:
            d_mc = abs(float(c_row["marginal_coverage"]) - exp_marg_cov)
            d_mce = abs(float(c_row["marginal_coverage_abs_error"]) - exp_marg_err)
            d_mp = abs(float(c_row["mpiw"]) - exp_mpiw)
            d_is_c = abs(float(c_row["interval_score"]) - exp_is)
            cur_max_c = max(d_c, d_f, d_p, d_w, d_e, d_mc, d_mce, d_mp, d_is_c)
        else:
            cur_max_c = max(d_c, d_f, d_p, d_w, d_e)

        if cur_max_c > max_cell_summary_discrepancy:
            max_cell_summary_discrepancy = cur_max_c
        if cur_max_c > TOL_ATOL:
            cell_summary_mismatches.append(f"{cfg}: discrepancy {cur_max_c} > {TOL_ATOL}")

    checks["cell_summary_reconstruction"] = {
        "status": "PASS"
        if (
            len(cell_summary_mismatches) == 0
            and len(df_smoke_cell) == EXPECTED_TOTAL_CELL_SUMMARIES_COUNT
        )
        else "FAIL",
        "expected_count": EXPECTED_TOTAL_CELL_SUMMARIES_COUNT,
        "actual_count": len(df_smoke_cell),
        "max_discrepancy": max_cell_summary_discrepancy,
        "mismatches_count": len(cell_summary_mismatches),
    }
    if cell_summary_mismatches:
        failing_reasons.append(f"Cell summary discrepancies: {cell_summary_mismatches[:5]}")

    # -------------------------------------------------------------------------
    # 7. Independent Bootstrap Draws, Statistics Arrays, & Contrasts
    # -------------------------------------------------------------------------
    # Generate independent draws and compare against saved draw files
    draws_mismatches: list[str] = []
    indep_draws: dict[str, np.ndarray[Any, Any]] = {}
    multiplicity_matrices: dict[str, np.ndarray[Any, Any]] = {}

    for ds in CONFIRMATORY_DATASETS:
        engs = expected_units[ds]
        d_arr = _reconstruct_bootstrap_draws(ds, engs, base, n_replicates=10000)
        indep_draws[ds] = d_arr

        # Check against saved bootstrap_draws_{ds}.npz
        saved_draw_p = s_dir / f"bootstrap_draws_{ds}.npz"
        if not saved_draw_p.exists():
            draws_mismatches.append(f"Missing bootstrap draws: {saved_draw_p}")
            continue
        data_saved = np.load(saved_draw_p)
        saved_d = data_saved["draws"]
        saved_u = list(data_saved["engines"])
        if saved_u != engs or not np.array_equal(saved_d, d_arr):
            draws_mismatches.append(f"Draws array mismatch for {ds}")

        # Build Multiplicity Matrix M shape (10000, N_engs)
        eng_to_idx = {u: i for i, u in enumerate(engs)}
        M = np.zeros((10000, len(engs)), dtype=float)
        for b in range(10000):
            for u in d_arr[b]:
                M[b, eng_to_idx[u]] += 1.0
        multiplicity_matrices[ds] = M

    checks["bootstrap_draws_exact_reconstruction"] = {
        "status": "PASS" if len(draws_mismatches) == 0 else "FAIL",
        "mismatches_count": len(draws_mismatches),
    }
    if draws_mismatches:
        failing_reasons.append(f"Bootstrap draws discrepancies: {draws_mismatches}")

    # Independently compute all 238 numeric arrays from engine outcomes
    # Precompute per-engine statistics:
    # 1. engine cost: average across seeds for each engine
    engine_cost_map: dict[tuple[str, str, str, int, str], dict[int, float]] = defaultdict(dict)
    engine_cov_map: dict[tuple[str, str, str, int, str], dict[int, float]] = defaultdict(dict)
    engine_mpiw_map: dict[tuple[str, str, str, int, str], dict[int, float]] = defaultdict(dict)
    engine_is_map: dict[tuple[str, str, str, int, str], dict[int, float]] = defaultdict(dict)

    # Subgroup coverage maps: (cfg, group_id) -> dict[unit -> cov]
    engine_regime_cov_map: dict[tuple[str, str, str, int, str], dict[str, dict[int, float]]] = (
        defaultdict(lambda: defaultdict(dict))
    )
    engine_stage_cov_map: dict[tuple[str, str, str, int, str], dict[str, dict[int, float]]] = (
        defaultdict(lambda: defaultdict(dict))
    )

    # Eligible subgroups per dataset
    eligible_regimes: dict[str, list[str]] = {}
    eligible_stages: dict[str, list[str]] = {}

    for ds in CONFIRMATORY_DATASETS:
        # Determine eligibility from original validation partition
        # Combine across seeds to count unique engines
        sample_traj = cached_trajectories[(ds, "GBR", 2026)]
        reg_counts = sample_traj.groupby("regime")["unit"].nunique()
        stg_counts = sample_traj.groupby("lifecycle_stage")["unit"].nunique()
        eligible_regimes[ds] = sorted(
            [str(r) for r, cnt in reg_counts.items() if cnt >= SUBGROUP_MIN_ENGINES]
        )
        eligible_stages[ds] = sorted(
            [str(s) for s, cnt in stg_counts.items() if cnt >= SUBGROUP_MIN_ENGINES]
        )

    for exp_cfg in all_expected_cfgs:
        ds, fam, s, m_id, cov, scen = exp_cfg
        u_cfg = (ds, fam, m_id, cov, scen)
        for u in expected_units[ds]:
            cost_u = float(
                np.mean(
                    [
                        reconstructed_outcomes[(ds, fam, sd, m_id, cov, scen, u)]["total_cost"]
                        for sd in CONFIRMATORY_SEEDS
                    ]
                )
            )
            engine_cost_map[u_cfg][u] = cost_u

            if m_id != CONTROL_SAFETY_MARGIN:
                cov_u = float(
                    np.mean(
                        [
                            cell_unit_dict[((ds, fam, sd, m_id, cov), u)]["cov_mean"]
                            for sd in CONFIRMATORY_SEEDS
                        ]
                    )
                )
                mpiw_u = float(
                    np.mean(
                        [
                            cell_unit_dict[((ds, fam, sd, m_id, cov), u)]["width_mean"]
                            for sd in CONFIRMATORY_SEEDS
                        ]
                    )
                )
                is_u = float(
                    np.mean(
                        [
                            cell_unit_dict[((ds, fam, sd, m_id, cov), u)]["is_mean"]
                            for sd in CONFIRMATORY_SEEDS
                        ]
                    )
                )
                engine_cov_map[u_cfg][u] = cov_u
                engine_mpiw_map[u_cfg][u] = mpiw_u
                engine_is_map[u_cfg][u] = is_u

    # Populate subgroup engine coverage maps for primary configurations (90% cov, primary scen)
    for ds in CONFIRMATORY_DATASETS:
        for fam in CONFIRMATORY_MODELS:
            for m_id in ("decision_aware_hcp", "global_hcp", "regime_hcp"):
                u_cfg = (ds, fam, m_id, PRIMARY_CANONICAL_COVERAGE, PRIMARY_COST_SCENARIO)
                cell_keys = [
                    (ds, fam, sd, m_id, PRIMARY_CANONICAL_COVERAGE) for sd in CONFIRMATORY_SEEDS
                ]

                for reg in eligible_regimes[ds]:
                    for u in expected_units[ds]:
                        cov_list = []
                        for ck in cell_keys:
                            u_d = cell_unit_dict[(ck, u)]
                            mask = u_d["regime"] == reg
                            if np.any(mask):
                                cov_list.append(float(np.mean(u_d["covered"][mask])))
                        if cov_list:
                            engine_regime_cov_map[u_cfg][reg][u] = float(np.mean(cov_list))

                for stg in eligible_stages[ds]:
                    for u in expected_units[ds]:
                        cov_list = []
                        for ck in cell_keys:
                            u_d = cell_unit_dict[(ck, u)]
                            mask = u_d["lifecycle_stage"] == stg
                            if np.any(mask):
                                cov_list.append(float(np.mean(u_d["covered"][mask])))
                        if cov_list:
                            engine_stage_cov_map[u_cfg][stg][u] = float(np.mean(cov_list))

    def _compute_replicate_subgroup_bounds(
        M_mat: np.ndarray[Any, Any],
        engs_list: list[int],
        cov_map: dict[str, dict[int, float]],
        el_groups: list[str],
        nom_cov: float = 0.90,
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        n_boot = M_mat.shape[0]
        if len(el_groups) == 0:
            return np.zeros(n_boot, dtype=float), np.full(n_boot, nom_cov, dtype=float)

        all_l: list[np.ndarray[Any, Any]] = []
        all_u: list[np.ndarray[Any, Any]] = []
        eng_idx_map = {u: i for i, u in enumerate(engs_list)}

        for grp in el_groups:
            c_dict = cov_map.get(grp, {})
            grp_engs = sorted(c_dict.keys())
            if len(grp_engs) == 0:
                all_l.append(np.zeros(n_boot, dtype=float))
                all_u.append(np.full(n_boot, nom_cov, dtype=float))
                continue

            indices = [eng_idx_map[u] for u in grp_engs]
            c_arr = np.array([c_dict[u] for u in grp_engs], dtype=float)
            w = M_mat[:, indices]
            sum_w = np.sum(w, axis=1)
            active = sum_w > 0

            cov_g = np.zeros(n_boot, dtype=float)
            cov_g[active] = (w[active] @ c_arr) / sum_w[active]
            err_g = np.abs(cov_g - nom_cov)

            low_g = np.where(active, err_g, 0.0)
            up_g = np.where(active, err_g, nom_cov)
            all_l.append(low_g)
            all_u.append(up_g)

        return np.max(all_l, axis=0), np.max(all_u, axis=0)

    # Compute Replicate Arrays
    reconstructed_stats: dict[str, dict[str, np.ndarray[Any, Any]]] = {
        ds: {} for ds in CONFIRMATORY_DATASETS
    }
    reconstructed_stats["RQ4"] = {}

    for ds in CONFIRMATORY_DATASETS:
        M_mat = multiplicity_matrices[ds]
        engs = expected_units[ds]
        N_eng = len(engs)

        for fam in CONFIRMATORY_MODELS:
            prop_cfg = (
                ds,
                fam,
                "decision_aware_hcp",
                PRIMARY_CANONICAL_COVERAGE,
                PRIMARY_COST_SCENARIO,
            )
            v_cost_prop = np.array([engine_cost_map[prop_cfg][u] for u in engs], dtype=float)
            rep_cost_prop = (M_mat @ v_cost_prop) / N_eng
            reconstructed_stats[ds][f"{fam}_decision_aware_hcp_cost"] = rep_cost_prop

            v_cov_prop = np.array([engine_cov_map[prop_cfg][u] for u in engs], dtype=float)
            rep_cov_prop = (M_mat @ v_cov_prop) / N_eng
            rep_cov_err = np.abs(rep_cov_prop - 0.90)
            reconstructed_stats[ds][f"{fam}_decision_aware_hcp_marginal_coverage_error"] = (
                rep_cov_err
            )
            reconstructed_stats[ds][f"{ds}_{fam}_decision_aware_hcp_marginal_coverage_error"] = (
                rep_cov_err
            )

            # Subgroup errors for proposed method
            p_reg_l, p_reg_u = _compute_replicate_subgroup_bounds(
                M_mat, engs, engine_regime_cov_map[prop_cfg], eligible_regimes[ds], nom_cov=0.90
            )
            reconstructed_stats[ds][f"{fam}_decision_aware_hcp_regime_error_lower"] = p_reg_l
            reconstructed_stats[ds][f"{fam}_decision_aware_hcp_regime_error_upper"] = p_reg_u
            reconstructed_stats[ds][f"{ds}_{fam}_decision_aware_hcp_regime_error_lower"] = p_reg_l
            reconstructed_stats[ds][f"{ds}_{fam}_decision_aware_hcp_regime_error_upper"] = p_reg_u

            p_stg_l, p_stg_u = _compute_replicate_subgroup_bounds(
                M_mat, engs, engine_stage_cov_map[prop_cfg], eligible_stages[ds], nom_cov=0.90
            )
            reconstructed_stats[ds][f"{fam}_decision_aware_hcp_stage_error_lower"] = p_stg_l
            reconstructed_stats[ds][f"{fam}_decision_aware_hcp_stage_error_upper"] = p_stg_u
            reconstructed_stats[ds][f"{ds}_{fam}_decision_aware_hcp_stage_error_lower"] = p_stg_l
            reconstructed_stats[ds][f"{ds}_{fam}_decision_aware_hcp_stage_error_upper"] = p_stg_u

            # Baselines
            for base_id in ("global_hcp", "regime_hcp"):
                b_cfg = (ds, fam, base_id, PRIMARY_CANONICAL_COVERAGE, PRIMARY_COST_SCENARIO)
                v_cost_base = np.array([engine_cost_map[b_cfg][u] for u in engs], dtype=float)
                rep_cost_base = (M_mat @ v_cost_base) / N_eng
                reconstructed_stats[ds][f"{fam}_{base_id}_cost"] = rep_cost_base

                # Cost improvement
                delta_cost = rep_cost_base - rep_cost_prop
                reconstructed_stats[ds][f"{ds}_{fam}_{base_id}_cost_improvement"] = delta_cost

                # Regime error improvement
                b_reg_l, b_reg_u = _compute_replicate_subgroup_bounds(
                    M_mat, engs, engine_regime_cov_map[b_cfg], eligible_regimes[ds], nom_cov=0.90
                )
                reconstructed_stats[ds][f"{fam}_{base_id}_regime_error_lower"] = b_reg_l
                reconstructed_stats[ds][f"{fam}_{base_id}_regime_error_upper"] = b_reg_u
                delta_reg_l = b_reg_l - p_reg_u
                delta_reg_u = b_reg_u - p_reg_l
                reconstructed_stats[ds][f"{ds}_{fam}_{base_id}_regime_error_improvement_lower"] = (
                    delta_reg_l
                )
                reconstructed_stats[ds][f"{ds}_{fam}_{base_id}_regime_error_improvement_upper"] = (
                    delta_reg_u
                )

                # Stage error improvement
                b_stg_l, b_stg_u = _compute_replicate_subgroup_bounds(
                    M_mat, engs, engine_stage_cov_map[b_cfg], eligible_stages[ds], nom_cov=0.90
                )
                reconstructed_stats[ds][f"{fam}_{base_id}_stage_error_lower"] = b_stg_l
                reconstructed_stats[ds][f"{fam}_{base_id}_stage_error_upper"] = b_stg_u
                delta_stg_l = b_stg_l - p_stg_u
                delta_stg_u = b_stg_u - p_stg_l
                reconstructed_stats[ds][f"{ds}_{fam}_{base_id}_stage_error_improvement_lower"] = (
                    delta_stg_l
                )
                reconstructed_stats[ds][f"{ds}_{fam}_{base_id}_stage_error_improvement_upper"] = (
                    delta_stg_u
                )

                # MPIW deterioration
                v_mpiw_prop = np.array([engine_mpiw_map[prop_cfg][u] for u in engs], dtype=float)
                v_mpiw_base = np.array([engine_mpiw_map[b_cfg][u] for u in engs], dtype=float)
                mpiw_det = (M_mat @ (v_mpiw_prop - v_mpiw_base)) / N_eng
                reconstructed_stats[ds][f"{ds}_{fam}_{base_id}_mpiw_deterioration"] = mpiw_det

                # Interval score deterioration
                v_is_prop = np.array([engine_is_map[prop_cfg][u] for u in engs], dtype=float)
                v_is_base = np.array([engine_is_map[b_cfg][u] for u in engs], dtype=float)
                is_det = (M_mat @ (v_is_prop - v_is_base)) / N_eng
                reconstructed_stats[ds][f"{ds}_{fam}_{base_id}_interval_score_deterioration"] = (
                    is_det
                )

            # Controls on FD002
            if ds == "FD002":
                for ctrl_id in CONTROL_ALL_FOUR:
                    c_cfg = (
                        "FD002",
                        fam,
                        ctrl_id,
                        PRIMARY_CANONICAL_COVERAGE,
                        PRIMARY_COST_SCENARIO,
                    )
                    v_cost_ctrl = np.array([engine_cost_map[c_cfg][u] for u in engs], dtype=float)
                    rep_cost_ctrl = (M_mat @ v_cost_ctrl) / N_eng
                    reconstructed_stats["FD002"][f"{fam}_{ctrl_id}_cost"] = rep_cost_ctrl
                    reconstructed_stats["FD002"][f"FD002_{fam}_{ctrl_id}_cost_improvement"] = (
                        rep_cost_ctrl - rep_cost_prop
                    )

    # RQ4 Aggregates (6 cells)
    six_cells = [
        ("FD001", "GBR"),
        ("FD001", "LSTM"),
        ("FD002", "GBR"),
        ("FD002", "LSTM"),
        ("FD004", "GBR"),
        ("FD004", "LSTM"),
    ]
    for base_id in ("global_hcp", "regime_hcp"):
        agg_cost = np.mean(
            [reconstructed_stats[d][f"{d}_{f}_{base_id}_cost_improvement"] for d, f in six_cells],
            axis=0,
        )
        reconstructed_stats["RQ4"][f"agg_{base_id}_cost_improvement"] = agg_cost
        reconstructed_stats["RQ4"][f"aggregate_{base_id}_cost_improvement"] = agg_cost

        agg_reg_l = np.mean(
            [
                reconstructed_stats[d][f"{d}_{f}_{base_id}_regime_error_improvement_lower"]
                for d, f in six_cells
            ],
            axis=0,
        )
        agg_reg_u = np.mean(
            [
                reconstructed_stats[d][f"{d}_{f}_{base_id}_regime_error_improvement_upper"]
                for d, f in six_cells
            ],
            axis=0,
        )
        reconstructed_stats["RQ4"][f"agg_{base_id}_regime_error_improvement_lower"] = agg_reg_l
        reconstructed_stats["RQ4"][f"agg_{base_id}_regime_error_improvement_upper"] = agg_reg_u

        agg_stg_l = np.mean(
            [
                reconstructed_stats[d][f"{d}_{f}_{base_id}_stage_error_improvement_lower"]
                for d, f in six_cells
            ],
            axis=0,
        )
        agg_stg_u = np.mean(
            [
                reconstructed_stats[d][f"{d}_{f}_{base_id}_stage_error_improvement_upper"]
                for d, f in six_cells
            ],
            axis=0,
        )
        reconstructed_stats["RQ4"][f"agg_{base_id}_stage_error_improvement_lower"] = agg_stg_l
        reconstructed_stats["RQ4"][f"agg_{base_id}_stage_error_improvement_upper"] = agg_stg_u

    # Validate against NPZ files on disk
    npz_mismatches: list[str] = []
    max_npz_discrepancy = 0.0
    total_npz_arrays_checked = 0

    expected_numeric_counts = {"FD001": 70, "FD002": 86, "FD004": 70, "RQ4": 12}

    for target_key in ("FD001", "FD002", "FD004", "RQ4"):
        target_npz_path = s_dir / f"bootstrap_statistics_{target_key}.npz"
        if not target_npz_path.exists():
            npz_mismatches.append(f"Missing NPZ file: {target_npz_path}")
            continue

        saved_npz = np.load(target_npz_path)
        saved_numeric_keys = [k for k in saved_npz.files if k != "__metadata__"]
        exp_count = expected_numeric_counts[target_key]

        if len(saved_numeric_keys) != exp_count:
            npz_mismatches.append(
                f"{target_key} numeric array count {len(saved_numeric_keys)} "
                f"!= expected {exp_count}"
            )

        # Compare each reconstructed array
        for arr_k, exp_arr in reconstructed_stats[target_key].items():
            total_npz_arrays_checked += 1
            if arr_k not in saved_npz.files:
                npz_mismatches.append(f"Array key '{arr_k}' missing from {target_key} NPZ")
                continue
            saved_arr = saved_npz[arr_k]
            if saved_arr.shape != (10000,):
                npz_mismatches.append(f"{target_key}/{arr_k} shape {saved_arr.shape} != (10000,)")
            if not np.all(np.isfinite(saved_arr)):
                npz_mismatches.append(f"Non-finite values in {target_key}/{arr_k}")

            diff = float(np.max(np.abs(saved_arr - exp_arr)))
            if diff > max_npz_discrepancy:
                max_npz_discrepancy = diff
            if diff > TOL_ATOL:
                npz_mismatches.append(f"{target_key}/{arr_k} discrepancy {diff} > {TOL_ATOL}")

        # Validate aliases equality
        if target_key == "RQ4":
            for b_id in ("global_hcp", "regime_hcp"):
                k1 = f"agg_{b_id}_cost_improvement"
                k2 = f"aggregate_{b_id}_cost_improvement"
                if not np.array_equal(saved_npz[k1], saved_npz[k2]):
                    npz_mismatches.append(f"Alias mismatch in RQ4: {k1} != {k2}")
        else:
            ds = target_key
            for fam in CONFIRMATORY_MODELS:
                for suffix in (
                    "marginal_coverage_error",
                    "regime_error_lower",
                    "regime_error_upper",
                    "stage_error_lower",
                    "stage_error_upper",
                ):
                    k1 = f"{fam}_decision_aware_hcp_{suffix}"
                    k2 = f"{ds}_{fam}_decision_aware_hcp_{suffix}"
                    if k1 not in saved_npz.files or k2 not in saved_npz.files:
                        npz_mismatches.append(f"Alias key missing in {ds}: {k1} or {k2}")
                    elif not np.array_equal(saved_npz[k1], saved_npz[k2]):
                        npz_mismatches.append(f"Alias mismatch in {ds}: {k1} != {k2}")

        # Validate lower <= upper for all bounded arrays
        for k in saved_numeric_keys:
            if k.endswith("_lower"):
                k_up = k[:-6] + "_upper"
                if k_up in saved_npz.files:
                    _check_finite_and_bounds(saved_npz[k], saved_npz[k_up], f"{target_key}/{k}")

    checks["bootstrap_statistics_npz_reconstruction"] = {
        "status": "PASS"
        if (len(npz_mismatches) == 0 and max_npz_discrepancy <= TOL_ATOL)
        else "FAIL",
        "total_numeric_arrays_checked": total_npz_arrays_checked,
        "max_discrepancy": max_npz_discrepancy,
        "mismatches_count": len(npz_mismatches),
    }
    if npz_mismatches:
        failing_reasons.append(f"Bootstrap statistics NPZ discrepancies: {npz_mismatches[:5]}")

    # -------------------------------------------------------------------------
    # 8. Reconstruct contrast_intervals.csv (74 contrasts)
    # -------------------------------------------------------------------------
    stat_specs = get_expected_contrast_statistic_specs()
    df_contrasts = pd.read_csv(s_dir / "contrast_intervals.csv", float_precision="round_trip")
    contrast_mismatches: list[str] = []
    max_contrast_discrepancy = 0.0

    contrast_row_map = {str(r.contrast_id): r for r in df_contrasts.itertuples()}

    for stat_id, spec in stat_specs.items():
        if stat_id not in contrast_row_map:
            contrast_mismatches.append(f"Contrast {stat_id} missing from contrast_intervals.csv")
            continue

        c_row = contrast_row_map[stat_id]
        target_group = "RQ4" if spec.target_npz == "bootstrap_statistics_RQ4.npz" else spec.dataset

        if spec.is_bounded:
            assert spec.lower_array_key is not None and spec.upper_array_key is not None
            arr_low = reconstructed_stats[target_group][spec.lower_array_key]
            arr_up = reconstructed_stats[target_group][spec.upper_array_key]

            exp_mean = float(np.mean(0.5 * (arr_low + arr_up)))
            exp_median = float(np.median(0.5 * (arr_low + arr_up)))
            exp_ci_95_l = float(np.quantile(arr_low, 0.025, method="linear"))
            exp_ci_95_h = float(np.quantile(arr_up, 0.975, method="linear"))
            exp_ci_dec_l = float(np.quantile(arr_low, 0.00625, method="linear"))
            exp_ci_dec_h = float(np.quantile(arr_up, 0.99375, method="linear"))
        else:
            assert spec.array_key is not None
            rep_arr = reconstructed_stats[target_group][spec.array_key]
            exp_mean = float(np.mean(rep_arr))
            exp_median = float(np.median(rep_arr))
            exp_ci_95_l = float(np.quantile(rep_arr, 0.025, method="linear"))
            exp_ci_95_h = float(np.quantile(rep_arr, 0.975, method="linear"))
            exp_ci_dec_l = float(np.quantile(rep_arr, 0.00625, method="linear"))
            exp_ci_dec_h = float(np.quantile(rep_arr, 0.99375, method="linear"))

        # Check metadata
        if (
            str(c_row.dataset) != spec.dataset
            or str(c_row.comparator) != spec.comparator
            or str(c_row.metric) != spec.metric
        ):
            contrast_mismatches.append(f"Metadata mismatch for contrast {stat_id}")
        if abs(float(c_row.margin) - spec.margin) > 1e-12:
            contrast_mismatches.append(f"Margin mismatch for contrast {stat_id}")
        if str(c_row.status) != "DEVELOPMENT_SMOKE_ONLY":
            contrast_mismatches.append(f"Status not DEVELOPMENT_SMOKE_ONLY for contrast {stat_id}")

        # Check numerical values
        d_mean = abs(float(c_row.mean) - exp_mean)
        d_med = abs(float(c_row.median) - exp_median)
        d_95_l = abs(float(c_row.ci_95_low) - exp_ci_95_l)
        d_95_h = abs(float(c_row.ci_95_high) - exp_ci_95_h)
        d_dec_l = abs(float(c_row.ci_decision_low) - exp_ci_dec_l)
        d_dec_h = abs(float(c_row.ci_decision_high) - exp_ci_dec_h)

        cur_d = max(d_mean, d_med, d_95_l, d_95_h, d_dec_l, d_dec_h)
        if cur_d > max_contrast_discrepancy:
            max_contrast_discrepancy = cur_d
        if cur_d > TOL_ATOL:
            contrast_mismatches.append(
                f"Numerical discrepancy in contrast {stat_id}: {cur_d} > {TOL_ATOL}"
            )

    checks["contrast_intervals_reconstruction"] = {
        "status": "PASS"
        if (len(contrast_mismatches) == 0 and len(df_contrasts) == len(stat_specs))
        else "FAIL",
        "expected_contrasts_count": len(stat_specs),
        "actual_contrasts_count": len(df_contrasts),
        "max_discrepancy": max_contrast_discrepancy,
        "mismatches_count": len(contrast_mismatches),
    }
    if contrast_mismatches:
        failing_reasons.append(f"Contrast intervals discrepancies: {contrast_mismatches[:5]}")

    # -------------------------------------------------------------------------
    # 9. Verify All 152 Component Evidence Records Numerically & Semantically
    # -------------------------------------------------------------------------
    manifest_rq = get_rq_component_manifest()
    all_comps = [c for rq in ("RQ1", "RQ2", "RQ3", "RQ4") for c in manifest_rq[rq]]
    df_comp = pd.read_csv(s_dir / "component_evidence.csv", float_precision="round_trip")
    comp_row_map = {str(r.component_id): r for r in df_comp.itertuples()}

    component_mismatches: list[str] = []
    max_comp_discrepancy = 0.0

    def get_obs_subgroup_err(d: str, m_fam: str, meth: str, fam_type: str) -> float:
        cfg = (d, m_fam, meth, PRIMARY_CANONICAL_COVERAGE, PRIMARY_COST_SCENARIO)
        c_map = engine_regime_cov_map[cfg] if fam_type == "regime" else engine_stage_cov_map[cfg]
        el_grps = eligible_regimes[d] if fam_type == "regime" else eligible_stages[d]
        if len(el_grps) == 0:
            return 0.90
        max_e = 0.0
        for grp in el_grps:
            c_dict = c_map.get(grp, {})
            if len(c_dict) > 0:
                c_val = float(np.mean(list(c_dict.values())))
                e_val = abs(c_val - 0.90)
                if e_val > max_e:
                    max_e = e_val
        return max_e

    for comp in all_comps:
        cid = comp.component_id
        if cid not in comp_row_map:
            component_mismatches.append(f"Component {cid} missing from component_evidence.csv")
            continue

        r = comp_row_map[cid]
        ev_kind, stat_id = map_component_to_evidence_spec(
            component_id=cid,
            rq_id=comp.rq_id,
            model_family=comp.model_family,
            dataset=comp.dataset,
            comparator=comp.comparator,
            metric=comp.metric,
            rule_type=comp.rule_type,
        )

        # Validate metadata fields
        if str(r.rq_id) != comp.rq_id:
            component_mismatches.append(f"{cid}: rq_id mismatch ({r.rq_id} != {comp.rq_id})")
        if str(r.dataset) != (comp.dataset or "ALL_6_CELLS"):
            component_mismatches.append(f"{cid}: dataset mismatch ({r.dataset})")
        if str(r.model_family) != (comp.model_family or "BOTH"):
            component_mismatches.append(f"{cid}: model_family mismatch ({r.model_family})")
        if (
            str(r.comparator) != comp.comparator
            or str(r.metric) != comp.metric
            or str(r.rule_type) != comp.rule_type
        ):
            component_mismatches.append(f"{cid}: comparator/metric/rule_type mismatch")
        if abs(float(r.margin) - comp.margin) > 1e-12:
            component_mismatches.append(f"{cid}: margin mismatch ({r.margin} != {comp.margin})")
        if str(r.evidence_kind) != ev_kind or str(r.statistic_id) != stat_id:
            component_mismatches.append(f"{cid}: evidence_kind/statistic_id mismatch")
        if str(r.status) != "DEVELOPMENT_SMOKE_ONLY":
            component_mismatches.append(f"{cid}: status not DEVELOPMENT_SMOKE_ONLY")

        # Reconstruct numerical values
        if ev_kind == "observed_failure":
            assert comp.dataset is not None and comp.model_family is not None
            exp_prop_fails = sum(
                1
                for s in CONFIRMATORY_SEEDS
                for u in expected_units[comp.dataset]
                if reconstructed_outcomes[
                    (
                        comp.dataset,
                        comp.model_family,
                        s,
                        "decision_aware_hcp",
                        PRIMARY_CANONICAL_COVERAGE,
                        PRIMARY_COST_SCENARIO,
                        u,
                    )
                ]["failed"]
            )
            exp_comp_fails = sum(
                1
                for s in CONFIRMATORY_SEEDS
                for u in expected_units[comp.dataset]
                if reconstructed_outcomes[
                    (
                        comp.dataset,
                        comp.model_family,
                        s,
                        comp.comparator,
                        PRIMARY_CANONICAL_COVERAGE,
                        PRIMARY_COST_SCENARIO,
                        u,
                    )
                ]["failed"]
            )

            if (
                pd.notna(r.observed_lower)
                or pd.notna(r.observed_upper)
                or pd.notna(r.ci_95_low)
                or pd.notna(r.ci_decision_low)
            ):
                component_mismatches.append(
                    f"{cid}: expected NaN for interval fields in failure safeguard"
                )
            if (
                int(r.proposed_failure_count) != exp_prop_fails
                or int(r.comparator_failure_count) != exp_comp_fails
            ):
                component_mismatches.append(
                    f"{cid}: failure count mismatch: proposed "
                    f"({r.proposed_failure_count} != {exp_prop_fails}), "
                    f"comparator ({r.comparator_failure_count} != {exp_comp_fails})"
                )
        elif comp.comparator == "nominal_90":
            assert comp.dataset is not None and comp.model_family is not None
            d = comp.dataset
            fam = comp.model_family
            cfg_da = (
                d,
                fam,
                "decision_aware_hcp",
                PRIMARY_CANONICAL_COVERAGE,
                PRIMARY_COST_SCENARIO,
            )

            if pd.notna(r.proposed_failure_count) or pd.notna(r.comparator_failure_count):
                component_mismatches.append(
                    f"{cid}: failure counts must be NaN for ceiling components"
                )

            if comp.metric == "marginal_coverage_abs_error":
                obs_cov = float(np.mean([engine_cov_map[cfg_da][u] for u in expected_units[d]]))
                exp_obs = abs(obs_cov - 0.90)
                rep_arr = reconstructed_stats[d][stat_id]
                exp_ci_95_l = float(np.quantile(rep_arr, 0.025, method="linear"))
                exp_ci_95_h = float(np.quantile(rep_arr, 0.975, method="linear"))
                exp_ci_dec_l = float(np.quantile(rep_arr, 0.00625, method="linear"))
                exp_ci_dec_h = float(np.quantile(rep_arr, 0.99375, method="linear"))
            elif comp.metric == "worst_regime_coverage_error":
                exp_obs = get_obs_subgroup_err(d, fam, "decision_aware_hcp", "regime")
                arr_l = reconstructed_stats[d][f"{stat_id}_lower"]
                arr_u = reconstructed_stats[d][f"{stat_id}_upper"]
                exp_ci_95_l = float(np.quantile(arr_l, 0.025, method="linear"))
                exp_ci_95_h = float(np.quantile(arr_u, 0.975, method="linear"))
                exp_ci_dec_l = float(np.quantile(arr_l, 0.00625, method="linear"))
                exp_ci_dec_h = float(np.quantile(arr_u, 0.99375, method="linear"))
            elif comp.metric == "worst_stage_coverage_error":
                exp_obs = get_obs_subgroup_err(d, fam, "decision_aware_hcp", "stage")
                arr_l = reconstructed_stats[d][f"{stat_id}_lower"]
                arr_u = reconstructed_stats[d][f"{stat_id}_upper"]
                exp_ci_95_l = float(np.quantile(arr_l, 0.025, method="linear"))
                exp_ci_95_h = float(np.quantile(arr_u, 0.975, method="linear"))
                exp_ci_dec_l = float(np.quantile(arr_l, 0.00625, method="linear"))
                exp_ci_dec_h = float(np.quantile(arr_u, 0.99375, method="linear"))
            else:
                raise ValueError(f"Unknown ceiling metric: {comp.metric}")

            d_ol = abs(float(r.observed_lower) - exp_obs)
            d_ou = abs(float(r.observed_upper) - exp_obs)
            d_95_l = abs(float(r.ci_95_low) - exp_ci_95_l)
            d_95_h = abs(float(r.ci_95_high) - exp_ci_95_h)
            d_dec_l = abs(float(r.ci_decision_low) - exp_ci_dec_l)
            d_dec_h = abs(float(r.ci_decision_high) - exp_ci_dec_h)

            cur_d = max(d_ol, d_ou, d_95_l, d_95_h, d_dec_l, d_dec_h)
            if cur_d > max_comp_discrepancy:
                max_comp_discrepancy = cur_d
            if cur_d > TOL_ATOL:
                component_mismatches.append(f"{cid}: discrepancy {cur_d} > {TOL_ATOL}")
        else:
            # Contrast components
            if pd.notna(r.proposed_failure_count) or pd.notna(r.comparator_failure_count):
                component_mismatches.append(
                    f"{cid}: failure counts must be NaN for contrast components"
                )

            if stat_id not in contrast_row_map:
                component_mismatches.append(
                    f"{cid}: statistic_id '{stat_id}' not found in contrast_intervals.csv"
                )
                continue

            c_info = contrast_row_map[stat_id]
            exp_ci_95_l = float(c_info.ci_95_low)
            exp_ci_95_h = float(c_info.ci_95_high)
            exp_ci_dec_l = float(c_info.ci_decision_low)
            exp_ci_dec_h = float(c_info.ci_decision_high)

            if comp.rq_id == "RQ4" and comp.dataset is None:
                if comp.metric == "aggregate_delta_cost":
                    vals = [
                        float(
                            np.mean(
                                [
                                    engine_cost_map[
                                        (
                                            d,
                                            f,
                                            comp.comparator,
                                            PRIMARY_CANONICAL_COVERAGE,
                                            PRIMARY_COST_SCENARIO,
                                        )
                                    ][u]
                                    for u in expected_units[d]
                                ]
                            )
                        )
                        - float(
                            np.mean(
                                [
                                    engine_cost_map[
                                        (
                                            d,
                                            f,
                                            "decision_aware_hcp",
                                            PRIMARY_CANONICAL_COVERAGE,
                                            PRIMARY_COST_SCENARIO,
                                        )
                                    ][u]
                                    for u in expected_units[d]
                                ]
                            )
                        )
                        for d, f in six_cells
                    ]
                    exp_obs = float(np.mean(vals))
                elif comp.metric == "aggregate_delta_regime_error":
                    vals_r = [
                        get_obs_subgroup_err(d, f, comp.comparator, "regime")
                        - get_obs_subgroup_err(d, f, "decision_aware_hcp", "regime")
                        for d, f in six_cells
                    ]
                    exp_obs = float(np.mean(vals_r))
                elif comp.metric == "aggregate_delta_stage_error":
                    vals_s = [
                        get_obs_subgroup_err(d, f, comp.comparator, "stage")
                        - get_obs_subgroup_err(d, f, "decision_aware_hcp", "stage")
                        for d, f in six_cells
                    ]
                    exp_obs = float(np.mean(vals_s))
                else:
                    raise ValueError(f"Unknown RQ4 metric: {comp.metric}")
            else:
                assert comp.dataset is not None and comp.model_family is not None
                d = comp.dataset
                fam = comp.model_family
                cfg_da = (
                    d,
                    fam,
                    "decision_aware_hcp",
                    PRIMARY_CANONICAL_COVERAGE,
                    PRIMARY_COST_SCENARIO,
                )
                cfg_comp = (
                    d,
                    fam,
                    comp.comparator,
                    PRIMARY_CANONICAL_COVERAGE,
                    PRIMARY_COST_SCENARIO,
                )

                if comp.metric in ("delta_cost", "cell_delta_cost"):
                    c_base = float(
                        np.mean([engine_cost_map[cfg_comp][u] for u in expected_units[d]])
                    )
                    c_prop = float(np.mean([engine_cost_map[cfg_da][u] for u in expected_units[d]]))
                    exp_obs = c_base - c_prop
                elif comp.metric in ("delta_regime_error", "cell_delta_regime_error"):
                    e_base = get_obs_subgroup_err(d, fam, comp.comparator, "regime")
                    e_prop = get_obs_subgroup_err(d, fam, "decision_aware_hcp", "regime")
                    exp_obs = e_base - e_prop
                elif comp.metric in ("delta_stage_error", "cell_delta_stage_error"):
                    e_base = get_obs_subgroup_err(d, fam, comp.comparator, "stage")
                    e_prop = get_obs_subgroup_err(d, fam, "decision_aware_hcp", "stage")
                    exp_obs = e_base - e_prop
                elif comp.metric == "mpiw_deterioration":
                    w_prop = float(np.mean([engine_mpiw_map[cfg_da][u] for u in expected_units[d]]))
                    w_base = float(
                        np.mean([engine_mpiw_map[cfg_comp][u] for u in expected_units[d]])
                    )
                    exp_obs = w_prop - w_base
                elif comp.metric == "interval_score_deterioration":
                    is_prop = float(np.mean([engine_is_map[cfg_da][u] for u in expected_units[d]]))
                    is_base = float(
                        np.mean([engine_is_map[cfg_comp][u] for u in expected_units[d]])
                    )
                    exp_obs = is_prop - is_base
                else:
                    raise ValueError(f"Unknown metric: {comp.metric}")

            d_ol = abs(float(r.observed_lower) - exp_obs)
            d_ou = abs(float(r.observed_upper) - exp_obs)
            d_95_l = abs(float(r.ci_95_low) - exp_ci_95_l)
            d_95_h = abs(float(r.ci_95_high) - exp_ci_95_h)
            d_dec_l = abs(float(r.ci_decision_low) - exp_ci_dec_l)
            d_dec_h = abs(float(r.ci_decision_high) - exp_ci_dec_h)

            cur_d = max(d_ol, d_ou, d_95_l, d_95_h, d_dec_l, d_dec_h)
            if cur_d > max_comp_discrepancy:
                max_comp_discrepancy = cur_d
            if cur_d > TOL_ATOL:
                component_mismatches.append(f"{cid}: discrepancy {cur_d} > {TOL_ATOL}")

    checks["component_evidence_reconstruction"] = {
        "status": "PASS"
        if (len(component_mismatches) == 0 and len(df_comp) == EXPECTED_TOTAL_COMPONENTS_COUNT)
        else "FAIL",
        "expected_count": EXPECTED_TOTAL_COMPONENTS_COUNT,
        "actual_count": len(df_comp),
        "max_discrepancy": max_comp_discrepancy,
        "mismatches_count": len(component_mismatches),
    }
    if component_mismatches:
        failing_reasons.append(f"Component evidence discrepancies: {component_mismatches[:5]}")

    all_passed = (
        len(failing_reasons) == 0
        and checks["validation_engine_counts"]["status"] == "PASS"
        and checks["point_predictions_complete_reconstruction"]["status"] == "PASS"
        and checks["interval_reconstruction"]["status"] == "PASS"
        and checks["engine_seed_outcomes_reconstruction"]["status"] == "PASS"
        and checks["decision_traces_reconstruction"]["status"] == "PASS"
        and checks["engine_metrics_reconstruction"]["status"] == "PASS"
        and checks["cell_summary_reconstruction"]["status"] == "PASS"
        and checks["bootstrap_draws_exact_reconstruction"]["status"] == "PASS"
        and checks["bootstrap_statistics_npz_reconstruction"]["status"] == "PASS"
        and checks["contrast_intervals_reconstruction"]["status"] == "PASS"
        and checks["component_evidence_reconstruction"]["status"] == "PASS"
    )

    return {
        "status": "PASS" if all_passed else "FAIL",
        "overall_match": all_passed,
        "failing_reasons": failing_reasons,
        "checks": checks,
    }
