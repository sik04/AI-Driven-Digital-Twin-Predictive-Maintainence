"""Execution provenance, environment tracking, and artifact immutability."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sklearn
import torch
import yaml

from intellitwin.data.artifacts import compute_sha256


def get_git_info(
    allow_dirty: bool = False,
    repo_root: Path | str = ".",
    ignored_paths: Sequence[str] | None = None,
) -> tuple[str, bool]:
    """Retrieve git HEAD commit SHA and porcelain dirty status.

    Parameters
    ----------
    allow_dirty : bool
        If False, raises RuntimeError when working tree is dirty or Git is unavailable.
    repo_root : Path or str
        Repository root directory where Git commands are executed.
    ignored_paths : Sequence[str], optional
        Deprecated. Never masks dirty status for official executions.

    Returns
    -------
    tuple[str, bool]
        (git_commit_sha, git_dirty)
    """
    root = Path(repo_root).resolve()
    try:
        sha_proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        sha = sha_proc.stdout.strip()
        if not sha:
            raise RuntimeError("git rev-parse HEAD returned empty output")

        status_proc = subprocess.run(
            ["git", "status", "--porcelain=v1", "-uall"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        status_lines = [line.strip() for line in status_proc.stdout.splitlines() if line.strip()]
        dirty = len(status_lines) > 0
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise RuntimeError(f"Git inspection failed: {exc}") from exc

    if dirty and not allow_dirty:
        dirty_summary = "\n".join(status_lines)
        raise RuntimeError(
            f"Official execution refused on dirty working tree:\n{dirty_summary}\n"
            "Working tree must be clean before running official tasks."
        )

    return sha, dirty


def capture_environment_metadata(
    device: str | None = None,
    command_args: list[str] | None = None,
) -> dict[str, Any]:
    """Capture runtime environment versions, platform, and UTC timestamp.

    Parameters
    ----------
    device : str, optional
        Actual device used for execution ("cpu" or "cuda"). If None, defaults
        strictly to "cpu" unless explicitly overridden.
    command_args : list[str], optional
        Command arguments executed.
    """
    actual_device = device if device is not None else "cpu"
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "device": actual_device,
        "packages": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "torch": torch.__version__,
            "pyyaml": yaml.__version__,
        },
        "command_args": list(sys.argv) if command_args is None else command_args,
    }


def compute_file_hashes(
    file_paths: Sequence[Path | str],
    base_dir: Path | str = ".",
) -> dict[str, str]:
    """Compute SHA-256 for a sequence of files, returned as relative POSIX paths."""
    base = Path(base_dir).resolve()
    hashes: dict[str, str] = {}
    for fp in file_paths:
        p = Path(fp)
        resolved_p = (base / p).resolve() if not p.is_absolute() else p.resolve()
        if not resolved_p.is_file():
            raise FileNotFoundError(f"File not found for hash calculation: {resolved_p}")
        try:
            rel = resolved_p.relative_to(base).as_posix()
        except ValueError:
            rel = resolved_p.as_posix()
        hashes[rel] = compute_sha256(resolved_p)
    return dict(sorted(hashes.items()))


def write_immutable_json(
    target_path: Path | str,
    data: dict[str, Any],
    overwrite: bool = False,
) -> None:
    """Write JSON atomically and enforce immutability against conflicting content.

    If target file already exists and has identical serialized content, operation succeeds.
    If target file exists with conflicting content and overwrite is False, raises RuntimeError.
    """
    p = Path(target_path)
    new_text = json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n"

    if p.exists() and not overwrite:
        existing_text = p.read_text(encoding="utf-8")
        if existing_text == new_text:
            return  # Identical deterministic content
        raise RuntimeError(
            f"Refusing to overwrite existing immutable artifact with conflicting content: {p}"
        )

    p.parent.mkdir(parents=True, exist_ok=True)
    temp_p = p.with_suffix(f"{p.suffix}.tmp_{os.getpid()}")
    temp_p.write_text(new_text, encoding="utf-8", newline="\n")
    temp_p.replace(p)


def write_immutable_csv(
    target_path: Path | str,
    df: pd.DataFrame,
    overwrite: bool = False,
) -> None:
    """Write CSV atomically and enforce immutability against conflicting content.

    If target file already exists and has identical content, operation succeeds.
    If target file exists with conflicting content and overwrite is False, raises RuntimeError.
    """
    p = Path(target_path)
    new_csv = df.to_csv(index=False, encoding="utf-8", lineterminator="\n", float_format="%.17g")

    if p.exists() and not overwrite:
        existing_csv = p.read_text(encoding="utf-8")
        if existing_csv == new_csv:
            return  # Identical deterministic content
        raise RuntimeError(
            f"Refusing to overwrite existing immutable artifact with conflicting content: {p}"
        )

    p.parent.mkdir(parents=True, exist_ok=True)
    temp_p = p.with_suffix(f"{p.suffix}.tmp_{os.getpid()}")
    temp_p.write_text(new_csv, encoding="utf-8", newline="\n")
    temp_p.replace(p)


def write_immutable_npz(
    target_path: Path | str,
    arrays: dict[str, np.ndarray[Any, Any]],
    metadata: dict[str, Any] | None = None,
    overwrite: bool = False,
) -> str:
    """Write NPZ archive atomically and enforce immutability against conflicting content.

    Semantic equivalence check:
    - Compares arrays by shape, dtype, and exact array equality.
    - Compares metadata by deserialized JSON equality.
    - Ignores ZIP-container internal timestamps.

    Returns the SHA-256 hash of the final written or verified file.
    """
    p = Path(target_path)
    save_dict: dict[str, Any] = dict(arrays)
    if metadata is not None:
        save_dict["__metadata__"] = np.array([json.dumps(metadata, sort_keys=True)])

    p.parent.mkdir(parents=True, exist_ok=True)
    temp_p = p.with_suffix(f"{p.suffix}.tmp_{os.getpid()}.npz")

    try:
        np.savez_compressed(temp_p, **save_dict)

        if p.exists() and not overwrite:
            # Compare existing vs new semantically
            with np.load(p, allow_pickle=False) as existing_npz:
                existing_keys = set(existing_npz.files)
                new_keys = set(save_dict.keys())
                if existing_keys != new_keys:
                    raise RuntimeError(
                        f"Refusing to overwrite NPZ {p}: key mismatch {existing_keys} vs {new_keys}"
                    )
                for k in new_keys:
                    ex_arr = existing_npz[k]
                    nw_arr = save_dict[k]
                    if ex_arr.shape != nw_arr.shape or ex_arr.dtype != nw_arr.dtype:
                        raise RuntimeError(
                            f"Refusing to overwrite NPZ {p}: array '{k}' shape/dtype mismatch "
                            f"{ex_arr.shape}/{ex_arr.dtype} vs {nw_arr.shape}/{nw_arr.dtype}"
                        )
                    if not np.array_equal(ex_arr, nw_arr):
                        raise RuntimeError(
                            f"Refusing to overwrite NPZ {p}: array '{k}' numerical content mismatch"
                        )
            # Identical semantic content: discard temp file and keep existing
            temp_p.unlink(missing_ok=True)
            return compute_sha256(p)

        temp_p.replace(p)
        return compute_sha256(p)
    finally:
        if temp_p.exists():
            temp_p.unlink(missing_ok=True)
