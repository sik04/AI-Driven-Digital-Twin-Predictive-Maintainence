"""Command-line interface to execute independent reference verification of confirmatory evidence.

Protocol: step09-v1
Scope: Independent reconstruction of predictions, intervals, simulations, summaries,
bootstrap distributions, contrast intervals, and RQ1–RQ4 hypothesis decisions.
Fails closed on any inconsistency or omission.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from intellitwin.confirmatory.verification import independently_verify_confirmatory_evidence
from intellitwin.provenance import write_immutable_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Independent Reference Audit for Confirmatory Evaluation Evidence"
    )
    parser.add_argument(
        "--evidence-dir",
        type=str,
        default="experiments/confirmatory_v1",
        help="Directory containing confirmatory evaluation artifacts to independently audit.",
    )
    parser.add_argument(
        "--partition",
        type=str,
        default="test",
        choices=["validation", "test"],
        help="Partition under evaluation ('test' for official confirmatory run).",
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
        "--output-audit",
        type=str,
        default=None,
        help=(
            "Path to write independent_audit.json "
            "(defaults to <evidence_dir>/independent_audit.json)."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Permit overwriting an existing independent_audit.json artifact.",
    )
    args = parser.parse_args()

    ev_dir = Path(args.evidence_dir).resolve()
    base = Path(args.base_dir).resolve()
    out_audit = (
        Path(args.output_audit).resolve()
        if args.output_audit
        else (ev_dir / "independent_audit.json")
    )

    print("=" * 80)
    print("IntelliTwin: Independent Reference Verification Audit")
    print(f"Evidence Directory:     {ev_dir}")
    print(f"Partition:              {args.partition.upper()}")
    print(f"Output Audit Path:      {out_audit}")
    print("=" * 80)

    try:
        audit_report = independently_verify_confirmatory_evidence(
            evidence_dir=ev_dir,
            partition=args.partition,
            base_dir=base,
            raw_data_dir=args.raw_data_dir,
        )
    except Exception as exc:
        print(
            f"\nFATAL AUDIT FAILURE: Exception encountered during independent reconstruction: {exc}"
        )
        sys.exit(1)

    # Save audit report
    write_immutable_json(out_audit, audit_report, overwrite=args.overwrite)
    print(f"\nSaved independent audit report to {out_audit}")

    print("\n" + "=" * 80)
    print(f"AUDIT OUTCOME: {audit_report['overall_status']}")
    print("Research Question Classifications:")
    for rq, st in audit_report.get("rq_classifications", {}).items():
        print(f"  {rq}: {st}")

    failing = audit_report.get("failing_reasons", [])
    if failing:
        print("\nFailing Reasons Detected:")
        for r in failing:
            print(f"  - {r}")

    print("=" * 80)

    if audit_report["overall_status"] != "PASS":
        print("\nERROR: Independent reference audit failed verification gates!")
        sys.exit(1)


if __name__ == "__main__":
    main()
