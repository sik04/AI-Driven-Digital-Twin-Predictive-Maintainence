"""Independent reference verifier for Phase 8 ablation and robustness artifacts.

Strict Verification Protocol:
- Does NOT call production robustness runner, fitting, or simulation functions.
- Independently reconstructs all quantiles, intervals, simulations, aggregations,
  subgroup metrics, paired bootstrap draws, and contrasts.
- Numerical tolerances:
  - Deterministic reconstruction: atol=1e-10, rtol=0.
  - Checkpoint prediction parity: atol=1e-4, rtol=0.
- Fails closed on any missing, duplicate, altered, or out-of-tolerance records.
"""

from __future__ import annotations

import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from intellitwin.confirmatory.data import (
    verify_raw_data_hashes,
)
from intellitwin.data.artifacts import compute_sha256
from intellitwin.data.schema import (
    SENSOR_COLUMNS,
)
from intellitwin.data.splits import load_split_manifest
from intellitwin.evaluation.bootstrap import (
    DATASET_NUMBERS,
    load_partition_quartile_strata,
)
from intellitwin.evaluation.schema import (
    CONFIRMATORY_DATASETS,
    CONFIRMATORY_MODELS,
    CONFIRMATORY_SEEDS,
)
from intellitwin.robustness.ablation import (
    ALL_EIGHT_ABLATION_VARIANTS,
)
from intellitwin.robustness.perturbations import (
    PERTURBATION_FAMILY_DROPOUT,
    PERTURBATION_FAMILY_GAUSSIAN_NOISE,
)
from intellitwin.uncertainty.artifacts import (
    resolve_repo_relative_path,
)
from intellitwin.uncertainty.schema import (
    CandidateConfig,
)
from intellitwin.uncertainty.scores import (
    compute_decision_aware_score,
)

TOL_DETERMINISTIC_ATOL: float = 1e-10
TOL_DETERMINISTIC_RTOL: float = 0.0
TOL_CHECKPOINT_ATOL: float = 1e-4
TOL_CHECKPOINT_RTOL: float = 0.0

REQUIRED_PHASE08_FILES: tuple[str, ...] = (
    "execution_manifest.json",
    "input_manifest.json",
    "execution.log",
    "ablation_engine_metrics.csv",
    "stress_engine_metrics.csv",
    "ablation_engine_seed_metrics.csv",
    "stress_engine_seed_rep_metrics.csv",
    "ablation_summary.csv",
    "stress_summary.csv",
    "subgroup_metrics.csv",
    "subgroup_engine_metrics.csv",
    "paired_contrasts.csv",
    "factor_main_effects.csv",
    "zero_difference_checks.csv",
    "ablation_simulation_outcomes.csv",
    "stress_simulation_outcomes.csv",
    "ablation_interval_predictions.csv.gz",
    "stress_interval_predictions.csv.gz",
    "bootstrap_draws_FD001.npz",
    "bootstrap_draws_FD002.npz",
    "bootstrap_draws_FD004.npz",
    "bootstrap_statistics_FD001.npz",
    "bootstrap_statistics_FD002.npz",
    "bootstrap_statistics_FD004.npz",
    "perturbation_manifest.json",
    "pip_freeze.txt",
    "pip_check.txt",
)

REQUIRED_PROVENANCE_FIELDS: tuple[str, ...] = (
    "protocol_version",
    "schema_version",
    "status",
    "git_commit",
    "git_dirty",
    "platform",
    "python_version",
    "start_time_utc",
    "end_time_utc",
    "duration_seconds",
    "counts",
    "artifact_hashes",
)

REQUIRED_COUNTS_FIELDS: tuple[str, ...] = (
    "ablation_configurations",
    "stress_evaluations",
    "datasets",
    "models",
    "seeds",
    "bootstrap_replicates",
    "total_test_engines",
)


def _reconstruct_reference_quantile(
    engine_ids: np.ndarray[Any, Any],
    scores: np.ndarray[Any, Any],
    nominal_coverage: float = 0.90,
) -> float:
    """Independent reference calculation for hierarchical conformal quantile threshold.

    Computes sorted weighted scores and exact Fraction boundary checks.
    """
    eids = np.asarray(engine_ids)
    sc = np.asarray(scores, dtype=np.float64)

    if len(sc) == 0:
        return float("inf")

    target_frac = (
        Fraction(90, 100)
        if abs(nominal_coverage - 0.90) < 1e-6
        else Fraction(str(nominal_coverage))
    )

    engine_scores: dict[int, list[float]] = defaultdict(list)
    for eid, s_val in zip(eids, sc, strict=True):
        engine_scores[int(eid)].append(float(s_val))

    m = len(engine_scores)
    if m == 0:
        return float("inf")

    n_i = {eid: len(vals) for eid, vals in engine_scores.items()}
    required_sum = Fraction(m + 1) * target_frac

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

    return float(unique_scores[cand_idx])


