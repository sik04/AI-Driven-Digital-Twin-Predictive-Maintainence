"""CLI interface to execute Phase 8 exploratory ablation and robustness evaluations.

Protocol: phase08-v1
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from intellitwin.provenance import write_immutable_json
from intellitwin.robustness.reporting import generate_phase08_reports_and_figures
from intellitwin.robustness.runner import execute_phase08_evaluation
from intellitwin.robustness.verification import independently_verify_phase08_evidence


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase 8 Exploratory Ablation and Robustness Runner"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="experiments/phase08_exploratory_v2",
        help="Directory to write Phase 8 evidence artifacts.",
    )
    parser.add_argument(
        "--report-dir",
        type=str,
        default="research/results/phase08_exploratory_v2",
        help="Directory to write synthesis reports and figures.",
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Repository root directory.",
    )
    parser.add_argument(
        "--raw-data-dir",
        type=str,
        default="data/raw/cmapss",
        help="Directory containing raw C-MAPSS text files.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting completed exploratory run.",
    )
    args = parser.parse_args()

    print("=" * 80)
    print("IntelliTwin: Phase 8 Exploratory Ablation & Robustness Analysis")
    print(f"Evidence Output Dir:    {args.output_dir}")
    print(f"Report Output Dir:      {args.report_dir}")
    print("=" * 80)

    try:
        res = execute_phase08_evaluation(
            output_dir=args.output_dir,
            base_dir=args.base_dir,
            raw_data_dir=args.raw_data_dir,
            overwrite=args.overwrite,
        )
        status = res.get("status")
        print(f"\nEvaluation status: {status}. Running independent reference verification audit...")
        ev_dir = Path(args.output_dir).resolve()
        audit_res = independently_verify_phase08_evidence(
            evidence_dir=ev_dir,
            base_dir=args.base_dir,
            raw_data_dir=args.raw_data_dir,
        )
        audit_path = ev_dir / "independent_audit.json"
        write_immutable_json(audit_path, audit_res, overwrite=args.overwrite)
        print(f"Independent audit status: {audit_res['overall_status']}")
        if audit_res["overall_status"] != "PASS":
            print(f"FATAL: Independent audit failed with reasons: {audit_res['failing_reasons']}")
            sys.exit(1)

        print("\nAudit passed! Generating verified reports and figures...")
        rep_res = generate_phase08_reports_and_figures(
            evidence_dir=args.output_dir,
            output_report_dir=args.report_dir,
            base_dir=args.base_dir,
        )
        print(f"Generated {len(rep_res['figures'])} figure files in {args.report_dir}/figures")
        print("Phase 8 execution and verification finished successfully.")
    except Exception as exc:
        print(f"\nFATAL ERROR: Phase 8 evaluation failed: {exc}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
