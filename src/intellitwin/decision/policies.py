"""Maintenance decision policies and scenario loading for Step 8."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import yaml

from intellitwin.simulator.costs import MaintenanceCostConfig
from intellitwin.simulator.types import MaintenanceAction, PredictionState


class UniqueKeySafeLoader(yaml.SafeLoader):
    """YAML SafeLoader that strictly rejects duplicate mapping keys."""


def _construct_mapping(
    loader: UniqueKeySafeLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        val = loader.construct_object(value_node, deep=deep)
        if key in mapping:
            raise ValueError(f"Duplicate YAML key detected: {key!r} in {node.start_mark}")
        mapping[key] = val
    return mapping


UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


def lower_bound_one_cycle_policy(state: PredictionState) -> MaintenanceAction:
    """Benchmark maintenance policy based on interval lower bound.

    Decision Rule:
        MAINTAIN_NOW if lower_rul <= 1.0
        CONTINUE otherwise

    Parameters
    ----------
    state : PredictionState
        Current decision epoch observation. Reads strictly state.lower_rul.
        Never inspects true RUL, failure cycle, lifecycle stage, or future predictions.

    Returns
    -------
    MaintenanceAction
        MAINTAIN_NOW or CONTINUE.
    """
    if math.isnan(state.lower_rul) or math.isinf(state.lower_rul):
        raise ValueError(f"Invalid non-finite lower_rul in policy state: {state.lower_rul}")

    if state.lower_rul <= 1.0:
        return MaintenanceAction.MAINTAIN_NOW
    return MaintenanceAction.CONTINUE


def load_primary_reference_cost(
    yaml_path: Path | str = "research/research_design/maintenance_cost_scenarios.yaml",
) -> MaintenanceCostConfig:
    """Load and verify frozen primary_reference maintenance cost configuration from YAML.

    Enforces safe YAML loading, rejects duplicate keys, and asserts:
        preventive_cost == 1.0
        failure_cost == 5.0
        wasted_rul_cost_per_cycle == 0.20

    Parameters
    ----------
    yaml_path : Path or str
        Path to maintenance_cost_scenarios.yaml.

    Returns
    -------
    MaintenanceCostConfig
        Validated frozen cost configuration.
    """
    p = Path(yaml_path)
    if not p.is_file():
        raise FileNotFoundError(f"Maintenance cost scenarios YAML not found at: {p}")

    with open(p, encoding="utf-8") as f:
        data = yaml.load(f, Loader=UniqueKeySafeLoader)

    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping at root of {p}, got {type(data).__name__}")

    scenarios = data.get("scenarios")
    if not isinstance(scenarios, dict):
        raise ValueError(f"Missing 'scenarios' mapping in {p}")

    prim = scenarios.get("primary_reference")
    if not isinstance(prim, dict):
        raise ValueError(f"Missing 'primary_reference' scenario in {p}")

    c_pm = float(prim.get("preventive_cost", 0.0))
    c_fail = float(prim.get("failure_cost", 0.0))
    c_waste = float(prim.get("wasted_rul_cost_per_cycle", 0.0))

    if abs(c_pm - 1.0) > 1e-9:
        raise ValueError(f"Expected primary_reference preventive_cost == 1.0, got {c_pm}")
    if abs(c_fail - 5.0) > 1e-9:
        raise ValueError(f"Expected primary_reference failure_cost == 5.0, got {c_fail}")
    if abs(c_waste - 0.20) > 1e-9:
        raise ValueError(
            f"Expected primary_reference wasted_rul_cost_per_cycle == 0.20, got {c_waste}"
        )

    return MaintenanceCostConfig(
        preventive_cost=c_pm,
        failure_cost=c_fail,
        wasted_rul_cost_per_cycle=c_waste,
    )