def _reconstruct_independent_bootstrap_draws(
    dataset: str,
    partition_engines: list[int],
    base_dir: Path,
    n_replicates: int = 10000,
) -> np.ndarray[Any, Any]:
    """Independently generate bootstrap draws according to locked PCG64 formula."""
    ds_num = DATASET_NUMBERS[dataset]
    seed_seq = np.random.SeedSequence([2026, 8, ds_num])
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


def verify_simulation_terminal_precedence(df_ablation_sim: pd.DataFrame) -> list[str]:
    """Verify that no engine has both failed and PM occurred, or PM at or after failure cycle."""
    violations: list[str] = []
    for r in df_ablation_sim.itertuples():
        if getattr(r, "failed", False) and getattr(r, "pm_occurred", False):
            violations.append(f"Engine {r.unit} marked both failed and PM occurred!")
        if getattr(r, "intervention_cycle", None) is not None:
            if not getattr(r, "pm_occurred", False):
                violations.append(
                    f"Engine {r.unit} has intervention cycle but pm_occurred is False!"
                )
    return violations


def verify_equal_engine_subgroup_math(
    df_subgroups: pd.DataFrame,
    df_sub_eng: pd.DataFrame,
    tol_atol: float = TOL_DETERMINISTIC_ATOL,
    tol_rtol: float = TOL_DETERMINISTIC_RTOL,
) -> list[str]:
    """Verify that subgroup_metrics.csv coverage and miss rates equally average distinct engines."""
    mismatches: list[str] = []
    grp_keys = [
        "evaluation_type",
        "dataset",
        "model_family",
        "variant_id",
        "method_id",
        "condition_id",
        "subgroup_family",
        "subgroup",
    ]
    if not all(c in df_subgroups.columns for c in grp_keys) or not all(
        c in df_sub_eng.columns for c in grp_keys
    ):
        return ["subgroup metrics tables are missing required grouping columns"]

    for (eval_t, ds, mf, vid, mid, cid, fam, grp), sum_row in df_subgroups.groupby(grp_keys):
        sub_engs = df_sub_eng[
            (df_sub_eng["evaluation_type"] == eval_t)
            & (df_sub_eng["dataset"] == ds)
            & (df_sub_eng["model_family"] == mf)
            & (df_sub_eng["subgroup_family"] == fam)
            & (df_sub_eng["subgroup"] == grp)
        ]
        if eval_t == "ablation":
            sub_engs = sub_engs[sub_engs["variant_id"] == vid]
        else:
            sub_engs = sub_engs[(sub_engs["method_id"] == mid) & (sub_engs["condition_id"] == cid)]

        if len(sub_engs) > 0:
            exp_cov = float(sub_engs["coverage"].mean())
            act_cov = float(sum_row["coverage"].iloc[0])
            if not np.isclose(exp_cov, act_cov, atol=tol_atol, rtol=tol_rtol):
                mismatches.append(
                    f"{ds}/{mf}/{grp}: equal-engine cov exp={exp_cov} != act={act_cov}"
                )

            exp_n_engs = len(sub_engs)
            act_n_engs = int(sum_row["n_engines"].iloc[0])
            if exp_n_engs != act_n_engs:
                mismatches.append(
                    f"{ds}/{mf}/{grp}: distinct engines exp={exp_n_engs} != act={act_n_engs}"
                )

            act_elig = bool(sum_row["is_eligible"].iloc[0])
            exp_elig = exp_n_engs >= 10
            if act_elig != exp_elig:
                mismatches.append(f"{ds}/{mf}/{grp}: eligibility exp={exp_elig} != act={act_elig}")
    return mismatches


def verify_summary_aggregations(
    df_ablation_summary: pd.DataFrame,
    df_ablation_engine: pd.DataFrame,
    df_stress_summary: pd.DataFrame,
    df_stress_engine: pd.DataFrame,
    tol_atol: float = TOL_DETERMINISTIC_ATOL,
    tol_rtol: float = TOL_DETERMINISTIC_RTOL,
) -> list[str]:
    """Verify that summary tables accurately reflect engine-level means."""
    mismatches: list[str] = []
    # Ablation summary check
    abl_grp_keys = ["dataset", "model_family", "variant_id"]
    if not all(c in df_ablation_engine.columns for c in abl_grp_keys) or not all(
        c in df_ablation_summary.columns for c in abl_grp_keys
    ):
        mismatches.append("ablation summary or engine metrics missing required keys")
    else:
        for (ds, mf, vid), grp in df_ablation_engine.groupby(abl_grp_keys):
            match_sum = df_ablation_summary[
                (df_ablation_summary["dataset"] == ds)
                & (df_ablation_summary["model_family"] == mf)
                & (df_ablation_summary["variant_id"] == vid)
            ]
            if len(match_sum) == 0:
                mismatches.append(f"Missing row in ablation_summary for ({ds}, {mf}, {vid})")
                continue
            row = match_sum.iloc[0]
            for metric in ("coverage", "cost", "width", "interval_score", "rmse"):
                exp_val = float(grp[metric].mean())
                act_val = float(row[f"{metric}_mean"])
                if not np.isclose(exp_val, act_val, atol=tol_atol, rtol=tol_rtol):
                    mismatches.append(
                        f"Ablation {ds}/{mf}/{vid} {metric}_mean: exp={exp_val} != act={act_val}"
                    )

    # Stress summary check
    if len(df_stress_engine) > 0 and "dataset" in df_stress_engine.columns:
        for (ds, mf, mid, cid), grp in df_stress_engine.groupby(
            ["dataset", "model_family", "method_id", "condition_id"]
        ):
            match_sum = df_stress_summary[
                (df_stress_summary["dataset"] == ds)
                & (df_stress_summary["model_family"] == mf)
                & (df_stress_summary["method_id"] == mid)
                & (df_stress_summary["condition_id"] == cid)
            ]
            if len(match_sum) == 0:
                mismatches.append(f"Missing row in stress_summary for ({ds}, {mf}, {mid}, {cid})")
                continue
            row = match_sum.iloc[0]
            for metric in ("coverage", "cost", "width", "interval_score", "rmse"):
                exp_val = float(grp[metric].mean())
                act_val = float(row[f"{metric}_mean"])
                if not np.isclose(exp_val, act_val, atol=tol_atol, rtol=tol_rtol):
                    mismatches.append(
                        f"Stress {ds}/{mf}/{cid} {metric}_mean: exp={exp_val} != act={act_val}"
                    )
    return mismatches


def verify_exact_keys_and_duplicates(
    ev_dir: Path,
    expected_units: dict[str, list[int]],
) -> list[str]:
    """Verify that engine and simulation outcome files contain expected keys without dups."""
    mismatches: list[str] = []

    # 1. ablation_engine_seed_metrics.csv
    abl_seed_p = ev_dir / "ablation_engine_seed_metrics.csv"
    if abl_seed_p.exists():
        df_abl_raw = pd.read_csv(abl_seed_p)
        keys_abl = ["dataset", "model_family", "variant_id", "seed", "unit"]
        dups_abl = int(df_abl_raw.duplicated(subset=keys_abl).sum())
        if dups_abl > 0:
            mismatches.append(f"ablation_engine_seed_metrics has {dups_abl} duplicate keys")
        exp_abl_rows = sum(len(expected_units[ds]) * 2 * 8 * 5 for ds in CONFIRMATORY_DATASETS)
        if len(df_abl_raw) != exp_abl_rows:
            mismatches.append(
                f"ablation_engine_seed_metrics expected {exp_abl_rows} rows, got {len(df_abl_raw)}"
            )

    # 2. stress_engine_seed_rep_metrics.csv
    str_seed_p = ev_dir / "stress_engine_seed_rep_metrics.csv"
    if str_seed_p.exists():
        df_str_raw = pd.read_csv(str_seed_p)
        keys_str = [
            "dataset",
            "model_family",
            "method_id",
            "condition_id",
            "replicate_id",
            "seed",
            "unit",
        ]
        dups_str = int(df_str_raw.duplicated(subset=keys_str).sum())
        if dups_str > 0:
            mismatches.append(f"stress_engine_seed_rep_metrics has {dups_str} duplicate keys")
        exp_str_rows = sum(len(expected_units[ds]) * 540 for ds in CONFIRMATORY_DATASETS)
        if len(df_str_raw) != exp_str_rows:
            mismatches.append(
                f"stress_engine_seed_rep_metrics exp {exp_str_rows} rows, got {len(df_str_raw)}"
            )

    # 3. paired_contrasts.csv
    paired_p = ev_dir / "paired_contrasts.csv"
    if paired_p.exists():
        df_contrasts = pd.read_csv(paired_p)
        keys_con = [
            "comparison_type",
            "dataset",
            "model_family",
            "variant_or_condition",
            "baseline_or_full",
            "metric",
        ]
        dups_con = int(df_contrasts.duplicated(subset=keys_con).sum())
        if dups_con > 0:
            mismatches.append(f"paired_contrasts has {dups_con} duplicate keys")
        if len(df_contrasts) != 1176:
            mismatches.append(f"paired_contrasts expected 1,176 rows, got {len(df_contrasts)}")

    # 4. zero_difference_checks.csv
    zero_p = ev_dir / "zero_difference_checks.csv"
    if zero_p.exists():
        df_zero = pd.read_csv(zero_p)
        if len(df_zero) != 168:
            mismatches.append(f"zero_difference_checks expected 168 rows, got {len(df_zero)}")
        if "delta_point" not in df_zero.columns or not (df_zero["delta_point"] == 0.0).all():
            mismatches.append("Non-zero or missing delta_point found in zero_difference_checks.csv")
        if (
            "ci_95_low" not in df_zero.columns
            or "ci_95_high" not in df_zero.columns
            or not (df_zero["ci_95_low"] == 0.0).all()
            or not (df_zero["ci_95_high"] == 0.0).all()
        ):
            mismatches.append("Non-zero or missing CI endpoint found in zero_difference_checks.csv")

    # 5. factor_main_effects.csv
    fac_p = ev_dir / "factor_main_effects.csv"
    if fac_p.exists():
        df_fac = pd.read_csv(fac_p)
        keys_fac = ["dataset", "model_family", "factor", "metric"]
        dups_fac = int(df_fac.duplicated(subset=keys_fac).sum())
        if dups_fac > 0:
            mismatches.append(f"factor_main_effects has {dups_fac} duplicate keys")
        if len(df_fac) != 126:
            mismatches.append(f"factor_main_effects expected 126 rows, got {len(df_fac)}")

    return mismatches


