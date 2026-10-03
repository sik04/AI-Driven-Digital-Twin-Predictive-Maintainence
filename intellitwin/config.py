"""
IntelliTwin Authoritative Configuration Module.
Provides centralized, reproducible configurations for datasets, engine-level splits,
feature engineering, and model training parameters.
"""

import os
from dataclasses import dataclass, field, asdict
from typing import List, Optional

# Root directory reference
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass
class DataConfig:
    """Authoritative Data and Splitting Configuration."""

    dataset_name: str = "NASA C-MAPSS FD001"
    sub_dataset: str = "FD001"
    data_dir: str = os.path.join(REPO_ROOT, "data", "cmapss")
    
    # Engine-level split parameters
    split_strategy: str = "engine_level"
    random_seed: int = 42
    validation_fraction: float = 0.20
    
    # Preprocessing parameters
    max_rul: int = 125
    seq_len: int = 30
    drop_constant_sensors: bool = True
    constant_variance_threshold: float = 1e-4
    add_rolling_features: bool = True
    rolling_window: int = 5
    
    # Artifact destination
    split_artifact_path: str = os.path.join(REPO_ROOT, "artifacts", "splits", "fd001_split.json")

    def to_dict(self):
        return asdict(self)


def get_default_data_config() -> DataConfig:
    """Return the authoritative default data configuration."""
    return DataConfig()
