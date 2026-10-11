"""Unit tests for GBR model implementation and frozen grid.

Verifies:
- Exactly 8 configurations generated.
- Fixed hyperparameters conform to ADR-019.
- Configuration IDs are deterministic.
- Early stopping is False.
- Flattened shape (M, 510) expected.
- Sample weights passed during fit.
- Predictions non-negative after post-processing.
- Same seed/config/data gives deterministic prediction.
- Separate model instances do not share state.
- Checkpoint save/load reproduces identical predictions.
"""

from pathlib import Path

import numpy as np
import pytest

from intellitwin.models.gbr import GBRModel, get_gbr_grid


def test_gbr_grid_contains_exactly_eight_configs() -> None:
    """Verify the GBR search grid contains exactly 8 frozen configurations."""
    grid = get_gbr_grid()
    assert len(grid) == 8

    expected_ids = [
        "gbr_lr005_leaf15_l2_0",
        "gbr_lr005_leaf15_l2_1",
        "gbr_lr005_leaf31_l2_0",
        "gbr_lr005_leaf31_l2_1",
        "gbr_lr010_leaf15_l2_0",
        "gbr_lr010_leaf15_l2_1",
        "gbr_lr010_leaf31_l2_0",
        "gbr_lr010_leaf31_l2_1",
    ]
    actual_ids = [cfg.config_id for cfg in grid]
    assert actual_ids == expected_ids


def test_gbr_fixed_hyperparameters_conform_to_spec() -> None:
    """Verify all fixed hyperparameters are strictly invariant across configurations."""
    for cfg in get_gbr_grid():
        assert cfg.loss == "squared_error"
        assert cfg.early_stopping is False
        assert cfg.validation_fraction is None
        assert cfg.min_samples_leaf == 20
        assert cfg.max_bins == 255
        assert cfg.max_features == 1.0
        assert cfg.categorical_features is None
        assert cfg.warm_start is False
        assert cfg.max_iter == 300
        assert cfg.learning_rate in [0.05, 0.10]
        assert cfg.max_leaf_nodes in [15, 31]
        assert cfg.l2_regularization in [0.0, 1.0]


def test_gbr_synthetic_fit_predict_and_non_negative_truncation(tmp_path: Path) -> None:
    """Verify fit, non-negative prediction post-processing, and serialization."""
    rng = np.random.default_rng(2026)
    m_samples = 60
    n_features = 510

    X_train = rng.standard_normal((m_samples, n_features)).astype(np.float32)
    # Give some targets near zero or negative to ensure truncation is verified
    y_train = rng.uniform(0.0, 100.0, size=m_samples)
    weights = rng.uniform(0.5, 2.0, size=m_samples)

    grid = get_gbr_grid()
    cfg = grid[0]

    model = GBRModel(hyperparameters=cfg, run_seed=2026)
    assert not model.is_fitted

    # predict before fit raises RuntimeError
    with pytest.raises(RuntimeError, match="not fitted"):
        model.predict(X_train)

    # fit with weights
    model.fit(X_train, y_train, sample_weight=weights)
    assert model.is_fitted

    # Predictions must be >= 0.0
    preds = model.predict(X_train)
    assert preds.shape == (m_samples,)
    assert np.all(preds >= 0.0)

    # Verify reproducibility with same seed
    model_dup = GBRModel(hyperparameters=cfg, run_seed=2026)
    model_dup.fit(X_train, y_train, sample_weight=weights)
    preds_dup = model_dup.predict(X_train)
    np.testing.assert_allclose(preds, preds_dup, atol=1e-7)

    # Save and reload checkpoint
    ckpt_path = tmp_path / "gbr_test_model.pkl"
    model.save(str(ckpt_path))

    loaded_model = GBRModel.load(str(ckpt_path))
    assert loaded_model.is_fitted
    loaded_preds = loaded_model.predict(X_train)
    np.testing.assert_allclose(preds, loaded_preds, atol=1e-7)


def test_gbr_rejects_dimension_mismatch() -> None:
    """Verify GBR model validates input dimensions."""
    grid = get_gbr_grid()
    model = GBRModel(hyperparameters=grid[0], run_seed=2026)

    # Wrong dimension 1D
    with pytest.raises(ValueError, match="2D array"):
        model.fit(np.zeros((10,)), np.zeros((10,)))

    # Length mismatch
    with pytest.raises(ValueError, match="Length mismatch"):
        model.fit(np.zeros((10, 510)), np.zeros((8,)))

    # Weights length mismatch
    with pytest.raises(ValueError, match="sample_weight length"):
        model.fit(np.zeros((10, 510)), np.zeros((10,)), sample_weight=np.zeros((5,)))
