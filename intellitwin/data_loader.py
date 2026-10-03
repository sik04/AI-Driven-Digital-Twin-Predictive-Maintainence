"""
IntelliTwin Data Loader & Preprocessing for NASA C-MAPSS Turbofan Engine Dataset.
Supports FD001 and FD002 with piecewise RUL labeling, sequence generation,
sensor selection, and condition normalization.
"""

import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler

# Column definitions for C-MAPSS dataset
INDEX_COLUMNS = ["unit", "cycle"]
SETTING_COLUMNS = ["setting_1", "setting_2", "setting_3"]
SENSOR_COLUMNS = [f"sensor_{i}" for i in range(1, 22)]
ALL_COLUMNS = INDEX_COLUMNS + SETTING_COLUMNS + SENSOR_COLUMNS

# In FD001, these sensors exhibit near-zero variance across all units
CONSTANT_SENSORS_FD001 = ["sensor_1", "sensor_5", "sensor_6", "sensor_10", 
                          "sensor_16", "sensor_18", "sensor_19"]
INFORMATIVE_SENSORS_FD001 = [s for s in SENSOR_COLUMNS if s not in CONSTANT_SENSORS_FD001]

# Health state definitions
STATE_HEALTHY = 0    # RUL > 60 cycles
STATE_DEGRADING = 1  # 20 < RUL <= 60 cycles
STATE_CRITICAL = 2   # RUL <= 20 cycles (catastrophic risk zone)
HEALTH_STATE_NAMES = {0: "Healthy", 1: "Degrading", 2: "Critical"}


