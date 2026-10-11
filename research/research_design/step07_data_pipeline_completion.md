# Step 7.2 — Data Preprocessing and Window Pipeline Completion Record

> **Status**: **COMPLETE**  
> **Protocol Reference**: `step07-data-v1` / ADR-019 / `step06-v2`  
> **Authors**: Mayank Singh, Shiksha Pandey, Ruchi Gupta  
> **Scope**: Deterministic C-MAPSS Data Loader, Preprocessing, Regime Assignment, Causal Windowing, Sample Weighting, and Artifact Persistence  
> **Model Implementation / Training**: None (Deferred to Step 7.3)

---

## 1. Specification and Integrity Summary

| Parameter | Frozen Value / Policy | Verification Result |
| :--- | :--- | :--- |
| **Datasets** | FD001 (control), FD002 (primary), FD004 (robustness) | All 3 datasets strictly validated |
| **Feature Count** | 17 features (3 settings + 14 degradation sensors) | Exact canonical column order verified |
| **Lookback ($W$)** | 30 cycles | Exact 30-cycle causal history |
| **Stride** | 1 cycle | Every consecutive valid endpoint $t \ge 30$ |
| **Padding** | None | Trajectories with $T < 30$ yield 0 windows |
| **Supervised Target Cap** | $\min(\text{rul\_true}, 125)$ | Applied to `rul_target` only; `rul_true` uncapped |
| **Preprocessing Fit** | Training partition engines only | Verified via synthetic anti-leakage tests |
| **Development Transform** | Training and validation partitions only | Verified via partition isolation tests |
| **Calibration Data Role** | Reserved for conformal calibration | **Untouched** (no windows constructed or transformed) |
| **Held-Out Test Data Role** | Reserved for confirmatory evaluation | **Untouched** (no windows constructed or evaluated) |
| **Equal-Engine Sample Weights** | $w_{i,t} = M / (N \cdot n_i)$ | Verified: engine weight sum $= M/N$, mean $= 1.0$ |

---

## 2. Preprocessor Artifacts and Reproducibility

Preprocessing parameters were fitted strictly on the frozen `train` engine partitions and persisted to deterministic JSON artifacts. Re-executing `scripts/build_step07_data_artifacts.py` regenerates identical bytes and SHA-256 hashes.

| Dataset | Operating Conditions | Preprocessor Artifact Path | SHA-256 Digest | Train Windows | Val Windows |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **FD001** | Single-condition (C1) | `experiments/preprocessing/FD001/preprocessor.json` | `6f88491a46e2a0b5f8955df85a71e991f1cffc600c5e8becb713a1520b1e1c0a` | 8,807 | 1,760 |
| **FD002** | 6 regimes (C1–C6) | `experiments/preprocessing/FD002/preprocessor.json` | `cef04b8dafc4c9f53aba7c6bcb0bc67fc981540abdafadc76fafa314684d856c` | 22,923 | 4,669 |
| **FD004** | 6 regimes (C1–C6) | `experiments/preprocessing/FD004/preprocessor.json` | `fdfa4c0284c38554f8b8026c27c71f56ebd9c157a47f9acd2baf9ae34cbe0502` | 27,068 | 5,201 |

- **Deterministic Regeneration Check**: `python scripts/build_step07_data_artifacts.py` executed twice; zero hash divergence.
- **Centroid Ordering**: Lexicographically sorted in standardized setting space; nearest-centroid assignment with lower-index tie-breaking.
- **Sensor Scaling**: Computed using population variance with `ddof=0` and unscaled $1.0$ fallback for zero-variance features.

---

## 3. Automated Verification and Test Results

### 3.1 Static Analysis and Formatting
- **Ruff Format**: Clean across `src`, `tests`, `scripts` (`31 files already formatted`).
- **Ruff Lint**: Clean across `src`, `tests`, `scripts` (`All checks passed!`).
- **Mypy**: Strict type-checking passed (`Success: no issues found in 31 source files`).

### 3.2 Core Synthetic Unit Tests
- **Command**: `pytest -m "not integration" --cov=src/intellitwin --cov-report=term-missing tests`
- **Result**: `97 passed, 7 deselected`
- **Coverage**: 91% total coverage across `src/intellitwin` (loader: 92%, splits: 86%, preprocessing: 92%, windowing: 89%, pipeline: 97%, artifacts: 95%).

### 3.3 Raw C-MAPSS Integration Tests
- **Command**: `pytest -m integration -v`
- **Result**: `7 passed, 97 deselected`
- **Validated Datasets**:
  - `tests/test_step07_data_integration.py::test_step07_data_pipeline_real_dataset[FD001]` PASSED
  - `tests/test_step07_data_integration.py::test_step07_data_pipeline_real_dataset[FD002]` PASSED
  - `tests/test_step07_data_integration.py::test_step07_data_pipeline_real_dataset[FD004]` PASSED
  - `tests/test_fd002_quartile_provenance.py::test_real_fd002_quartile_provenance_reconstruction` PASSED
  - `tests/test_simulator_validation_pilot.py::test_real_fd002_validation_pilot_execution` PASSED
  - `tests/test_split_generator.py::test_real_data_fd001_regeneration` PASSED
  - `tests/test_split_generator.py::test_real_data_fd004_regeneration` PASSED

---

## 4. Scientific Safeguards & Boundary Affirmation

1. **Frozen Engine Splits**: Partition assignments in `data/splits/fd001_engine_split_seed_2026.json`, `data/splits/fd002_engine_split_seed_2026.json`, and `data/splits/fd004_engine_split_seed_2026.json` are byte-for-byte unchanged.
2. **Strict Data Role Separation**: Preprocessor parameters were fitted exclusively on training engines. Validation data was transformed strictly using frozen preprocessor parameters. Calibration and held-out test engines were never transformed into sequence windows or inspected.
3. **No Model Code**: No GBR or LSTM model training, checkpointing, or hyperparameter selection was conducted.
4. **Step 6 Simulator Invariants**: Maintenance cost scenarios and effect thresholds are unmodified.
5. **Baseline Main Commit**: Branch created from verified main baseline `b2c13a86496248c0250d36eb097edf39f761e1b6`.
