# Experiment Record: EXP-{{ID}}

> **Important**: All experiments—including failed, null, or anomalous runs—must be permanently recorded in this directory. Negative findings are critical scientific evidence and prevent duplication of futile approaches.

---

## 1. Metadata and Context
- **Experiment ID**: EXP-{{ID}}
- **Execution Date**: YYYY-MM-DD
- **Author(s) Responsible**: [Mayank Singh / Shiksha Pandey / Ruchi Gupta]
- **Target Roadmap Phase**: Phase [0-12]
- **Research Question Addressed**: [RQ1 / RQ2 / RQ3 / RQ4]
- **Protocol Version**: `step06-v2`
- **Approval Reference**: ADR-018

---

## 2. Provenance, Code & Environment
- **Git Commit SHA**: `{{COMMIT_SHA}}`
- **Git Worktree Status**: [Clean (git_dirty=false) / Dirty (git_dirty=true)]
- **Python Version**: `{{PYTHON_VERSION}}`
- **Key Package Versions**:
  - `torch`: `{{TORCH_VERSION}}`
  - `numpy`: `{{NUMPY_VERSION}}`
  - `scipy`: `{{SCIPY_VERSION}}`
  - `scikit-learn`: `{{SKLEARN_VERSION}}`
  - `pandas`: `{{PANDAS_VERSION}}`
- **Hardware Platform**: [OS, CPU Model, GPU Model, CUDA Driver]
- **Random Seeds (Planned Suite)**: `[2026, 2027, 2028, 2029, 2030]`
- **Run Seed (Current Execution)**: `{{RUN_SEED}}`
- **Bootstrap Generator Specification**: `numpy.random.Generator(PCG64(SeedSequence([2026, 6, dataset_number])))`, $B = 10,000$ replicates

---

## 3. Dataset, Split Manifest & Preprocessing Hashes
- **Dataset Source**: [e.g., NASA C-MAPSS FD002]
- **Engine Split Protocol**: Frozen engine-level split manifest (`data/splits/{{SPLIT_FILE}}.json`, lifetime quartile stratification, seed 2026)
- **Raw Data SHA-256**: `{{DATASET_SHA256}}`
- **Split Manifest File**: `data/splits/{{SPLIT_FILE}}.json`
- **Split Manifest SHA-256**: `{{SPLIT_MANIFEST_SHA256}}`
- **Preprocessing Artifact Hashes**:
  - Setting Scaler SHA-256: `{{SETTING_SCALER_SHA256}}`
  - K-Means Model SHA-256: `{{KMEANS_SHA256}}`
  - Sensor Norm Stats SHA-256: `{{SENSOR_NORM_SHA256}}`
- **Feature Vector Schema (17 Features)**: `["setting1", "setting2", "setting3", "s2", "s3", "s4", "s7", "s8", "s9", "s11", "s12", "s13", "s14", "s15", "s17", "s20", "s21"]`
- **Sequence Window Configuration**: Lookback = 30 (causal lookback), Stride = 1, No Padding, Endpoints = [30, T]
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

## 5. Calibration & Maintenance Policy Configuration
- **Calibration Method**: [Global Split Conformal / Condition-Aware / Proposed]
- **Calibration Split Partition**: Calibration Engines Only
- **Nominal Coverage ($1 - \alpha$)**: Primary 90% ($\alpha = 0.10$) [Secondary: 80%, 95%]
- **Calibration Response Target**: Uncapped `rul_true`
- **Maintenance Cost Scenario ID**: [`primary_reference` / `failure_sensitive` / `waste_sensitive`]
- **Scenario Cost Values**:
  - Preventive Maintenance Cost ($C_{\text{PM}}$): `{{C_PM}}`
  - Failure Cost ($C_{\text{FAIL}}$): `{{C_FAIL}}`
  - Wasted Life Cost Per Cycle ($C_{\text{WASTE}}$): `{{C_WASTE}}`
- **Maintenance Policy Specification**: [e.g. MAINTAIN_NOW when lower_rul <= threshold]

---

## 6. Empirical Results & Artifact Locations
- **Performance Summary**:
  | Metric | Validation | Test Estimate [95% Descriptive CI] | Confirmatory Decision Result [98.75% CI] | 5-Seed Summary (Mean +/- Std Across Seeds) | Baseline Comparison Contrast |
  | :--- | :---: | :---: | :---: | :---: | :---: |
  | Mean Absolute Error (MAE) | | | — | | |
  | Root Mean Squared Error (RMSE) | | | — | | |
  | Prediction Interval Coverage Probability (PICP) | | | | | |
  | Mean Prediction Interval Width (MPIW) | | | | | $D_{\text{width}}$: |
  | Winkler Interval Score ($\bar{\text{IS}}_{0.10}$) | | | | | $D_{\text{score}}$: |
  | Mean Simulated Cost ($\bar{C}$) | | | | | $\Delta_{\text{cost}}$: |
  | Worst-Group Coverage Error | | | | | $\Delta_{\text{error}}$: |
  | Fleet Failure Rate | | | — | | $\Delta_{\text{fail}}$: |
  | Cost-Inefficient Early PM Rate ($W > r_{\text{equal}}$) | | | — | | |

  *(Note: 95% descriptive CIs report estimation uncertainty; 98.75% decision CIs apply Bonferroni FWER control across RQs under ADR-018. The 5-Seed summary quantifies training stochasticity. These uncertainty sources are never conflated).*

- **Output Artifact Locations**:
  - Model Checkpoint: `experiments/checkpoints/exp_{{ID}}/`
  - Predictions / Calibration Logs: `experiments/runs/exp_{{ID}}/`
  - Outcome Summary JSON: `experiments/records/exp_{{ID}}_summary.json`

---

## 7. Observations, Anomalies, and Failures
- **Observed Convergence Dynamics**:
- **Anomalies / Subgroup Coverage Failures**:
- **Missing Predictions / Degenerate Intervals Record**:
- **Protocol Deviations (if any, labeled exploratory)**:
- **Limitations & Confounders**:

---

## 8. Scientific Conclusion and Next Step
- **Component Condition Results**:
  - Condition 1: [Pass / Fail / Indeterminate]
  - Condition 2: [Pass / Fail / Indeterminate]
  - Failure Safeguard: [Pass / Fail]
- **Hypothesis Evaluation**: [Supported / Unsupported / Inconclusive]
- **Decision Rationale**:
- **Next Action**:
