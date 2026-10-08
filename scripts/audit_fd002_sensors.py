"""Reproducible script for FD002 training-only sensor diagnostic.

This script loads train_FD002.txt, filters to the 130 training engines defined in
data/splits/fd002_engine_split_seed_2026.json, and computes overall, regime-wise
(std and range), and temporal correlation diagnostics for sensors s1 through s21.

No non-training engines are inspected, no data is downloaded automatically,
and no final feature selection decisions are locked by this script.
"""

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Define repository paths
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "data" / "raw" / "cmapss" / "train_FD002.txt"
SPLIT_MANIFEST_PATH = REPO_ROOT / "data" / "splits" / "fd002_engine_split_seed_2026.json"
OUTPUT_CSV_PATH = (
    REPO_ROOT / "research" / "research_design" / "fd002_training_sensor_diagnostic.csv"
)

# Standard C-MAPSS column names
COLUMNS = [
    "unit",
    "cycle",
    "setting1",
    "setting2",
    "setting3",
] + [f"s{i}" for i in range(1, 22)]

# Diagnostic classification threshold (DESCRIPTIVE ONLY)
# NOTE: This threshold is used ONLY for descriptive labeling in this exploratory diagnostic.
# It is NOT a locked research decision and NOT a feature-selection threshold.
# The final sensor inclusion/exclusion decision will be made separately in Step 5.2B.
# Changing this descriptive label threshold does NOT redefine the underlying raw statistics.
DIAGNOSTIC_NEAR_CONSTANT_STD_THRESHOLD = 0.01


