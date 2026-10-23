"""Confirmatory evaluation pipeline for held-out test assessment.

This package provides an isolated execution and verification path for Step 9
confirmatory evaluation across the frozen 930-configuration matrix.
"""

from __future__ import annotations

from intellitwin.confirmatory.data import (
    FROZEN_RAW_SOURCE_HASHES,
    generate_predictions_for_cell,
    load_and_prepare_partition_windows,
    load_or_generate_point_predictions,
    verify_raw_data_hashes,
)
from intellitwin.confirmatory.runner import (
    compute_subgroup_bounds,
    run_confirmatory_evaluation,
)
from intellitwin.confirmatory.verification import (
    independently_verify_confirmatory_evidence,
)

__all__ = [
    "FROZEN_RAW_SOURCE_HASHES",
    "compute_subgroup_bounds",
    "generate_predictions_for_cell",
    "independently_verify_confirmatory_evidence",
    "load_and_prepare_partition_windows",
    "load_or_generate_point_predictions",
    "run_confirmatory_evaluation",
    "verify_raw_data_hashes",
]
