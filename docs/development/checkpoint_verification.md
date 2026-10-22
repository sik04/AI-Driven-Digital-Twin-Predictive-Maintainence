# Checkpoint Verification & Reproducibility Guide

## Overview

This guide details the environment configuration, mechanical verification protocol, and prediction reproduction workflow for Portion B of the IntelliTwin predictive maintenance platform.

The verification wrapper independently confirms that:
1. All 30 base model metadata records agree on exact software dependencies.
2. The runtime execution environment matches those declared versions before any checkpoint is loaded.
3. Model checkpoints unpickle without `sklearn.exceptions.InconsistentVersionWarning`.
4. Model predictions reproduce across 60 validation and calibration records within numerical tolerance ($\le 10^{-4}$).
5. Protected baseline inputs remain strictly immutable across execution.
6. Held-out test inference remains unstarted (`NOT_STARTED`).

---

## Matched Verification Environment

### Dependency Specification

All 30 base model metadata files (`experiments/base_models/{dataset}/{model_family}/seed_{seed}/metadata.json`) uniformly declare the following runtime environment:

- **Python**: `3.14.0` (CPython 64-bit on Windows)
- **NumPy**: `2.5.3`
- **pandas**: `3.0.6`
- **scikit-learn**: `1.9.1`
- **PyTorch**: `2.14.1+cpu`
- **PyYAML**: `6.0.3`

### Environment Specification Files

The environment files are located in `requirements/checkpoint-verification/`:
- `requirements.in`: High-level runtime pins and testing/linting requirements.
- `requirements-windows-py314.lock.txt`: Fully resolved lockfile containing transitive dependencies.
- `environment_spec.json`: Machine-readable specification recording Python version, package sources, and setup commands.

### Package Sources & Installation

1. **PyTorch CPU Wheels**: Sourced directly from the official PyTorch wheel repository:
   ```
   https://download.pytorch.org/whl/cpu
   ```
2. **PyPI Packages**: Standard packages resolved from `https://pypi.org/simple`.

### Setup Instructions

To instantiate the metadata-matched, explicitly locked verification environment:

```powershell
# 1. Create a fresh virtual environment using Python 3.14.0 with seed packages (pip)
uv venv --seed .venv_checkpoint_verification --python <path_to_python_3.14.0>

# 2. Install explicitly locked dependencies
.\.venv_checkpoint_verification\Scripts\pip.exe install -r requirements/checkpoint-verification/requirements-windows-py314.lock.txt

# 3. Install project in editable mode without pulling unpinned dependencies
.\.venv_checkpoint_verification\Scripts\pip.exe install -e . --no-deps

# 4. Confirm environment consistency
.\.venv_checkpoint_verification\Scripts\pip.exe check
```

---

## Verification Wrapper Usage

The official verification wrapper is located at `scripts/verify_checkpoint_environment.py`.

### Command-Line Arguments

- `--raw-data-dir`: Directory containing raw C-MAPSS training text files (default: `data/raw/cmapss`).
- `--output-dir`: Required directory for generating the verification handoff bundle.
- `--base-dir`: Repository root directory (default: `.`).
- `--allow-dirty`: Flag permitting execution on a dirty git working tree (disallowed for official handoff).
- `--skip-raw-reproduction`: Test flag to bypass raw prediction inference (produces non-PASS status).

### Official Execution Command

Official evidence generation requires execution from a clean source state into an external staging directory:

```powershell
python scripts/verify_checkpoint_environment.py --output-dir <staging_directory_path>
```

---

## Verification Gates & Mechanical Invariants

The wrapper enforces the following sequence of strict verification gates:

1. **Git State Verification**:
   Requires `git_dirty == False` at entry. Captures the exact source commit SHA.
2. **Mechanical Metadata Audit**:
   Scans all 30 base model metadata files (`experiments/base_models/*/*/seed_*/metadata.json`). Verifies complete agreement on Python, NumPy, pandas, scikit-learn, and PyTorch versions.
3. **Runtime Pre-Load Verification**:
   Compares active runtime versions (`sys.version_info`, `np.__version__`, `pd.__version__`, `sklearn.__version__`, `torch.__version__`) against expected versions. Execution halts before checkpoint loading if any mismatch exists.
4. **Environment Health Check**:
   Executes `python -m pip check` to verify zero broken package requirements.
5. **Protected Input Hashing (Pre-Execution)**:
   Computes SHA-256 digests for all protected inputs across 11 categories:
   - `splits_and_quartiles`
   - `model_metadata`
   - `model_registry`
   - `checkpoints`
   - `preprocessing`
   - `calibrator_registry`
   - `calibrator_bundles`
   - `calibration_selection`
   - `prediction_caches`
   - `verification_sources`
   - `environment_specification`
6. **Raw Source Dataset Hash Verification**:
   Verifies frozen SHA-256 hashes of `train_FD001.txt`, `train_FD002.txt`, and `train_FD004.txt`.
7. **Sklearn InconsistentVersionWarning Trap**:
   Executes the full Step 8 audit under warning traps. Treats `sklearn.exceptions.InconsistentVersionWarning` as a fatal error.
8. **Prediction Reproduction Audit**:
   Executes CPU inference across 60 records (3 datasets $\times$ 2 model families $\times$ 5 seeds $\times$ 2 partitions):
   - Partitions: strictly validation and calibration engines.
   - Batch size: 256.
   - Asserts finite predictions, exact key alignment, and maximum absolute error $\le 10^{-4}$.
9. **Protected Input Hashing (Post-Execution)**:
   Re-computes hashes of all protected inputs to prove zero mutation occurred during execution.
10. **Evidence Generation**:
    Generates all 6 required handoff artifacts into the specified output directory.

---

## Generated Evidence Handoff Bundle

Official evidence is committed under `experiments/checkpoint_verification_v1/`:

1. `environment_verification.json`:
   Core execution report conforming to schema `checkpoint-environment-verification-v1`. Contains environment metadata, version comparisons, reproduction statistics, warning counts, and verification status (`PASS`).
2. `step08_full_audit.json`:
   Complete output of `run_step08_audit(full_audit=True)` including registry checks, cache checks, LOEO reconstruction, and detailed records for all 60 reproductions.
3. `input_manifest.json`:
   Manifest mapping POSIX repository-relative paths to SHA-256 digests for all protected inputs, raw source files, and pre/post comparison results.
4. `execution.log`:
   Verbatim console log captured during verification execution.
5. `pip_freeze.txt`:
   Complete package freeze of the verification virtual environment.
6. `pip_check.txt`:
   Output of `pip check` demonstrating unbroken dependency requirements.

---

## Strict Scientific Boundaries

- **Zero Retraining or Refitting**: All base model checkpoints and preprocessors are loaded read-only from frozen artifacts.
- **Zero Held-Out Trajectory Inference**: Test engines remain uninspected and unreferenced. `held_out_execution_status` is locked at `NOT_STARTED`.
- **Zero Tolerance Loosening**: Numerical tolerances remain strictly $\le 10^{-4}$.
- **Immutable Artifacts**: Historical reports, pre-existing models, calibration registries, and splits are never modified.
