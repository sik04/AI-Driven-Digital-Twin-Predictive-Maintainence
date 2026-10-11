"""Canonical schema, column constants, and dataset metadata for C-MAPSS data pipelines.

This module defines the immutable column layout, predictive feature order,
lifecycle stage definitions, and Step 7 benchmark dataset specifications.
"""

from typing import Final

# ---------------------------------------------------------------------------
# Canonical Raw Column Layout (26 columns)
# ---------------------------------------------------------------------------
RAW_COLUMNS: Final[tuple[str, ...]] = (
    "unit",
    "cycle",
    "setting1",
    "setting2",
    "setting3",
    "s1",
    "s2",
    "s3",
    "s4",
    "s5",
    "s6",
    "s7",
    "s8",
    "s9",
    "s10",
    "s11",
    "s12",
    "s13",
    "s14",
    "s15",
    "s16",
    "s17",
    "s18",
    "s19",
    "s20",
    "s21",
)

# ---------------------------------------------------------------------------
# Operational Setting Columns (3 features)
# ---------------------------------------------------------------------------
SETTING_COLUMNS: Final[tuple[str, ...]] = (
    "setting1",
    "setting2",
    "setting3",
)

# ---------------------------------------------------------------------------
# Frozen Retained Degradation Sensor Columns (14 features)
# Constant/uninformative sensors (s1, s5, s6, s10, s16, s18, s19) are dropped.
# ---------------------------------------------------------------------------
SENSOR_COLUMNS: Final[tuple[str, ...]] = (
    "s2",
    "s3",
    "s4",
    "s7",
    "s8",
    "s9",
    "s11",
    "s12",
    "s13",
    "s14",
    "s15",
    "s17",
    "s20",
    "s21",
)

# ---------------------------------------------------------------------------
# Canonical Predictive Feature Vector (17 features)
# Exact order: 3 operational settings followed by 14 retained sensors.
# ---------------------------------------------------------------------------
FEATURE_COLUMNS: Final[tuple[str, ...]] = (
    "setting1",
    "setting2",
    "setting3",
    "s2",
    "s3",
    "s4",
    "s7",
    "s8",
    "s9",
    "s11",
    "s12",
    "s13",
    "s14",
    "s15",
    "s17",
    "s20",
    "s21",
)

# Structural assertions
assert len(SETTING_COLUMNS) == 3, f"Expected 3 settings, got {len(SETTING_COLUMNS)}"
assert len(SENSOR_COLUMNS) == 14, f"Expected 14 sensors, got {len(SENSOR_COLUMNS)}"
assert len(FEATURE_COLUMNS) == 17, f"Expected 17 features, got {len(FEATURE_COLUMNS)}"
assert "unit" not in FEATURE_COLUMNS, "unit must never be in FEATURE_COLUMNS"
assert "cycle" not in FEATURE_COLUMNS, "cycle must never be in FEATURE_COLUMNS"

# ---------------------------------------------------------------------------
# Step 7 Benchmark Dataset Specifications
# ---------------------------------------------------------------------------
SUPPORTED_DATASETS: Final[tuple[str, ...]] = ("FD001", "FD002", "FD004")

EXPECTED_ENGINE_COUNTS: Final[dict[str, int]] = {
    "FD001": 100,
    "FD002": 260,
    "FD004": 249,
}

RAW_FILENAMES: Final[dict[str, str]] = {
    "FD001": "data/raw/cmapss/train_FD001.txt",
    "FD002": "data/raw/cmapss/train_FD002.txt",
    "FD004": "data/raw/cmapss/train_FD004.txt",
}

SPLIT_MANIFEST_PATHS: Final[dict[str, str]] = {
    "FD001": "data/splits/fd001_engine_split_seed_2026.json",
    "FD002": "data/splits/fd002_engine_split_seed_2026.json",
    "FD004": "data/splits/fd004_engine_split_seed_2026.json",
}

FROZEN_PARTITION_COUNTS: Final[dict[str, dict[str, int]]] = {
    "FD001": {"train": 50, "calibration": 20, "validation": 10, "test": 20},
    "FD002": {"train": 130, "calibration": 52, "validation": 26, "test": 52},
    "FD004": {"train": 124, "calibration": 50, "validation": 25, "test": 50},
}

# ---------------------------------------------------------------------------
# Sequence Windowing and Label Constants
# ---------------------------------------------------------------------------
LOOKBACK: Final[int] = 30
STRIDE: Final[int] = 1
FLATTENED_FEATURE_DIM: Final[int] = 510  # 30 * 17
RUL_CAP: Final[int] = 125

# ---------------------------------------------------------------------------
# Retrospective Lifecycle Stages
# ---------------------------------------------------------------------------
EARLY_STAGE: Final[str] = "early"
MID_STAGE: Final[str] = "mid"
LATE_STAGE: Final[str] = "late"
LIFECYCLE_STAGES: Final[tuple[str, ...]] = (EARLY_STAGE, MID_STAGE, LATE_STAGE)


def get_lifecycle_stage(cycle: int, failure_cycle: int) -> str:
    """Compute retrospective lifecycle stage for an endpoint cycle t.

    Parameters
    ----------
    cycle : int
        Endpoint cycle t (1 <= cycle <= failure_cycle).
    failure_cycle : int
        Terminal failure cycle T.

    Returns
    -------
    str
        "early" if 3*t <= T,
        "mid" if T < 3*t <= 2*T,
        "late" if 2*T < 3*t <= 3*T.
    """
    if cycle <= 0 or failure_cycle <= 0:
        raise ValueError(
            f"cycle ({cycle}) and failure_cycle ({failure_cycle}) must be positive integers."
        )
    if cycle > failure_cycle:
        raise ValueError(f"cycle ({cycle}) exceeds failure_cycle ({failure_cycle}).")

    if 3 * cycle <= failure_cycle:
        return EARLY_STAGE
    if 3 * cycle <= 2 * failure_cycle:
        return MID_STAGE
    return LATE_STAGE
