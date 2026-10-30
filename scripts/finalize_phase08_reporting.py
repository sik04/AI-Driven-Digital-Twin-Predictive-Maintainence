"""Finalize Phase 8 scientific reporting, publication figures, and final receipt.

Protocol: phase08-v1
Binds reporting strictly to an audited, passing Phase 8 evidence bundle.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import intellitwin.robustness.verification as verif_mod
from intellitwin.data.artifacts import compute_sha256
from intellitwin.provenance import write_immutable_json
from intellitwin.robustness.reporting import (
    generate_phase08_reports_and_figures,
    resolve_repo_path,
    to_repo_relative_posix,
)


def finalize_phase08_reporting(
    evidence_dir: Path | str,
    output_report_dir: Path | str,
    audit_path: Path | str | None = None,
    base_dir: Path | str = ".",
    overwrite: bool = False,
) -> Path:
    """Execute reporting and generate the non-circular final receipt.

    Raises:
        FileExistsError: If output_report_dir contains completed reports and overwrite is False.
        RuntimeError: If independent audit did not pass or manifest hashes mismatch.
        ValueError: If evidence, report, or audit paths are outside base_dir.
    """
    base = Path(base_dir).resolve()
    ev_dir = resolve_repo_path(evidence_dir, base)
    rep_dir = resolve_repo_path(output_report_dir, base)
    audit_p = (
        resolve_repo_path(audit_path, base)
        if audit_path is not None
        else (ev_dir / "independent_audit.json")
    )

    # Validate repository containment before writing any files
    _ = to_repo_relative_posix(ev_dir, base)
    _ = to_repo_relative_posix(rep_dir, base)
    _ = to_repo_relative_posix(audit_p, base)

    if rep_dir.exists() and not overwrite:
        # Check if already contains completed reports
        key_files = ["results_summary.md", "writing_handoff.md", "final_receipt.json"]
        if any((rep_dir / f).exists() for f in key_files):
            raise FileExistsError(
                f"Report directory '{rep_dir}' already exists and contains completed reports. "
                "Use --overwrite to permit overwriting."
            )

    rep_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("IntelliTwin: Finalize Phase 8 Scientific Reporting")
    print(f"Evidence Directory: {ev_dir}")
    print(f"Audit Path:         {audit_p}")
    print(f"Report Directory:    {rep_dir}")
    print("=" * 80)

    # 1. Generate reports, tables, figures, and writing handoff
    results = generate_phase08_reports_and_figures(
        evidence_dir=ev_dir,
        output_report_dir=rep_dir,
        audit_path=audit_p,
        base_dir=base,
    )
    print(f"Successfully generated scientific synthesis at: {results['results_summary']}")
    print(f"Successfully generated writing handoff at:      {results['writing_handoff']}")

    # Copy independent_audit.json into rep_dir if not already there (binary byte-for-byte)
    dest_audit = rep_dir / "independent_audit.json"
    if audit_p != dest_audit:
        shutil.copyfile(audit_p, dest_audit)

    # 2. Build non-circular final receipt
    man_p = ev_dir / "execution_manifest.json"
    ev_manifest_sha = compute_sha256(man_p) if man_p.exists() else ""
    audit_sha = compute_sha256(audit_p)
    verifier_sha = compute_sha256(Path(verif_mod.__file__))

    # Hash all generated report artifacts, excluding final_receipt.json itself
    report_hashes: dict[str, str] = {}
    for fpath in sorted(rep_dir.rglob("*")):
        if fpath.is_file() and fpath.name != "final_receipt.json":
            rel_name = fpath.relative_to(rep_dir).as_posix()
            report_hashes[rel_name] = compute_sha256(fpath)

    receipt = {
        "protocol_version": "phase08-v1",
        "execution_manifest_sha256": ev_manifest_sha,
        "independent_audit_sha256": audit_sha,
        "verifier_source_sha256": verifier_sha,
        "report_artifact_hashes": report_hashes,
    }

    receipt_p = rep_dir / "final_receipt.json"
    write_immutable_json(receipt_p, receipt, overwrite=overwrite)
    print(f"Successfully wrote final receipt to:             {receipt_p}")
    print("=" * 80)
    return receipt_p


def main() -> None:
    parser = argparse.ArgumentParser(description="Finalize Phase 8 Reporting & Synthesis")
    parser.add_argument(
        "--evidence-dir",
        type=str,
        required=True,
        help="Directory containing verified Phase 8 evidence.",
    )
    parser.add_argument(
        "--audit-path",
        type=str,
        default=None,
        help="Path to passing independent_audit.json.",
    )
    parser.add_argument(
        "--report-dir",
        type=str,
        required=True,
        help="Destination directory for finalized reports and figures.",
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Repository root directory.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Permit overwriting an existing report directory.",
    )
    args = parser.parse_args()

    try:
        finalize_phase08_reporting(
            evidence_dir=args.evidence_dir,
            output_report_dir=args.report_dir,
            audit_path=args.audit_path,
            base_dir=args.base_dir,
            overwrite=args.overwrite,
        )
    except Exception as exc:
        print(f"\nFATAL REPORTING FAILURE: {exc}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
