"""Configuration selection and deterministic tie-breaking for base predictors.

Implements the frozen Step 7.1 / ADR-019 model-selection procedure:
- Candidate configurations are evaluated across selection seeds [2026, 2027].
- Primary selection score: mean uncapped-RUL RMSE across seeds 2026 and 2027:
    selection_score(c) = (rmse_2026 + rmse_2027) / 2
- Deterministic tie-breaking when abs(score_a - score_b) < 1e-6:
    1. Lower worst-seed RMSE: min max(rmse_2026, rmse_2027)
    2. Lower complexity:
       - GBR: fewer max_leaf_nodes, then smaller l2_regularization, then smaller learning_rate
       - LSTM: smaller hidden_size, then smaller learning_rate
    3. Lexicographically smaller configuration ID.
"""

import functools
import math
from dataclasses import dataclass
from typing import Any

from intellitwin.models.metrics import ModelEvaluationMetrics

SELECTION_SEEDS: tuple[int, int] = (2026, 2027)
TIE_THRESHOLD: float = 1e-6


@dataclass(frozen=True)
class CandidateEvaluationResult:
    """Aggregated evaluation record for a candidate configuration across selection seeds."""

    config_id: str
    hyperparameters: dict[str, Any]
    seed_metrics: dict[int, ModelEvaluationMetrics]
    mean_selection_score: float
    worst_seed_rmse: float


@dataclass(frozen=True)
class SelectionOutcome:
    """Outcome of the frozen model-selection procedure."""

    selected_config_id: str
    selected_hyperparameters: dict[str, Any]
    selection_score: float
    selected_worst_seed_rmse: float
    tie_detected: bool
    tie_break_rule_used: str | None
    ranked_candidates: list[CandidateEvaluationResult]


def evaluate_candidate(
    config_id: str,
    hyperparameters: dict[str, Any],
    seed_metrics: dict[int, ModelEvaluationMetrics],
) -> CandidateEvaluationResult:
    """Validate seeds and calculate candidate selection score.

    Parameters
    ----------
    config_id : str
        Configuration identifier.
    hyperparameters : dict[str, Any]
        Configuration hyperparameters.
    seed_metrics : dict[int, ModelEvaluationMetrics]
        Mapping from seed to evaluation metrics. Must contain exactly seeds 2026 and 2027.

    Returns
    -------
    CandidateEvaluationResult
        Aggregated candidate result.
    """
    actual_seeds = sorted(seed_metrics.keys())
    expected_seeds = sorted(SELECTION_SEEDS)
    if actual_seeds != expected_seeds:
        raise ValueError(
            f"Candidate '{config_id}' must contain exactly seeds {expected_seeds}, "
            f"got {actual_seeds}."
        )

    for seed, m in seed_metrics.items():
        if not math.isfinite(m.uncapped_rmse) or not math.isfinite(m.uncapped_mae):
            raise ValueError(f"Candidate '{config_id}' has non-finite metric at seed {seed}: {m}")

    rmse_2026 = seed_metrics[2026].uncapped_rmse
    rmse_2027 = seed_metrics[2027].uncapped_rmse

    mean_score = (rmse_2026 + rmse_2027) / 2.0
    worst_rmse = max(rmse_2026, rmse_2027)

    return CandidateEvaluationResult(
        config_id=config_id,
        hyperparameters=dict(hyperparameters),
        seed_metrics=dict(seed_metrics),
        mean_selection_score=mean_score,
        worst_seed_rmse=worst_rmse,
    )


def _compare_candidates(
    a: CandidateEvaluationResult,
    b: CandidateEvaluationResult,
    model_family: str,
) -> int:
    """Compare two candidates according to frozen tie-breaking rules.

    Returns negative if a is preferred over b, positive if b is preferred over a, 0 if identical.
    """
    # 1. Primary selection score
    score_diff = a.mean_selection_score - b.mean_selection_score
    if abs(score_diff) >= TIE_THRESHOLD:
        return -1 if score_diff < 0 else 1

    # Tie detected: Rule 1 - Lower worst-seed RMSE
    worst_diff = a.worst_seed_rmse - b.worst_seed_rmse
    if abs(worst_diff) >= TIE_THRESHOLD:
        return -1 if worst_diff < 0 else 1

    # Rule 2 - Lower complexity
    fam = model_family.upper()
    if fam == "GBR":
        # Fewer max_leaf_nodes
        leaf_diff = int(a.hyperparameters.get("max_leaf_nodes", 0)) - int(
            b.hyperparameters.get("max_leaf_nodes", 0)
        )
        if leaf_diff != 0:
            return -1 if leaf_diff < 0 else 1

        # Smaller l2_regularization
        l2_diff = float(a.hyperparameters.get("l2_regularization", 0.0)) - float(
            b.hyperparameters.get("l2_regularization", 0.0)
        )
        if abs(l2_diff) > 1e-9:
            return -1 if l2_diff < 0 else 1

        # Smaller learning_rate
        lr_diff = float(a.hyperparameters.get("learning_rate", 0.0)) - float(
            b.hyperparameters.get("learning_rate", 0.0)
        )
        if abs(lr_diff) > 1e-9:
            return -1 if lr_diff < 0 else 1

    elif fam == "LSTM":
        # Smaller hidden_size
        h_diff = int(a.hyperparameters.get("hidden_size", 0)) - int(
            b.hyperparameters.get("hidden_size", 0)
        )
        if h_diff != 0:
            return -1 if h_diff < 0 else 1

        # Smaller learning_rate
        lr_diff = float(a.hyperparameters.get("learning_rate", 0.0)) - float(
            b.hyperparameters.get("learning_rate", 0.0)
        )
        if abs(lr_diff) > 1e-9:
            return -1 if lr_diff < 0 else 1

    # Rule 3 - Lexicographically smaller config_id
    if a.config_id != b.config_id:
        return -1 if a.config_id < b.config_id else 1

    return 0


def select_best_configuration(
    candidates: list[CandidateEvaluationResult],
    model_family: str,
) -> SelectionOutcome:
    """Select the winning configuration from evaluated candidates.

    Parameters
    ----------
    candidates : list[CandidateEvaluationResult]
        List of evaluated candidates.
    model_family : str
        Model family identifier ("GBR" or "LSTM").

    Returns
    -------
    SelectionOutcome
        Selected configuration, ranking, and tie-breaking details.
    """
    if not candidates:
        raise ValueError("Cannot select from empty candidate list.")

    fam = model_family.upper()
    if fam not in {"GBR", "LSTM"}:
        raise ValueError(f"Unknown model_family '{model_family}'. Expected 'GBR' or 'LSTM'.")

    # Sort candidates using frozen comparison
    def _cmp_wrapper(a: Any, b: Any) -> int:
        return _compare_candidates(a, b, fam)

    ranked = sorted(candidates, key=functools.cmp_to_key(_cmp_wrapper))

    winner = ranked[0]
    tie_detected = False
    tie_break_rule_used: str | None = None

    if len(ranked) > 1:
        runner_up = ranked[1]
        score_diff = abs(winner.mean_selection_score - runner_up.mean_selection_score)
        if score_diff < TIE_THRESHOLD:
            tie_detected = True
            worst_diff = abs(winner.worst_seed_rmse - runner_up.worst_seed_rmse)
            if worst_diff >= TIE_THRESHOLD:
                tie_break_rule_used = "worst_seed_rmse"
            else:
                # Check if complexity differs
                if fam == "GBR":
                    c_diff = (
                        winner.hyperparameters.get("max_leaf_nodes")
                        != runner_up.hyperparameters.get("max_leaf_nodes")
                        or winner.hyperparameters.get("l2_regularization")
                        != runner_up.hyperparameters.get("l2_regularization")
                        or winner.hyperparameters.get("learning_rate")
                        != runner_up.hyperparameters.get("learning_rate")
                    )
                else:  # LSTM
                    c_diff = winner.hyperparameters.get(
                        "hidden_size"
                    ) != runner_up.hyperparameters.get("hidden_size") or winner.hyperparameters.get(
                        "learning_rate"
                    ) != runner_up.hyperparameters.get("learning_rate")

                if c_diff:
                    tie_break_rule_used = "complexity"
                else:
                    tie_break_rule_used = "lexicographical"

    return SelectionOutcome(
        selected_config_id=winner.config_id,
        selected_hyperparameters=winner.hyperparameters,
        selection_score=winner.mean_selection_score,
        selected_worst_seed_rmse=winner.worst_seed_rmse,
        tie_detected=tie_detected,
        tie_break_rule_used=tie_break_rule_used,
        ranked_candidates=ranked,
    )
