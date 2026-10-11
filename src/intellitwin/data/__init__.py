"""IntelliTwin C-MAPSS data loading, preprocessing, and windowing package.

Provides deterministic data pipelines conforming strictly to Step 5, Step 6,
and Step 7 protocol freezes.
"""

from intellitwin.data.artifacts import (
    compute_sha256,
    load_preprocessor_artifact,
    save_preprocessor_artifact,
)
from intellitwin.data.loader import load_cmapss_run_to_failure
from intellitwin.data.pipeline import (
    PreparedDataset,
    prepare_dataset_for_model_development,
)
from intellitwin.data.preprocessing import (
    FittedPreprocessor,
    ScalerParams,
    fit_preprocessor,
)
from intellitwin.data.schema import (
    EARLY_STAGE,
    EXPECTED_ENGINE_COUNTS,
    FEATURE_COLUMNS,
    FLATTENED_FEATURE_DIM,
    FROZEN_PARTITION_COUNTS,
    LATE_STAGE,
    LIFECYCLE_STAGES,
    LOOKBACK,
    MID_STAGE,
    RAW_COLUMNS,
    RAW_FILENAMES,
    RUL_CAP,
    SENSOR_COLUMNS,
    SETTING_COLUMNS,
    SPLIT_MANIFEST_PATHS,
    STRIDE,
    SUPPORTED_DATASETS,
    get_lifecycle_stage,
)
from intellitwin.data.splits import (
    SplitManifest,
    load_split_manifest,
    select_partition,
    validate_split_manifest,
)
from intellitwin.data.windowing import (
    WindowDataset,
    compute_equal_engine_sample_weights,
    construct_windows,
)

__all__ = [
    # Schema & constants
    "RAW_COLUMNS",
    "SETTING_COLUMNS",
    "SENSOR_COLUMNS",
    "FEATURE_COLUMNS",
    "SUPPORTED_DATASETS",
    "EXPECTED_ENGINE_COUNTS",
    "RAW_FILENAMES",
    "SPLIT_MANIFEST_PATHS",
    "FROZEN_PARTITION_COUNTS",
    "LOOKBACK",
    "STRIDE",
    "FLATTENED_FEATURE_DIM",
    "RUL_CAP",
    "EARLY_STAGE",
    "MID_STAGE",
    "LATE_STAGE",
    "LIFECYCLE_STAGES",
    "get_lifecycle_stage",
    # Loader
    "load_cmapss_run_to_failure",
    # Splits
    "SplitManifest",
    "load_split_manifest",
    "validate_split_manifest",
    "select_partition",
    # Preprocessing
    "ScalerParams",
    "FittedPreprocessor",
    "fit_preprocessor",
    # Windowing & Weights
    "WindowDataset",
    "construct_windows",
    "compute_equal_engine_sample_weights",
    # Artifacts
    "compute_sha256",
    "save_preprocessor_artifact",
    "load_preprocessor_artifact",
    # Pipeline
    "PreparedDataset",
    "prepare_dataset_for_model_development",
]