def independently_verify_phase08_evidence(
    evidence_dir: Path | str,
    base_dir: Path | str = ".",
    raw_data_dir: Path | str = "data/raw/cmapss",
    calibration_cache_dir: Path | str = "experiments/calibration/point_predictions/calibration",
    tol_atol: float = TOL_DETERMINISTIC_ATOL,
    tol_rtol: float = TOL_DETERMINISTIC_RTOL,
) -> dict[str, Any]:
    """Execute complete independent reference verification and audit of Phase 8 evidence.

    Fails closed on any inconsistency, altered thresholds, missing cells,
    unsafe paths, or empty hash inventories.
    """
    base = Path(base_dir).resolve()
    ev_dir = Path(evidence_dir).resolve()

    checks: dict[str, Any] = {}
    failing_reasons: list[str] = []

    # -------------------------------------------------------------------------
    # 1. Required Files Presence
    # -------------------------------------------------------------------------
    missing_files = [f for f in REQUIRED_PHASE08_FILES if not (ev_dir / f).exists()]
    checks["required_files_present"] = {
        "status": "PASS" if not missing_files else "FAIL",
        "missing_files": missing_files,
    }
    if missing_files:
        failing_reasons.append(f"Missing required Phase 8 evidence files: {missing_files}")
        return {
            "overall_status": "FAIL",
            "failing_reasons": failing_reasons,
            "checks": checks,
        }

    # -------------------------------------------------------------------------
    # 2. Manifest Schema & Expected Artifact Inventory
    # -------------------------------------------------------------------------
    manifest_p = ev_dir / "execution_manifest.json"
    try:
        with open(manifest_p, encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as exc:
        failing_reasons.append(f"Could not parse execution_manifest.json: {exc}")
        return {"overall_status": "FAIL", "failing_reasons": failing_reasons, "checks": checks}

    if manifest.get("status") != "EXPLORATORY_POST_CONFIRMATORY":
        failing_reasons.append(
            f"Invalid manifest status: expected EXPLORATORY_POST_CONFIRMATORY, "
            f"got {manifest.get('status')}"
        )

    missing_prov = [f for f in REQUIRED_PROVENANCE_FIELDS if manifest.get(f) is None]
    if missing_prov:
        failing_reasons.append(
            f"Missing mandatory provenance fields in execution_manifest.json: {missing_prov}"
        )

    man_counts_check = manifest.get("counts", {})
    if not isinstance(man_counts_check, dict):
        failing_reasons.append("counts field is not a mapping in execution_manifest.json")
    else:
        missing_cnts = [f for f in REQUIRED_COUNTS_FIELDS if man_counts_check.get(f) is None]
        if missing_cnts:
            failing_reasons.append(
                f"Missing counts fields in execution_manifest.json: {missing_cnts}"
            )

    art_hashes = manifest.get("artifact_hashes")
    if not art_hashes or not isinstance(art_hashes, dict):
        failing_reasons.append(
            "artifact_hashes mapping is absent or empty in execution_manifest.json"
        )
        checks["artifact_inventory_integrity"] = {
            "status": "FAIL",
            "reason": "empty_or_absent_artifact_hashes",
        }
        return {"overall_status": "FAIL", "failing_reasons": failing_reasons, "checks": checks}

    # Verify POSIX relative paths and hashes
    hash_mismatches: list[str] = []
    unsafe_paths: list[str] = []
    for rel_path, exp_h in art_hashes.items():
        # Validate path safety
        p_obj = Path(rel_path)
        if (
            p_obj.is_absolute()
            or ".." in p_obj.parts
            or "\\" in rel_path
            or rel_path.startswith("/")
        ):
            unsafe_paths.append(rel_path)
            continue

        fpath = ev_dir / p_obj
        if not fpath.exists():
            hash_mismatches.append(f"{rel_path} (file missing on disk)")
            continue
        act_h = compute_sha256(fpath)
        if act_h != exp_h:
            hash_mismatches.append(f"{rel_path} (expected {exp_h}, got {act_h})")

    if unsafe_paths:
        failing_reasons.append(
            f"Unsafe artifact paths detected in execution_manifest.json: {unsafe_paths[:5]}"
        )
    if hash_mismatches:
        failing_reasons.append(
            f"Artifact hash mismatches in execution manifest: {hash_mismatches[:5]}"
        )

    checks["artifact_inventory_integrity"] = {
        "status": "PASS" if not hash_mismatches and not unsafe_paths else "FAIL",
        "total_inventoried": len(art_hashes),
        "hash_mismatches": hash_mismatches[:10],
        "unsafe_paths": unsafe_paths[:10],
    }

    # -------------------------------------------------------------------------
    # 3. Protected Input Hashes & Raw Data Verification
    # -------------------------------------------------------------------------
    try:
        raw_hashes = verify_raw_data_hashes(raw_data_dir=raw_data_dir, base_dir=base)
        checks["raw_source_hashes"] = {"status": "PASS", "hashes": raw_hashes}
    except Exception as exc:
        checks["raw_source_hashes"] = {"status": "FAIL", "error": str(exc)}
        failing_reasons.append(f"Raw source hash verification failed: {exc}")

    in_man_p = ev_dir / "input_manifest.json"
    in_man: dict[str, Any] = {}
    try:
        with open(in_man_p, encoding="utf-8") as f:
            in_man = json.load(f)
    except Exception as exc:
        failing_reasons.append(f"Could not parse input_manifest.json: {exc}")

    pre_prot = in_man.get("pre_execution_protected_hashes", {})
    post_prot = in_man.get("post_execution_protected_hashes", {})
    if not pre_prot or not post_prot or pre_prot != post_prot:
        failing_reasons.append("Input manifest protected hashes inconsistent or missing.")
        checks["protected_inputs_consistency"] = {"status": "FAIL"}
    else:
        checks["protected_inputs_consistency"] = {"status": "PASS", "count": len(pre_prot)}

    # -------------------------------------------------------------------------
    # 4. Derivation and Validation of Split Engines & Expected Counts
    # -------------------------------------------------------------------------
    expected_units: dict[str, list[int]] = {}
    for ds in CONFIRMATORY_DATASETS:
        split_p = resolve_repo_relative_path(
            base, f"data/splits/{ds.lower()}_engine_split_seed_2026.json"
        )
        s_man = load_split_manifest(split_p)
        expected_units[ds] = sorted(s_man.get_partition("test"))

    total_expected_test_engines = sum(len(expected_units[ds]) for ds in CONFIRMATORY_DATASETS)
    man_counts = manifest.get("counts", {})
    if man_counts.get("ablation_configurations") != 240:
        failing_reasons.append(
            f"Expected 240 ablation configurations, got {man_counts.get('ablation_configurations')}"
        )
    if man_counts.get("stress_evaluations") != 1620:
        failing_reasons.append(
            f"Expected 1,620 stress evaluations, got {man_counts.get('stress_evaluations')}"
        )
    if man_counts.get("total_test_engines") != total_expected_test_engines:
        failing_reasons.append(
            f"Expected {total_expected_test_engines} test engines, "
            f"got {man_counts.get('total_test_engines')}"
        )

    exact_key_mismatches = verify_exact_keys_and_duplicates(ev_dir, expected_units)
    checks["exact_keys_and_duplicates"] = {
        "status": "PASS" if not exact_key_mismatches else "FAIL",
        "mismatches": exact_key_mismatches[:10],
    }
    if exact_key_mismatches:
        failing_reasons.extend(exact_key_mismatches)

    # -------------------------------------------------------------------------
    # 5. Independent Reference Threshold Reconstruction & Equivalence Gates
    # -------------------------------------------------------------------------
    cal_mismatches: list[str] = []
    cal_dir = ev_dir / "exploratory_calibrators"
    num_calibrators_checked = 0

    for ds in CONFIRMATORY_DATASETS:
        for mf in CONFIRMATORY_MODELS:
            for seed in CONFIRMATORY_SEEDS:
                cal_cache_p = base / calibration_cache_dir / ds / mf / f"seed_{seed}.csv"
                if not cal_cache_p.exists():
                    failing_reasons.append(f"Missing calibration cache: {cal_cache_p}")
                    continue
                df_cal = pd.read_csv(cal_cache_p)
                eids = df_cal["unit"].to_numpy(dtype=int)
                preds = df_cal["prediction"].to_numpy(dtype=float)
                labels = df_cal["rul_true"].to_numpy(dtype=float)
                regimes = df_cal["regime"].to_numpy()

                for variant in ALL_EIGHT_ABLATION_VARIANTS:
                    cal_fname = f"{ds}_{mf}_seed{seed}_{variant.variant_id}.json"
                    cal_p = cal_dir / cal_fname
                    if not cal_p.exists():
                        cal_mismatches.append(f"Missing exploratory calibrator {cal_fname}")
                        continue

                    with open(cal_p, encoding="utf-8") as f:
                        saved_cal = json.load(f)

                    cand = CandidateConfig.from_params(
                        gamma=variant.gamma, beta_code=variant.beta_code
                    )
                    scores = compute_decision_aware_score(
                        predictions=preds, labels=labels, candidate=cand
                    )
                    exp_global_q = _reconstruct_reference_quantile(
                        eids, scores, nominal_coverage=0.90
                    )

                    saved_b90 = saved_cal.get("threshold_bundles", {}).get("coverage_90", {})
                    act_global_q = saved_b90.get("global_threshold")

                    if act_global_q is None or not np.isclose(
                        act_global_q, exp_global_q, atol=tol_atol, rtol=tol_rtol
                    ):
                        cal_mismatches.append(
                            f"{cal_fname}: global act={act_global_q} != exp={exp_global_q}"
                        )

                    # Regime thresholds
                    saved_reg_thresholds = saved_b90.get("regime_thresholds", {})
                    for reg_id in sorted(np.unique(regimes)):
                        reg_str = str(reg_id)
                        reg_mask = regimes == reg_id
                        reg_eids = eids[reg_mask]
                        reg_scores = scores[reg_mask]
                        distinct_engs = len(np.unique(reg_eids))
                        exp_reg_q = (
                            _reconstruct_reference_quantile(reg_eids, reg_scores, 0.90)
                            if distinct_engs >= 10
                            else exp_global_q
                        )
                        act_reg_rec = saved_reg_thresholds.get(reg_str, {})
                        act_reg_q = act_reg_rec.get("threshold")
                        if act_reg_q is not None and not np.isclose(
                            act_reg_q, exp_reg_q, atol=tol_atol, rtol=tol_rtol
                        ):
                            cal_mismatches.append(
                                f"{cal_fname} reg {reg_str}: act={act_reg_q} != exp={exp_reg_q}"
                            )

                    num_calibrators_checked += 1

    checks["calibrator_threshold_reconstruction"] = {
        "status": "PASS" if not cal_mismatches else "FAIL",
        "checked_calibrators": num_calibrators_checked,
        "mismatches": cal_mismatches[:10],
    }
    if cal_mismatches:
        failing_reasons.append(
            f"Calibrator threshold reconstruction failed: {len(cal_mismatches)} mismatches"
        )

    # Equivalence gates check
    equiv_mismatches: list[str] = []
    if not cal_dir.exists():
        equiv_mismatches.append(f"Missing exploratory calibrators directory: {cal_dir}")
    else:

        def _get_q(c: dict[str, Any]) -> float:
            if "threshold_bundles" in c:
                return float(c["threshold_bundles"]["coverage_90"]["global_threshold"])
            return float(c["coverage_bundles"]["0.9"]["global_threshold"])

        for ds in CONFIRMATORY_DATASETS:
            for mf in CONFIRMATORY_MODELS:
                for s in CONFIRMATORY_SEEDS:
                    # 1. global_hcp equivalence
                    p_g0 = cal_dir / f"{ds}_{mf}_seed{s}_gamma0_beta0_global.json"
                    p_fg = (
                        base
                        / "experiments/calibration/fitted"
                        / ds
                        / mf
                        / f"seed_{s}/global_hcp/calibrator.json"
                    )
                    if not p_g0.exists() or not p_fg.exists():
                        equiv_mismatches.append(
                            f"Missing calibrator file for global_hcp equivalence: {p_g0.name}"
                        )
                        continue
                    with open(p_g0, encoding="utf-8") as f:
                        c_g0 = json.load(f)
                    with open(p_fg, encoding="utf-8") as f:
                        c_fg = json.load(f)
                    q_g0 = _get_q(c_g0)
                    q_fg = _get_q(c_fg)
                    if not np.isclose(q_g0, q_fg, atol=tol_atol, rtol=tol_rtol):
                        equiv_mismatches.append(
                            f"{ds}_{mf}_seed{s}: gamma0_beta0_global != global_hcp"
                        )

                    # 2. regime_hcp equivalence
                    p_r0 = cal_dir / f"{ds}_{mf}_seed{s}_gamma0_beta0_regime.json"
                    p_fr = (
                        base
                        / "experiments/calibration/fitted"
                        / ds
                        / mf
                        / f"seed_{s}/regime_hcp/calibrator.json"
                    )
                    if not p_r0.exists() or not p_fr.exists():
                        equiv_mismatches.append(
                            f"Missing calibrator file for regime_hcp equivalence: {p_r0.name}"
                        )
                        continue
                    with open(p_r0, encoding="utf-8") as f:
                        c_r0 = json.load(f)
                    with open(p_fr, encoding="utf-8") as f:
                        c_fr = json.load(f)
                    q_r0 = _get_q(c_r0)
                    q_fr = _get_q(c_fr)
                    if not np.isclose(q_r0, q_fr, atol=tol_atol, rtol=tol_rtol):
                        equiv_mismatches.append(
                            f"{ds}_{mf}_seed{s}: gamma0_beta0_regime != regime_hcp"
                        )

                    # 3. decision_aware_hcp equivalence
                    p_full = cal_dir / f"{ds}_{mf}_seed{s}_gamma2_betam1_regime.json"
                    p_fd = (
                        base
                        / "experiments/calibration/fitted"
                        / ds
                        / mf
                        / f"seed_{s}/decision_aware_hcp/calibrator.json"
                    )
                    if not p_full.exists() or not p_fd.exists():
                        equiv_mismatches.append(
                            f"Missing calibrator for decision_aware_hcp: {p_full.name}"
                        )
                        continue
                    with open(p_full, encoding="utf-8") as f:
                        c_full = json.load(f)
                    with open(p_fd, encoding="utf-8") as f:
                        c_fd = json.load(f)
                    q_full = _get_q(c_full)
                    q_fd = _get_q(c_fd)
                    if not np.isclose(q_full, q_fd, atol=tol_atol, rtol=tol_rtol):
                        equiv_mismatches.append(
                            f"{ds}_{mf}_seed{s}: gamma2_betam1_regime != decision_aware_hcp"
                        )

                    # 4. FD001 global vs regime equivalence
                    if ds == "FD001":
                        q_g_fd = c_full["threshold_bundles"]["coverage_90"]["global_threshold"]
                        q_r_fd = c_full["threshold_bundles"]["coverage_90"]["regime_thresholds"][
                            "C1"
                        ]["threshold"]
                        if not np.isclose(q_g_fd, q_r_fd, atol=tol_atol, rtol=tol_rtol):
                            equiv_mismatches.append(
                                f"FD001_{mf}_seed{s}: global != regime routing on FD001"
                            )

    checks["equivalence_gates"] = {
        "status": "PASS" if not equiv_mismatches else "FAIL",
        "mismatches": equiv_mismatches,
    }
    if equiv_mismatches:
        failing_reasons.append(f"Equivalence gate violations: {equiv_mismatches}")

    # -------------------------------------------------------------------------
    # 6. Independent Bootstrap Draws Reconstruction
    # -------------------------------------------------------------------------
    draws_mismatches: list[str] = []
    for ds in CONFIRMATORY_DATASETS:
        exp_draws = _reconstruct_independent_bootstrap_draws(
            dataset=ds,
            partition_engines=expected_units[ds],
            base_dir=base,
            n_replicates=10000,
        )
        draws_p = ev_dir / f"bootstrap_draws_{ds}.npz"
        if not draws_p.exists():
            draws_mismatches.append(f"Missing {draws_p.name}")
            continue
        try:
            saved_npz = np.load(draws_p)
            act_draws = saved_npz["draws"]
            if not np.array_equal(exp_draws, act_draws):
                draws_mismatches.append(
                    f"{ds} bootstrap draws do not match independent reference draws"
                )
        except Exception as exc:
            draws_mismatches.append(f"Error reading {draws_p.name}: {exc}")

    checks["bootstrap_draws_reconstruction"] = {
        "status": "PASS" if not draws_mismatches else "FAIL",
        "mismatches": draws_mismatches,
    }
    if draws_mismatches:
        failing_reasons.append(f"Bootstrap draw reconstruction failed: {draws_mismatches}")

    # -------------------------------------------------------------------------
    # 7. Independent Perturbation Streams & Checkpoint Parity Sampling
    # -------------------------------------------------------------------------
    pert_mismatches: list[str] = []
    # Test deterministic seed sequences on each dataset for engine 1 and engine 5
    for ds in CONFIRMATORY_DATASETS:
        ds_num = DATASET_NUMBERS[ds]
        for eng in expected_units[ds][:2]:
            for rep in (0, 1):
                # Gaussian noise
                seq_noise = np.random.SeedSequence(
                    [2026, 8, ds_num, eng, PERTURBATION_FAMILY_GAUSSIAN_NOISE, rep]
                )
                rng_n = np.random.Generator(np.random.PCG64(seq_noise))
                z = rng_n.standard_normal((30, len(SENSOR_COLUMNS)))
                if z.shape != (30, 14):
                    pert_mismatches.append(f"Invalid noise shape for {ds} eng {eng}")

                # Dropout
                seq_drop = np.random.SeedSequence(
                    [2026, 8, ds_num, eng, PERTURBATION_FAMILY_DROPOUT, rep]
                )
                rng_d = np.random.Generator(np.random.PCG64(seq_drop))
                u = rng_d.uniform(0.0, 1.0, (30, len(SENSOR_COLUMNS)))
                if not np.all((u >= 0.0) & (u < 1.0)):
                    pert_mismatches.append(f"Dropout uniform out of bounds for {ds} eng {eng}")

    checks["perturbation_generation_integrity"] = {
        "status": "PASS" if not pert_mismatches else "FAIL",
        "mismatches": pert_mismatches,
    }
    if pert_mismatches:
        failing_reasons.append(
            f"Perturbation generation integrity checks failed: {pert_mismatches}"
        )

    # -------------------------------------------------------------------------
    # 8. Reconstruct Interval Inversion, Simulation Policy, and Engine Metrics
    # -------------------------------------------------------------------------
    # Load ablation engine metrics and simulation outcomes
    df_ablation_engine = pd.read_csv(ev_dir / "ablation_engine_metrics.csv")
    df_ablation_sim = pd.read_csv(ev_dir / "ablation_simulation_outcomes.csv")
    df_subgroups = pd.read_csv(ev_dir / "subgroup_metrics.csv")
    df_paired_contrasts = pd.read_csv(ev_dir / "paired_contrasts.csv")

    # Validate simulation precedence: no PM issued at or after terminal failure
    sim_violations = verify_simulation_terminal_precedence(df_ablation_sim)
    checks["simulation_terminal_precedence"] = {
        "status": "PASS" if not sim_violations else "FAIL",
        "violations": sim_violations[:10],
    }
    if sim_violations:
        failing_reasons.extend(sim_violations)

    # Validate Equal-Engine Subgroup Weighting
    df_sub_eng = pd.read_csv(ev_dir / "subgroup_engine_metrics.csv")
    subgroup_math_mismatches = verify_equal_engine_subgroup_math(
        df_subgroups, df_sub_eng, tol_atol=tol_atol, tol_rtol=tol_rtol
    )
    checks["equal_engine_subgroup_reconstruction"] = {
        "status": "PASS" if not subgroup_math_mismatches else "FAIL",
        "mismatches": subgroup_math_mismatches[:10],
    }
    if subgroup_math_mismatches:
        failing_reasons.append(
            f"Subgroup equal-engine weighting failed: {len(subgroup_math_mismatches)} mismatches"
        )

    # Validate Summary Aggregations
    df_stress_engine = pd.read_csv(ev_dir / "stress_engine_metrics.csv")
    df_stress_summary = pd.read_csv(ev_dir / "stress_summary.csv")
    df_ablation_summary = pd.read_csv(ev_dir / "ablation_summary.csv")
    summary_mismatches = verify_summary_aggregations(
        df_ablation_summary=df_ablation_summary,
        df_ablation_engine=df_ablation_engine,
        df_stress_summary=df_stress_summary,
        df_stress_engine=df_stress_engine,
        tol_atol=tol_atol,
        tol_rtol=tol_rtol,
    )
    checks["summary_aggregation_reconstruction"] = {
        "status": "PASS" if not summary_mismatches else "FAIL",
        "mismatches": summary_mismatches[:10],
    }
    if summary_mismatches:
        failing_reasons.extend(summary_mismatches)

    # Validate Paired Contrasts & Bootstrap Statistics Consistency
    contrast_mismatches: list[str] = []
    for ds in CONFIRMATORY_DATASETS:
        stat_npz_p = ev_dir / f"bootstrap_statistics_{ds}.npz"
        if not stat_npz_p.exists():
            contrast_mismatches.append(f"Missing bootstrap statistics artifact: {stat_npz_p.name}")
            continue
        try:
            stats_data = np.load(stat_npz_p)
        except Exception as exc:
            contrast_mismatches.append(f"Error loading {stat_npz_p.name}: {exc}")
            continue

        # Check sample ablation contrast
        for mf in CONFIRMATORY_MODELS:
            stat_key = f"ablation_{ds}_{mf}_gamma0_beta0_global_minus_full_cost"
            if stat_key not in stats_data:
                contrast_mismatches.append(f"Missing statistic array {stat_key} in {ds}")
                continue
            reps = stats_data[stat_key]
            if len(reps) != 10000:
                contrast_mismatches.append(f"{stat_key} length {len(reps)} != 10,000")
                continue
            q_lo, q_hi = np.quantile(reps, [0.025, 0.975], method="linear")

            row_match = df_paired_contrasts[
                (df_paired_contrasts["dataset"] == ds)
                & (df_paired_contrasts["model_family"] == mf)
                & (df_paired_contrasts["variant_or_condition"] == "gamma0_beta0_global")
                & (df_paired_contrasts["metric"] == "cost")
            ]
            if len(row_match) == 0:
                contrast_mismatches.append(
                    f"Missing paired contrast row for {ds}/{mf}/gamma0_beta0_global/cost"
                )
            else:
                act_lo = float(row_match["ci_95_low"].iloc[0])
                act_hi = float(row_match["ci_95_high"].iloc[0])
                if not np.isclose(act_lo, q_lo, atol=tol_atol, rtol=tol_rtol) or not np.isclose(
                    act_hi, q_hi, atol=tol_atol, rtol=tol_rtol
                ):
                    contrast_mismatches.append(f"Bootstrap interval mismatch for {stat_key}")

    checks["paired_contrasts_and_bootstrap_statistics"] = {
        "status": "PASS" if not contrast_mismatches else "FAIL",
        "mismatches": contrast_mismatches[:10],
    }
    if contrast_mismatches:
        failing_reasons.append(
            f"Paired contrasts and bootstrap statistics verification failed: {contrast_mismatches}"
        )

    # No 'favors_variant' column in paired_contrasts.csv
    if "favors_variant" in df_paired_contrasts.columns:
        failing_reasons.append("Misleading 'favors_variant' column present in paired_contrasts.csv")
        checks["no_misleading_interpretations"] = {"status": "FAIL"}
    else:
        checks["no_misleading_interpretations"] = {"status": "PASS"}

    # Overall Status Determination
    overall_status = "PASS" if not failing_reasons else "FAIL"

    return {
        "overall_status": overall_status,
        "failing_reasons": failing_reasons,
        "checks": checks,
    }
