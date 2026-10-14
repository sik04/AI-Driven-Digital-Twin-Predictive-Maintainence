"""Step 9: Confirmatory Evaluation Validation-Only Smoke Run Script.

Protocol: step09-v1
Scope: End-to-end evaluation machinery test on validation partition engines only.
Strict Boundary:
- Evaluates strictly on validation engines (FD001: 10, FD002: 26, FD004: 25 engines).
- Executes 10,000 stratified engine-cluster bootstrap draws per dataset.
- Evaluates 3 datasets, both models, 5 seeds, 3 methods, 3 coverages, 3 scenarios,
  and all four FD002 controls.
- Strictly labels all outputs DEVELOPMENT_SMOKE_ONLY.
- Does NOT emit confirmatory RQ classifications.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from intellitwin.evaluation.runner import run_full_validation_smoke
from intellitwin.evaluation.schema import PROTOCOL_VERSION


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Step 9: Confirmatory Evaluation Validation Smoke Run (930 Configurations)"
    )
    parser.add_argument(
        "--controls-dir",
        type=str,
        default="experiments/pretest_verification_v2/controls",
        help="Directory containing verified FD002 controls",
    )
    parser.add_argument(
        "--step08-audit",
        type=str,
        default="experiments/pretest_verification_v2/step08_full_audit.json",
        help="Path to passing Step 8 full audit report",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="experiments/pretest_verification_v2/validation_smoke",
        help="Directory to write smoke run outputs",
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Repository root base directory",
    )
    parser.add_argument(
        "--n-bootstrap",
        type=int,
        default=10000,
        help="Number of stratified bootstrap replicates (default: 10000)",
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
    print("Step 9: Validation-Only Smoke Evaluation Run (DEVELOPMENT ONLY)")
    print(f"Protocol: {PROTOCOL_VERSION}")
    print(f"Controls Directory: {args.controls_dir}")
    print(f"Step 8 Audit Path: {args.step08_audit}")
    print(f"Output Directory: {out_base}")
    print(f"Bootstrap Replicates: {args.n_bootstrap}")
    print("=" * 80)

    try:
        manifest = run_full_validation_smoke(
            controls_dir=args.controls_dir,
            step08_audit_path=args.step08_audit,
            output_dir=out_base,
            base_dir=base,
            n_bootstrap=args.n_bootstrap,
            allow_dirty=args.allow_dirty,
        )
    except Exception as exc:
        print(f"\nERROR in validation smoke run: {exc}")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("VALIDATION SMOKE RUN COMPLETE (STATUS: PASS - DEVELOPMENT ONLY)")
    print(f"Total Configurations: {manifest['counts']['total_configurations']}")
    print(f"Total Outcome Rows: {manifest['counts']['total_outcome_rows']}")
    print(f"Total Summary Rows: {manifest['counts']['total_summary_rows']}")
    print(f"Bootstrap Replicates: {manifest['counts']['bootstrap_replicates']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
