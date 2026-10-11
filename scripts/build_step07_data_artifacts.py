"""Deterministic builder for Step 7 C-MAPSS preprocessing artifacts.

Executes for datasets FD001, FD002, and FD004:
- Loads and validates raw run-to-failure trajectories.
- Validates frozen split manifests.
- Fits preprocessing strictly on training engines.
- Persists deterministic preprocessor JSON artifacts (with SHA-256 provenance).
- Transforms training and validation engines, constructing sequence windows.
- Computes equal-engine training sample weights and verifies mathematical invariants.
- Strictly excludes calibration and held-out test data from window construction.
"""

from pathlib import Path

from intellitwin.data.artifacts import (
    compute_sha256,
    save_preprocessor_artifact,
)
from intellitwin.data.loader import load_cmapss_run_to_failure
from intellitwin.data.preprocessing import fit_preprocessor
from intellitwin.data.schema import (
    EXPECTED_ENGINE_COUNTS,
    RAW_FILENAMES,
    SPLIT_MANIFEST_PATHS,
    SUPPORTED_DATASETS,
)
from intellitwin.data.splits import (
    load_split_manifest,
    select_partition,
    validate_split_manifest,
)
from intellitwin.data.windowing import (
    compute_equal_engine_sample_weights,
    construct_windows,
)


def build_dataset_artifacts(dataset_name: str, repo_root: Path) -> dict[str, str | int]:
    """Build and verify preprocessing artifact for a single dataset.

    Parameters
    ----------
    dataset_name : str
        "FD001", "FD002", or "FD004".
    repo_root : Path
        Repository root directory.

    Returns
    -------
    dict
        Summary metrics and artifact paths.
    """
    raw_rel = RAW_FILENAMES[dataset_name]
    manifest_rel = SPLIT_MANIFEST_PATHS[dataset_name]
    raw_path = repo_root / raw_rel
    manifest_path = repo_root / manifest_rel

    if not raw_path.is_file():
        raise FileNotFoundError(
            f"Raw C-MAPSS data file missing: {raw_path}. "
            "Cannot construct artifacts without raw source data."
        )

    expected_count = EXPECTED_ENGINE_COUNTS[dataset_name]
    raw_sha = compute_sha256(raw_path)
    manifest_sha = compute_sha256(manifest_path)

    # 1. Load and strictly validate raw data
    df_raw = load_cmapss_run_to_failure(
        path=raw_path,
        dataset_name=dataset_name,
        expected_engine_count=expected_count,
    )

    # 2. Load and validate frozen split manifest
    manifest = load_split_manifest(manifest_path)
    validate_split_manifest(
        manifest=manifest,
        expected_dataset=dataset_name,
        expected_engine_count=expected_count,
    )

    # 3. Training-only preprocessing fit
    df_train_raw = select_partition(df_raw, manifest, "train")
    preprocessor = fit_preprocessor(df_train=df_train_raw, dataset_name=dataset_name)

    # 4. Save preprocessor artifact to experiments/preprocessing/{dataset}/preprocessor.json
    out_rel = f"experiments/preprocessing/{dataset_name}/preprocessor.json"
    out_path = repo_root / out_rel
    artifact_sha = save_preprocessor_artifact(
        preprocessor=preprocessor,
        output_path=out_path,
        source_raw_path=raw_rel,
        source_raw_sha256=raw_sha,
        split_manifest_path=manifest_rel,
        split_manifest_sha256=manifest_sha,
    )

    # 5. Transform training data & construct windows
    df_train_trans = preprocessor.transform(df_train_raw)
    train_windows = construct_windows(df_train_trans)

    # 6. Compute equal-engine sample weights
    train_weights = compute_equal_engine_sample_weights(train_windows.engine_ids)

    # 7. Validation-only transform & construct windows
    df_val_raw = select_partition(df_raw, manifest, "validation")
    df_val_trans = preprocessor.transform(df_val_raw)
    val_windows = construct_windows(df_val_trans)

    # Integrity verification
    assert len(train_weights) == len(train_windows)
    assert train_windows.X_sequence.shape[1:] == (30, 17)
    assert val_windows.X_sequence.shape[1:] == (30, 17)

    return {
        "dataset": dataset_name,
        "raw_file": raw_rel,
        "raw_sha256": raw_sha,
        "manifest_file": manifest_rel,
        "manifest_sha256": manifest_sha,
        "train_engines": len(manifest.train),
        "validation_engines": len(manifest.validation),
        "train_windows": len(train_windows),
        "validation_windows": len(val_windows),
        "artifact_path": out_rel,
        "artifact_sha256": artifact_sha,
    }


def main() -> None:
    """Build artifacts for all Step 7 datasets."""
    repo_root = Path(__file__).resolve().parent.parent

    print("=" * 80)
    print("STEP 7.2 PREPROCESSING ARTIFACT BUILDER")
    print("=" * 80)

    results: list[dict[str, str | int]] = []
    for ds in SUPPORTED_DATASETS:
        print(f"\nProcessing {ds}...")
        res = build_dataset_artifacts(ds, repo_root)
        results.append(res)
        print(f"  Artifact: {res['artifact_path']}")
        print(f"  SHA-256:  {res['artifact_sha256']}")
        print(f"  Train:    {res['train_engines']} engines -> {res['train_windows']} windows")
        print(
            f"  Val:      {res['validation_engines']} engines -> "
            f"{res['validation_windows']} windows"
        )

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for res in results:
        print(
            f"{res['dataset']}: {res['artifact_path']} | SHA256: {res['artifact_sha256']} | "
            f"Train Windows: {res['train_windows']} | Val Windows: {res['validation_windows']}"
        )


if __name__ == "__main__":
    main()
