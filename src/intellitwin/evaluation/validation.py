"""Trajectory validation, observability constraints, and strict anti-leakage checks."""

from __future__ import annotations

from collections.abc import Collection
from pathlib import Path
from typing import Any

import numpy as np

from intellitwin.evaluation.schema import VALID_REGIMES


class TrajectoryValidationError(ValueError):
    """Raised when an engine trajectory violates continuity or integrity constraints."""


class DataLeakageError(RuntimeError):
    """Raised when non-permitted partition data is accessed or requested."""


def normalize_regime_id(regime: Any) -> int:
    """Convert string or int regime to standard integer in {1..6}.

    Accepts 1..6, '1'..'6', 'C1'..'C6', 'c1'..'c6'.
    """
    if isinstance(regime, (int, np.integer)):
        val = int(regime)
    else:
        s = str(regime).strip().upper()
        if s.startswith("C"):
            s = s[1:]
        try:
            val = int(s)
        except ValueError as exc:
            raise TrajectoryValidationError(f"Invalid regime identifier: {regime}") from exc

    if val not in VALID_REGIMES:
        raise TrajectoryValidationError(f"Regime {val} not in legal regimes {VALID_REGIMES}")
    return val


def validate_trajectory(
    unit: int,
    cycles: np.ndarray | list[int],
    predictions: np.ndarray | list[float],
    regimes: np.ndarray | list[Any],
    terminal_cycle: int,
    lower_bounds: np.ndarray | list[float] | None = None,
    upper_bounds: np.ndarray | list[float] | None = None,
    rul_trues: np.ndarray | list[float] | None = None,
) -> None:
    """Validate that an engine trajectory satisfies complete chronological requirements.

    Requirements:
    - Terminal cycle T > 30.
    - Endpoints run strictly from cycle 30 through T with step 1.
    - No missing cycles, no duplicate cycles.
    - Predictions are finite and non-negative.
    - Regimes are legal (1..6).
    - If lower/upper bounds provided: 0 <= lower <= prediction <= upper.
    - If rul_true provided: rul_true == T - cycle.
    """
    if terminal_cycle <= 30:
        raise TrajectoryValidationError(f"Engine {unit} has terminal cycle {terminal_cycle} <= 30.")

    cyc_arr = np.asarray(cycles, dtype=int)
    n = len(cyc_arr)
    expected_cycles = np.arange(30, terminal_cycle + 1, dtype=int)

    if n != len(expected_cycles):
        raise TrajectoryValidationError(
            f"Engine {unit} has {n} endpoints; "
            f"expected {len(expected_cycles)} (cycles 30..{terminal_cycle})."
        )

    if not np.array_equal(cyc_arr, expected_cycles):
        raise TrajectoryValidationError(
            f"Engine {unit} cycles do not match contiguous 30..{terminal_cycle} sequence."
        )

    pred_arr = np.asarray(predictions, dtype=float)
    if len(pred_arr) != n:
        raise TrajectoryValidationError(
            f"Engine {unit} prediction count {len(pred_arr)} != cycle count {n}."
        )
    if not np.all(np.isfinite(pred_arr)):
        raise TrajectoryValidationError(f"Engine {unit} contains non-finite predictions.")
    if np.any(pred_arr < 0.0):
        raise TrajectoryValidationError(f"Engine {unit} contains negative predictions.")

    for r in regimes:
        normalize_regime_id(r)

    if lower_bounds is not None and upper_bounds is not None:
        low_arr = np.asarray(lower_bounds, dtype=float)
        upp_arr = np.asarray(upper_bounds, dtype=float)
        if len(low_arr) != n or len(upp_arr) != n:
            raise TrajectoryValidationError(
                f"Engine {unit} interval bound lengths do not match trajectory length."
            )
        if not np.all(np.isfinite(low_arr)) or not np.all(np.isfinite(upp_arr)):
            raise TrajectoryValidationError(f"Engine {unit} intervals contain non-finite values.")
        if np.any(low_arr < -1e-9):
            raise TrajectoryValidationError(f"Engine {unit} contains negative lower bounds.")
        if np.any(low_arr - pred_arr > 1e-6):
            raise TrajectoryValidationError(
                f"Engine {unit} has lower bound exceeding point prediction."
            )
        if np.any(upp_arr - pred_arr < -1e-6):
            raise TrajectoryValidationError(
                f"Engine {unit} has upper bound less than point prediction."
            )

    if rul_trues is not None:
        true_arr = np.asarray(rul_trues, dtype=float)
        expected_true = (terminal_cycle - cyc_arr).astype(float)
        if not np.allclose(true_arr, expected_true, atol=1e-5):
            raise TrajectoryValidationError(f"Engine {unit} true RUL does not match T - cycle.")


def assert_permitted_partition_only(
    actual_units: Collection[int],
    expected_units: Collection[int],
    forbidden_units: Collection[int] | None = None,
    partition_name: str = "validation",
) -> None:
    """Ensure evaluated engines belong strictly to permitted partition with no leakage."""
    actual_set = set(actual_units)
    expected_set = set(expected_units)

    if actual_set != expected_set:
        diff = actual_set.symmetric_difference(expected_set)
        raise DataLeakageError(
            f"Engine partition mismatch for {partition_name}: symmetric difference {diff}"
        )

    if forbidden_units is not None:
        forbidden_set = set(forbidden_units)
        overlap = actual_set.intersection(forbidden_set)
        if overlap:
            raise DataLeakageError(
                f"Forbidden engines {overlap} detected in {partition_name} evaluation!"
            )


def assert_no_held_out_path(path_or_str: Path | str) -> None:
    """Enforce pre-test barrier: reject any path referencing held-out or test data."""
    s = str(path_or_str).lower().replace("\\", "/")
    forbidden_tokens = ["official_test", "held_out", "test_fd", "data/test"]
    for tok in forbidden_tokens:
        if tok in s:
            raise DataLeakageError(
                f"Pre-test barrier: request references forbidden test path '{path_or_str}'."
            )
