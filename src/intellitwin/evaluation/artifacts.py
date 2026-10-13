"""Output schemas, file contracts, and artifact serialization for confirmatory evaluation."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Final

import numpy as np

# Frozen Confirmatory Output Filenames
OUTPUT_POINT_PREDICTIONS: Final[str] = "point_predictions.csv"
OUTPUT_INTERVAL_PREDICTIONS: Final[str] = "interval_predictions.csv"
OUTPUT_DECISION_TRACES: Final[str] = "decision_traces.csv"
OUTPUT_ENGINE_SEED_OUTCOMES: Final[str] = "engine_seed_outcomes.csv"
OUTPUT_ENGINE_METRICS: Final[str] = "engine_metrics.csv"
OUTPUT_SUBGROUP_METRICS: Final[str] = "subgroup_metrics.csv"
OUTPUT_CELL_SUMMARY: Final[str] = "cell_summary.csv"
OUTPUT_CONTRAST_INTERVALS: Final[str] = "contrast_intervals.csv"
OUTPUT_RQ_COMPONENT_DECISIONS: Final[str] = "rq_component_decisions.csv"
OUTPUT_RQ_DECISIONS: Final[str] = "rq_decisions.json"
OUTPUT_SENSITIVITY_SUMMARY: Final[str] = "sensitivity_summary.csv"
OUTPUT_EXECUTION_MANIFEST: Final[str] = "execution_manifest.json"
OUTPUT_AUDIT_REPORT: Final[str] = "audit_report.json"

ALL_CONFIRMATORY_OUTPUT_FILES: Final[tuple[str, ...]] = (
    OUTPUT_POINT_PREDICTIONS,
    OUTPUT_INTERVAL_PREDICTIONS,
    OUTPUT_DECISION_TRACES,
    OUTPUT_ENGINE_SEED_OUTCOMES,
    OUTPUT_ENGINE_METRICS,
    OUTPUT_SUBGROUP_METRICS,
    OUTPUT_CELL_SUMMARY,
    OUTPUT_CONTRAST_INTERVALS,
    OUTPUT_RQ_COMPONENT_DECISIONS,
    OUTPUT_RQ_DECISIONS,
    OUTPUT_SENSITIVITY_SUMMARY,
    OUTPUT_EXECUTION_MANIFEST,
    OUTPUT_AUDIT_REPORT,
)

# Contract Column Schemas
SCHEMA_POINT_PREDICTIONS: Final[tuple[str, ...]] = (
    "dataset",
    "model_family",
    "seed",
    "unit",
    "endpoint_cycle",
    "prediction",
    "rul_true",
    "rul_target",
    "regime",
    "lifecycle_stage",
)

SCHEMA_INTERVAL_PREDICTIONS: Final[tuple[str, ...]] = (
    "dataset",
    "model_family",
    "seed",
    "method_id",
    "nominal_coverage",
    "unit",
    "endpoint_cycle",
    "prediction",
    "lower_bound",
    "upper_bound",
    "covered",
    "interval_width",
    "interval_score",
    "fallback_used",
    "regime",
    "lifecycle_stage",
)

SCHEMA_DECISION_TRACES: Final[tuple[str, ...]] = (
    "dataset",
    "model_family",
    "seed",
    "method_or_control_id",
    "nominal_coverage",
    "unit",
    "cycle",
    "action",
)

SCHEMA_ENGINE_SEED_OUTCOMES: Final[tuple[str, ...]] = (
    "dataset",
    "model_family",
    "seed",
    "method_or_control_id",
    "nominal_coverage",
    "scenario_id",
    "unit",
    "terminal_event",
    "intervention_cycle",
    "failed",
    "pm",
    "wasted_rul",
    "total_cost",
    "is_cost_inefficient_early_pm",
)

SCHEMA_ENGINE_METRICS: Final[tuple[str, ...]] = (
    "dataset",
    "model_family",
    "seed",
    "method_or_control_id",
    "nominal_coverage",
    "scenario_id",
    "unit",
    "coverage",
    "mpiw",
    "mean_interval_score",
    "rmse",
    "total_cost",
    "failed",
    "pm",
    "wasted_rul",
)

SCHEMA_SUBGROUP_METRICS: Final[tuple[str, ...]] = (
    "dataset",
    "model_family",
    "method_id",
    "nominal_coverage",
    "subgroup_family",
    "subgroup_id",
    "engine_count",
    "coverage",
    "coverage_abs_error",
    "is_eligible",
)

SCHEMA_CELL_SUMMARY: Final[tuple[str, ...]] = (
    "dataset",
    "model_family",
    "method_or_control_id",
    "nominal_coverage",
    "scenario_id",
    "mean_cost",
    "failure_rate",
    "pm_rate",
    "mean_wasted_rul",
    "fleet_early_pm_rate",
    "pm_only_early_pm_rate",
    "marginal_coverage",
    "marginal_coverage_abs_error",
    "worst_regime_error",
    "worst_stage_error",
    "mpiw",
    "interval_score",
)

SCHEMA_CONTRAST_INTERVALS: Final[tuple[str, ...]] = (
    "rq_id",
    "contrast_name",
    "dataset",
    "model_family",
    "comparator_id",
    "metric_name",
    "estimate",
    "ci_lower",
    "ci_upper",
    "confidence_level",
    "bound_type",
    "affected_replicates",
)

SCHEMA_RQ_COMPONENT_DECISIONS: Final[tuple[str, ...]] = (
    "rq_id",
    "component_id",
    "component_description",
    "dataset",
    "model_family",
    "comparator_id",
    "metric_name",
    "ci_lower",
    "ci_upper",
    "margin",
    "test_direction",
    "decision",
)


def save_bootstrap_draws_npz(
    path: Path | str,
    draws: np.ndarray,
    dataset: str,
    column_order: Sequence[int],
    replicate_count: int,
) -> None:
    """Save bootstrap engine draws as a structured NumPy archive without pickle.

    Loads safely with allow_pickle=False.
    """
    p = Path(path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    metadata_json = json.dumps(
        {
            "dataset": dataset,
            "n_replicates": replicate_count,
            "engine_order": list(column_order),
        }
    )
    np.savez_compressed(
        p,
        draws=draws.astype(np.int64),
        metadata=np.array(metadata_json, dtype=str),
    )


def load_bootstrap_draws_npz(path: Path | str) -> tuple[np.ndarray, dict[str, Any]]:
    """Load bootstrap draws without pickle."""
    p = Path(path).resolve()
    with np.load(p, allow_pickle=False) as data:
        draws = data["draws"]
        meta_str = str(data["metadata"])
        metadata = json.loads(meta_str)
    return draws, metadata
