"""Unit tests for configuration selection and deterministic tie-breaking.

Verifies:
- Lower mean selection score wins.
- Tie (< 1e-6) resolved by worst-seed RMSE.
- Tie resolved by GBR complexity (fewer leaf nodes, smaller l2, smaller lr).
- Tie resolved by LSTM complexity (smaller hidden size, smaller lr).
- Tie resolved by lexicographic config ID.
- Rejection of missing seed (e.g. only 2026).
- Rejection of extra seed (e.g. 2026, 2027, 2028).
- Rejection of non-finite metrics.
"""

import pytest

from intellitwin.models.metrics import ModelEvaluationMetrics
from intellitwin.models.selection import (
    evaluate_candidate,
    select_best_configuration,
)


def _make_metrics(
    rmse: float, mae: float = 10.0, capped_rmse: float = 15.0
) -> ModelEvaluationMetrics:
    return ModelEvaluationMetrics(
        uncapped_rmse=rmse,
        uncapped_mae=mae,
        capped_rmse=capped_rmse,
        engine_count=26,
        window_count=500,
    )


def test_lower_mean_selection_score_wins() -> None:
    """Candidate with lower mean uncapped RMSE across seeds 2026 and 2027 wins."""
    # Candidate A: 2026=20.0, 2027=22.0 -> mean = 21.0
    # Candidate B: 2026=19.0, 2027=21.0 -> mean = 20.0 (Winner)
    c_a = evaluate_candidate(
        config_id="cfg_a",
        hyperparameters={"learning_rate": 0.05},
        seed_metrics={2026: _make_metrics(20.0), 2027: _make_metrics(22.0)},
    )
    c_b = evaluate_candidate(
        config_id="cfg_b",
        hyperparameters={"learning_rate": 0.10},
        seed_metrics={2026: _make_metrics(19.0), 2027: _make_metrics(21.0)},
    )

    outcome = select_best_configuration([c_a, c_b], model_family="GBR")
    assert outcome.selected_config_id == "cfg_b"
    assert outcome.selection_score == 20.0
    assert not outcome.tie_detected


def test_tie_broken_by_worst_seed_rmse() -> None:
    """When mean scores are tied within 1e-6, lower worst-seed RMSE wins."""
    # Candidate A: 2026=20.0, 2027=20.0 -> mean=20.0, worst=20.0 (Winner)
    # Candidate B: 2026=18.0, 2027=22.0 -> mean=20.0, worst=22.0
    c_a = evaluate_candidate(
        config_id="cfg_a",
        hyperparameters={"learning_rate": 0.05, "max_leaf_nodes": 31, "l2_regularization": 1.0},
        seed_metrics={2026: _make_metrics(20.0), 2027: _make_metrics(20.0)},
    )
    c_b = evaluate_candidate(
        config_id="cfg_b",
        hyperparameters={"learning_rate": 0.05, "max_leaf_nodes": 15, "l2_regularization": 0.0},
        seed_metrics={2026: _make_metrics(18.0), 2027: _make_metrics(22.0)},
    )

    outcome = select_best_configuration([c_a, c_b], model_family="GBR")
    assert outcome.selected_config_id == "cfg_a"
    assert outcome.tie_detected
    assert outcome.tie_break_rule_used == "worst_seed_rmse"


def test_tie_broken_by_gbr_complexity() -> None:
    """When mean and worst-seed RMSE tie, GBR complexity order is applied."""
    # 1. Fewer max_leaf_nodes
    c_15 = evaluate_candidate(
        config_id="cfg_leaf15",
        hyperparameters={"max_leaf_nodes": 15, "l2_regularization": 1.0, "learning_rate": 0.10},
        seed_metrics={2026: _make_metrics(20.0), 2027: _make_metrics(20.0)},
    )
    c_31 = evaluate_candidate(
        config_id="cfg_leaf31",
        hyperparameters={"max_leaf_nodes": 31, "l2_regularization": 0.0, "learning_rate": 0.05},
        seed_metrics={2026: _make_metrics(20.0), 2027: _make_metrics(20.0)},
    )
    out1 = select_best_configuration([c_31, c_15], model_family="GBR")
    assert out1.selected_config_id == "cfg_leaf15"
    assert out1.tie_break_rule_used == "complexity"

    # 2. Smaller l2_regularization
    c_l2_0 = evaluate_candidate(
        config_id="cfg_l2_0",
        hyperparameters={"max_leaf_nodes": 15, "l2_regularization": 0.0, "learning_rate": 0.10},
        seed_metrics={2026: _make_metrics(20.0), 2027: _make_metrics(20.0)},
    )
    c_l2_1 = evaluate_candidate(
        config_id="cfg_l2_1",
        hyperparameters={"max_leaf_nodes": 15, "l2_regularization": 1.0, "learning_rate": 0.05},
        seed_metrics={2026: _make_metrics(20.0), 2027: _make_metrics(20.0)},
    )
    out2 = select_best_configuration([c_l2_1, c_l2_0], model_family="GBR")
    assert out2.selected_config_id == "cfg_l2_0"
    assert out2.tie_break_rule_used == "complexity"

    # 3. Smaller learning_rate
    c_lr005 = evaluate_candidate(
        config_id="cfg_lr005",
        hyperparameters={"max_leaf_nodes": 15, "l2_regularization": 0.0, "learning_rate": 0.05},
        seed_metrics={2026: _make_metrics(20.0), 2027: _make_metrics(20.0)},
    )
    c_lr010 = evaluate_candidate(
        config_id="cfg_lr010",
        hyperparameters={"max_leaf_nodes": 15, "l2_regularization": 0.0, "learning_rate": 0.10},
        seed_metrics={2026: _make_metrics(20.0), 2027: _make_metrics(20.0)},
    )
    out3 = select_best_configuration([c_lr010, c_lr005], model_family="GBR")
    assert out3.selected_config_id == "cfg_lr005"
    assert out3.tie_break_rule_used == "complexity"


def test_tie_broken_by_lstm_complexity() -> None:
    """When mean and worst-seed RMSE tie, LSTM complexity order is applied."""
    # 1. Smaller hidden_size
    c_h32 = evaluate_candidate(
        config_id="lstm_h32",
        hyperparameters={"hidden_size": 32, "learning_rate": 0.001},
        seed_metrics={2026: _make_metrics(20.0), 2027: _make_metrics(20.0)},
    )
    c_h64 = evaluate_candidate(
        config_id="lstm_h64",
        hyperparameters={"hidden_size": 64, "learning_rate": 0.0003},
        seed_metrics={2026: _make_metrics(20.0), 2027: _make_metrics(20.0)},
    )
    out1 = select_best_configuration([c_h64, c_h32], model_family="LSTM")
    assert out1.selected_config_id == "lstm_h32"
    assert out1.tie_break_rule_used == "complexity"

    # 2. Smaller learning_rate
    c_lr0003 = evaluate_candidate(
        config_id="lstm_lr0003",
        hyperparameters={"hidden_size": 32, "learning_rate": 0.0003},
        seed_metrics={2026: _make_metrics(20.0), 2027: _make_metrics(20.0)},
    )
    c_lr0010 = evaluate_candidate(
        config_id="lstm_lr0010",
        hyperparameters={"hidden_size": 32, "learning_rate": 0.001},
        seed_metrics={2026: _make_metrics(20.0), 2027: _make_metrics(20.0)},
    )
    out2 = select_best_configuration([c_lr0010, c_lr0003], model_family="LSTM")
    assert out2.selected_config_id == "lstm_lr0003"
    assert out2.tie_break_rule_used == "complexity"


def test_final_tie_break_lexicographic() -> None:
    """When all metrics and hyperparameters tie, lexicographical config_id wins."""
    c_a = evaluate_candidate(
        config_id="cfg_alpha",
        hyperparameters={"hidden_size": 32, "learning_rate": 0.0003},
        seed_metrics={2026: _make_metrics(20.0), 2027: _make_metrics(20.0)},
    )
    c_b = evaluate_candidate(
        config_id="cfg_beta",
        hyperparameters={"hidden_size": 32, "learning_rate": 0.0003},
        seed_metrics={2026: _make_metrics(20.0), 2027: _make_metrics(20.0)},
    )
    out = select_best_configuration([c_b, c_a], model_family="LSTM")
    assert out.selected_config_id == "cfg_alpha"
    assert out.tie_break_rule_used == "lexicographical"


def test_selection_rejects_missing_or_extra_seeds() -> None:
    """Only exactly seeds 2026 and 2027 are accepted."""
    # Missing seed 2027
    with pytest.raises(ValueError, match="must contain exactly seeds"):
        evaluate_candidate(
            config_id="cfg_incomplete",
            hyperparameters={},
            seed_metrics={2026: _make_metrics(20.0)},
        )

    # Extra seed 2028
    with pytest.raises(ValueError, match="must contain exactly seeds"):
        evaluate_candidate(
            config_id="cfg_extra",
            hyperparameters={},
            seed_metrics={
                2026: _make_metrics(20.0),
                2027: _make_metrics(20.0),
                2028: _make_metrics(20.0),
            },
        )


def test_selection_rejects_non_finite_metric() -> None:
    """Non-finite metrics are rejected."""
    with pytest.raises(ValueError, match="non-finite metric"):
        evaluate_candidate(
            config_id="cfg_nan",
            hyperparameters={},
            seed_metrics={
                2026: _make_metrics(float("nan")),
                2027: _make_metrics(20.0),
            },
        )