class CMAPSSDataLoader:
    """Loads and preprocesses NASA C-MAPSS dataset."""

    def __init__(self, data_dir="data/cmapss", sub_dataset="FD001", max_rul=125, seq_len=30):
        self.data_dir = data_dir
        self.sub_dataset = sub_dataset
        self.max_rul = max_rul
        self.seq_len = seq_len
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.train_df = None
        self.test_df = None
        self.y_test_last = None

    def load_raw_data(self):
        """Load raw training and test data files."""
        train_path = os.path.join(self.data_dir, f"train_{self.sub_dataset}.txt")
        test_path = os.path.join(self.data_dir, f"test_{self.sub_dataset}.txt")
        rul_path = os.path.join(self.data_dir, f"RUL_{self.sub_dataset}.txt")

        if not os.path.exists(train_path):
            raise FileNotFoundError(f"Missing train data at {train_path}")

        # C-MAPSS files are whitespace-delimited
        train_df = pd.read_csv(train_path, sep=r"\s+", header=None, names=ALL_COLUMNS)
        test_df = pd.read_csv(test_path, sep=r"\s+", header=None, names=ALL_COLUMNS)
        rul_df = pd.read_csv(rul_path, sep=r"\s+", header=None, names=["rul"])

        return train_df, test_df, rul_df

    def compute_rul_labels(self, train_df, test_df, rul_df):
        """Compute true Remaining Useful Life with piecewise linear capping."""
        # Train RUL: run-to-failure trajectories
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

        # Test RUL: trajectory ends before failure
        test_rul_map = {unit: rul_df.iloc[unit - 1]["rul"] for unit in test_df["unit"].unique()}
        test_rul_list = []
        for unit, group in test_df.groupby("unit"):
            last_cycle = group["cycle"].max()
            true_last_rul = test_rul_map[unit]
            # At each cycle: remaining cycles = (last_cycle - cycle) + true_last_rul
            rul = (last_cycle - group["cycle"]) + true_last_rul
            rul_capped = rul.clip(upper=self.max_rul)
            test_rul_list.extend(rul_capped.values)
        test_df["rul"] = test_rul_list
        test_df["health_state"] = np.where(
            test_df["rul"] > 60, STATE_HEALTHY,
            np.where(test_df["rul"] > 20, STATE_DEGRADING, STATE_CRITICAL)
        )

        return train_df, test_df, rul_df["rul"].values

    def prepare_data(self, drop_constant=True, add_features=True):
        """Complete preparation pipeline: load, label, filter, feature-engineer, scale."""
        raw_train, raw_test, rul_test = self.load_raw_data()
        train_df, test_df, y_test_last = self.compute_rul_labels(raw_train, raw_test, rul_test)

        if drop_constant:
            low_var_cols = []
            for col in SENSOR_COLUMNS:
                if train_df[col].std() < 1e-4:
                    low_var_cols.append(col)
            active_sensors = [c for c in SENSOR_COLUMNS if c not in low_var_cols]
        else:
            active_sensors = SENSOR_COLUMNS

        feature_cols = SETTING_COLUMNS + active_sensors

        if add_features:
            train_df = self._add_rolling_features(train_df, active_sensors, window=5)
            test_df = self._add_rolling_features(test_df, active_sensors, window=5)
            # Update feature columns with rolling features
            feature_cols = [c for c in train_df.columns if c not in INDEX_COLUMNS + ["rul", "health_state"]]

        # Fit scaler on training features only
        self.scaler.fit(train_df[feature_cols])
        train_df[feature_cols] = self.scaler.transform(train_df[feature_cols])
        test_df[feature_cols] = self.scaler.transform(test_df[feature_cols])

        self.feature_columns = feature_cols
        self.train_df = train_df
        self.test_df = test_df
        self.y_test_last = y_test_last

        return train_df, test_df, feature_cols

    @staticmethod
    def _add_rolling_features(df, sensor_cols, window=5):
        """Add rolling mean and rolling std to capture temporal degradation dynamics."""
        df = df.copy()
        rolling_means = []
        rolling_stds = []
        for unit, group in df.groupby("unit"):
            rm = group[sensor_cols].rolling(window=window, min_periods=1).mean()
            rs = group[sensor_cols].rolling(window=window, min_periods=1).std().fillna(0)
            rolling_means.append(rm)
            rolling_stds.append(rs)
        
        rm_df = pd.concat(rolling_means).add_suffix("_mean5")
        rs_df = pd.concat(rolling_stds).add_suffix("_std5")
        
        df = pd.concat([df, rm_df, rs_df], axis=1)
        return df

    def get_tabular_data(self, val_ratio=0.2, random_state=42):
        """Return tabular train, validation, and test matrices."""
        if self.train_df is None:
            self.prepare_data()

        # Split at asset (unit) level to avoid data leakage
        unique_units = self.train_df["unit"].unique()
        np.random.seed(random_state)
        shuffled_units = np.random.permutation(unique_units)
        split_idx = int(len(unique_units) * (1 - val_ratio))
        train_units = shuffled_units[:split_idx]
        val_units = shuffled_units[split_idx:]

        train_split = self.train_df[self.train_df["unit"].isin(train_units)]
        val_split = self.train_df[self.train_df["unit"].isin(val_units)]

        X_train = train_split[self.feature_columns].values
        y_train_rul = train_split["rul"].values
        y_train_state = train_split["health_state"].values

        X_val = val_split[self.feature_columns].values
        y_val_rul = val_split["rul"].values
        y_val_state = val_split["health_state"].values

        # Test set: entire test set and final cycle of each test engine
        X_test_all = self.test_df[self.feature_columns].values
        y_test_rul_all = self.test_df["rul"].values
        y_test_state_all = self.test_df["health_state"].values

        # Last cycle per unit (standard C-MAPSS benchmark evaluation)
        last_cycles = self.test_df.groupby("unit").last().reset_index()
        X_test_last = last_cycles[self.feature_columns].values
        y_test_last_rul = last_cycles["rul"].values
        y_test_last_state = last_cycles["health_state"].values

        return {
            "X_train": X_train,
            "y_train_rul": y_train_rul,
            "y_train_state": y_train_state,
            "X_val": X_val,
            "y_val_rul": y_val_rul,
            "y_val_state": y_val_state,
            "X_test_all": X_test_all,
            "y_test_rul_all": y_test_rul_all,
            "y_test_state_all": y_test_state_all,
            "X_test_last": X_test_last,
            "y_test_last_rul": y_test_last_rul,
            "y_test_last_state": y_test_last_state,
            "feature_columns": self.feature_columns,
        }

    def get_sequential_data(self, val_ratio=0.2, random_state=42):
        """Construct (N, seq_len, num_features) 3D tensors for LSTM and GRU."""
        if self.train_df is None:
            self.prepare_data()

        unique_units = self.train_df["unit"].unique()
        np.random.seed(random_state)
        shuffled_units = np.random.permutation(unique_units)
        split_idx = int(len(unique_units) * (1 - val_ratio))
        train_units = set(shuffled_units[:split_idx])
        val_units = set(shuffled_units[split_idx:])

        def _build_sequences(df, unit_filter=None):
            X_seqs, y_rul_seqs, y_state_seqs = [], [], []
            for unit, group in df.groupby("unit"):
                if unit_filter is not None and unit not in unit_filter:
                    continue
                feat_vals = group[self.feature_columns].values
                rul_vals = group["rul"].values
                state_vals = group["health_state"].values
                n_samples = len(group)
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

            return np.array(X_seqs, dtype=np.float32), np.array(y_rul_seqs, dtype=np.float32), np.array(y_state_seqs, dtype=np.int64)

        X_train_seq, y_train_rul_seq, y_train_state_seq = _build_sequences(self.train_df, train_units)
        X_val_seq, y_val_rul_seq, y_val_state_seq = _build_sequences(self.train_df, val_units)

        # For test set, extract last sequence for each engine (standard benchmark protocol)
        X_test_last_seq = []
        y_test_last_rul = []
        y_test_last_state = []
        for unit, group in self.test_df.groupby("unit"):
            feat_vals = group[self.feature_columns].values
            rul_val = group["rul"].iloc[-1]
            state_val = group["health_state"].iloc[-1]
            n_samples = len(group)
            if n_samples < self.seq_len:
                pad_len = self.seq_len - n_samples
                pad_feat = np.repeat(feat_vals[:1], pad_len, axis=0)
                feat_vals = np.vstack([pad_feat, feat_vals])
            X_test_last_seq.append(feat_vals[-self.seq_len:])
            y_test_last_rul.append(rul_val)
            y_test_last_state.append(state_val)

        return {
            "X_train_seq": X_train_seq,
            "y_train_rul_seq": y_train_rul_seq,
            "y_train_state_seq": y_train_state_seq,
            "X_val_seq": X_val_seq,
            "y_val_rul_seq": y_val_rul_seq,
            "y_val_state_seq": y_val_state_seq,
            "X_test_last_seq": np.array(X_test_last_seq, dtype=np.float32),
            "y_test_last_rul": np.array(y_test_last_rul, dtype=np.float32),
            "y_test_last_state": np.array(y_test_last_state, dtype=np.int64),
        }
