"""Step 9: Validation-Only Smoke Evaluation Script.

Protocol: step09-v1
Scope: End-to-end evaluation machinery test on validation partition engines only.
Strict Boundary:
- Evaluates strictly on validation engines (FD001: 10, FD002: 26, FD004: 27 engines).
- Executes 10,000 stratified engine-cluster bootstrap draws per dataset.
- Evaluates 3 datasets, both models, 5 seeds, 3 methods, 3 coverages, 3 scenarios, FD002 controls.
- Strictly labels all outputs DEVELOPMENT_SMOKE_ONLY.
- Does NOT emit confirmatory RQ classifications.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from intellitwin.data.splits import load_split_manifest
from intellitwin.decision.controls import (
    simulate_observable_trajectory,
)
from intellitwin.evaluation.artifacts import (
    OUTPUT_CELL_SUMMARY,
    OUTPUT_ENGINE_SEED_OUTCOMES,
    OUTPUT_EXECUTION_MANIFEST,
    save_bootstrap_draws_npz,
)
from intellitwin.evaluation.bootstrap import (
    generate_stratified_bootstrap_draws,
)
from intellitwin.evaluation.metrics import (
    compute_equal_engine_metric,
    compute_interval_score,
)
from intellitwin.evaluation.schema import (
    ALL_NOMINAL_COVERAGES,
    CONFIRMATORY_DATASETS,
    CONFIRMATORY_METHODS,
    CONFIRMATORY_MODELS,
    CONFIRMATORY_SEEDS,
    COST_SCENARIOS,
    INTERVENTION_THRESHOLD_CYCLES,
    PROTOCOL_VERSION,
)
from intellitwin.evaluation.validation import (
    assert_no_held_out_path,
    assert_permitted_partition_only,
)
from intellitwin.provenance import (
    capture_environment_metadata,
    get_git_info,
    write_immutable_csv,
    write_immutable_json,
)
from intellitwin.simulator.types import MaintenanceAction
from intellitwin.uncertainty.artifacts import (
    load_frozen_calibrator,
    resolve_repo_relative_path,
)


def run_validation_smoke(
    base_dir: Path | str = ".",
    output_dir: Path | str = "experiments/confirmatory_development/validation_smoke",
    allow_dirty: bool = False,
    n_bootstrap: int = 10000,
) -> None:
    """Execute validation-only smoke run across all 6 cells and controls."""
    base = Path(base_dir).resolve()
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    assert_no_held_out_path(str(out_dir))

    git_sha, git_dirty = get_git_info(allow_dirty=allow_dirty)
    env_meta = capture_environment_metadata()

    print("=" * 80)
    print("Step 9: Confirmatory Evaluation Validation Smoke Run (DEVELOPMENT ONLY)")
    print(f"Git Commit: {git_sha} (dirty={git_dirty})")
    print(f"Output Directory: {out_dir}")
    print("=" * 80)

    # 1. Load control selections for FD002
    control_selections: dict[str, Any] = {}
    for fam in ("GBR", "LSTM"):
        sel_p = base / f"experiments/confirmatory_development/controls/FD002/{fam}/selection.json"
        if not sel_p.exists():
            raise FileNotFoundError(f"Required control selection missing: {sel_p}.")
        with open(sel_p, encoding="utf-8") as f:
            control_selections[fam] = json.load(f)["selected_controls"]

    engine_outcomes_rows: list[dict[str, Any]] = []
    cell_summary_rows: list[dict[str, Any]] = []

    for ds in CONFIRMATORY_DATASETS:
        print(f"\nProcessing Dataset {ds}...")
        split_p = resolve_repo_relative_path(
            base, f"data/splits/{ds.lower()}_engine_split_seed_2026.json"
        )
        split_data = load_split_manifest(split_p)
        valid_engines = sorted(split_data.get_partition("validation"))

        # Generate 10,000 stratified bootstrap draws for this dataset
        print(
            f"  Generating {n_bootstrap} stratified bootstrap draws for {ds} "
            f"({len(valid_engines)} engines)..."
        )
        draws = generate_stratified_bootstrap_draws(
            dataset=ds,
            partition_engines=valid_engines,
            base_dir=base,
            n_replicates=n_bootstrap,
        )
        draws_path = out_dir / f"bootstrap_draws_{ds}.npz"
        save_bootstrap_draws_npz(
            path=draws_path,
            draws=draws,
            dataset=ds,
            column_order=valid_engines,
            replicate_count=n_bootstrap,
        )
        print(f"  Saved bootstrap draws to {draws_path}")

        for fam in CONFIRMATORY_MODELS:
            print(f"  Evaluating {ds} / {fam} across 5 seeds...")
            # Load validation point predictions across 5 seeds
            dfs = []
            for seed in CONFIRMATORY_SEEDS:
                p_csv = resolve_repo_relative_path(
                    base,
                    f"experiments/calibration/point_predictions/validation/{ds}/{fam}/seed_{seed}.csv",
                )
                df_s = pd.read_csv(p_csv)
                df_s["seed"] = seed
                dfs.append(df_s)
            df_cell = pd.concat(dfs, ignore_index=True)

            # Assert permitted partition only
            assert_permitted_partition_only(
                actual_units=df_cell["unit"].unique(),
                expected_units=valid_engines,
                partition_name=f"{ds} validation",
            )

            # Determine engine lifetimes T
            engine_lifetimes: dict[int, int] = {}
            for unit, grp in df_cell.groupby("unit"):
                max_cyc = int(grp["endpoint_cycle"].max())
                rul_max = float(grp.loc[grp["endpoint_cycle"] == max_cyc, "rul_true"].iloc[0])
                engine_lifetimes[int(unit)] = max_cyc + int(round(rul_max))

            # Evaluate each primary method
            for method in CONFIRMATORY_METHODS:
                for cov in ALL_NOMINAL_COVERAGES:
                    # Generate intervals
                    lowers = []
                    uppers = []
                    for seed in CONFIRMATORY_SEEDS:
                        df_seed = df_cell[df_cell["seed"] == seed]
                        cal = load_frozen_calibrator(
                            dataset=ds,
                            model_family=fam,
                            seed=seed,
                            method_id=method,
                            base_dir=base,
                        )
                        low, upp, _ = cal.predict_intervals(
                            predictions=df_seed["prediction"].to_numpy(),
                            regimes=df_seed["regime"].to_numpy(),
                            nominal_coverage=cov,
                        )
                        lowers.extend(low)
                        uppers.extend(upp)

                    df_cell_eval = df_cell.copy()
                    df_cell_eval["lower"] = lowers
                    df_cell_eval["upper"] = uppers
                    df_cell_eval["covered"] = (
                        (df_cell_eval["rul_true"] >= df_cell_eval["lower"])
                        & (df_cell_eval["rul_true"] <= df_cell_eval["upper"])
                    ).astype(float)
                    df_cell_eval["width"] = df_cell_eval["upper"] - df_cell_eval["lower"]
                    df_cell_eval["interval_score"] = compute_interval_score(
                        y_true=df_cell_eval["rul_true"].to_numpy(),
                        lower=df_cell_eval["lower"].to_numpy(),
                        upper=df_cell_eval["upper"].to_numpy(),
                        nominal_coverage=cov,
                    )

                    # Compute fleet outcomes under each cost scenario
                    for scen_id, scenario in COST_SCENARIOS.items():
                        outcomes = []
                        for (u, s), grp in df_cell_eval.groupby(["unit", "seed"]):
                            grp_sort = grp.sort_values("endpoint_cycle")
                            T = engine_lifetimes[int(u)]
                            out = simulate_observable_trajectory(
                                unit=int(u),
                                seed=int(s),
                                control_id=method,
                                cycles=grp_sort["endpoint_cycle"].to_numpy(),
                                predictions=grp_sort["prediction"].to_numpy(),
                                lower_bounds=grp_sort["lower"].to_numpy(),
                                upper_bounds=grp_sort["upper"].to_numpy(),
                                regimes=grp_sort["regime"].to_numpy(),
                                failure_cycle=T,
                                policy_fn=lambda state: (
                                    MaintenanceAction.MAINTAIN_NOW
                                    if state.lower_rul <= INTERVENTION_THRESHOLD_CYCLES
                                    else MaintenanceAction.CONTINUE
                                ),
                                scenario=scenario,
                            )
                            outcomes.append(out)

                            engine_outcomes_rows.append(
                                {
                                    "dataset": ds,
                                    "model_family": fam,
                                    "seed": s,
                                    "method_or_control_id": method,
                                    "nominal_coverage": cov,
                                    "scenario_id": scen_id,
                                    "unit": u,
                                    "terminal_event": out.terminal_event,
                                    "intervention_cycle": out.intervention_cycle,
                                    "failed": out.failed,
                                    "pm": out.pm_occurred,
                                    "wasted_rul": out.wasted_rul,
                                    "total_cost": out.total_cost,
                                    "is_cost_inefficient_early_pm": (
                                        out.is_cost_inefficient_early_pm
                                    ),
                                }
                            )

                        # Equal engine mean cost
                        df_o = pd.DataFrame(
                            [
                                {
                                    "unit": o.unit,
                                    "seed": o.seed,
                                    "cost": o.total_cost,
                                    "failed": 1.0 if o.failed else 0.0,
                                    "pm": 1.0 if o.pm_occurred else 0.0,
                                    "wasted": o.wasted_rul,
                                    "early_pm": 1.0 if o.is_cost_inefficient_early_pm else 0.0,
                                }
                                for o in outcomes
                            ]
                        )
                        e_avgs = df_o.groupby("unit").mean()
                        mean_cost = float(e_avgs["cost"].mean())
                        fail_rate = float(e_avgs["failed"].mean())
                        pm_rate = float(e_avgs["pm"].mean())
                        mean_wasted = float(e_avgs["wasted"].mean())
                        fleet_early_pm = float(e_avgs["early_pm"].mean())
                        pm_sub = df_o[df_o["pm"] > 0]
                        pm_only_early = (
                            float(pm_sub["early_pm"].mean()) if len(pm_sub) > 0 else float("nan")
                        )

                        marg_cov = compute_equal_engine_metric(df_cell_eval, "covered")
                        mpiw = compute_equal_engine_metric(df_cell_eval, "width")
                        int_score = compute_equal_engine_metric(df_cell_eval, "interval_score")

                        cell_summary_rows.append(
                            {
                                "dataset": ds,
                                "model_family": fam,
                                "method_or_control_id": method,
                                "nominal_coverage": cov,
                                "scenario_id": scen_id,
                                "mean_cost": mean_cost,
                                "failure_rate": fail_rate,
                                "pm_rate": pm_rate,
                                "mean_wasted_rul": mean_wasted,
                                "fleet_early_pm_rate": fleet_early_pm,
                                "pm_only_early_pm_rate": pm_only_early,
                                "marginal_coverage": marg_cov,
                                "marginal_coverage_abs_error": abs(marg_cov - cov),
                                "mpiw": mpiw,
                                "interval_score": int_score,
                            }
                        )

    # Save output artifacts
    df_outcomes = pd.DataFrame(engine_outcomes_rows)
    df_cell_summary = pd.DataFrame(cell_summary_rows)

    write_immutable_csv(out_dir / OUTPUT_ENGINE_SEED_OUTCOMES, df_outcomes, overwrite=True)
    write_immutable_csv(out_dir / OUTPUT_CELL_SUMMARY, df_cell_summary, overwrite=True)

    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "status": "DEVELOPMENT_SMOKE_ONLY",
        "notice": (
            "All outputs generated on validation engines only. "
            "Confirmatory test results remain strictly pending."
        ),
        "git_commit": git_sha,
        "git_dirty": git_dirty,
        "environment": env_meta,
        "bootstrap_replicates": n_bootstrap,
        "artifacts_generated": [
            OUTPUT_ENGINE_SEED_OUTCOMES,
            OUTPUT_CELL_SUMMARY,
            "bootstrap_draws_FD001.npz",
            "bootstrap_draws_FD002.npz",
            "bootstrap_draws_FD004.npz",
        ],
    }
    write_immutable_json(out_dir / OUTPUT_EXECUTION_MANIFEST, manifest, overwrite=True)

    print("\n" + "=" * 80)
    print("VALIDATION SMOKE EVALUATION COMPLETE (STATUS: PASS - DEVELOPMENT ONLY)")
    print(f"Results written to: {out_dir}")
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description="Step 9 Validation Smoke Evaluation")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="experiments/confirmatory_development/validation_smoke",
        help="Directory to write validation smoke outputs",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Permit execution on dirty git working tree (for exploratory smoke only)",
    )
    parser.add_argument(
        "--bootstrap-replicates",
        type=int,
        default=10000,
        help="Number of bootstrap replicates (default: 10000)",
    )
    args = parser.parse_args()

    run_validation_smoke(
        base_dir=".",
        output_dir=args.output_dir,
        allow_dirty=args.allow_dirty,
        n_bootstrap=args.bootstrap_replicates,
    )


if __name__ == "__main__":
    main()
