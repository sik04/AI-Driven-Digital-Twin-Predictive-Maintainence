"""Maintenance cost model calculations and configuration."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MaintenanceCostConfig:
    """Configuration for simulated maintenance cost structure.

    Validation Rules:
    - preventive_cost > 0
    - failure_cost > preventive_cost
    - wasted_rul_cost_per_cycle >= 0
    """

    preventive_cost: float
    failure_cost: float
    wasted_rul_cost_per_cycle: float

    def __post_init__(self) -> None:
        """Validate cost configuration parameters."""
        if self.preventive_cost <= 0:
            raise ValueError(f"preventive_cost must be > 0, got {self.preventive_cost}")
        if self.failure_cost <= self.preventive_cost:
            msg = (
                f"failure_cost ({self.failure_cost}) must be > "
                f"preventive_cost ({self.preventive_cost})"
            )
            raise ValueError(msg)
        if self.wasted_rul_cost_per_cycle < 0:
            raise ValueError(
                f"wasted_rul_cost_per_cycle must be >= 0, got {self.wasted_rul_cost_per_cycle}"
            )


def preventive_maintenance_cost(config: MaintenanceCostConfig, wasted_rul: float) -> float:
    """Compute cost for preventive maintenance intervention.

    Formula: C_PM + C_WASTE * wasted_rul
    """
    if wasted_rul < 0:
        raise ValueError(f"wasted_rul must be >= 0, got {wasted_rul}")
    return config.preventive_cost + config.wasted_rul_cost_per_cycle * wasted_rul


def failure_maintenance_cost(config: MaintenanceCostConfig) -> float:
    """Compute cost for unmitigated functional failure.

    Formula: C_FAIL
    """
    return config.failure_cost
