"""
IntelliTwin Data Loader & Preprocessing for NASA C-MAPSS Turbofan Engine Dataset.
Implements the scientifically valid data splitting and preprocessing protocol:
1. Deterministic asset-level (engine/unit) train/validation/test splitting.
2. Complete data isolation: feature selection and StandardScaler fitting occur
   exclusively on training engines (train_units).
3. Engine-safe temporal feature engineering (rolling mean/std per unit).
4. Boundary-safe sequence generation (sequences never cross engine boundaries).
5. Reproducible split persistence to artifacts/splits/.
"""

import os
import json
from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any, Optional

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from intellitwin.config import get_default_data_config, DataConfig

# Column definitions for NASA C-MAPSS dataset
INDEX_COLUMNS = ["unit", "cycle"]
SETTING_COLUMNS = ["setting_1", "setting_2", "setting_3"]
SENSOR_COLUMNS = [f"sensor_{i}" for i in range(1, 22)]
ALL_COLUMNS = INDEX_COLUMNS + SETTING_COLUMNS + SENSOR_COLUMNS

# In FD001, sensors with near-zero operational variance across units
CONSTANT_SENSORS_FD001 = [
    "sensor_1", "sensor_5", "sensor_6", "sensor_10",
    "sensor_16", "sensor_18", "sensor_19"
]
INFORMATIVE_SENSORS_FD001 = [s for s in SENSOR_COLUMNS if s not in CONSTANT_SENSORS_FD001]

# Discrete Health State Definitions
STATE_HEALTHY = 0    # RUL > 60 cycles
STATE_DEGRADING = 1  # 20 < RUL <= 60 cycles
STATE_CRITICAL = 2   # RUL <= 20 cycles (catastrophic failure risk zone)
HEALTH_STATE_NAMES = {0: "Healthy", 1: "Degrading", 2: "Critical"}


