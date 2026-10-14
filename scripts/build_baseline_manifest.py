"""Rebuild preservation manifest from git at baseline f1edce7fdf48b45513ff90a680da49701451d9cb."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
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

ACTUAL_BASELINE_COMMIT = "f1edce7fdf48b45513ff90a680da49701451d9cb"
HISTORICAL_WRONG_COMMIT = "f1edce7858c9748b6ee92e7c4f4a3b7849e7b235"


def build_baseline_manifest(
    output_path: Path | str,
    base_dir: Path | str = ".",
    repo_root: Path | str | None = None,
    allow_dirty: bool = False,
) -> dict[str, Any]:
    """Rebuild baseline preservation manifest from Git blob tree at ACTUAL_BASELINE_COMMIT."""
    base = Path(base_dir).resolve()
    root = Path(repo_root).resolve() if repo_root is not None else Path(".").resolve()
    out_p = Path(output_path)
    if not out_p.is_absolute():
        out_p = (base / out_p).resolve()

    git_sha, git_dirty = get_git_info(allow_dirty=allow_dirty, repo_root=root)
    env_meta = capture_environment_metadata(device="cpu")

    # Read historical baseline to get historical inventory of 724 files
    hist_baseline_p = resolve_repo_relative_path(
        root, "experiments/audits/step08_repair_baseline.json"
    )
    with open(hist_baseline_p, encoding="utf-8") as f:
        hist_baseline = json.load(f)
    hist_artifacts: dict[str, dict[str, Any]] = hist_baseline.get("protected_artifacts", {})

    # Inspect git tree at ACTUAL_BASELINE_COMMIT
    cmd = ["git", "ls-tree", "-r", ACTUAL_BASELINE_COMMIT]
    tree_out = subprocess.check_output(cmd, cwd=str(root), text=True)
    git_blobs: dict[str, str] = {}
    for line in tree_out.strip().split("\n"):
        parts = line.strip().split(None, 3)
        if len(parts) == 4 and parts[1] == "blob":
            git_blobs[parts[3]] = parts[2]

    # Category A: Repository-tracked protected artifacts
    tracked_expected = sorted(set(hist_artifacts.keys()).intersection(set(git_blobs.keys())))

    # Fast batch compute sha256 for all tracked blobs using git cat-file --batch
    blob_ids_to_fetch = [git_blobs[p] for p in tracked_expected]
    proc = subprocess.Popen(
        ["git", "cat-file", "--batch"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        cwd=str(root),
    )
    stdin_data = "\n".join(blob_ids_to_fetch) + "\n"
    stdout_data, _ = proc.communicate(stdin_data.encode("ascii"))

    blob_hashes: dict[str, tuple[str, int]] = {}
    pos = 0
    for b_id in blob_ids_to_fetch:
        header_end = stdout_data.index(b"\n", pos)
        header = stdout_data[pos:header_end].decode("ascii")
        parts = header.split()
        size = int(parts[2])
        content_start = header_end + 1
        content = stdout_data[content_start : content_start + size]
        blob_hashes[b_id] = (hashlib.sha256(content).hexdigest(), size)
        pos = content_start + size + 1

    tracked_artifacts: dict[str, dict[str, Any]] = {}
    matched_count = 0
    missing_count = 0
    changed_count = 0

    for rel_path in tracked_expected:
        local_p = base / rel_path
        blob_id = git_blobs[rel_path]
        git_sha256, size_bytes = blob_hashes[blob_id]

        if not local_p.exists():
            missing_count += 1
            status = "MISSING"
            curr_sha256 = None
        else:
            with open(local_p, "rb") as f:
                local_bytes = f.read()
            curr_sha256 = hashlib.sha256(local_bytes).hexdigest()
            if curr_sha256 == git_sha256:
                matched_count += 1
                status = "MATCHED"
            else:
                changed_count += 1
                status = "CHANGED"

        tracked_artifacts[rel_path] = {
            "git_blob_id": blob_id,
            "git_sha256": git_sha256,
            "current_sha256": curr_sha256,
            "size_bytes": size_bytes,
            "verification_status": status,
        }

    # Category B: Historical local-only model-selection search checkpoints (not tracked in Git)
    local_only_keys = sorted(set(hist_artifacts.keys()) - set(git_blobs.keys()))
    local_only_checkpoints: dict[str, dict[str, Any]] = {}
    local_available_count = 0
    local_absent_count = 0

    for rel_path in local_only_keys:
        local_p = base / rel_path
        hist_entry = hist_artifacts[rel_path]
        expected_sha = hist_entry.get("sha256")
        local_size_bytes = hist_entry.get("size_bytes")

        if local_p.exists():
            local_available_count += 1
            curr_sha = compute_sha256(local_p)
            verified = curr_sha == expected_sha
            status = "AVAILABLE_LOCALLY_VERIFIED" if verified else "AVAILABLE_LOCALLY_CHANGED"
        else:
            local_absent_count += 1
            curr_sha = None
            status = "NOT_AVAILABLE_LOCAL_ONLY"

        local_only_checkpoints[rel_path] = {
            "historical_sha256": expected_sha,
            "current_sha256": curr_sha,
            "size_bytes": local_size_bytes,
            "tracked_in_git": False,
            "status": status,
        }

    # Registry portability migration verification
    orig_registry_blob = subprocess.check_output(
        [
            "git",
            "show",
            f"{ACTUAL_BASELINE_COMMIT}:experiments/calibration/calibration_registry.json",
        ],
        cwd=str(root),
    )
    orig_reg_sha256 = hashlib.sha256(orig_registry_blob).hexdigest()
    orig_reg_obj = json.loads(orig_registry_blob.decode("utf-8"))

    curr_reg_p = resolve_repo_relative_path(
        root, "experiments/calibration/calibration_registry.json"
    )
    with open(curr_reg_p, "rb") as f:
        curr_reg_bytes = f.read()
    curr_reg_sha256 = hashlib.sha256(curr_reg_bytes).hexdigest()
    curr_reg_obj = json.loads(curr_reg_bytes.decode("utf-8"))

    # Compare non-path fields and normalized paths
    diffs = []
    for k, v in orig_reg_obj["entries"].items():
        if k not in curr_reg_obj["entries"]:
            diffs.append(f"Missing entry {k}")
            continue
        c_v = curr_reg_obj["entries"][k]
        for field, val in v.items():
            if field == "calibrator_artifact_path":
                orig_norm = str(val).replace("\\\\", "/").replace("\\", "/")
                curr_norm = str(c_v[field]).replace("\\\\", "/").replace("\\", "/")
                if orig_norm != curr_norm:
                    diffs.append(f"Path mismatch {k}: {val} vs {c_v[field]}")
            else:
                if val != c_v.get(field):
                    diffs.append(f"Field mismatch {k}.{field}: {val} vs {c_v.get(field)}")

    reg_migration_pass = len(diffs) == 0

    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "schema_version": "step09-baseline-manifest-v2",
        "manifest_timestamp_utc": env_meta["timestamp_utc"],
        "baseline_commit": ACTUAL_BASELINE_COMMIT,
        "historical_wrong_commit_corrected": HISTORICAL_WRONG_COMMIT,
        "source_execution_commit": git_sha,
        "git_dirty": git_dirty,
        "environment": env_meta,
        "repository_tracked_protected_artifacts": {
            "expected": len(tracked_expected),
            "found": matched_count + changed_count,
            "matched": matched_count,
            "missing": missing_count,
            "changed": changed_count,
            "status": "PASS" if (missing_count == 0 and changed_count == 0) else "FAIL",
            "artifacts": tracked_artifacts,
        },
        "historical_local_only_model_selection_checkpoints": {
            "total_listed": len(local_only_keys),
            "available_locally": local_available_count,
            "absent_locally": local_absent_count,
            "notice": (
                "These 72 model-selection search checkpoints were exploratory local files "
                "never tracked in Git. They are not substitutes for the 30 mandatory "
                "production checkpoints."
            ),
            "artifacts": local_only_checkpoints,
        },
        "registry_portability_migration": {
            "original_sha256": orig_reg_sha256,
            "current_sha256": curr_reg_sha256,
            "entries_count": len(orig_reg_obj["entries"]),
            "non_path_fields_agree": reg_migration_pass,
            "entries_agreement_pass": reg_migration_pass,
            "differences_count": len(diffs),
            "migration_type": (
                "path-only portability migration "
                "(backslashes replaced with canonical forward slashes)"
            ),
        },
    }

    out_p.parent.mkdir(parents=True, exist_ok=True)
    write_immutable_json(out_p, manifest, overwrite=False)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild Git baseline preservation manifest")
    parser.add_argument(
        "--output-path",
        type=str,
        default="experiments/pretest_verification_v2/baseline_manifest.json",
        help="Path to write baseline_manifest.json",
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

    print("=" * 80)
    print("Rebuilding Preservation Manifest from Git Baseline")
    print(f"Target Baseline: {ACTUAL_BASELINE_COMMIT}")
    print(f"Output: {args.output_path}")
    print("=" * 80)

    res = build_baseline_manifest(
        output_path=args.output_path,
        base_dir=args.base_dir,
        allow_dirty=args.allow_dirty,
    )
    t = res["repository_tracked_protected_artifacts"]
    print(
        f"Tracked Artifacts: expected={t['expected']}, matched={t['matched']}, "
        f"missing={t['missing']}, changed={t['changed']}"
    )
    print(f"Tracked Status: {t['status']}")
    print(f"Registry Migration: {res['registry_portability_migration']['entries_agreement_pass']}")


if __name__ == "__main__":
    main()
