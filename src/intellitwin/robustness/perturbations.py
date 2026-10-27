"""Perturbation generators and corrupted feature-stream builders for Experiment B stress tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from intellitwin.data.schema import SENSOR_COLUMNS
from intellitwin.data.windowing import WindowDataset, construct_windows
from intellitwin.evaluation.bootstrap import DATASET_NUMBERS

PERTURBATION_FAMILY_GAUSSIAN_NOISE: int = 1
PERTURBATION_FAMILY_DROPOUT: int = 2


@dataclass(frozen=True)
class StressCondition:
    """Specification of an engineering stress probe."""

    condition_id: str
    condition_type: str  # "clean", "sensor_gaussian_noise", "sensor_dropout", "setting1_bias"
    param_value: float | None
    replicates: int
    is_deterministic: bool


ALL_STRESS_CONDITIONS: tuple[StressCondition, ...] = (
    StressCondition("clean", "clean", None, 1, True),
    StressCondition("noise_std_005", "sensor_gaussian_noise", 0.05, 3, False),
    StressCondition("noise_std_010", "sensor_gaussian_noise", 0.10, 3, False),
    StressCondition("noise_std_020", "sensor_gaussian_noise", 0.20, 3, False),
    StressCondition("dropout_prob_005", "sensor_dropout", 0.05, 3, False),
    StressCondition("dropout_prob_010", "sensor_dropout", 0.10, 3, False),
    StressCondition("setting1_bias_plus_020", "setting1_bias", 0.20, 1, True),
    StressCondition("setting1_bias_minus_020", "setting1_bias", -0.20, 1, True),
)

STRESS_CONDITION_BY_ID: dict[str, StressCondition] = {
    c.condition_id: c for c in ALL_STRESS_CONDITIONS
}


def generate_engine_noise_array(
    dataset: str,
    engine_id: int,
    replicate_id: int,
    n_cycles: int,
) -> np.ndarray[Any, Any]:
    """Generate deterministic standard normal draws for the 14 retained sensor columns.

    PRNG: PCG64 with SeedSequence([2026, 8, dataset_number, engine_id, 1, replicate_id]).
    Returns array of shape (n_cycles, 14).
    """
    ds_num = DATASET_NUMBERS[dataset]
    seq = np.random.SeedSequence(
        [2026, 8, ds_num, engine_id, PERTURBATION_FAMILY_GAUSSIAN_NOISE, replicate_id]
    )
    rng = np.random.Generator(np.random.PCG64(seq))
    z = rng.standard_normal(size=(n_cycles, len(SENSOR_COLUMNS)))
    return np.asarray(z, dtype=np.float64)


def generate_engine_dropout_uniforms(
    dataset: str,
    engine_id: int,
    replicate_id: int,
    n_cycles: int,
) -> np.ndarray[Any, Any]:
    """Generate deterministic uniform draws for the 14 retained sensor columns.

    PRNG: PCG64 with SeedSequence([2026, 8, dataset_number, engine_id, 2, replicate_id]).
    Returns array of shape (n_cycles, 14) with values in [0, 1).
    """
    ds_num = DATASET_NUMBERS[dataset]
    seq = np.random.SeedSequence(
        [2026, 8, ds_num, engine_id, PERTURBATION_FAMILY_DROPOUT, replicate_id]
    )
    rng = np.random.Generator(np.random.PCG64(seq))
    u = rng.uniform(0.0, 1.0, size=(n_cycles, len(SENSOR_COLUMNS)))
    return np.asarray(u, dtype=np.float64)


def apply_stream_perturbation(
    df_preprocessed: pd.DataFrame,
    dataset: str,
    condition: StressCondition,
    replicate_id: int = 0,
) -> pd.DataFrame:
    """Apply engineering stress probe to the preprocessed feature stream before windowing.

    Rules:
    - Applied engine-by-engine in ascending cycle order.
    - Gaussian noise: scales standard normal draws by param_value and adds to SENSOR_COLUMNS only.
    - Sensor dropout: masks sensors where uniform < param_value. Missing values are imputed
      using forward fill (last observed value of that sensor in the same engine). If missing
      at cycle 1, 0.0 is used.
    - Setting bias: adds param_value to normalized setting1 only.
    - Clean: returns exact unperturbed copy.
    - Labels, failure cycles, engine IDs, cycle numbers, and clean regime labels remain unchanged.
    """
    df_perturbed = df_preprocessed.copy()

    if condition.condition_type == "clean":
        return df_perturbed

    if condition.condition_type == "setting1_bias":
        bias = float(condition.param_value if condition.param_value is not None else 0.0)
        df_perturbed["setting1"] = df_perturbed["setting1"] + bias
        return df_perturbed

    # Noise or dropout applies engine-by-engine
    sensor_list = list(SENSOR_COLUMNS)
    values_matrix = df_perturbed[sensor_list].to_numpy(dtype=np.float64, copy=True)
    unit_arr = df_perturbed["unit"].to_numpy()
    cycle_arr = df_perturbed["cycle"].to_numpy()

    for unit in sorted(np.unique(unit_arr)):
        idx_order = np.flatnonzero(unit_arr == unit)
        sort_perm = np.argsort(cycle_arr[idx_order])
        sorted_indices = idx_order[sort_perm]
        n_cyc = len(sorted_indices)

        if condition.condition_type == "sensor_gaussian_noise":
            sigma = float(condition.param_value if condition.param_value is not None else 0.0)
            z = generate_engine_noise_array(
                dataset=dataset,
                engine_id=int(unit),
                replicate_id=replicate_id,
                n_cycles=n_cyc,
            )
            values_matrix[sorted_indices] += sigma * z

        elif condition.condition_type == "sensor_dropout":
            prob = float(condition.param_value if condition.param_value is not None else 0.0)
            u = generate_engine_dropout_uniforms(
                dataset=dataset,
                engine_id=int(unit),
                replicate_id=replicate_id,
                n_cycles=n_cyc,
            )
            dropout_mask = u < prob  # True where sensor is dropped
            eng_vals = values_matrix[sorted_indices]
            for j in range(len(sensor_list)):
                last_val = 0.0
                for c in range(n_cyc):
                    if dropout_mask[c, j]:
                        eng_vals[c, j] = last_val
                    else:
                        last_val = eng_vals[c, j]
            values_matrix[sorted_indices] = eng_vals
        else:
            raise ValueError(f"Unknown condition type: {condition.condition_type}")

    df_perturbed[sensor_list] = values_matrix
    return df_perturbed


def construct_perturbed_windows(
    df_preprocessed: pd.DataFrame,
    dataset: str,
    condition: StressCondition,
    replicate_id: int = 0,
) -> WindowDataset:
    """Construct causal overlapping windows from a perturbed feature stream."""
    df_perturbed = apply_stream_perturbation(
        df_preprocessed=df_preprocessed,
        dataset=dataset,
        condition=condition,
        replicate_id=replicate_id,
    )
    return construct_windows(df_perturbed)
