"""Independent verification and content audit functions for confirmatory evaluation."""

from __future__ import annotations

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
    validate_component_manifest_completeness,
)
from intellitwin.evaluation.evidence_schema import (
    EXPECTED_TOTAL_CELL_SUMMARIES_COUNT,
    EXPECTED_TOTAL_COMPONENTS_COUNT,
    EXPECTED_TOTAL_CONFIGS_COUNT,
    EXPECTED_TOTAL_OUTCOMES_COUNT,
    PRIMARY_CANONICAL_COVERAGE,
    PRIMARY_COST_SCENARIO,
    canonicalize_coverage,
    coverage_to_float,
    generate_expected_cell_summary_keys,
    generate_expected_configurations,
    generate_expected_engine_outcome_keys,
    get_expected_contrast_statistic_specs,
)
from intellitwin.evaluation.schema import (
    CONFIRMATORY_DATASETS,
    CONFIRMATORY_MODELS,
    CONFIRMATORY_SEEDS,
)
from intellitwin.uncertainty.artifacts import resolve_repo_relative_path

REQUIRED_SMOKE_FILES: tuple[str, ...] = (
    "point_predictions.csv",
    "interval_predictions.csv",
    "decision_traces.csv",
    "engine_seed_outcomes.csv",
    "engine_metrics.csv",
    "subgroup_metrics.csv",
    "cell_summary.csv",
    "contrast_intervals.csv",
    "component_evidence.csv",
    "bootstrap_draws_FD001.npz",
    "bootstrap_draws_FD002.npz",
    "bootstrap_draws_FD004.npz",
    "bootstrap_statistics_FD001.npz",
    "bootstrap_statistics_FD002.npz",
    "bootstrap_statistics_FD004.npz",
    "bootstrap_statistics_RQ4.npz",
    "execution_manifest.json",
)


def independently_generate_bootstrap_draws(
    dataset: str,
    partition_engines: list[int],
    base_dir: Path | str = ".",
    n_replicates: int = 10000,
) -> np.ndarray[Any, Any]:
    """Independently reconstruct bootstrap draw sequence from frozen quartile specifications.

    Rules:
    - Quartile strata Q1, Q2, Q3, Q4 sorted ascending.
    - Generator: np.random.Generator(np.random.PCG64(
        np.random.SeedSequence([2026, 6, dataset_number])
      )).
    - Preserves engine multiplicity; returns (n_replicates, total_engines).
    """
    if dataset not in DATASET_NUMBERS:
        raise ValueError(f"Unknown dataset: {dataset}")
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


