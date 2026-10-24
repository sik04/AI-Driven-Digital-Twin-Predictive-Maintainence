"""Command-line interface to execute the frozen Step 9 confirmatory evaluation matrix.

Protocol: step09-v1
Scope: End-to-end evaluation across 930 configurations.
Partitions:
- validation: Pre-exposure verification and numerical equivalence mode.
- test: Held-out confirmatory evaluation mode (requires explicit --confirm-held-out).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from intellitwin.confirmatory.runner import run_confirmatory_evaluation
from intellitwin.evaluation.schema import PROTOCOL_VERSION


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Step 9 Confirmatory Evaluation CLI (930 Configurations)"
    )
    parser.add_argument(
        "--partition",
        type=str,
        required=True,
        choices=["validation", "test"],
        help=(
            "Evaluation partition ('validation' for smoke equivalence, "
            "'test' for official confirmatory)."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Destination directory for outputs. Must be empty or non-existent prior to run.",
    )
    parser.add_argument(
        "--pretest-dir",
        type=str,
        default="experiments/pretest_verification_v6",
        help="Directory containing verified pre-test readiness evidence bundle.",
    )
    parser.add_argument(
        "--raw-data-dir",
        type=str,
        default="data/raw/cmapss",
        help="Directory containing raw C-MAPSS training run-to-failure text files.",
    )
    parser.add_argument(
        "--controls-dir",
        type=str,
        default="experiments/pretest_verification_v2/controls",
        help="Directory containing verified FD002 benchmark control parameter selections.",
    )
    parser.add_argument(
        "--confirm-held-out",
        action="store_true",
        help="Mandatory gate authorizing official evaluation on held-out test data.",
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Repository root directory.",
    )
    parser.add_argument(
        "--n-bootstrap",
        type=int,
        default=10000,
        help="Number of stratified bootstrap replicates (default: 10000).",
    )
    parser.add_argument(
        "--use-validation-cache",
        action="store_true",
        default=True,
        help="Use existing point prediction caches when running in validation equivalence mode.",
    )
    parser.add_argument(
        "--no-validation-cache",
        dest="use_validation_cache",
        action="store_false",
        help="Force fresh prediction generation from checkpoints during validation mode.",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Permit execution on dirty git working tree (strictly forbidden for test partition).",
    )
    args = parser.parse_args()

    out_base = Path(args.output_dir).resolve()
    base = Path(args.base_dir).resolve()

    print("=" * 80)
    print("IntelliTwin: Confirmatory Evaluation Execution")
    print(f"Protocol:               {PROTOCOL_VERSION}")
    print(f"Partition:              {args.partition.upper()}")
    print(f"Output Directory:       {out_base}")
    print(f"Pre-Test Directory:     {args.pretest_dir}")
    print(f"Confirm Held-Out:       {args.confirm_held_out}")
    print(f"Bootstrap Replicates:   {args.n_bootstrap}")
    print("=" * 80)

    try:
        manifest = run_confirmatory_evaluation(
            partition=args.partition,
            output_dir=out_base,
            pretest_dir=args.pretest_dir,
            raw_data_dir=args.raw_data_dir,
            controls_dir=args.controls_dir,
            base_dir=base,
            n_bootstrap=args.n_bootstrap,
            confirm_held_out=args.confirm_held_out,
            use_validation_cache=args.use_validation_cache,
            allow_dirty=args.allow_dirty,
        )
    except Exception as exc:
        print(f"\nFATAL ERROR during confirmatory evaluation execution: {exc}")
        sys.exit(1)

    print("\n" + "=" * 80)
    print(f"CONFIRMATORY EVALUATION COMPLETED SUCCESSFULLY (STATUS: {manifest['status']})")
    print(f"Partition:              {manifest['partition']}")
    print(f"Total Configurations:   {manifest['counts']['total_configurations']}")
    print(f"Total Outcome Rows:     {manifest['counts']['total_outcome_rows']}")
    print(f"Total Summary Rows:     {manifest['counts']['total_summary_rows']}")
    print(f"Component Evidence:     {manifest['counts']['component_evidence_rows']}")
    print(f"Duration:               {manifest['duration_seconds']}s")
    if "rq_classifications" in manifest:
        print("Research Question Classifications:")
        for rq, st in manifest["rq_classifications"].items():
            print(f"  {rq}: {st}")
    print("=" * 80)


if __name__ == "__main__":
    main()