class CMAPSSDataLoader:
    """Loads and preprocesses NASA C-MAPSS dataset with strict data isolation."""

    def __init__(
        self,
        data_dir: Optional[str] = None,
        sub_dataset: str = "FD001",
        max_rul: int = 125,
        seq_len: int = 30,
        val_ratio: float = 0.20,
        random_state: int = 42,
        split_strategy: str = "engine_level",
        config: Optional[DataConfig] = None,
    ):
        cfg = config or get_default_data_config()
        self.data_dir = data_dir if data_dir is not None else cfg.data_dir
        self.sub_dataset = sub_dataset or cfg.sub_dataset
        self.max_rul = max_rul if max_rul is not None else cfg.max_rul
        self.seq_len = seq_len if seq_len is not None else cfg.seq_len
        self.val_ratio = val_ratio if val_ratio is not None else cfg.validation_fraction
        self.random_state = random_state if random_state is not None else cfg.random_seed
        self.split_strategy = split_strategy or cfg.split_strategy
        self.constant_variance_threshold = cfg.constant_variance_threshold
        self.rolling_window = cfg.rolling_window
        self.split_artifact_path = cfg.split_artifact_path

        self.scaler = StandardScaler()
        self.feature_columns: Optional[List[str]] = None
        self.active_sensors: Optional[List[str]] = None
        self.train_df: Optional[pd.DataFrame] = None
        self.test_df: Optional[pd.DataFrame] = None
        self.y_test_last: Optional[np.ndarray] = None

        # Authoritative split identifiers
        self.train_units: Optional[List[int]] = None
        self.val_units: Optional[List[int]] = None
        self.test_units: Optional[List[int]] = None
        self.split_metadata: Optional[Dict[str, Any]] = None

    def load_raw_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Load raw training and test data files from disk."""
        train_path = os.path.join(self.data_dir, f"train_{self.sub_dataset}.txt")
        test_path = os.path.join(self.data_dir, f"test_{self.sub_dataset}.txt")
        rul_path = os.path.join(self.data_dir, f"RUL_{self.sub_dataset}.txt")

        if not os.path.exists(train_path):
            raise FileNotFoundError(f"Missing train data file at {train_path}")
        if not os.path.exists(test_path):
            raise FileNotFoundError(f"Missing test data file at {test_path}")
        if not os.path.exists(rul_path):
            raise FileNotFoundError(f"Missing ground-truth RUL file at {rul_path}")

        # C-MAPSS text files are whitespace-delimited with 26 numeric columns
        train_df = pd.read_csv(train_path, sep=r"\s+", header=None, names=ALL_COLUMNS)
        test_df = pd.read_csv(test_path, sep=r"\s+", header=None, names=ALL_COLUMNS)
        rul_df = pd.read_csv(rul_path, sep=r"\s+", header=None, names=["rul"])

        return train_df, test_df, rul_df

    def compute_rul_labels(
        self, train_df: pd.DataFrame, test_df: pd.DataFrame, rul_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
        """Compute piecewise linear Remaining Useful Life (RUL) labels and health states."""
        train_df = train_df.copy()
        test_df = test_df.copy()

        # Training RUL: run-to-failure trajectories
        rul_list = []
        for unit, group in train_df.groupby("unit"):
            max_cycle = group["cycle"].max()
            rul = max_cycle - group["cycle"]
            rul_capped = rul.clip(upper=self.max_rul)
            rul_list.extend(rul_capped.values)
        train_df["rul"] = rul_list

        # Assign discrete health state classes
        train_df["health_state"] = np.where(
            train_df["rul"] > 60, STATE_HEALTHY,
            np.where(train_df["rul"] > 20, STATE_DEGRADING, STATE_CRITICAL)
        )

        # Test RUL: trajectories end prior to failure, true final RUL in rul_df
        test_rul_map = {unit: rul_df.iloc[unit - 1]["rul"] for unit in test_df["unit"].unique()}
        test_rul_list = []
        for unit, group in test_df.groupby("unit"):
            last_cycle = group["cycle"].max()
            true_last_rul = test_rul_map[unit]
            # Remaining cycles at each step = (last_cycle - cycle) + true_last_rul
            rul = (last_cycle - group["cycle"]) + true_last_rul
            rul_capped = rul.clip(upper=self.max_rul)
            test_rul_list.extend(rul_capped.values)
        test_df["rul"] = test_rul_list
        test_df["health_state"] = np.where(
            test_df["rul"] > 60, STATE_HEALTHY,
            np.where(test_df["rul"] > 20, STATE_DEGRADING, STATE_CRITICAL)
        )

        return train_df, test_df, rul_df["rul"].values

    def get_engine_split(
        self,
        all_train_units: Optional[List[int]] = None,
        test_units: Optional[List[int]] = None,
    ) -> Tuple[List[int], List[int], List[int]]:
        """Establish authoritative, deterministic engine-level split.
        
        Guarantees:
        1. complete unit isolation: train_units intersect val_units is empty.
        2. complete coverage: train_units union val_units == all_train_units.
        3. strict determinism via local RandomState seeded with self.random_state.
        """
        if all_train_units is None:
            all_train_units = list(range(1, 101)) if self.sub_dataset == "FD001" else list(range(1, 261))
        
        all_train_units = sorted([int(u) for u in all_train_units])
        n_units = len(all_train_units)
        
        # Deterministic shuffle using local RandomState (does not pollute global random state)
        rng = np.random.RandomState(self.random_state)
        shuffled = rng.permutation(all_train_units)
        
        split_idx = int(n_units * (1.0 - self.val_ratio))
        train_units = sorted([int(u) for u in shuffled[:split_idx]])
        val_units = sorted([int(u) for u in shuffled[split_idx:]])

        if test_units is not None:
            test_units = sorted([int(u) for u in test_units])
        else:
            test_units = list(range(1, 101)) if self.sub_dataset == "FD001" else list(range(1, 260))

        # Scientific isolation assertions
        assert set(train_units).isdisjoint(set(val_units)), "CRITICAL: train_units and val_units overlap!"
        assert set(train_units) | set(val_units) == set(all_train_units), "CRITICAL: Engine split lost units!"
        assert len(train_units) + len(val_units) == n_units, "CRITICAL: Unit count mismatch!"

        self.train_units = train_units
        self.val_units = val_units
        self.test_units = test_units

        self.split_metadata = {
            "dataset": f"NASA C-MAPSS {self.sub_dataset}",
            "split_strategy": self.split_strategy,
            "random_seed": self.random_state,
            "validation_fraction": self.val_ratio,
            "total_train_units": n_units,
            "train_unit_count": len(train_units),
            "val_unit_count": len(val_units),
            "test_unit_count": len(test_units),
            "train_units": train_units,
            "validation_units": val_units,
            "test_units": test_units,
        }

        return self.train_units, self.val_units, self.test_units

    def save_split_artifact(self, filepath: Optional[str] = None) -> str:
        """Persist authoritative split metadata to disk."""
        path = filepath or self.split_artifact_path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if self.split_metadata is None:
            self.get_engine_split()
        
        payload = dict(self.split_metadata)
        payload["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        payload["preprocessing_rule"] = "StandardScaler and feature selection fitted strictly on train_units only"
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return path

    def load_split_artifact(self, filepath: Optional[str] = None) -> Dict[str, Any]:
        """Load persisted split metadata from disk."""
        path = filepath or self.split_artifact_path
        if not os.path.exists(path):
            raise FileNotFoundError(f"Split artifact not found at {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.train_units = [int(u) for u in data["train_units"]]
        self.val_units = [int(u) for u in data["validation_units"]]
        self.test_units = [int(u) for u in data["test_units"]]
        self.split_metadata = data
        return data

    @staticmethod
    def _add_rolling_features(df: pd.DataFrame, sensor_cols: List[str], window: int = 5) -> pd.DataFrame:
        """Add rolling mean and rolling standard deviation per engine.
        
        Engine-Safety Guarantee:
        Features are computed within each unit independently (groupby('unit')).
        Observations from one engine NEVER enter the rolling window of another engine.
        """
        df = df.copy()
        rolling_dfs = []
        for unit, group in df.groupby("unit"):
            group_sorted = group.sort_values("cycle")
            rm = group_sorted[sensor_cols].rolling(window=window, min_periods=1).mean().add_suffix(f"_mean{window}")
            rs = group_sorted[sensor_cols].rolling(window=window, min_periods=1).std().fillna(0).add_suffix(f"_std{window}")
            rolling_dfs.append(pd.concat([rm, rs], axis=1))

        roll_all = pd.concat(rolling_dfs)
        # Concatenate along columns, aligned on index
        df = pd.concat([df, roll_all], axis=1)
        return df

    def prepare_data(
        self,
        drop_constant: bool = True,
        add_features: bool = True,
        save_artifact: bool = True,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
        """Complete data preparation protocol with strict data isolation.
        
        Scientific Execution Sequence:
        1. Load raw files & assign RUL / discrete health state labels.
        2. Establish authoritative engine-level split (train_units vs val_units).
        3. Feature selection: compute sensor variance strictly on train_units.
        4. Feature engineering: compute rolling statistics per unit.
        5. Scaling: FIT StandardScaler EXCLUSIVELY on train_units.
        6. Transform train_units, val_units, and test_df using the fitted scaler.
        """
        raw_train, raw_test, rul_test = self.load_raw_data()
        train_df, test_df, y_test_last = self.compute_rul_labels(raw_train, raw_test, rul_test)

        # 1. Establish engine split FIRST
        self.get_engine_split(
            all_train_units=train_df["unit"].unique(),
            test_units=test_df["unit"].unique()
        )

        train_mask = train_df["unit"].isin(self.train_units)
        val_mask = train_df["unit"].isin(self.val_units)

        # 2. Feature selection learned EXCLUSIVELY from training engines
        train_only_df = train_df.loc[train_mask]
        if drop_constant:
            low_var_cols = []
            for col in SENSOR_COLUMNS:
                if train_only_df[col].std() < self.constant_variance_threshold:
                    low_var_cols.append(col)
            active_sensors = [c for c in SENSOR_COLUMNS if c not in low_var_cols]
        else:
            active_sensors = SENSOR_COLUMNS

        self.active_sensors = active_sensors
        feature_cols = SETTING_COLUMNS + active_sensors

        # 3. Engine-safe temporal feature engineering
        if add_features:
            train_df = self._add_rolling_features(train_df, active_sensors, window=self.rolling_window)
            test_df = self._add_rolling_features(test_df, active_sensors, window=self.rolling_window)
            feature_cols = [c for c in train_df.columns if c not in INDEX_COLUMNS + ["rul", "health_state"]]

        self.feature_columns = feature_cols

        # Ensure feature columns are float64 to support floating-point standardized values
        train_df[feature_cols] = train_df[feature_cols].astype(np.float64)
        test_df[feature_cols] = test_df[feature_cols].astype(np.float64)

        # 4. Strict Preprocessing Isolation:
        # Fit scaler EXCLUSIVELY on training engine rows (train_mask)
        self.scaler.fit(train_df.loc[train_mask, feature_cols])

        # Transform training engines
        train_df.loc[train_mask, feature_cols] = self.scaler.transform(train_df.loc[train_mask, feature_cols])

        # Transform validation engines (TRANSFORM ONLY - NO FIT)
        train_df.loc[val_mask, feature_cols] = self.scaler.transform(train_df.loc[val_mask, feature_cols])

        # Transform test engines (TRANSFORM ONLY - NO FIT)
        test_df[feature_cols] = self.scaler.transform(test_df[feature_cols])

        self.train_df = train_df
        self.test_df = test_df
        self.y_test_last = y_test_last

        # Update metadata with exact sample counts
        if self.split_metadata:
            self.split_metadata.update({
                "train_samples": int(train_mask.sum()),
                "validation_samples": int(val_mask.sum()),
                "test_samples": len(test_df),
                "feature_count": len(feature_cols),
                "sequence_length": self.seq_len,
                "max_rul": self.max_rul,
                "rolling_window": self.rolling_window,
            })

        if save_artifact:
            self.save_split_artifact()

        return train_df, test_df, feature_cols

    def get_tabular_data(
        self,
        val_ratio: Optional[float] = None,
        random_state: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Return tabular train, validation, and test matrices with full unit traceability."""
        if self.train_df is None:
            self.prepare_data()

        # Preserve authoritative split
        train_split = self.train_df[self.train_df["unit"].isin(self.train_units)]
        val_split = self.train_df[self.train_df["unit"].isin(self.val_units)]

        X_train = train_split[self.feature_columns].values
        y_train_rul = train_split["rul"].values
        y_train_state = train_split["health_state"].values
        train_unit_ids = train_split["unit"].values

        X_val = val_split[self.feature_columns].values
        y_val_rul = val_split["rul"].values
        y_val_state = val_split["health_state"].values
        val_unit_ids = val_split["unit"].values

        # Complete test set
        X_test_all = self.test_df[self.feature_columns].values
        y_test_rul_all = self.test_df["rul"].values
        y_test_state_all = self.test_df["health_state"].values
        test_unit_ids_all = self.test_df["unit"].values

        # Last cycle per unit (standard C-MAPSS benchmark evaluation)
        last_cycles = self.test_df.groupby("unit").last().reset_index()
        X_test_last = last_cycles[self.feature_columns].values
        y_test_last_rul = last_cycles["rul"].values
        y_test_last_state = last_cycles["health_state"].values
        test_last_unit_ids = last_cycles["unit"].values

        return {
            "X_train": X_train,
            "y_train_rul": y_train_rul,
            "y_train_state": y_train_state,
            "train_unit_ids": train_unit_ids,
            "X_val": X_val,
            "y_val_rul": y_val_rul,
            "y_val_state": y_val_state,
            "val_unit_ids": val_unit_ids,
            "X_test_all": X_test_all,
            "y_test_rul_all": y_test_rul_all,
            "y_test_state_all": y_test_state_all,
            "test_unit_ids_all": test_unit_ids_all,
            "X_test_last": X_test_last,
            "y_test_last_rul": y_test_last_rul,
            "y_test_last_state": y_test_last_state,
            "test_last_unit_ids": test_last_unit_ids,
            "train_units": self.train_units,
            "val_units": self.val_units,
            "test_units": self.test_units,
            "feature_columns": self.feature_columns,
        }

    def get_sequential_data(
        self,
        val_ratio: Optional[float] = None,
        random_state: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Construct 3D sequential tensors (N, seq_len, num_features) with boundary safety.
        
        Boundary-Safety Guarantee:
        Sequences are extracted strictly within each individual engine's trajectory.
        Every sequence belongs to exactly one engine ID (recorded in seq_units).
        """
        if self.train_df is None:
            self.prepare_data()

        train_units_set = set(self.train_units)
        val_units_set = set(self.val_units)

        def _build_sequences(df: pd.DataFrame, unit_filter: Optional[set] = None):
            X_seqs = []
            y_rul_seqs = []
            y_state_seqs = []
            seq_units = []

            for unit, group in df.groupby("unit"):
                if unit_filter is not None and unit not in unit_filter:
                    continue
                group_sorted = group.sort_values("cycle")
                feat_vals = group_sorted[self.feature_columns].values
                rul_vals = group_sorted["rul"].values
                state_vals = group_sorted["health_state"].values
                n_samples = len(group_sorted)

                if n_samples < self.seq_len:
                    # Pad front if trajectory is shorter than seq_len
                    pad_len = self.seq_len - n_samples
                    pad_feat = np.repeat(feat_vals[:1], pad_len, axis=0)
                    feat_vals = np.vstack([pad_feat, feat_vals])
                    rul_vals = np.concatenate([np.repeat(rul_vals[0], pad_len), rul_vals])
                    state_vals = np.concatenate([np.repeat(state_vals[0], pad_len), state_vals])
                    n_samples = self.seq_len

                for i in range(self.seq_len, n_samples + 1):
                    X_seqs.append(feat_vals[i - self.seq_len:i])
                    y_rul_seqs.append(rul_vals[i - 1])
                    y_state_seqs.append(state_vals[i - 1])
                    seq_units.append(int(unit))

            return (
                np.array(X_seqs, dtype=np.float32),
                np.array(y_rul_seqs, dtype=np.float32),
                np.array(y_state_seqs, dtype=np.int64),
                np.array(seq_units, dtype=np.int32),
            )

        X_train_seq, y_train_rul_seq, y_train_state_seq, train_seq_units = _build_sequences(
            self.train_df, train_units_set
        )
        X_val_seq, y_val_rul_seq, y_val_state_seq, val_seq_units = _build_sequences(
            self.train_df, val_units_set
        )

        # For test set, extract last sequence for each engine (standard benchmark protocol)
        X_test_last_seq = []
        y_test_last_rul = []
        y_test_last_state = []
        test_seq_units = []

        for unit, group in self.test_df.groupby("unit"):
            group_sorted = group.sort_values("cycle")
            feat_vals = group_sorted[self.feature_columns].values
            rul_val = group_sorted["rul"].iloc[-1]
            state_val = group_sorted["health_state"].iloc[-1]
            n_samples = len(group_sorted)

            if n_samples < self.seq_len:
                pad_len = self.seq_len - n_samples
                pad_feat = np.repeat(feat_vals[:1], pad_len, axis=0)
                feat_vals = np.vstack([pad_feat, feat_vals])

            X_test_last_seq.append(feat_vals[-self.seq_len:])
            y_test_last_rul.append(rul_val)
            y_test_last_state.append(state_val)
            test_seq_units.append(int(unit))

        return {
            "X_train_seq": X_train_seq,
            "y_train_rul_seq": y_train_rul_seq,
            "y_train_state_seq": y_train_state_seq,
            "train_seq_units": train_seq_units,
            "X_val_seq": X_val_seq,
            "y_val_rul_seq": y_val_rul_seq,
            "y_val_state_seq": y_val_state_seq,
            "val_seq_units": val_seq_units,
            "X_test_last_seq": np.array(X_test_last_seq, dtype=np.float32),
            "y_test_last_rul": np.array(y_test_last_rul, dtype=np.float32),
            "y_test_last_state": np.array(y_test_last_state, dtype=np.int64),
            "test_seq_units": np.array(test_seq_units, dtype=np.int32),
            "train_units": self.train_units,
            "val_units": self.val_units,
            "test_units": self.test_units,
        }
