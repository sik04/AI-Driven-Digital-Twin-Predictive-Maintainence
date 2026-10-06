"""Reproducible script for FD002 training-only sensor diagnostic.

This script loads train_FD002.txt, filters to the 130 training engines defined in
data/splits/fd002_engine_split_seed_2026.json, and computes overall, regime-wise,
and temporal correlation diagnostics for sensors s1 through s21.

No non-training engines are inspected, no data is downloaded automatically,
and no final feature selection decisions are locked by this script.
"""

import json
from pathlib import Path
import sys
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# Define repository paths
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "data" / "raw" / "cmapss" / "train_FD002.txt"
SPLIT_MANIFEST_PATH = REPO_ROOT / "data" / "splits" / "fd002_engine_split_seed_2026.json"
OUTPUT_CSV_PATH = REPO_ROOT / "research" / "research_design" / "fd002_training_sensor_diagnostic.csv"

# Standard C-MAPSS column names
COLUMNS = [
    "unit",
    "cycle",
    "setting1",
    "setting2",
    "setting3",
] + [f"s{i}" for i in range(1, 22)]


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
    with open(SPLIT_MANIFEST_PATH, "r", encoding="utf-8") as f:
        split_data = json.load(f)

    train_engines = set(split_data["partitions"]["train"])
    assert len(train_engines) == 130, f"Expected 130 training engines, found {len(train_engines)}"

    # 2. Load C-MAPSS raw FD002 file
    # Space-separated file without header
    df_raw = pd.read_csv(
        DATA_PATH,
        sep=r"\s+",
        header=None,
        names=COLUMNS,
        engine="python"
    )

    # 3. Filter to training engines ONLY
    df_train = df_raw[df_raw["unit"].isin(train_engines)].copy()
    unique_train_units = set(df_train["unit"].unique())
    assert unique_train_units == train_engines, "Training dataframe engine set mismatch"

    # Verify no leakage from calibration, validation, or test engines
    calib_engines = set(split_data["partitions"]["calibration"])
    val_engines = set(split_data["partitions"]["validation"])
    test_engines = set(split_data["partitions"]["test"])
    non_train_engines = calib_engines | val_engines | test_engines

    assert len(unique_train_units & non_train_engines) == 0, "Non-training engines leaked into training dataframe!"

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
        (c_idx, df_train.loc[raw_clusters == c_idx, "setting1"].mean())
        for c_idx in range(6)
    ]
    # Sort cluster indices by ascending setting1 mean
    sorted_clusters = [c_idx for c_idx, _ in sorted(cluster_setting1_means, key=lambda x: x[1])]
    cluster_to_regime = {old_c: new_r + 1 for new_r, old_c in enumerate(sorted_clusters)}

    regime_labels = np.array([cluster_to_regime[c] for c in raw_clusters])
    df_train["regime"] = regime_labels

    # 5. Compute per-sensor diagnostics
    sensor_rows = []

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
        corrs = []
        for unit_id, unit_group in df_train.groupby("unit"):
            if len(unit_group) > 1 and unit_group[s_col].std() > 0:
                corr = unit_group[s_col].corr(unit_group["cycle"])
                if not np.isnan(corr):
                    corrs.append(abs(corr))
                else:
                    corrs.append(0.0)
            else:
                corrs.append(0.0)

        median_abs_corr = float(np.median(corrs)) if len(corrs) > 0 else 0.0

        # Per-regime std
        regime_stds = {}
        for r in range(1, 7):
            r_vals = df_train.loc[df_train["regime"] == r, s_col]
            regime_stds[f"regime_{r}_std"] = float(r_vals.std()) if len(r_vals) > 0 else 0.0

        # Classify variation behavior
        # Constant: std == 0 (or range == 0)
        # Near-constant: std < 0.001 or range < 0.01 or n_unique <= 5
        # Variable: noticeable variation
        if val_std == 0.0 or val_range == 0.0 or n_unique <= 1:
            variation_class = "constant"
            note = "Constant across all operating conditions and engines (zero variation)."
        elif val_std < 0.01 and max(regime_stds.values()) < 0.01:
            variation_class = "near-constant / extremely low variation"
            note = "Near-constant with extremely low overall and within-regime variation."
        else:
            variation_class = "variable"
            # Distinguish if variation is mostly operating-condition driven vs within-regime
            max_reg_std = max(regime_stds.values())
            if max_reg_std < 0.1 * val_std:
                note = "Variable overall, but variation is primarily operating-condition driven (low within-regime std)."
            else:
                note = "Variable with substantial within-regime variation and/or degradation trend."

        row_dict = {
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
