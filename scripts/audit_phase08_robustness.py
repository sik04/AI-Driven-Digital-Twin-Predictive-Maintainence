"""CLI interface to execute independent reference verification audit for Phase 8.

Protocol: phase08-v1
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from intellitwin.provenance import write_immutable_json
from intellitwin.robustness.verification import independently_verify_phase08_evidence


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 8 Independent Reference Audit")
    parser.add_argument(
        "--evidence-dir",
        type=str,
        default="experiments/phase08_exploratory_v2",
        help="Directory containing Phase 8 evaluation artifacts to audit.",
    )
    parser.add_argument(
        "--output-audit",
        type=str,
        default=None,
        help="Output path for independent_audit.json.",
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
        help="Permit overwriting an existing independent audit file.",
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
    print("IntelliTwin: Phase 8 Independent Reference Verification Audit")
    print(f"Evidence Directory:     {ev_dir}")
    print(f"Output Audit Path:      {out_audit}")
    print("=" * 80)

    try:
        report = independently_verify_phase08_evidence(
            evidence_dir=ev_dir,
            base_dir=base,
            raw_data_dir=args.raw_data_dir,
        )
    except Exception as exc:
        print(f"\nFATAL AUDIT FAILURE: Exception encountered: {exc}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        failure_report = {
            "schema_version": "phase08-independent-audit-v3",
            "overall_status": "FAIL",
            "failing_reasons": [f"Audit execution exception: {type(exc).__name__}: {exc}"],
            "checks": {},
            "max_discrepancies": {"overall": None},
        }
        try:
            write_immutable_json(out_audit, failure_report, overwrite=args.overwrite)
            print(f"Wrote structured failure report to: {out_audit}", file=sys.stderr)
        except Exception:
            pass
        sys.exit(1)

    write_immutable_json(out_audit, report, overwrite=args.overwrite)
    print(f"\nSaved independent audit report to {out_audit}")
    print("=" * 80)
    print(f"AUDIT OUTCOME: {report.get('overall_status')}")
    if report.get("overall_status") != "PASS" or report.get("failing_reasons"):
        print("FAILING REASONS:")
        for r in report.get("failing_reasons", []):
            print(f"  - {r}")
        sys.exit(1)
    else:
        print("All reference checks passed with zero failing reasons.")


if __name__ == "__main__":
    main()
