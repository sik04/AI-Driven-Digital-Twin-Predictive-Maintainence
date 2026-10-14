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
import json
import sys
from pathlib import Path
from typing import Any

from intellitwin.data.artifacts import compute_sha256
from intellitwin.decision.controls import run_fd002_control_selection
from intellitwin.evaluation.schema import PRIMARY_COST_SCENARIO
from intellitwin.provenance import (
    capture_environment_metadata,
    get_git_info,
    write_immutable_csv,
    write_immutable_json,
)
from intellitwin.uncertainty.artifacts import resolve_repo_relative_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Step 9: Benchmark Matched-Conservatism Control Parameter Selection"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="experiments/pretest_verification_v2/controls",
        help="Base directory to store control selection artifacts",
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Repository root base directory",
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
    base = Path(args.base_dir).resolve()

    print("=" * 80)
    print("Step 9: Prespecified Benchmark Control Parameter Selection (FD002 Validation Only)")
    print(f"Cost scenario: {args.scenario_id}")
    print(f"Output directory: {out_base}")
    print("=" * 80)

    git_sha, git_dirty = get_git_info(allow_dirty=args.allow_dirty, repo_root=base)
    env_meta = capture_environment_metadata(device="cpu")

    reconstruction_results: dict[str, Any] = {
        "git_commit": git_sha,
        "git_dirty": git_dirty,
        "environment": env_meta,
        "scenario_id": args.scenario_id,
        "models": {},
        "overall_status": "PASS",
    }

    for fam in ("GBR", "LSTM"):
        print(f"\nSelecting controls for FD002 / {fam}...")
        try:
            df_cand, df_outcomes, sel_json = run_fd002_control_selection(
                model_family=fam,
                base_dir=base,
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

        # Refuse overwrite in official execution paths
        write_immutable_csv(cand_csv_p, df_cand, overwrite=False)
        write_immutable_csv(outcomes_csv_p, df_outcomes, overwrite=False)
        write_immutable_json(sel_json_p, sel_json, overwrite=False)

        # Check matched width readiness
        mw_ctrl = sel_json["selected_controls"]["matched_width_interval"]
        width_diff = float(mw_ctrl["width_diff"])
        matched_width_readiness = width_diff <= 1.0

        # Load historical selection for comparison
        hist_p = resolve_repo_relative_path(
            base, f"experiments/confirmatory_development/controls/FD002/{fam}/selection.json"
        )
        hist_sel: dict[str, Any] = {}
        if hist_p.exists():
            with open(hist_p, encoding="utf-8") as f:
                hist_sel = json.load(f).get("selected_controls", {})

        comp_dict: dict[str, Any] = {}
        for c_id, c_data in sel_json["selected_controls"].items():
            hist_c = hist_sel.get(c_id, {})
            param_name = c_data["parameter_name"]
            new_val = c_data["parameter_value"]
            old_val = hist_c.get("parameter_value")
            agrees = (new_val == old_val) and (
                c_data.get("interval_source") == hist_c.get("interval_source")
            )
            comp_dict[c_id] = {
                "parameter_name": param_name,
                "new_parameter_value": new_val,
                "historical_parameter_value": old_val,
                "new_source": c_data.get("interval_source"),
                "historical_source": hist_c.get("interval_source"),
                "agrees": agrees,
            }

        reconstruction_results["models"][fam] = {
            "target_mpiw": sel_json["proposed_target_mpiw"],
            "matched_width_diff": width_diff,
            "matched_width_readiness_pass": matched_width_readiness,
            "comparisons": comp_dict,
            "artifact_hashes": {
                "candidate_metrics_csv": compute_sha256(cand_csv_p),
                "engine_seed_outcomes_csv": compute_sha256(outcomes_csv_p),
                "selection_json": compute_sha256(sel_json_p),
            },
        }

        if not matched_width_readiness:
            reconstruction_results["overall_status"] = "FAIL"

        print(f"  Target proposed MPIW: {sel_json['proposed_target_mpiw']:.4f} cycles")
        for c_id, c_data in sel_json["selected_controls"].items():
            param_str = f"{c_data['parameter_name']}={c_data['parameter_value']}"
            cost_str = f"cost={c_data['metrics']['mean_cost']:.4f} SCU"
            src_str = f"source={c_data['interval_source']}"
            print(f"  Selected {c_id:<25}: {param_str:<15} {src_str:<22} {cost_str}")
        print(f"  Saved artifacts to: {fam_dir}")

    # Write control_reconstruction.json in parent directory of controls
    reconstruct_json_p = out_base.parent / "control_reconstruction.json"
    write_immutable_json(reconstruct_json_p, reconstruction_results, overwrite=False)
    print(f"\nSaved control reconstruction report to {reconstruct_json_p}")

    st = reconstruction_results["overall_status"]
    print(f"CONTROL SELECTION COMPLETE (STATUS: {st} - DEVELOPMENT ONLY)")
    print("=" * 80)

    if reconstruction_results["overall_status"] != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
