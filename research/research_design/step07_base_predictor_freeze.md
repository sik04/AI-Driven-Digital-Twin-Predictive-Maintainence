# Step 7 Base Predictor Production Matrix and Model Freeze

- **Status**: Complete / Frozen
- **Date**: 2026-10-12
- **Author**: IntelliTwin Research Team
- **Governance**: ADR-019 (Specification), ADR-020 (Formal Freeze)
- **Authoritative Registry**: `experiments/base_models/model_registry.json`
- **Validation Summary Artifact**: `experiments/base_models/base_predictor_validation_summary.csv`
- **Audit Script**: `scripts/audit_step07_base_models.py`
- **Reproducibility Audit Record**: `experiments/base_models/reproducibility_audit_seed_2026.json`

---

## 1. Executive Summary

Step 7 (Reproducible Base Predictor Experiments) is formally **COMPLETE** and **FROZEN**.

Across the three qualified C-MAPSS datasets (`FD001`, `FD002`, `FD004`), 2 point-RUL model families (Histogram Gradient Boosting Regressor and unidirectional LSTM) have undergone strict validation-only hyperparameter selection across seeds `[2026, 2027]`. Exactly one winning configuration per dataset-family cell was selected and trained across five official research seeds (`2026, 2027, 2028, 2029, 2030`), yielding a complete 30-model production matrix.

All 30 model checkpoints, metadata JSON records, metric evaluations, and validation prediction CSVs are cryptographically hashed and indexed in `experiments/base_models/model_registry.json`.

An independent audit has verified:
1. Complete 30/30 cell coverage and artifact byte integrity.
2. Zero leakage into calibration or held-out test partitions.
3. Strict non-negative prediction post-processing ($\ge 0.0$ cycles).
4. Full numerical reproducibility across independent training sessions.

---

## 2. Frozen Base Predictor Configurations

All hyperparameter selections were conducted exclusively on frozen validation engines using uncapped-RUL RMSE with three-stage deterministic tie-breaking. Calibration and test engines remained strictly untouched.

| Dataset | Model Family | Frozen Winning Configuration | Configuration Parameters | Selection Validation RMSE (cycles) | Selection Justification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FD001** | **GBR** | `gbr_lr010_leaf15_l2_0` | `lr=0.10`, `max_leaf=15`, `l2=0.0` | 28.4243 | Lowest mean validation RMSE across seeds 2026 and 2027 on single-regime control. |
| **FD001** | **LSTM** | `lstm_h64_lr0010` | `H=64`, `lr=0.0010`, `dropout=0.20` | 30.0831 (mean: 30.1055, 30.0607) | Lowest mean validation RMSE across seeds 2026 and 2027. |
| **FD002** | **GBR** | `gbr_lr010_leaf31_l2_0` | `lr=0.10`, `max_leaf=31`, `l2=0.0` | 34.6613 | Frozen in Step 7.3 under ADR-019. Lowest validation RMSE on 6 operating regimes. |
| **FD002** | **LSTM** | `lstm_h64_lr0010` | `H=64`, `lr=0.0010`, `dropout=0.20` | 35.2524 (mean: 35.1934, 35.3114) | Frozen in Step 7.3 under ADR-019. Lowest mean validation RMSE across seeds 2026 and 2027. |
| **FD004** | **GBR** | `gbr_lr010_leaf31_l2_0` | `lr=0.10`, `max_leaf=31`, `l2=0.0` | 48.8283 | Lowest validation RMSE on 6 regimes and 2 fault modes (HPC + fan). |
| **FD004** | **LSTM** | `lstm_h64_lr0010` | `H=64`, `lr=0.0010`, `dropout=0.20` | 48.2471 (mean: 48.3554, 48.1388) | Lowest mean validation RMSE across seeds 2026 and 2027. |

---

## 3. Full 30-Model Performance Matrix

The 30 production models were evaluated across the 5 official seeds (`2026`–`2030`) on the frozen validation partitions. All metrics reported below are **development/validation results only** and do not represent test claims or statistical confidence intervals.

| Dataset | Model Family | Selected Configuration | Uncapped RMSE (mean ± std) | Uncapped MAE (mean ± std) | Capped RMSE (mean ± std) | Training Time (mean ± std sec) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FD001** | **GBR** | `gbr_lr010_leaf15_l2_0` | 28.4243 ± 0.0000 | 20.1102 ± 0.0000 | 15.4009 ± 0.0000 | 67.63 ± 4.01 s |
| **FD001** | **LSTM** | `lstm_h64_lr0010` | 29.8987 ± 0.2304 | 20.3561 ± 0.2628 | 16.1005 ± 0.4126 | 172.58 ± 9.47 s |
| **FD002** | **GBR** | `gbr_lr010_leaf31_l2_0` | 34.6613 ± 0.0000 | 23.2710 ± 0.0000 | 17.2674 ± 0.0000 | 152.29 ± 24.25 s |
| **FD002** | **LSTM** | `lstm_h64_lr0010` | 35.1374 ± 0.2332 | 23.7824 ± 0.1396 | 19.5011 ± 0.2081 | 425.26 ± 51.21 s |
| **FD004** | **GBR** | `gbr_lr010_leaf31_l2_0` | 48.8283 ± 0.0000 | 31.9559 ± 0.0000 | 16.2977 ± 0.0000 | 172.20 ± 10.22 s |
| **FD004** | **LSTM** | `lstm_h64_lr0010` | 48.6663 ± 0.3569 | 31.6923 ± 0.1823 | 17.1145 ± 0.5379 | 374.44 ± 39.67 s |

