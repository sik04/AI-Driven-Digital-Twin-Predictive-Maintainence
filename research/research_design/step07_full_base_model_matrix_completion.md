# Step 7.4 Completion Record: Full Multi-Dataset / Five-Seed Base-Model Matrix

- **Status**: COMPLETE
- **Execution Date**: 2026-10-12
- **Protocol Baseline**: ADR-019 / Step 7.1 (`research/research_design/step07_base_predictor_specification.md`)
- **Git Branch**: `feat/step7-full-base-model-matrix`

---

## 1. Selected Frozen Configurations (6 Cells)

| Dataset | Model Family | Selected Configuration ID | Hyperparameters Summary | Selection Score (Mean Val RMSE) | Worst-Seed Val RMSE |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FD001** | GBR | `gbr_lr010_leaf15_l2_0` | lr=0.10, max_leaf_nodes=15, l2=0.0, max_iter=300 | 28.4243 | 28.4243 |
| **FD001** | LSTM | `lstm_h64_lr0010` | hidden_size=64, lr=0.0010, batch=256, AdamW | 30.0831 | 30.1055 |
| **FD002** | GBR | `gbr_lr010_leaf31_l2_0` | lr=0.10, max_leaf_nodes=31, l2=0.0, max_iter=300 | 34.6613 | 34.6613 |
| **FD002** | LSTM | `lstm_h64_lr0010` | hidden_size=64, lr=0.0010, batch=256, AdamW | 35.2524 | 35.3113 |
| **FD004** | GBR | `gbr_lr010_leaf31_l2_0` | lr=0.10, max_leaf_nodes=31, l2=0.0, max_iter=300 | 48.8283 | 48.8283 |
| **FD004** | LSTM | `lstm_h64_lr0010` | hidden_size=64, lr=0.0010, batch=256, AdamW | 48.2471 | 48.3554 |

*Note: FD002 winning configurations were strictly preserved from Step 7.3 under ADR-019 and not retuned.*

---

## 2. Production Matrix Dimensions and Totals

- **Datasets**: `FD001`, `FD002`, `FD004` (3 datasets)
- **Model Families**: `GBR`, `LSTM` (2 model families)
- **Official Seeds**: `2026`, `2027`, `2028`, `2029`, `2030` (5 seeds, no extras, no missing, no replacements)
- **Total Official Models**: **30** (3 datasets × 2 families × 5 seeds)

---

## 3. Verification and Integrity Audits

- **Total Final Models Trained**: 30 / 30
- **Checkpoint Load Verification on CPU**: **30 / 30 PASSED**
- **Metadata Record Verification**: **30 / 30 PASSED**
- **Validation Prediction Artifacts**: **30 / 30 PASSED**
- **Calibration Data Used**: **NO** (Strictly excluded from base-predictor development)
- **Held-Out Test Data Used**: **NO** (Strictly excluded from base-predictor development)
- **Training Target**: $\min(\text{rul\_true}, 125)$
- **Validation Evaluation Target**: Uncapped $\text{rul\_true}$
- **Prediction Post-Processing**: Non-negative truncation $\max(0.0, \hat{y})$ (no upper cap at 125)

---

## 4. Five-Seed Production Performance Summaries

### Summary Artifact Paths
1. `experiments/base_models/FD001/GBR/summary.json`
2. `experiments/base_models/FD001/LSTM/summary.json`
3. `experiments/base_models/FD002/GBR/summary.json`
4. `experiments/base_models/FD002/LSTM/summary.json`
5. `experiments/base_models/FD004/GBR/summary.json`
6. `experiments/base_models/FD004/LSTM/summary.json`

### Validation Performance Summary (Development/Validation Results Only)

> [!NOTE]
> These metrics represent development and validation partition evaluations only. They do NOT constitute confirmatory held-out test evidence. Seed variability reflects optimization stochasticity across the official seed suite and does not constitute a statistical confidence interval.

| Dataset | Family | Configuration | Uncapped RMSE (mean ± std) | Uncapped MAE (mean ± std) | Capped RMSE (mean ± std) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FD001** | GBR | `gbr_lr010_leaf15_l2_0` | $28.4243 \pm 0.0000$ | $20.1102 \pm 0.0000$ | $15.4009 \pm 0.0000$ |
| **FD001** | LSTM | `lstm_h64_lr0010` | $29.8987 \pm 0.2304$ | $20.3561 \pm 0.2628$ | $16.1005 \pm 0.4126$ |
| **FD002** | GBR | `gbr_lr010_leaf31_l2_0` | $34.6613 \pm 0.0000$ | $23.2710 \pm 0.0000$ | $17.2674 \pm 0.0000$ |
| **FD002** | LSTM | `lstm_h64_lr0010` | $35.1374 \pm 0.2332$ | $23.7824 \pm 0.1396$ | $19.5011 \pm 0.2081$ |
| **FD004** | GBR | `gbr_lr010_leaf31_l2_0` | $48.8283 \pm 0.0000$ | $31.9559 \pm 0.0000$ | $16.2977 \pm 0.0000$ |
| **FD004** | LSTM | `lstm_h64_lr0010` | $48.6663 \pm 0.3569$ | $31.6923 \pm 0.1823$ | $17.1145 \pm 0.5379$ |

---

## 5. Artifact Completeness per Model Directory

Each seed directory under `experiments/base_models/{DATASET}/{FAMILY}/seed_{SEED}/` contains:
- `checkpoint`: Serialized model checkpoint (CPU loadable).
- `metadata.json`: Machine-readable metadata conforming to schema `step07-base-model-v1`.
- `metrics.json`: Uncapped RMSE, uncapped MAE, and capped RMSE.
- `validation_predictions.csv`: Sequential predictions sorted strictly by `unit ASC, endpoint_cycle ASC`.
