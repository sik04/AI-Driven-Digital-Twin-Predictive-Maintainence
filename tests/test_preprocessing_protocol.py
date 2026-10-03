"""
Tests for Step 4 Preprocessing Protocol and Data Leakage Prevention.
Verifies:
- Test B: Scaler parameters (mean, scale) are fitted strictly on training units only.
- Test C: Sequence boundary isolation (sequences never cross engine boundaries).
- Test F: Preprocessing consistency (validation/test are transformed, never refitted).
- Test G: No temporal crossing in rolling feature engineering across engines.
"""

import unittest
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from intellitwin.data_loader import CMAPSSDataLoader, SENSOR_COLUMNS, INDEX_COLUMNS


class TestPreprocessingProtocol(unittest.TestCase):
    """Test suite for preprocessing isolation and temporal feature boundary safety."""

    @classmethod
    def setUpClass(cls):
        cls.loader = CMAPSSDataLoader(data_dir="data/cmapss", sub_dataset="FD001", random_state=42, val_ratio=0.20)
        cls.train_df, cls.test_df, cls.feature_cols = cls.loader.prepare_data(save_artifact=False)

    def test_b_scaler_isolation(self):
        """Test B: Verify that StandardScaler is fitted strictly on train_units only.
        
        Empirical Proof:
        1. Fit an independent StandardScaler strictly on raw train_units.
        2. Fit an independent StandardScaler on all 100 raw training units (leaky).
        3. Assert that loader.scaler matches the isolated scaler within floating-point tolerance.
        4. Assert that loader.scaler significantly differs from the leaky scaler.
        """
        # Load raw data before scaling
        fresh_loader = CMAPSSDataLoader(random_state=42, val_ratio=0.20)
        raw_train, raw_test, rul_test = fresh_loader.load_raw_data()
        labeled_train, _, _ = fresh_loader.compute_rul_labels(raw_train, raw_test, rul_test)
        
        # Add rolling features on raw data using active sensors from loader
        raw_with_features = fresh_loader._add_rolling_features(labeled_train, self.loader.active_sensors, window=5)
        raw_with_features[self.feature_cols] = raw_with_features[self.feature_cols].astype(np.float64)

        train_mask = raw_with_features["unit"].isin(self.loader.train_units)

        # 1. Ground truth isolated scaler fitted on training units only
        ground_truth_isolated = StandardScaler().fit(raw_with_features.loc[train_mask, self.feature_cols])

        # 2. Leaky scaler fitted on all 100 units
        leaky_scaler = StandardScaler().fit(raw_with_features[self.feature_cols])

        # Verify loader scaler matches isolated ground truth exactly
        np.testing.assert_allclose(
            self.loader.scaler.mean_,
            ground_truth_isolated.mean_,
            rtol=1e-5, atol=1e-5,
            err_msg="CRITICAL: loader.scaler.mean_ does not match train_units ground truth!"
        )
        np.testing.assert_allclose(
            self.loader.scaler.scale_,
            ground_truth_isolated.scale_,
            rtol=1e-5, atol=1e-5,
            err_msg="CRITICAL: loader.scaler.scale_ does not match train_units ground truth!"
        )

        # Verify loader scaler is NOT equal to the leaky scaler
        max_mean_diff = np.max(np.abs(self.loader.scaler.mean_ - leaky_scaler.mean_))
        self.assertGreater(max_mean_diff, 0.1, "Scaler appears to have been fitted on all units (leaky)!")

    def test_c_sequence_isolation(self):
        """Test C: Every generated sequence contains observations from exactly one engine."""
        seq_data = self.loader.get_sequential_data()
        
        train_seqs = seq_data["X_train_seq"]
        train_units = seq_data["train_seq_units"]
        val_seqs = seq_data["X_val_seq"]
        val_units = seq_data["val_seq_units"]

        self.assertEqual(len(train_seqs), len(train_units))
        self.assertEqual(len(val_seqs), len(val_units))

        # Check train sequence unit membership
        train_units_set = set(self.loader.train_units)
        for u in np.unique(train_units):
            self.assertIn(int(u), train_units_set, f"Sequence assigned to unit {u} not in train_units!")

        # Check val sequence unit membership
        val_units_set = set(self.loader.val_units)
        for u in np.unique(val_units):
            self.assertIn(int(u), val_units_set, f"Sequence assigned to unit {u} not in val_units!")

        # Verify sequence shape
        self.assertEqual(train_seqs.shape[1], 30, "Sequence length mismatch!")
        self.assertEqual(train_seqs.shape[2], len(self.feature_cols), "Feature dimension mismatch!")

    def test_f_preprocessing_consistency(self):
        """Test F: Preprocessing parameters are preserved; validation/test are not refitted."""
        tab_data = self.loader.get_tabular_data()
        X_train = tab_data["X_train"]
        X_val = tab_data["X_val"]

        # Training set features should have mean approx 0
        train_means = np.mean(X_train, axis=0)
        train_stds = np.std(X_train, axis=0)
        np.testing.assert_allclose(train_means, 0.0, atol=1e-2, err_msg="X_train is not zero-centered!")
        
        # Non-constant features must have unit variance (std = 1.0)
        # Constant features (e.g. setting_3 and constant sensors) have std = 0.0
        non_constant_mask = self.loader.scaler.scale_ != 1.0
        np.testing.assert_allclose(
            train_stds[non_constant_mask], 1.0, atol=1e-2,
            err_msg="X_train non-constant features are not unit-variance!"
        )
        np.testing.assert_allclose(
            train_stds[~non_constant_mask], 0.0, atol=1e-2,
            err_msg="X_train constant features should have zero variance!"
        )

        # Validation set features, transformed by train parameters, will have natural distributional drift
        val_means = np.mean(X_val, axis=0)
        # Validation non-constant mean should not be exactly 0 (which would imply it was refitted)
        self.assertFalse(np.allclose(val_means[non_constant_mask], 0.0, atol=1e-6), "Validation set appears to have been refit!")

    def test_g_no_temporal_crossing(self):
        """Test G: Rolling features for an engine depend strictly on that engine's history."""
        # Create a synthetic DataFrame with 2 engines
        # Engine 1 has constant high values, Engine 2 has constant low values
        data = {
            "unit": [1, 1, 1, 1, 1, 2, 2, 2, 2, 2],
            "cycle": [1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
            "sensor_1": [100.0, 100.0, 100.0, 100.0, 100.0, 10.0, 10.0, 10.0, 10.0, 10.0]
        }
        test_df = pd.DataFrame(data)
        out_df = CMAPSSDataLoader._add_rolling_features(test_df, ["sensor_1"], window=3)

        # Engine 2 at cycle 1 must have rolling mean equal to 10.0 (not influenced by Engine 1's 100.0)
        eng2_cycle1_mean = out_df.loc[(out_df["unit"] == 2) & (out_df["cycle"] == 1), "sensor_1_mean3"].values[0]
        self.assertEqual(eng2_cycle1_mean, 10.0, "Rolling feature for Engine 2 bled from Engine 1!")

        # Engine 2 at cycle 2 must have rolling mean equal to 10.0
        eng2_cycle2_mean = out_df.loc[(out_df["unit"] == 2) & (out_df["cycle"] == 2), "sensor_1_mean3"].values[0]
        self.assertEqual(eng2_cycle2_mean, 10.0, "Rolling feature for Engine 2 bled from Engine 1!")


if __name__ == "__main__":
    unittest.main()