def run_sensor_diagnostic() -> pd.DataFrame:
    """Execute training-only sensor diagnostic for FD002."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Missing required raw data file at '{DATA_PATH}'. "
            "Data must be placed locally in data/raw/cmapss/"
        )

    if not SPLIT_MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"Missing required engine split manifest at '{SPLIT_MANIFEST_PATH}'."
        )

    # 1. Load split manifest and get training engines
    with open(SPLIT_MANIFEST_PATH, encoding="utf-8") as f:
        split_data = json.load(f)

    train_engines = set(split_data["partitions"]["train"])
    assert len(train_engines) == 130, f"Expected 130 training engines, found {len(train_engines)}"

    # 2. Load C-MAPSS raw FD002 file (space-separated, no header)
    df_raw = pd.read_csv(DATA_PATH, sep=r"\s+", header=None, names=COLUMNS, engine="python")

    # 3. Filter to training engines ONLY
    df_train = df_raw[df_raw["unit"].isin(train_engines)].copy()
    unique_train_units = set(df_train["unit"].unique())
    assert unique_train_units == train_engines, "Training dataframe engine set mismatch"

    # Verify no leakage from calibration, validation, or test engines
    calib_engines = set(split_data["partitions"]["calibration"])
    val_engines = set(split_data["partitions"]["validation"])
    test_engines = set(split_data["partitions"]["test"])
    non_train_engines = calib_engines | val_engines | test_engines

    assert len(unique_train_units & non_train_engines) == 0, (
        "Non-training engines leaked into training dataframe!"
    )

    n_rows = len(df_train)
    print(f"Verified training engines count: {len(unique_train_units)}")
    print(f"Total training rows loaded: {n_rows}")

    # 4. Operating Setting Scaling & K-Means (k=6) fit on training settings ONLY
    setting_cols = ["setting1", "setting2", "setting3"]
    scaler = StandardScaler()
    scaled_settings = scaler.fit_transform(df_train[setting_cols])

    kmeans = KMeans(n_clusters=6, random_state=2026, n_init=10)
    raw_clusters = kmeans.fit_predict(scaled_settings)

    # Map cluster indices (0..5) to Regimes 1..6 ordered by cluster mean setting1
    cluster_setting1_means = [
        (c_idx, float(df_train.loc[raw_clusters == c_idx, "setting1"].mean())) for c_idx in range(6)
    ]
    # Sort cluster indices by ascending setting1 mean
    sorted_clusters = [c_idx for c_idx, _ in sorted(cluster_setting1_means, key=lambda x: x[1])]
    cluster_to_regime = {old_c: new_r + 1 for new_r, old_c in enumerate(sorted_clusters)}

    regime_labels = np.array([cluster_to_regime[c] for c in raw_clusters])
    df_train["regime"] = regime_labels

    # 5. Compute per-sensor diagnostics
    sensor_rows: list[dict[str, Any]] = []

    for i in range(1, 22):
        s_col = f"s{i}"
        s_vals = df_train[s_col]

        missing_count = int(s_vals.isna().sum())
        n_unique = int(s_vals.nunique())
        val_min = float(s_vals.min())
        val_max = float(s_vals.max())
        val_range = val_max - val_min
        val_mean = float(s_vals.mean())
        val_std = float(s_vals.std())
        val_var = float(s_vals.var())

        # Median absolute Pearson correlation across training engines (sensor vs cycle)
        corrs: list[float] = []
        for _unit_id, unit_group in df_train.groupby("unit"):
            if len(unit_group) > 1 and float(unit_group[s_col].std()) > 0:
                corr = float(unit_group[s_col].corr(unit_group["cycle"]))
                if not np.isnan(corr):
                    corrs.append(abs(corr))
                else:
                    corrs.append(0.0)
            else:
                corrs.append(0.0)

        median_abs_corr = float(np.median(corrs)) if len(corrs) > 0 else 0.0

        # Per-regime std and range
        regime_stds: dict[str, float] = {}
        regime_ranges: dict[str, float] = {}
        for r in range(1, 7):
            r_vals = df_train.loc[df_train["regime"] == r, s_col]
            if len(r_vals) > 0:
                r_std = float(r_vals.std())
                r_rng = float(r_vals.max() - r_vals.min())
            else:
                r_std = 0.0
                r_rng = 0.0
            regime_stds[f"regime_{r}_std"] = r_std
            regime_ranges[f"regime_{r}_range"] = r_rng

        # Descriptive exploratory classification (DIAGNOSTIC ONLY)
        # Note: These classifications are descriptive conveniences and do NOT lock
        # final sensor selection.
        max_reg_std = max(regime_stds.values())
        if val_std == 0.0 or val_range == 0.0 or n_unique <= 1:
            variation_class = "constant"
            note = "Constant across all operating conditions and engines (zero variation)."
        elif (
            val_std < DIAGNOSTIC_NEAR_CONSTANT_STD_THRESHOLD
            and max_reg_std < DIAGNOSTIC_NEAR_CONSTANT_STD_THRESHOLD
        ):
            variation_class = "near-constant / extremely low variation"
            note = (
                f"Descriptively near-constant (std < {DIAGNOSTIC_NEAR_CONSTANT_STD_THRESHOLD}) "
                "with extremely low overall and within-regime variation. Diagnostic label only."
            )
        else:
            variation_class = "variable"
            if max_reg_std < 0.1 * val_std:
                note = (
                    "Variable overall, but variation is primarily operating-condition driven "
                    "(low within-regime std)."
                )
            else:
                note = "Variable with substantial within-regime variation and/or degradation trend."

        row_dict: dict[str, Any] = {
            "sensor": s_col,
            "n_rows": n_rows,
            "missing_count": missing_count,
            "unique_values": n_unique,
            "min": round(val_min, 6),
            "max": round(val_max, 6),
            "range": round(val_range, 6),
            "mean": round(val_mean, 6),
            "std": round(val_std, 6),
            "variance": round(val_var, 6),
            "median_abs_engine_cycle_correlation": round(median_abs_corr, 6),
            "regime_1_std": round(regime_stds["regime_1_std"], 6),
            "regime_2_std": round(regime_stds["regime_2_std"], 6),
            "regime_3_std": round(regime_stds["regime_3_std"], 6),
            "regime_4_std": round(regime_stds["regime_4_std"], 6),
            "regime_5_std": round(regime_stds["regime_5_std"], 6),
            "regime_6_std": round(regime_stds["regime_6_std"], 6),
            "regime_1_range": round(regime_ranges["regime_1_range"], 6),
            "regime_2_range": round(regime_ranges["regime_2_range"], 6),
            "regime_3_range": round(regime_ranges["regime_3_range"], 6),
            "regime_4_range": round(regime_ranges["regime_4_range"], 6),
            "regime_5_range": round(regime_ranges["regime_5_range"], 6),
            "regime_6_range": round(regime_ranges["regime_6_range"], 6),
            "variation_classification": variation_class,
            "diagnostic_note": note,
        }
        sensor_rows.append(row_dict)

    df_out = pd.DataFrame(sensor_rows)

    # Save to CSV
    OUTPUT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(OUTPUT_CSV_PATH, index=False)
    print(f"Successfully generated sensor diagnostic CSV at: {OUTPUT_CSV_PATH}")

    return df_out


if __name__ == "__main__":
    try:
        run_sensor_diagnostic()
    except Exception as e:
        print(f"Error during sensor diagnostic: {e}", file=sys.stderr)
        sys.exit(1)
