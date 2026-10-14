"""Generate supersession.json documenting historical records superseded for readiness purposes."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from intellitwin.data.artifacts import compute_sha256
from intellitwin.evaluation.schema import PROTOCOL_VERSION
from intellitwin.provenance import (
    capture_environment_metadata,
    get_git_info,
    write_immutable_json,
)
from intellitwin.uncertainty.artifacts import resolve_repo_relative_path


def build_supersession_manifest(
    output_path: Path | str = "experiments/pretest_verification_v2/supersession.json",
    base_dir: Path | str = ".",
    allow_dirty: bool = False,
) -> dict[str, Any]:
    """Generate supersession.json documenting superseded records."""
    base = Path(base_dir).resolve()
    out_p = Path(output_path)
    if not out_p.is_absolute():
        out_p = (base / out_p).resolve()

    git_sha, git_dirty = get_git_info(allow_dirty=allow_dirty, repo_root=base)
    env_meta = capture_environment_metadata(device="cpu")

    superseded_records = [
        {
            "historical_path": "experiments/audits/step08_repair_baseline.json",
            "historical_sha256": compute_sha256(
                resolve_repo_relative_path(base, "experiments/audits/step08_repair_baseline.json")
            ),
            "reason_superseded": (
                "Recorded incorrect historical baseline commit SHA "
                "(f1edce7858c9748b6ee92e7c4f4a3b7849e7b235 instead of actual "
                "f1edce7fdf48b45513ff90a680da49701451d9cb), and conflated git-tracked "
                "protected artifacts with 72 local-only untracked model selection checkpoints "
                "without distinguishing public repository availability."
            ),
            "replacement_evidence_path": (
                "experiments/pretest_verification_v2/baseline_manifest.json"
            ),
        },
        {
            "historical_path": "experiments/audits/step08_repair_verification.json",
            "historical_sha256": compute_sha256(
                resolve_repo_relative_path(
                    base, "experiments/audits/step08_repair_verification.json"
                )
            ),
            "reason_superseded": (
                "Recorded checkpoint_prediction_reproduction = NOT RUN while claiming "
                "overall_status = PASS. Full Step 8 verification requires official execution "
                "of raw checkpoint prediction CPU reproduction across 60 model/partition checks "
                "with absolute error <= 1e-4."
            ),
            "replacement_evidence_path": (
                "experiments/pretest_verification_v2/step08_full_audit.json"
            ),
        },
        {
            "historical_path": (
                "experiments/confirmatory_development/controls/FD002/GBR/selection.json"
            ),
            "historical_sha256": compute_sha256(
                resolve_repo_relative_path(
                    base, "experiments/confirmatory_development/controls/FD002/GBR/selection.json"
                )
            ),
            "reason_superseded": (
                "Executed with --allow-dirty (recording git_dirty=true) and used rounded "
                "tolerance buckets rather than the locked minimum-relative tie-breaking rule "
                "(<= minimum + 1e-8)."
            ),
            "replacement_evidence_path": (
                "experiments/pretest_verification_v2/controls/FD002/GBR/selection.json"
            ),
        },
        {
            "historical_path": (
                "experiments/confirmatory_development/controls/FD002/LSTM/selection.json"
            ),
            "historical_sha256": compute_sha256(
                resolve_repo_relative_path(
                    base, "experiments/confirmatory_development/controls/FD002/LSTM/selection.json"
                )
            ),
            "reason_superseded": (
                "Executed with --allow-dirty (recording git_dirty=true) and used rounded "
                "tolerance buckets rather than the locked minimum-relative tie-breaking rule "
                "(<= minimum + 1e-8)."
            ),
            "replacement_evidence_path": (
                "experiments/pretest_verification_v2/controls/FD002/LSTM/selection.json"
            ),
        },
        {
            "historical_path": (
                "experiments/confirmatory_development/validation_smoke/execution_manifest.json"
            ),
            "historical_sha256": compute_sha256(
                resolve_repo_relative_path(
                    base,
                    "experiments/confirmatory_development/validation_smoke/execution_manifest.json",
                )
            ),
            "reason_superseded": (
                "Executed with --allow-dirty (recording git_dirty=true), evaluated only 810 "
                "primary configurations without evaluating the 120 control configurations, "
                "generated bootstrap draws without applying them to calculate replicate statistics "
                "or confidence intervals, and omitted point predictions, interval predictions, "
                "and decision traces."
            ),
            "replacement_evidence_path": (
                "experiments/pretest_verification_v2/validation_smoke/execution_manifest.json"
            ),
        },
        {
            "historical_path": "experiments/confirmatory_development/protocol_freeze.json",
            "historical_sha256": compute_sha256(
                resolve_repo_relative_path(
                    base, "experiments/confirmatory_development/protocol_freeze.json"
                )
            ),
            "reason_superseded": (
                "Bound superseded Step 8 and smoke artifacts, excluded audit files from "
                "dirty-state checks, and assembled the freeze before content-level evidence "
                "verification."
            ),
            "replacement_evidence_path": (
                "experiments/pretest_verification_v2/protocol_freeze.json"
            ),
        },
        {
            "historical_path": "experiments/confirmatory_development/pretest_audit.json",
            "historical_sha256": compute_sha256(
                resolve_repo_relative_path(
                    base, "experiments/confirmatory_development/pretest_audit.json"
                )
            ),
            "reason_superseded": (
                "Shallow file-presence check that did not verify configuration matrix counts, "
                "outcome rows, trace simulations, replicate arrays, or confidence interval "
                "reconstructions."
            ),
            "replacement_evidence_path": "experiments/pretest_verification_v2/pretest_audit.json",
        },
    ]

    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "schema_version": "step09-supersession-v1",
        "timestamp_utc": env_meta["timestamp_utc"],
        "source_execution_commit": git_sha,
        "git_dirty": git_dirty,
        "environment": env_meta,
        "superseded_count": len(superseded_records),
        "superseded_records": superseded_records,
    }

    out_p.parent.mkdir(parents=True, exist_ok=True)
    write_immutable_json(out_p, manifest, overwrite=False)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate supersession.json")
    parser.add_argument(
        "--output-path",
        type=str,
        default="experiments/pretest_verification_v2/supersession.json",
        help="Path to write supersession.json",
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Repository root base directory",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Permit execution on dirty working tree",
    )
    args = parser.parse_args()

    res = build_supersession_manifest(
        output_path=args.output_path,
        base_dir=args.base_dir,
        allow_dirty=args.allow_dirty,
    )
    print(
        f"PASS: Generated supersession manifest with {res['superseded_count']} superseded records."
    )


if __name__ == "__main__":
    main()
