"""Reproducibility utilities for point-RUL base predictors.

Implements deterministic seed controls across Python, NumPy, and PyTorch (CPU and CUDA),
as specified in ADR-019 and Step 7.1.
"""

import random

import numpy as np
import torch


def set_global_seed(seed: int) -> None:
    """Set global random seeds for deterministic execution.

    Parameters
    ----------
    seed : int
        Seed integer.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    # Enable deterministic algorithms with warning fallback if non-deterministic
    try:
        torch.use_deterministic_algorithms(True, warn_only=True)
    except Exception:
        pass


def resolve_device() -> torch.device:
    """Resolve compute device (CUDA if available, otherwise CPU).

    Returns
    -------
    torch.device
        Target execution device.
    """
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")