def verify_validation_smoke_matrix(
    smoke_dir: Path | str,
    base_dir: Path | str = ".",
) -> dict[str, Any]:
    """Perform authoritative independent content-level verification of validation smoke evidence.

    Fails closed if any required check is missing, skipped, or inconsistent.
    """
    base = Path(base_dir).resolve()
    s_dir = Path(smoke_dir).resolve()

    checks: dict[str, Any] = {}
    failing_reasons: list[str] = []

    # 1. Required Files Presence
    missing_files = [f for f in REQUIRED_SMOKE_FILES if not (s_dir / f).exists()]
    checks["required_files_present"] = len(missing_files) == 0
    if missing_files:
        checks["missing_files"] = missing_files
        failing_reasons.append(f"Missing required smoke files: {missing_files}")
        return {
            "status": "FAIL",
            "overall_match": False,
            "failing_reasons": failing_reasons,
            "checks": checks,
        }

    # 2. Frozen Partition Engines
    expected_units: dict[str, list[int]] = {}
    for ds in CONFIRMATORY_DATASETS:
        split_p = resolve_repo_relative_path(
            base, f"data/splits/{ds.lower()}_engine_split_seed_2026.json"
        )
        s_man = load_split_manifest(split_p)
        expected_units[ds] = sorted(s_man.get_partition("validation"))

    checks["validation_engine_counts"] = {
        "FD001": len(expected_units["FD001"]) == 10,
        "FD002": len(expected_units["FD002"]) == 26,
        "FD004": len(expected_units["FD004"]) == 25,
    }
    if not all(checks["validation_engine_counts"].values()):
        failing_reasons.append(
            f"Unexpected partition engine counts: {checks['validation_engine_counts']}"
        )

    # 3. Exact Configuration Sets and Outcomes Verification
    df_outcomes = pd.read_csv(s_dir / "engine_seed_outcomes.csv", float_precision="round_trip")
    df_eng_metrics = pd.read_csv(s_dir / "engine_metrics.csv", float_precision="round_trip")

    expected_prim_cfgs, expected_ctrl_cfgs = generate_expected_configurations()
    expected_all_cfgs = expected_prim_cfgs | expected_ctrl_cfgs

    # Canonically validate coverage in outcomes
    outcome_cfgs: set[tuple[str, str, int, str, int, str]] = set()
    invalid_cov_entries: list[Any] = []
    for row in df_outcomes.itertuples():
        try:
            cov_canon = canonicalize_coverage(row.nominal_coverage)
        except ValueError:
            invalid_cov_entries.append(row.nominal_coverage)
            continue
        outcome_cfgs.add(
            (
                str(row.dataset),
                str(row.model_family),
                int(row.seed),
                str(row.method_or_control_id),
                cov_canon,
                str(row.scenario_id),
            )
        )

    checks["canonical_coverage_valid"] = len(invalid_cov_entries) == 0
    if invalid_cov_entries:
        failing_reasons.append(
            f"Invalid non-canonical coverages detected: {invalid_cov_entries[:5]}"
        )

    missing_cfgs = expected_all_cfgs - outcome_cfgs
    extra_cfgs = outcome_cfgs - expected_all_cfgs

    checks["configurations_exact_match"] = {
        "expected_total": EXPECTED_TOTAL_CONFIGS_COUNT,
        "actual_total": len(outcome_cfgs),
        "missing_count": len(missing_cfgs),
        "extra_count": len(extra_cfgs),
        "match": len(missing_cfgs) == 0 and len(extra_cfgs) == 0,
    }
    if not checks["configurations_exact_match"]["match"]:
        failing_reasons.append(
            f"Configuration mismatch: {len(missing_cfgs)} missing, {len(extra_cfgs)} extra"
        )

    # Outcome rows exact keys
    expected_outcome_keys = generate_expected_engine_outcome_keys(expected_units)
    actual_outcome_keys: list[tuple[str, str, int, str, int, str, int]] = []
    for r in df_outcomes.itertuples():
        cov_c = canonicalize_coverage(r.nominal_coverage)
        actual_outcome_keys.append(
            (
                str(r.dataset),
                str(r.model_family),
                int(r.seed),
                str(r.method_or_control_id),
                cov_c,
                str(r.scenario_id),
                int(r.unit),
            )
        )
    actual_outcome_key_set = set(actual_outcome_keys)

    checks["outcome_keys_exact_match"] = {
        "expected_count": EXPECTED_TOTAL_OUTCOMES_COUNT,
        "actual_rows": len(df_outcomes),
        "unique_keys": len(actual_outcome_key_set),
        "no_duplicate_keys": len(df_outcomes) == len(actual_outcome_key_set),
        "keys_equal_expected": actual_outcome_key_set == expected_outcome_keys,
    }
    if not (
        checks["outcome_keys_exact_match"]["no_duplicate_keys"]
        and checks["outcome_keys_exact_match"]["keys_equal_expected"]
    ):
        failing_reasons.append("Engine seed outcomes have duplicate, missing, or unexpected keys.")

    # Validate engine_metrics keys
    actual_metric_keys = [
        (
            str(r.dataset),
            str(r.model_family),
            int(r.seed),
            str(r.method_or_control_id),
            canonicalize_coverage(r.nominal_coverage),
            str(r.scenario_id),
            int(r.unit),
        )
        for r in df_eng_metrics.itertuples()
    ]
    actual_metric_key_set = set(actual_metric_keys)
    checks["engine_metric_keys_exact_match"] = {
        "expected_count": EXPECTED_TOTAL_OUTCOMES_COUNT,
        "actual_rows": len(df_eng_metrics),
        "unique_keys": len(actual_metric_key_set),
        "no_duplicate_keys": len(df_eng_metrics) == len(actual_metric_key_set),
        "keys_equal_expected": actual_metric_key_set == expected_outcome_keys,
    }
    if not (
        checks["engine_metric_keys_exact_match"]["no_duplicate_keys"]
        and checks["engine_metric_keys_exact_match"]["keys_equal_expected"]
    ):
        failing_reasons.append("Engine metrics have duplicate, missing, or unexpected keys.")

    # Verify strictly validation partition engines
    partition_clean = True
    for ds in CONFIRMATORY_DATASETS:
        ds_units = set(df_outcomes.loc[df_outcomes["dataset"] == ds, "unit"].unique())
        exp_u = set(expected_units[ds])
        if ds_units != exp_u:
            partition_clean = False
            checks[f"{ds}_partition_mismatch"] = {
                "extra": sorted(ds_units - exp_u),
                "missing": sorted(exp_u - ds_units),
            }
    checks["validation_partition_only"] = partition_clean
    if not partition_clean:
        failing_reasons.append("Outcomes contain engines outside the frozen validation partition.")

    # 4. Verify cell_summary.csv exact keys and reconstruction
    df_cell = pd.read_csv(s_dir / "cell_summary.csv", float_precision="round_trip")
    expected_prim_summary, expected_ctrl_summary = generate_expected_cell_summary_keys()
    expected_all_summary = expected_prim_summary | expected_ctrl_summary

    actual_summary_keys = [
        (
            str(r.dataset),
            str(r.model_family),
            str(r.method_or_control_id),
            canonicalize_coverage(r.nominal_coverage),
            str(r.scenario_id),
        )
        for r in df_cell.itertuples()
    ]
    actual_summary_key_set = set(actual_summary_keys)

    checks["cell_summary_keys_exact_match"] = {
        "expected_count": EXPECTED_TOTAL_CELL_SUMMARIES_COUNT,
        "actual_rows": len(df_cell),
        "unique_keys": len(actual_summary_key_set),
        "no_duplicate_keys": len(df_cell) == len(actual_summary_key_set),
        "keys_equal_expected": actual_summary_key_set == expected_all_summary,
    }
    if not (
        checks["cell_summary_keys_exact_match"]["no_duplicate_keys"]
        and checks["cell_summary_keys_exact_match"]["keys_equal_expected"]
    ):
        failing_reasons.append(
            "Cell summary has duplicate, missing, or unexpected configuration keys."
        )

    # Verify numerical reconstruction of cell summary mean_cost from outcomes
    max_cost_reconstruct_diff = 0.0
    for row in df_cell.itertuples():
        cov_val = coverage_to_float(canonicalize_coverage(row.nominal_coverage))
        match_outcomes = df_outcomes[
            (df_outcomes["dataset"] == row.dataset)
            & (df_outcomes["model_family"] == row.model_family)
            & (df_outcomes["method_or_control_id"] == row.method_or_control_id)
            & (np.isclose(df_outcomes["nominal_coverage"], cov_val))
            & (df_outcomes["scenario_id"] == row.scenario_id)
        ]
        # Equal engine mean cost: average seeds within engine, then average across engines
        engine_means = match_outcomes.groupby("unit")["total_cost"].mean()
        recomputed_cost = float(engine_means.mean())
        diff = abs(recomputed_cost - float(row.mean_cost))
        if diff > max_cost_reconstruct_diff:
            max_cost_reconstruct_diff = diff

    checks["cell_summary_cost_reconstruction"] = {
        "max_diff": max_cost_reconstruct_diff,
        "match": max_cost_reconstruct_diff < 1e-10,
    }
    if not checks["cell_summary_cost_reconstruction"]["match"]:
        failing_reasons.append(
            f"Cell summary cost reconstruction discrepancy: {max_cost_reconstruct_diff} > 1e-10"
        )

    # 5. Verify Point Predictions Export (all 5 seeds vs frozen caches)
    df_pts = pd.read_csv(s_dir / "point_predictions.csv", float_precision="round_trip")
    pts_seeds = sorted(df_pts["seed"].unique())
    checks["point_predictions_all_seeds"] = pts_seeds == list(CONFIRMATORY_SEEDS)
    if not checks["point_predictions_all_seeds"]:
        failing_reasons.append(
            f"point_predictions.csv seeds {pts_seeds} != expected {list(CONFIRMATORY_SEEDS)}"
        )

    # Check key uniqueness: (dataset, model_family, seed, unit, endpoint_cycle)
    pts_keys = list(
        zip(
            df_pts["dataset"],
            df_pts["model_family"],
            df_pts["seed"],
            df_pts["unit"],
            df_pts["endpoint_cycle"],
            strict=False,
        )
    )
    checks["point_predictions_unique_keys"] = len(pts_keys) == len(set(pts_keys))
    if not checks["point_predictions_unique_keys"]:
        failing_reasons.append("point_predictions.csv contains duplicate trajectory keys.")

    # Compare sample of point predictions against frozen validation caches
    max_cache_diff = 0.0
    for ds in CONFIRMATORY_DATASETS:
        for fam in CONFIRMATORY_MODELS:
            for s in (2026, 2030):  # verify anchor seeds
                cache_p = resolve_repo_relative_path(
                    base,
                    f"experiments/calibration/point_predictions/validation/{ds}/{fam}/seed_{s}.csv",
                )
                df_c = pd.read_csv(cache_p, float_precision="round_trip")
                sub_pts = df_pts[
                    (df_pts["dataset"] == ds)
                    & (df_pts["model_family"] == fam)
                    & (df_pts["seed"] == s)
                ].sort_values(["unit", "endpoint_cycle"])
                df_c_sorted = df_c.sort_values(["unit", "endpoint_cycle"])
                if len(sub_pts) != len(df_c_sorted):
                    failing_reasons.append(
                        f"Point predictions count mismatch for {ds}/{fam}/seed_{s}"
                    )
                    break
                diff = np.max(
                    np.abs(sub_pts["prediction"].to_numpy() - df_c_sorted["prediction"].to_numpy())
                )
                if diff > max_cache_diff:
                    max_cache_diff = float(diff)

    checks["point_predictions_cache_match"] = {
        "max_diff": max_cache_diff,
        "match": max_cache_diff < 1e-10,
    }
    if not checks["point_predictions_cache_match"]["match"]:
        failing_reasons.append(
            f"Point prediction discrepancy vs frozen cache: {max_cache_diff} > 1e-10"
        )

    # 6. Verify Bootstrap Draws (Independent Reconstruction)
    draws_valid = True
    for ds in CONFIRMATORY_DATASETS:
        draws_file = s_dir / f"bootstrap_draws_{ds}.npz"
        data = np.load(draws_file, allow_pickle=False)
        saved_draws = data["draws"]
        saved_engines = list(data["engines"])

        if saved_engines != expected_units[ds]:
            draws_valid = False
            failing_reasons.append(
                f"Saved engines for {ds} do not match frozen sorted validation partition."
            )

        if saved_draws.shape != (10000, len(expected_units[ds])):
            draws_valid = False
            failing_reasons.append(
                f"Draws array shape for {ds} {saved_draws.shape} != "
                f"(10000, {len(expected_units[ds])})"
            )

        # Independently reconstruct draw sequence
        indep_draws = independently_generate_bootstrap_draws(
            dataset=ds,
            partition_engines=expected_units[ds],
            base_dir=base,
            n_replicates=10000,
        )
        if not np.array_equal(saved_draws, indep_draws):
            draws_valid = False
            failing_reasons.append(
                f"Saved bootstrap draws for {ds} do not match independent PRNG reconstruction."
            )

    checks["bootstrap_draws_exact_reconstruction"] = draws_valid

    # 7. Fail-Closed CI Verification against Explicit Statistic Specs
    stat_specs = get_expected_contrast_statistic_specs()
    df_contrasts = pd.read_csv(s_dir / "contrast_intervals.csv", float_precision="round_trip")

    if len(df_contrasts) != len(stat_specs):
        failing_reasons.append(
            f"contrast_intervals.csv row count {len(df_contrasts)} != expected {len(stat_specs)}"
        )

    # Load all NPZ files
    npz_data: dict[str, Any] = {}
    for ds in CONFIRMATORY_DATASETS:
        npz_data[f"bootstrap_statistics_{ds}.npz"] = np.load(
            s_dir / f"bootstrap_statistics_{ds}.npz", allow_pickle=False
        )
    npz_data["bootstrap_statistics_RQ4.npz"] = np.load(
        s_dir / "bootstrap_statistics_RQ4.npz", allow_pickle=False
    )

    contrast_row_map = {str(r.contrast_id): r for r in df_contrasts.itertuples()}
    max_ci_discrepancy = 0.0
    compared_stats_count = 0
    failing_stat_ids: list[str] = []

    for stat_id, spec in stat_specs.items():
        if stat_id not in contrast_row_map:
            failing_stat_ids.append(stat_id)
            failing_reasons.append(
                f"Required contrast statistic '{stat_id}' missing from contrast_intervals.csv"
            )
            continue

        c_row = contrast_row_map[stat_id]
        target_npz = npz_data.get(spec.target_npz)
        if target_npz is None:
            failing_stat_ids.append(stat_id)
            failing_reasons.append(
                f"Target NPZ '{spec.target_npz}' not found for statistic '{stat_id}'"
            )
            continue

        if spec.is_bounded:
            assert spec.lower_array_key is not None and spec.upper_array_key is not None
            if (
                spec.lower_array_key not in target_npz.files
                or spec.upper_array_key not in target_npz.files
            ):
                failing_stat_ids.append(stat_id)
                failing_reasons.append(
                    f"Bounded keys '{spec.lower_array_key}'/'{spec.upper_array_key}' "
                    f"missing from {spec.target_npz}"
                )
                continue
            arr_low = target_npz[spec.lower_array_key]
            arr_up = target_npz[spec.upper_array_key]
            if len(arr_low) != 10000 or len(arr_up) != 10000:
                failing_stat_ids.append(stat_id)
                failing_reasons.append(f"Array length for bounded stat '{stat_id}' != 10000")
                continue
            if not (np.all(np.isfinite(arr_low)) and np.all(np.isfinite(arr_up))):
                failing_stat_ids.append(stat_id)
                failing_reasons.append(
                    f"Non-finite values detected in bounded arrays for '{stat_id}'"
                )
                continue

            indep_ci_95_l = float(np.quantile(arr_low, 0.025, method="linear"))
            indep_ci_95_h = float(np.quantile(arr_up, 0.975, method="linear"))
            indep_ci_dec_l = float(np.quantile(arr_low, 0.00625, method="linear"))
            indep_ci_dec_h = float(np.quantile(arr_up, 0.99375, method="linear"))
        else:
            assert spec.array_key is not None
            if spec.array_key not in target_npz.files:
                failing_stat_ids.append(stat_id)
                failing_reasons.append(
                    f"Scalar array key '{spec.array_key}' missing from {spec.target_npz}"
                )
                continue
            rep_arr = target_npz[spec.array_key]
            if len(rep_arr) != 10000:
                failing_stat_ids.append(stat_id)
                failing_reasons.append(f"Array length for scalar stat '{stat_id}' != 10000")
                continue
            if not np.all(np.isfinite(rep_arr)):
                failing_stat_ids.append(stat_id)
                failing_reasons.append(
                    f"Non-finite values detected in scalar array for '{stat_id}'"
                )
                continue

            indep_ci_95_l = float(np.quantile(rep_arr, 0.025, method="linear"))
            indep_ci_95_h = float(np.quantile(rep_arr, 0.975, method="linear"))
            indep_ci_dec_l = float(np.quantile(rep_arr, 0.00625, method="linear"))
            indep_ci_dec_h = float(np.quantile(rep_arr, 0.99375, method="linear"))

        diff_95_l = abs(indep_ci_95_l - float(c_row.ci_95_low))
        diff_95_h = abs(indep_ci_95_h - float(c_row.ci_95_high))
        diff_dec_l = abs(indep_ci_dec_l - float(c_row.ci_decision_low))
        diff_dec_h = abs(indep_ci_dec_h - float(c_row.ci_decision_high))
        max_d = max(diff_95_l, diff_95_h, diff_dec_l, diff_dec_h)

        if max_d > max_ci_discrepancy:
            max_ci_discrepancy = max_d
        if max_d > 1e-10:
            failing_stat_ids.append(stat_id)
            failing_reasons.append(f"CI numerical discrepancy for '{stat_id}': {max_d} > 1e-10")

        compared_stats_count += 1

    checks["ci_verification"] = {
        "expected_stats_count": len(stat_specs),
        "compared_stats_count": compared_stats_count,
        "max_discrepancy": max_ci_discrepancy,
        "failing_statistic_ids": failing_stat_ids,
        "match": len(failing_stat_ids) == 0 and compared_stats_count == len(stat_specs),
    }

    # 8. Component Evidence Verification
    df_comp = pd.read_csv(s_dir / "component_evidence.csv", float_precision="round_trip")
    manifest_rq = get_rq_component_manifest()
    all_expected_comp_ids: set[str] = set()
    for rq in ("RQ1", "RQ2", "RQ3", "RQ4"):
        all_expected_comp_ids.update(c.component_id for c in manifest_rq[rq])

    actual_comp_ids = list(df_comp["component_id"])
    comp_unique_ids = set(actual_comp_ids)

    checks["component_evidence_completeness"] = {
        "expected_count": EXPECTED_TOTAL_COMPONENTS_COUNT,
        "actual_rows": len(df_comp),
        "unique_count": len(comp_unique_ids),
        "no_duplicates": len(df_comp) == len(comp_unique_ids),
        "exact_match": comp_unique_ids == all_expected_comp_ids,
    }
    if not (
        checks["component_evidence_completeness"]["no_duplicates"]
        and checks["component_evidence_completeness"]["exact_match"]
    ):
        failing_reasons.append(
            "Component evidence contains duplicate, missing, or unexpected component IDs."
        )

    # Validate completeness with decisions.py validator
    try:
        val_res = validate_component_manifest_completeness(evaluated_component_ids=actual_comp_ids)
        checks["component_manifest_validation"] = val_res
    except Exception as exc:
        checks["component_manifest_validation"] = {"all_valid": False, "error": str(exc)}
        failing_reasons.append(f"Component manifest validation raised: {exc}")

    # Verify failure safeguard counts against outcomes
    failure_mismatches: list[str] = []
    for r in df_comp.itertuples():
        if r.evidence_kind == "observed_failure":
            prop_cnt = int(
                df_outcomes[
                    (df_outcomes["dataset"] == r.dataset)
                    & (df_outcomes["model_family"] == r.model_family)
                    & (df_outcomes["method_or_control_id"] == "decision_aware_hcp")
                    & (df_outcomes["nominal_coverage"] == PRIMARY_CANONICAL_COVERAGE)
                    & (df_outcomes["scenario_id"] == PRIMARY_COST_SCENARIO)
                ]["failed"].sum()
            )
            comp_cnt = int(
                df_outcomes[
                    (df_outcomes["dataset"] == r.dataset)
                    & (df_outcomes["model_family"] == r.model_family)
                    & (df_outcomes["method_or_control_id"] == r.comparator)
                    & (df_outcomes["nominal_coverage"] == PRIMARY_CANONICAL_COVERAGE)
                    & (df_outcomes["scenario_id"] == PRIMARY_COST_SCENARIO)
                ]["failed"].sum()
            )
            if (
                int(r.proposed_failure_count) != prop_cnt
                or int(r.comparator_failure_count) != comp_cnt
            ):
                failure_mismatches.append(r.component_id)

    checks["failure_safeguards_exact_match"] = {
        "mismatches": failure_mismatches,
        "match": len(failure_mismatches) == 0,
    }
    if failure_mismatches:
        failing_reasons.append(
            f"Failure safeguard count mismatch for components: {failure_mismatches}"
        )

    # Verify developmental smoke only status
    all_smoke_status = (
        all(s == "DEVELOPMENT_SMOKE_ONLY" for s in df_contrasts["status"])
        and all(s == "DEVELOPMENT_SMOKE_ONLY" for s in df_comp["status"])
        and all(s == "DEVELOPMENT_SMOKE_ONLY" for s in df_cell["status"])
    )
    checks["development_smoke_status_only"] = all_smoke_status
    if not all_smoke_status:
        failing_reasons.append(
            "Non-development or premature confirmatory status detected in artifacts."
        )

    all_passed = (
        checks["required_files_present"]
        and all(checks["validation_engine_counts"].values())
        and checks["canonical_coverage_valid"]
        and checks["configurations_exact_match"]["match"]
        and checks["outcome_keys_exact_match"]["no_duplicate_keys"]
        and checks["outcome_keys_exact_match"]["keys_equal_expected"]
        and checks["engine_metric_keys_exact_match"]["no_duplicate_keys"]
        and checks["engine_metric_keys_exact_match"]["keys_equal_expected"]
        and checks["validation_partition_only"]
        and checks["cell_summary_keys_exact_match"]["no_duplicate_keys"]
        and checks["cell_summary_keys_exact_match"]["keys_equal_expected"]
        and checks["cell_summary_cost_reconstruction"]["match"]
        and checks["point_predictions_all_seeds"]
        and checks["point_predictions_unique_keys"]
        and checks["point_predictions_cache_match"]["match"]
        and checks["bootstrap_draws_exact_reconstruction"]
        and checks["ci_verification"]["match"]
        and checks["component_evidence_completeness"]["exact_match"]
        and checks["component_manifest_validation"].get("all_valid", False)
        and checks["failure_safeguards_exact_match"]["match"]
        and checks["development_smoke_status_only"]
    )

    return {
        "status": "PASS" if all_passed else "FAIL",
        "overall_match": all_passed,
        "failing_reasons": failing_reasons,
        "checks": checks,
    }
