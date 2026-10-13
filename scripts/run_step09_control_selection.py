"""Step 9: Benchmark Matched-Conservatism Control Parameter Selection Script.

Protocol: step09-v1
Scope: Selects parameters for all four prespecified RQ3 controls on FD002 validation engines:
1. matched_width_interval (matched to proposed method validation MPIW)
2. widened_interval (cost-optimal lambda >= 1.0)
3. point_safety_margin (cost-optimal margin m in 0..250 cycles)
4. earlier_intervention (cost-optimal horizon h in 1..251 cycles)

Strict Anti-Leakage Boundary:
- Evaluates strictly on FD002 validation engines across 5 frozen seeds.
- Rejects training, calibration, and test data requests before execution.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from intellitwin.decision.controls import run_fd002_control_selection
from intellitwin.evaluation.schema import PRIMARY_COST_SCENARIO
from intellitwin.provenance import write_immutable_csv, write_immutable_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Step 9: Benchmark Matched-Conservatism Control Parameter Selection"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="experiments/confirmatory_development/controls",
        help="Base directory to store control selection artifacts",
    )
    parser.add_argument(
        "--scenario-id",
        type=str,
        default=PRIMARY_COST_SCENARIO,
        help="Cost scenario to evaluate for control selection (default: primary_reference)",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Permit execution on dirty git working tree (for exploratory runs only)",
    )
    args = parser.parse_args()

    out_base = Path(args.output_dir).resolve()

    print("=" * 80)
    print("Step 9: Prespecified Benchmark Control Parameter Selection (FD002 Validation Only)")
    print(f"Cost scenario: {args.scenario_id}")
    print(f"Output directory: {out_base}")
    print("=" * 80)

    for fam in ("GBR", "LSTM"):
        print(f"\nSelecting controls for FD002 / {fam}...")
        try:
            df_cand, df_outcomes, sel_json = run_fd002_control_selection(
                model_family=fam,
                base_dir=".",
                scenario_id=args.scenario_id,
                allow_dirty=args.allow_dirty,
            )
        except Exception as exc:
            print(f"FAILED control selection for {fam}: {exc}")
            sys.exit(1)

        fam_dir = out_base / "FD002" / fam
        fam_dir.mkdir(parents=True, exist_ok=True)

        cand_csv_p = fam_dir / "candidate_metrics.csv"
        outcomes_csv_p = fam_dir / "engine_seed_outcomes.csv"
        sel_json_p = fam_dir / "selection.json"

        write_immutable_csv(cand_csv_p, df_cand, overwrite=True)
        write_immutable_csv(outcomes_csv_p, df_outcomes, overwrite=True)
        write_immutable_json(sel_json_p, sel_json, overwrite=True)

        print(f"  Target proposed MPIW: {sel_json['proposed_target_mpiw']:.4f} cycles")
        for c_id, c_data in sel_json["selected_controls"].items():
            param_str = f"{c_data['parameter_name']}={c_data['parameter_value']}"
            cost_str = f"cost={c_data['metrics']['mean_cost']:.4f} SCU"
            src_str = f"source={c_data['interval_source']}"
            print(f"  Selected {c_id:<25}: {param_str:<15} {src_str:<22} {cost_str}")
        print(f"  Saved artifacts to: {fam_dir}")

    print("\n" + "=" * 80)
    print("CONTROL SELECTION COMPLETE (STATUS: PASS - DEVELOPMENT ONLY)")
    print("=" * 80)


if __name__ == "__main__":
    main()