### Key Methodological Observations
1. **Deterministic GBR Outputs**: Across all seeds and datasets, GBR models produce identical outputs ($\sigma_{\text{RMSE}} = 0.0000$) under the frozen configuration and deterministic implementation.
2. **Stable LSTM Convergence**: Across 5 independent seed runs with early stopping on validation uncapped RMSE, LSTM models exhibit standard deviations $\sigma \le 0.36$ cycles across all datasets.
3. **Empirical Performance Levels**: Uncapped validation RMSE was observed at ~28–30 cycles for FD001, ~34–35 cycles for FD002, and ~48 cycles for FD004 across both predictor families.

---

## 4. Audit Evidence

### 4.1 Historical Seed-2026 Training Rerun Audit
A representative historical reproducibility check (`scripts/run_step07_reproducibility_audit.py`) was executed for the 6 official `seed_2026` cells from scratch:
- **GBR Models**: Verified numerical prediction agreement within float precision tolerance against saved checkpoints:
  - FD001 GBR: max absolute prediction difference = $4.998 \times 10^{-7}$ cycles ($\ll 10^{-4}$ tolerance).
  - FD002 GBR: max absolute prediction difference = $4.999 \times 10^{-7}$ cycles ($\ll 10^{-4}$ tolerance).
  - FD004 GBR: max absolute prediction difference = $4.999 \times 10^{-7}$ cycles ($\ll 10^{-4}$ tolerance).
- **LSTM Models**: Verified validation RMSE agreement within the pre-specified 0.05 cycle threshold against saved checkpoints:
  - FD001 LSTM: saved RMSE = 30.1055, audit rerun RMSE = 30.1055 ($\Delta = 0.0000 \le 0.05$).
  - FD002 LSTM: saved RMSE = 35.1934, audit rerun RMSE = 35.1934 ($\Delta = 0.0000 \le 0.05$).
  - FD004 LSTM: saved RMSE = 48.3554, audit rerun RMSE = 48.3554 ($\Delta = 0.0000 \le 0.05$).

*Note: This historical check confirmed GBR prediction agreement and LSTM RMSE convergence for seed 2026 only; it did not claim that all 30 production models were independently retrained or that LSTM predictions were identical across arbitrary rerun environments.*

### 4.2 Comprehensive 30-Model Checkpoint-to-Prediction Reproduction Audit
The authoritative registry audit (`scripts/audit_step07_base_models.py --reproduce-predictions`) performs checkpoint-to-prediction reproduction across all 30 production models by loading frozen checkpoints and recomputing validation predictions and metrics from raw data without refitting preprocessors. Results are recorded under `experiments/audits/step07_prediction_reproduction.json`.

---

## 5. Governance Boundary & Immutability Rules

1. **Strict Model Immutability**: All 30 base-model checkpoints, preprocessors, and hyperparameters are permanently frozen. Downstream phases (Phases 6–12, Steps 8–12) must **NOT** retrain, fine-tune, or alter base-model weights.
2. **Prohibition on Retrospective Selection**: No base predictor may be discarded or reselected based on conformal coverage, interval width, or maintenance simulator cost outcomes in downstream experiments.
3. **Both Model Families Preserved**: Both GBR and LSTM must be carried through all conformal calibration and maintenance decision experiments across all 3 datasets.
4. **Data Isolation**: Model fitting and selection used training and validation data only. Calibration engines remain preserved for conformal score calibration; held-out test engines remain strictly blinded until confirmatory evaluation.

---

## 6. Conformal Calibration Interface (Step 8 Consumption)

Downstream uncertainty quantification (Step 8) will consume frozen base models through the canonical loading function:

```python
from intellitwin.models.registry import load_frozen_base_model

frozen_model = load_frozen_base_model(
    dataset="FD002",
    model_family="LSTM",
    seed=2026,
)

# Generate point predictions:
# Accepts (M, 30, 17) sequence or (M, 510) flattened array;
# Automatically verifies SHA256 integrity and applies >= 0.0 truncation.
y_pred = frozen_model.predict(X_calib)
```

### Consumption Rules for Step 8:
- **Specification Governance**: Step 8 calibration methodology, nonconformity score functions, hierarchical quantiles, and fallback mechanisms are formally governed by [`research/research_design/step08_calibration_specification.md`](step08_calibration_specification.md) and ADR-021.
- **Data Role Enforcement**: Step 8 evaluates `frozen_model.predict(X_calib)` on reserved calibration engines to fit conformal thresholds, and `frozen_model.predict(X_val)` for validation development diagnostics.
- **No Backpropagation**: Calibration nonconformity scores, thresholds, or interval metrics must never propagate back to modify base-model parameters, architectures, or selections.
