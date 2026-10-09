# Experiment Record: EXP-{{ID}}

> **Important**: All experiments—including failed, null, or anomalous runs—must be permanently recorded in this directory. Negative findings are critical scientific evidence and prevent duplication of futile approaches.

---

## 1. Metadata and Context
- **Experiment ID**: EXP-{{ID}}
- **Execution Date**: YYYY-MM-DD
- **Author(s) Responsible**: [Mayank Singh / Shiksha Pandey / Ruchi Gupta]
- **Target Roadmap Phase**: Phase [0-12]
- **Research Question Addressed**: [RQ1 / RQ2 / RQ3 / RQ4]
- **Protocol Version**: Step 5 Data Protocol v1.0

---

## 2. Provenance, Code & Environment
- **Git Commit SHA**: `{{COMMIT_SHA}}`
- **Git Worktree Status**: [Clean / Dirty]
- **Python Version**: `{{PYTHON_VERSION}}`
- **Key Package Versions**:
  - `torch`: `{{TORCH_VERSION}}`
  - `numpy`: `{{NUMPY_VERSION}}`
  - `scipy`: `{{SCIPY_VERSION}}`
  - `scikit-learn`: `{{SKLEARN_VERSION}}`
- **Hardware Platform**: [OS, CPU Model, GPU Model, CUDA Driver]
- **Model Run Seed**: `[2026, 2027, 2028, 2029, 2030]`

---

## 3. Dataset, Split Manifest & Preprocessing Hashes
- **Dataset Source**: [e.g., NASA C-MAPSS FD002]
- **Raw Data SHA-256**: `{{DATASET_SHA256}}`
- **Split Manifest File**: `data/splits/{{SPLIT_FILE}}.json`
- **Split Manifest SHA-256**: `{{SPLIT_MANIFEST_SHA256}}`
- **Preprocessing Artifact Hashes**:
  - Setting Scaler SHA-256: `{{SETTING_SCALER_SHA256}}`
  - K-Means Model SHA-256: `{{KMEANS_SHA256}}`
  - Sensor Norm Stats SHA-256: `{{SENSOR_NORM_SHA256}}`
- **Feature Vector Schema (17 Features)**: `["setting1", "setting2", "setting3", "s2", "s3", "s4", "s7", "s8", "s9", "s11", "s12", "s13", "s14", "s15", "s17", "s20", "s21"]`
- **Sequence Window Configuration**: Lookback = 30, Stride = 1, No Padding, Endpoints = [30, T]
- **Capped Training Target ($RUL_{target}$)**: $\min(\text{RUL}_{true}, 125)$

---

## 4. Model Architecture & Hyperparameters
- **Model Type / Architecture**:
- **Full Model Configuration**:
- **Baseline Compared Against**:
- **Loss Function**:
- **Optimization Algorithm & Learning Rate**:
- **Batch Size & Epochs**:

---

## 5. Calibration & Conformal Configuration (If Applicable)
- **Calibration Method**: [Global Split Conformal / Condition-Aware / Proposed]
- **Calibration Split Partition**: Calibration Engines Only
- **Nominal Coverage ($1 - \alpha$)**: 90% ($\alpha = 0.10$) [Secondary: 80%, 95%]
- **Calibration Response Target**: Uncapped `rul_true`

---

## 6. Empirical Results & Artifact Locations
- **Performance Summary**:
  | Metric | Validation | Test Mean +/- Std | Baseline Comparison |
  | :--- | :---: | :---: | :---: |
  | MAE (cycles) | | | |
  | RMSE (cycles) | | | |
  | PICP (%) | | | |
  | MPIW (cycles) | | | |
  | Mean Simulated Cost ($\bar{C}$) | | | |
- **Output Artifact Locations**:
  - Model Checkpoint: `experiments/checkpoints/exp_{{ID}}/`
  - Predictions / Calibration Logs: `experiments/runs/exp_{{ID}}/`
  - Outcome Summary JSON: `experiments/records/exp_{{ID}}_summary.json`

---

## 7. Observations, Anomalies, and Failures
- **Observed Convergence Dynamics**:
- **Anomalies / Subgroup Coverage Failures**:
- **Limitations & Confounders**:

---

## 8. Scientific Conclusion and Next Step
- **Hypothesis Evaluation**: [Supported / Partially Supported / Refuted / Inconclusive]
- **Decision Rationale**:
- **Next Action**:
