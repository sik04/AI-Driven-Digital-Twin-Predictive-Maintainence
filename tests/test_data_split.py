"""
Tests for Step 4 Authoritative Engine-Level Data Splitting Protocol.
Verifies:
- Test A: Zero unit overlap between train, validation, and test partitions.
- Test D: Strict determinism and reproducibility under identical random seed.
- Test E: Exact consistency between persisted split artifacts and loaded data.
- Single authoritative split verification across tabular and sequential pipelines.
"""

import os
import json
import unittest
import numpy as np

from intellitwin.data_loader import CMAPSSDataLoader
from intellitwin.config import get_default_data_config


class TestDataSplittingProtocol(unittest.TestCase):
    """Test suite for engine-level splitting integrity and non-overlap guarantees."""

    @classmethod
    def setUpClass(cls):
        cls.loader = CMAPSSDataLoader(data_dir="data/cmapss", sub_dataset="FD001", random_state=42, val_ratio=0.20)
        cls.train_df, cls.test_df, cls.feature_cols = cls.loader.prepare_data(save_artifact=True)

    def test_a_no_unit_overlap(self):
        """Test A: Verify pairwise disjointness of train, validation, and test engine IDs."""
        train_u = set(self.loader.train_units)
        val_u = set(self.loader.val_units)
        test_u = set(self.loader.test_units)

        # 1. Train and validation must be strictly disjoint subsets of the training pool
        self.assertTrue(train_u.isdisjoint(val_u), "Data leakage: train_units and val_units share engine IDs!")
        self.assertEqual(len(train_u & val_u), 0)

        # 2. Total units in training pool must equal 100 for FD001
        all_train_pool = train_u | val_u
        self.assertEqual(len(all_train_pool), 100)
        self.assertEqual(all_train_pool, set(range(1, 101)))

        # 3. Check exact split counts: 80% train (80 engines), 20% val (20 engines)
        self.assertEqual(len(train_u), 80)
        self.assertEqual(len(val_u), 20)

        # 4. Test engines in FD001 test set must have 100 independent units
        self.assertEqual(len(test_u), 100)

    def test_d_deterministic_split(self):
        """Test D: Running split twice with same seed yields identical engine IDs."""
        loader_1 = CMAPSSDataLoader(random_state=42, val_ratio=0.20)
        t1, v1, te1 = loader_1.get_engine_split()

        loader_2 = CMAPSSDataLoader(random_state=42, val_ratio=0.20)
        t2, v2, te2 = loader_2.get_engine_split()

        self.assertEqual(t1, t2, "Non-deterministic split: identical seed produced different train_units!")
        self.assertEqual(v1, v2, "Non-deterministic split: identical seed produced different val_units!")
        self.assertEqual(te1, te2, "Non-deterministic split: identical seed produced different test_units!")

        # Different seed must produce a different partition
        loader_3 = CMAPSSDataLoader(random_state=999, val_ratio=0.20)
        t3, v3, _ = loader_3.get_engine_split()
        self.assertNotEqual(t1, t3, "Random seed has no effect on unit splitting!")
        self.assertNotEqual(v1, v3, "Random seed has no effect on unit splitting!")

    def test_e_split_artifact_reproducibility(self):
        """Test E: Persisted split artifact matches loaded pipeline state exactly."""
        cfg = get_default_data_config()
        artifact_path = cfg.split_artifact_path
        self.assertTrue(os.path.exists(artifact_path), f"Missing split artifact at {artifact_path}")

        with open(artifact_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        self.assertEqual(meta["dataset"], "NASA C-MAPSS FD001")
        self.assertEqual(meta["split_strategy"], "engine_level")
        self.assertEqual(meta["random_seed"], 42)
        self.assertEqual(meta["validation_fraction"], 0.20)
        self.assertEqual(meta["train_unit_count"], 80)
        self.assertEqual(meta["val_unit_count"], 20)
        self.assertEqual(meta["test_unit_count"], 100)
        self.assertEqual(meta["train_units"], self.loader.train_units)
        self.assertEqual(meta["validation_units"], self.loader.val_units)
        self.assertEqual(meta["test_units"], self.loader.test_units)

    def test_single_authoritative_split_across_data_formats(self):
        """Verify tabular and sequential formats consume the identical engine split."""
        tab_data = self.loader.get_tabular_data()
        seq_data = self.loader.get_sequential_data()

        # Tabular units
        tab_train_units = set(np.unique(tab_data["train_unit_ids"]))
        tab_val_units = set(np.unique(tab_data["val_unit_ids"]))

        # Sequential units
        seq_train_units = set(np.unique(seq_data["train_seq_units"]))
        seq_val_units = set(np.unique(seq_data["val_seq_units"]))

        self.assertEqual(tab_train_units, set(self.loader.train_units))
        self.assertEqual(tab_val_units, set(self.loader.val_units))
        self.assertEqual(seq_train_units, set(self.loader.train_units))
        self.assertEqual(seq_val_units, set(self.loader.val_units))


if __name__ == "__main__":
    unittest.main()
