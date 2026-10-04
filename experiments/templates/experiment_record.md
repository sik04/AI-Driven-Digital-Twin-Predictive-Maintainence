# Experiment Record: EXP-{{ID}}

> **Important**: All experiments—including failed, null, or anomalous runs—must be permanently recorded in this directory. Negative findings are critical scientific evidence and prevent duplication of futile approaches.

---

## 1. Metadata and Context
- **Experiment ID**: EXP-{{ID}}
- **Execution Date**: YYYY-MM-DD
- **Author(s) Responsible**: [Mayank Singh / Shiksha Pandey / Ruchi Gupta]
- **Target Roadmap Phase**: Phase [0-12]
- **Research Question Addressed**: [RQ1 / RQ2 / RQ3 / RQ4]
- **Specific Hypothesis Tested**:

---

## 2. Provenance and Environment
- **Git Commit SHA**: `{{COMMIT_SHA}}`
- **Clean Git Tree**: [Yes / No]
- **Python Version**:
- **Key Dependencies & Versions**:
  - `torch`:
  - `numpy`:
  - `scipy`:
  - `scikit-learn`:
- **Hardware Platform**: [OS, CPU Model, GPU Model, CUDA Driver]
- **Random Seeds**:
  - Master Seed: `42`
  - Trial Seeds: `[42, 123, 456, ...]`

---

## 3. Dataset and Preprocessing
- **Dataset Source**: [e.g., NASA C-MAPSS FD001]
- **Dataset Version / MD5**:
- **Engine Split Protocol**:
  - Train Engines: `[List or Count]`
  - Validation Engines: `[List or Count]`
  - Test Engines: `[List or Count]`
- **Lookahead Isolation Verified**: [Yes / No]
- **Normalization Fitted On**: [Training Set Only]
- **Sequence Window Length ($T_w$)**:
- **Maximum RUL Cap ($RUL_{max}$)**:

---

## 4. Model Architecture & Hyperparameters
- **Model Type / Architecture**:
- **Baseline Compared Against**:
- **Loss Function**:
- **Optimization Algorithm & Learning Rate**:
- **Batch Size & Epochs**:
- **Early Stopping Criteria**:

---

## 5. Metrics and Prediction Units
- **Prediction Unit**: Operating cycles
- **Evaluation Metrics Recorded**:
  - Root Mean Squared Error (RMSE)
  - PHM 2008 Asymmetric Score
  - Prediction Interval Coverage Probability (PICP) [@ 90% or 95%]
  - Mean Prediction Interval Width (MPIW)
  - Wall-clock Training & Inference Time

---

## 6. Empirical Results & Artifact Locations
- **Performance Summary**:
  | Metric | Validation | Test Mean +/- Std | Baseline Comparison |
  | :--- | :---: | :---: | :---: |
  | RMSE (cycles) | | | |
  | PHM Score | | | |
  | PICP (%) | | | |
  | MPIW (cycles) | | | |
- **Checkpoint Location**: `experiments/checkpoints/exp_{{ID}}/`
- **Output Logs / Plots**: `experiments/runs/exp_{{ID}}/`

---

## 7. Observations, Anomalies, and Failures
- **Observed Convergence Dynamics**:
- **Anomalies / Failure Modes**:
  - Did the model exhibit divergence, severe late predictions, or interval collapse?
- **Limitations & Confounders**:

---

## 8. Scientific Conclusion and Next Step
- **Hypothesis Evaluation**: [Supported / Partially Supported / Refuted / Inconclusive]
- **Decision Rationale**:
- **Next Follow-up Experiment / Action**:
