"""Stratified engine-cluster bootstrap and confidence interval computation."""

from __future__ import annotations

import json
from collections.abc import Collection, Sequence
from pathlib import Path

import numpy as np

from intellitwin.evaluation.schema import (
    BOOTSTRAP_REPLICATES,
    DECISION_QUANTILES,
)
from intellitwin.uncertainty.artifacts import resolve_repo_relative_path

DATASET_NUMBERS: dict[str, int] = {
    "FD001": 1,
    "FD002": 2,
    "FD004": 4,
}


def load_partition_quartile_strata(
    dataset: str,
    partition_engines: Collection[int],
    base_dir: Path | str = ".",
) -> dict[str, list[int]]:
    """Load frozen lifetime-quartile stratum memberships for evaluated partition engines.

    Requirements:
    - Uses frozen split manifest for FD001/FD004.
    - Uses frozen quartile-provenance file for FD002.
    - Sorts engine IDs within strata ascending.
    - Quartiles are fixed and never recomputed from sample.
    """
    base = Path(base_dir).resolve()
    part_set = set(partition_engines)
    strata: dict[str, list[int]] = {"Q1": [], "Q2": [], "Q3": [], "Q4": []}

    if dataset in ("FD001", "FD004"):
        manifest_rel = f"data/splits/{dataset.lower()}_engine_split_seed_2026.json"
        manifest_p = resolve_repo_relative_path(base, manifest_rel)
        with open(manifest_p, encoding="utf-8") as f:
            data = json.load(f)
        for q_entry in data.get("quartile_membership", []):
            q_name = q_entry["quartile"]
            if q_name in strata:
                engs = [int(e) for e in q_entry.get("engine_ids", []) if int(e) in part_set]
                strata[q_name] = sorted(engs)
    elif dataset == "FD002":
        prov_rel = "data/splits/fd002_lifetime_quartile_provenance.json"
        prov_p = resolve_repo_relative_path(base, prov_rel)
        with open(prov_p, encoding="utf-8") as f:
            data = json.load(f)
        q_mem = data.get("quartile_membership", {})
        for q_name in ("Q1", "Q2", "Q3", "Q4"):
            entry = q_mem.get(q_name, {})
            engs = [int(e) for e in entry.get("engine_ids", []) if int(e) in part_set]
            strata[q_name] = sorted(engs)
    else:
        raise ValueError(f"Unsupported dataset for quartile loading: {dataset}")

    # Integrity check: every partition engine must belong to exactly one stratum
    assigned = []
    for eng_list in strata.values():
        assigned.extend(eng_list)
    if set(assigned) != part_set:
        raise ValueError(
            f"Quartile stratum mismatch for {dataset}: "
            f"assigned {len(assigned)} != partition {len(part_set)}"
        )

    return strata


def generate_stratified_bootstrap_draws(
    dataset: str,
    partition_engines: Collection[int],
    base_dir: Path | str = ".",
    n_replicates: int = BOOTSTRAP_REPLICATES,
) -> np.ndarray:
    """Generate deterministic stratified engine-cluster bootstrap draws.

    Rules:
    - Draw stratum by stratum in order Q1, Q2, Q3, Q4.
    - Each stratum draws its original number of engine indices with replacement.
    - PRNG: np.random.Generator(PCG64(SeedSequence([2026, 6, dataset_number]))).
    - Retains duplicate engine multiplicity (does not deduplicate).
    - Returns array of shape (n_replicates, n_total_engines).
    """
    if dataset not in DATASET_NUMBERS:
        raise ValueError(
            f"Unknown dataset {dataset}; expected one of {list(DATASET_NUMBERS.keys())}"
        )

    ds_num = DATASET_NUMBERS[dataset]
    seed_seq = np.random.SeedSequence([2026, 6, ds_num])
    rng = np.random.Generator(np.random.PCG64(seed_seq))

    strata = load_partition_quartile_strata(dataset, partition_engines, base_dir=base_dir)

    total_engines = sum(len(engs) for engs in strata.values())
    draws = np.zeros((n_replicates, total_engines), dtype=int)

    for b in range(n_replicates):
        row_engs: list[int] = []
        for q_name in ("Q1", "Q2", "Q3", "Q4"):
            engs = strata[q_name]
            n_q = len(engs)
            if n_q > 0:
                idx_draws = rng.integers(0, n_q, size=n_q)
                for idx in idx_draws:
                    row_engs.append(engs[idx])
        draws[b, :] = row_engs

    return draws


def compute_bootstrap_ci(
    replicate_values: np.ndarray | Sequence[float],
    quantiles: tuple[float, float] = DECISION_QUANTILES,
) -> tuple[float, float]:
    """Compute bootstrap quantile interval using linear interpolation."""
    arr = np.asarray(replicate_values, dtype=float)
    if len(arr) == 0:
        raise ValueError("Cannot compute quantiles on empty replicate array.")
    q_low, q_high = quantiles
    low = float(np.quantile(arr, q=q_low, method="linear"))
    high = float(np.quantile(arr, q=q_high, method="linear"))
    return (low, high)


def compute_conservative_bounded_ci(
    lower_bounds: np.ndarray | Sequence[float],
    upper_bounds: np.ndarray | Sequence[float],
    quantiles: tuple[float, float] = DECISION_QUANTILES,
) -> tuple[float, float]:
    """Compute conservative confidence interval across replicates with bounded uncertainties."""
    low_arr = np.asarray(lower_bounds, dtype=float)
    upp_arr = np.asarray(upper_bounds, dtype=float)
    if len(low_arr) != len(upp_arr):
        raise ValueError("lower_bounds and upper_bounds must have identical length.")

    q_low, q_high = quantiles
    overall_low = float(np.quantile(low_arr, q=q_low, method="linear"))
    overall_high = float(np.quantile(upp_arr, q=q_high, method="linear"))
    return (overall_low, overall_high)
