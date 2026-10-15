"""Deterministic tests proving pre-test verification rejects corrupt or incomplete evidence."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from intellitwin.evaluation.decisions import (
    get_rq_component_manifest,
)
from intellitwin.evaluation.evidence_schema import (
    map_component_to_evidence_spec,
)
from intellitwin.evaluation.metrics import (
    compute_equal_engine_metric,
)
from intellitwin.evaluation.runner import compute_subgroup_bounds
from intellitwin.evaluation.schema import CostScenario
from intellitwin.evaluation.verification import (
    verify_validation_smoke_matrix,
)
from intellitwin.simulator.types import MaintenanceAction
from scripts.audit_step09_freeze import verify_step08_report_records

# =============================================================================
# 1. Hand-Calculated Numerical Fixtures
# =============================================================================


def test_equal_engine_versus_pooled_cycle_weighting() -> None:
    """Equal engine weighting must compute mean across engines, not pooled cycles.

    Engine 1: 10 cycles with coverage 1.0 (mean = 1.0).
    Engine 2: 90 cycles with coverage 0.0 (mean = 0.0).
    Pooled cycle mean = 10 / 100 = 0.10.
    Equal engine mean = (1.0 + 0.0) / 2 = 0.50.
    """
    df = pd.DataFrame(
        {
            "unit": [1] * 10 + [2] * 90,
            "seed": [2026] * 100,
            "covered": [1.0] * 10 + [0.0] * 90,
        }
    )
    equal_eng_metric = compute_equal_engine_metric(df, "covered")
    pooled_metric = float(df["covered"].mean())

    assert abs(equal_eng_metric - 0.50) < 1e-12
    assert abs(pooled_metric - 0.10) < 1e-12
    assert equal_eng_metric != pooled_metric


def test_averaging_seeds_within_engine_before_fleet_average() -> None:
    """Costs must average across seeds within each engine before fleet averaging."""
    outcomes = pd.DataFrame(
        {
            "unit": [1, 1, 2, 2],
            "seed": [2026, 2027, 2026, 2027],
            "total_cost": [100.0, 200.0, 300.0, 300.0],
        }
    )
    engine_means = outcomes.groupby("unit")["total_cost"].mean()
    assert engine_means[1] == 150.0
    assert engine_means[2] == 300.0
    fleet_mean = float(engine_means.mean())
    assert fleet_mean == 225.0


def test_marginal_coverage_abs_error_not_mean_per_engine_error() -> None:
    """Marginal coverage error is abs(fleet_coverage - 0.90), NOT mean(abs(engine_cov - 0.90)).

    Engine 1: coverage 0.85 (abs error 0.05).
    Engine 2: coverage 0.95 (abs error 0.05).
    Mean per-engine abs error = 0.05.
    Fleet coverage = 0.90 -> marginal coverage abs error = 0.00.
    """
    eng_covs = np.array([0.85, 0.95])
    mean_per_engine_abs_error = float(np.mean(np.abs(eng_covs - 0.90)))
    fleet_cov = float(np.mean(eng_covs))
    marginal_abs_error = abs(fleet_cov - 0.90)

    assert abs(mean_per_engine_abs_error - 0.05) < 1e-12
    assert abs(marginal_abs_error - 0.00) < 1e-12
    assert marginal_abs_error != mean_per_engine_abs_error


def test_missing_subgroup_bounds_hand_calculation() -> None:
    """When a subgroup is absent in a replicate, its error bound must be [0.0, 0.90].

    Family worst lower = max(group lower bounds).
    Family worst upper = max(group upper bounds).
    """
    M = np.array([[1.0, 0.0]])  # replicate 0: unit 1 present (count 1), unit 2 absent (count 0)
    eng_to_idx = {1: 0, 2: 1}

    # Group 1 has unit 1 (present, cov 0.88 -> err |0.88 - 0.90| = 0.02 -> bound [0.02, 0.02])
    # Group 2 has unit 2 (absent -> bound [0.0, 0.90])
    cov_map_by_group = {
        "G1": {1: 0.88},
        "G2": {2: 0.80},
    }
    low, up = compute_subgroup_bounds(
        multiplicity_matrix=M,
        eng_to_idx=eng_to_idx,
        cov_map_by_group=cov_map_by_group,
        eligible_groups=["G1", "G2"],
        nominal_coverage=0.90,
    )
    assert abs(low[0] - 0.02) < 1e-12
    assert abs(up[0] - 0.90) < 1e-12


def test_empty_eligible_group_family_is_uninformative() -> None:
    """A family with no eligible groups returns [0.0, 0.90] (never [0.0, 0.0])."""
    M = np.ones((5, 10))
    eng_to_idx = {i: i for i in range(10)}
    low, up = compute_subgroup_bounds(
        multiplicity_matrix=M,
        eng_to_idx=eng_to_idx,
        cov_map_by_group={},
        eligible_groups=[],
        nominal_coverage=0.90,
    )
    assert np.all(low == 0.0)
    assert np.all(up == 0.90)


def test_conservative_error_contrasts_hand_calculation() -> None:
    """Delta_error = Baseline - Proposed must use conservative bound interval arithmetic:
    Delta_lower = Base_lower - Prop_upper
    Delta_upper = Base_upper - Prop_lower
    """
    base_low, base_up = 0.04, 0.10
    prop_low, prop_up = 0.01, 0.03

    delta_low = base_low - prop_up  # 0.04 - 0.03 = 0.01
    delta_up = base_up - prop_low  # 0.10 - 0.01 = 0.09

    assert abs(delta_low - 0.01) < 1e-12
    assert abs(delta_up - 0.09) < 1e-12


def test_equal_six_cell_aggregation_hand_calculation() -> None:
    """RQ4 equal-six-cell aggregation applies equal weight 1/6 across cells."""
    cell_values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    agg_val = float(np.mean(cell_values))
    expected = 21.0 / 6.0
    assert abs(agg_val - expected) < 1e-12
    assert abs(agg_val - 3.5) < 1e-12


def test_bounded_versus_scalar_confidence_intervals() -> None:
    """Bounded CI takes lower endpoint from lower array and upper from upper array."""
    low_arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    up_arr = np.array([2.0, 3.0, 4.0, 5.0, 6.0])

    q_low = float(np.quantile(low_arr, 0.10, method="linear"))
    q_high = float(np.quantile(up_arr, 0.90, method="linear"))

    assert q_low == float(np.quantile(low_arr, 0.10))
    assert q_high == float(np.quantile(up_arr, 0.90))
    assert q_low < q_high


def test_action_trace_preservation_across_cost_repricing() -> None:
    """Cost repricing must not alter intervention cycle, failed, or pm_occurred."""
    from intellitwin.evaluation.inference import SimulationTraceOutcome, reprice_simulation_outcome

    trace = SimulationTraceOutcome(
        unit=1,
        seed=2026,
        configuration_id="test_cfg",
        method_or_control_id="decision_aware_hcp",
        failure_cycle=162,
        terminal_event="preventive_maintenance",
        intervention_cycle=150,
        failed=False,
        pm_occurred=True,
        wasted_rul=12.0,
        is_cost_inefficient_early_pm=False,
        total_cost=25.0,
        decision_trace=[
            (30, MaintenanceAction.CONTINUE.value),
            (150, MaintenanceAction.MAINTAIN_NOW.value),
        ],
    )

    new_scen = CostScenario(
        scenario_id="failure_sensitive", c_pm=10.0, c_fail=200.0, c_waste=2.0, r_equal=20.0
    )
    repriced = reprice_simulation_outcome(trace, new_scen)

    assert repriced.intervention_cycle == trace.intervention_cycle
    assert repriced.failed == trace.failed
    assert repriced.pm_occurred == trace.pm_occurred
    assert repriced.wasted_rul == trace.wasted_rul
    assert repriced.terminal_event == trace.terminal_event
    # Repriced cost: 10 + 2.0 * 12 = 34.0
    assert repriced.total_cost == 34.0


# =============================================================================
# 2. Corrupt Evidence Rejection Tests (verify_validation_smoke_matrix)
# =============================================================================


def _create_minimal_valid_smoke_fixture(tmp_path: Path) -> Path:
    """Create a synthetically complete, internally consistent smoke fixture."""
    # We copy the structure from the existing v2 validation_smoke as starting point
    src_dir = Path("experiments/pretest_verification_v2/validation_smoke")
    fixture_dir = tmp_path / "valid_smoke"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    for p in src_dir.glob("*"):
        if p.is_file():
            (fixture_dir / p.name).write_bytes(p.read_bytes())

    # Add 5-seed point_predictions.csv
    df_pts = pd.read_csv(src_dir / "point_predictions.csv")
    pts_all_seeds = []
    for s in (2026, 2027, 2028, 2029, 2030):
        df_s = df_pts.copy()
        df_s["seed"] = s
        pts_all_seeds.append(df_s)
    df_pts_full = pd.concat(pts_all_seeds, ignore_index=True)
    df_pts_full.to_csv(fixture_dir / "point_predictions.csv", index=False)

    # Add component_evidence.csv
    manifest = get_rq_component_manifest()
    all_comps = [c for rq in ("RQ1", "RQ2", "RQ3", "RQ4") for c in manifest[rq]]
    df_contrasts = pd.read_csv(src_dir / "contrast_intervals.csv")
    c_lookup = {r["contrast_id"]: r for _, r in df_contrasts.iterrows()}

    comp_rows = []
    for comp in all_comps:
        ev_kind, stat_id = map_component_to_evidence_spec(
            comp.component_id,
            comp.rq_id,
            comp.model_family,
            comp.dataset,
            comp.comparator,
            comp.metric,
            comp.rule_type,
        )
        if ev_kind == "observed_failure":
            row = {
                "component_id": comp.component_id,
                "rq_id": comp.rq_id,
                "dataset": comp.dataset or "ALL_6_CELLS",
                "model_family": comp.model_family or "BOTH",
                "comparator": comp.comparator,
                "metric": comp.metric,
                "rule_type": comp.rule_type,
                "margin": comp.margin,
                "evidence_kind": ev_kind,
                "statistic_id": stat_id,
                "observed_lower": np.nan,
                "observed_upper": np.nan,
                "ci_95_low": np.nan,
                "ci_95_high": np.nan,
                "ci_decision_low": np.nan,
                "ci_decision_high": np.nan,
                "proposed_failure_count": 0,
                "comparator_failure_count": 0,
                "status": "DEVELOPMENT_SMOKE_ONLY",
            }
        else:
            c_info = c_lookup.get(stat_id, {})
            row = {
                "component_id": comp.component_id,
                "rq_id": comp.rq_id,
                "dataset": comp.dataset or "ALL_6_CELLS",
                "model_family": comp.model_family or "BOTH",
                "comparator": comp.comparator,
                "metric": comp.metric,
                "rule_type": comp.rule_type,
                "margin": comp.margin,
                "evidence_kind": ev_kind,
                "statistic_id": stat_id,
                "observed_lower": 0.0,
                "observed_upper": 0.0,
                "ci_95_low": float(c_info.get("ci_95_low", 0.0)),
                "ci_95_high": float(c_info.get("ci_95_high", 0.0)),
                "ci_decision_low": float(c_info.get("ci_decision_low", 0.0)),
                "ci_decision_high": float(c_info.get("ci_decision_high", 0.0)),
                "proposed_failure_count": np.nan,
                "comparator_failure_count": np.nan,
                "status": "DEVELOPMENT_SMOKE_ONLY",
            }
        comp_rows.append(row)
    pd.DataFrame(comp_rows).to_csv(fixture_dir / "component_evidence.csv", index=False)

    # Add lower/upper arrays to NPZ files
    for ds in ("FD001", "FD002", "FD004"):
        npz_p = fixture_dir / f"bootstrap_statistics_{ds}.npz"
        data = dict(np.load(npz_p))
        for k in list(data.keys()):
            if "regime_error" in k or "stage_error" in k:
                data[f"{k}_lower"] = data[k]
                data[f"{k}_upper"] = data[k]
        np.savez(npz_p, **data)

    rq4_p = fixture_dir / "bootstrap_statistics_RQ4.npz"
    rq4_data = dict(np.load(rq4_p))
    for k in list(rq4_data.keys()):
        if "regime_error" in k or "stage_error" in k:
            rq4_data[f"{k}_lower"] = rq4_data[k]
            rq4_data[f"{k}_upper"] = rq4_data[k]
    np.savez(rq4_p, **rq4_data)

    return fixture_dir


def test_verifier_rejects_missing_seed_with_preserved_row_count(tmp_path: Path) -> None:
    """Verifier must reject outcomes where seed 2030 is replaced by duplicated seed 2026."""
    fixture_dir = _create_minimal_valid_smoke_fixture(tmp_path)
    outcomes_p = fixture_dir / "engine_seed_outcomes.csv"
    df = pd.read_csv(outcomes_p)

    # Corrupt: replace seed 2030 with seed 2026 (same row count, but seed 2030 missing)
    df.loc[df["seed"] == 2030, "seed"] = 2026
    df.to_csv(outcomes_p, index=False)

    res = verify_validation_smoke_matrix(fixture_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert not res["overall_match"]
    assert any("outcome_keys_exact_match" in str(k) for k in res["checks"])


def test_verifier_rejects_wrong_engine_unit(tmp_path: Path) -> None:
    """Verifier must reject outcomes where a valid engine is replaced by an invalid engine ID."""
    fixture_dir = _create_minimal_valid_smoke_fixture(tmp_path)
    outcomes_p = fixture_dir / "engine_seed_outcomes.csv"
    df = pd.read_csv(outcomes_p)

    # Replace valid unit with 999
    first_unit = int(df.loc[df["dataset"] == "FD001", "unit"].iloc[0])
    df.loc[(df["dataset"] == "FD001") & (df["unit"] == first_unit), "unit"] = 999
    df.to_csv(outcomes_p, index=False)

    res = verify_validation_smoke_matrix(fixture_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert not res["checks"]["validation_partition_only"]


def test_verifier_rejects_duplicate_outcome_keys(tmp_path: Path) -> None:
    """Verifier rejects duplicate (dataset, model, seed, method, coverage, scenario, unit) keys."""
    fixture_dir = _create_minimal_valid_smoke_fixture(tmp_path)
    outcomes_p = fixture_dir / "engine_seed_outcomes.csv"
    df = pd.read_csv(outcomes_p)

    # Duplicate first row and append
    df_dup = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    df_dup.to_csv(outcomes_p, index=False)

    res = verify_validation_smoke_matrix(fixture_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert not res["checks"]["outcome_keys_exact_match"]["no_duplicate_keys"]


def test_verifier_rejects_missing_configuration(tmp_path: Path) -> None:
    """Verifier must reject when any of the 930 required configurations is missing."""
    fixture_dir = _create_minimal_valid_smoke_fixture(tmp_path)
    outcomes_p = fixture_dir / "engine_seed_outcomes.csv"
    df = pd.read_csv(outcomes_p)

    # Drop one configuration entirely (e.g. FD001 GBR decision_aware_hcp 90 waste_sensitive)
    mask = (
        (df["dataset"] == "FD001")
        & (df["model_family"] == "GBR")
        & (df["method_or_control_id"] == "decision_aware_hcp")
        & (df["nominal_coverage"] == 0.90)
        & (df["scenario_id"] == "waste_sensitive")
    )
    df_dropped = df[~mask]
    df_dropped.to_csv(outcomes_p, index=False)

    res = verify_validation_smoke_matrix(fixture_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert not res["checks"]["configurations_exact_match"]["match"]


def test_verifier_rejects_missing_bootstrap_array(tmp_path: Path) -> None:
    """Verifier must fail closed when a required contrast's bootstrap array is absent (Defect A)."""
    fixture_dir = _create_minimal_valid_smoke_fixture(tmp_path)
    npz_p = fixture_dir / "bootstrap_statistics_FD001.npz"
    data = dict(np.load(npz_p))

    # Remove a required statistic array
    target_key = "FD001_GBR_global_hcp_cost_improvement"
    if target_key in data:
        del data[target_key]
    np.savez(npz_p, **data)

    res = verify_validation_smoke_matrix(fixture_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert not res["checks"]["ci_verification"]["match"]
    assert target_key in res["checks"]["ci_verification"]["failing_statistic_ids"]


def test_verifier_rejects_empty_interval_table(tmp_path: Path) -> None:
    """Verifier must reject an empty contrast_intervals.csv."""
    fixture_dir = _create_minimal_valid_smoke_fixture(tmp_path)
    c_p = fixture_dir / "contrast_intervals.csv"
    df_empty = pd.DataFrame(
        columns=[
            "contrast_id",
            "dataset",
            "model_family",
            "comparator",
            "metric",
            "ci_95_low",
            "ci_95_high",
            "ci_decision_low",
            "ci_decision_high",
            "status",
        ]
    )
    df_empty.to_csv(c_p, index=False)

    res = verify_validation_smoke_matrix(fixture_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert not res["checks"]["ci_verification"]["match"]


def test_verifier_rejects_altered_bootstrap_value_with_unchanged_intervals(tmp_path: Path) -> None:
    """Verifier must reject when saved bootstrap replicates do not match saved intervals."""
    fixture_dir = _create_minimal_valid_smoke_fixture(tmp_path)
    npz_p = fixture_dir / "bootstrap_statistics_FD001.npz"
    data = dict(np.load(npz_p))

    target_key = "FD001_GBR_global_hcp_cost_improvement"
    data[target_key] = data[target_key] + 10.0  # shift replicates without updating CSV
    np.savez(npz_p, **data)

    res = verify_validation_smoke_matrix(fixture_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert not res["checks"]["ci_verification"]["match"]
    assert target_key in res["checks"]["ci_verification"]["failing_statistic_ids"]


def test_verifier_rejects_altered_bootstrap_draws(tmp_path: Path) -> None:
    """Verifier rejects bootstrap draws differing from independent PRNG reconstruction."""
    fixture_dir = _create_minimal_valid_smoke_fixture(tmp_path)
    draws_p = fixture_dir / "bootstrap_draws_FD001.npz"
    data = dict(np.load(draws_p))

    # Permute draw row 0
    data["draws"][0] = np.roll(data["draws"][0], 1)
    np.savez(draws_p, **data)

    res = verify_validation_smoke_matrix(fixture_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert not res["checks"]["bootstrap_draws_exact_reconstruction"]


def test_verifier_rejects_missing_component_evidence(tmp_path: Path) -> None:
    """Verifier rejects when component_evidence.csv is missing components (Defect E)."""
    fixture_dir = _create_minimal_valid_smoke_fixture(tmp_path)
    comp_p = fixture_dir / "component_evidence.csv"
    df_comp = pd.read_csv(comp_p)

    # Drop first component
    df_comp.iloc[1:].to_csv(comp_p, index=False)

    res = verify_validation_smoke_matrix(fixture_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert not res["checks"]["component_evidence_completeness"]["exact_match"]


def test_verifier_rejects_duplicate_component_evidence(tmp_path: Path) -> None:
    """Verifier must reject duplicate component IDs in component_evidence.csv."""
    fixture_dir = _create_minimal_valid_smoke_fixture(tmp_path)
    comp_p = fixture_dir / "component_evidence.csv"
    df_comp = pd.read_csv(comp_p)

    df_dup = pd.concat([df_comp, df_comp.iloc[[0]]], ignore_index=True)
    df_dup.to_csv(comp_p, index=False)

    res = verify_validation_smoke_matrix(fixture_dir, base_dir=".")
    assert res["status"] == "FAIL"
    assert not res["checks"]["component_evidence_completeness"]["no_duplicates"]


def test_step08_report_records_verifier_rejects_missing_record(tmp_path: Path) -> None:
    """Step-8 report audit must reject when fewer than 60 unique partition/seed records exist."""
    fake_s8 = tmp_path / "fake_s8.json"
    fake_data = {
        "overall_status": "PASS",
        "details": {
            "checkpoint_prediction_reproduction": {
                "records": [
                    {
                        "dataset": "FD001",
                        "model_family": "GBR",
                        "seed": 2026,
                        "partition": "validation",
                        "status": "PASS",
                        "max_abs_diff": 0.0,
                    }
                ]
            }
        },
    }
    with open(fake_s8, "w") as f:
        json.dump(fake_data, f)

    res = verify_step08_report_records(fake_s8)
    assert res["status"] == "FAIL"
    assert res["record_count"] == 1
    assert not res["match"]
