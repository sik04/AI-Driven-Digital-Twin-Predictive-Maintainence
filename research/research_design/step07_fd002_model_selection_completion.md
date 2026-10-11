# Step 7.3 — FD002 Base-Model Implementation and Configuration Selection Completion Record

> **Status**: **COMPLETE**  
> **Dataset**: **FD002** — 6 operating conditions, 1 fault mode  
> **Protocol Reference**: `step07-selection-v1` / ADR-019 / `step07-base-predictor-v1`  
> **Selection Metric**: Equal-engine-weighted uncapped-RUL RMSE  
> **Selection Seeds**: 2026, 2027  
> **Calibration Data Used**: **NO**  
> **Held-Out Test Data Used**: **NO**  
> **Model-Selection Result Role**: Development/validation result only; **NOT** confirmatory RQ1–RQ4 evidence  

---

## 1. Specification and Provenance Boundaries

| Field | Value / Status |
| :--- | :--- |
| **Status** | **COMPLETE** |
| **Dataset** | FD002 |
| **Training Target** | `min(rul_true, 125)` (`rul_target_cap_125`) |
| **Validation Selection Metric** | Equal-engine-weighted uncapped-RUL RMSE |
| **Prediction Post-Processing** | Non-negative truncation: $\max(0.0, \hat{y})$ (no validation upper capping) |
| **Selection Seeds** | 2026, 2027 |
| **Preprocessing Artifact Path** | `experiments/preprocessing/FD002/preprocessor.json` |
| **Preprocessing Artifact SHA-256** | `cef04b8dafc4c9f53aba7c6bcb0bc67fc981540abdafadc76fafa314684d856c` |
| **Raw FD002 SHA-256** | `dac6c4dbc4e7c1bdeb5747da3d313d05c395bb99801b44a002b26a2ba13d788f` |
| **Split Manifest Path** | `data/splits/fd002_engine_split_seed_2026.json` |
| **Split Manifest SHA-256** | `57c815e4c97d9016bbfe9c91ab90738df0f3487910df889a0c631dde71894e41` |
| **Training Partition** | 130 engines, 22,923 windows |
| **Validation Partition** | 26 engines, 4,669 windows |
| **Calibration Partition** | 52 engines, UNTOUCHED (reserved for conformal calibration) |
| **Held-Out Test Partition** | 52 engines, UNTOUCHED (reserved for confirmatory evaluation) |
| **Implementation Commit** | `eba327dcc8eec660e06cf238e3a207d3af9826c1` |

---

## 2. GBR Selection Results (16 Runs)

- **Candidate Configurations**: 8 fixed grid configurations (learning rate $\in \{0.05, 0.10\}$, max leaf nodes $\in \{15, 31\}$, L2 regularization $\in \{0.0, 1.0\}$)
- **Selection Seeds**: 2026, 2027 (16 total GBR runs)
- **Training Input**: Flattened causal windows $(M, 510)$ with equal-engine sample weights
- **Loss**: Squared error, no internal early stopping, `max_iter=300`

### 2.1 Candidate Performance Summary

| Configuration ID | Learning Rate | Max Leaf Nodes | L2 Reg | Seed 2026 Val RMSE | Seed 2027 Val RMSE | Mean Selection RMSE | Worst-Seed Val RMSE | Val MAE (2026 / 2027) | Capped RMSE (2026 / 2027) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `gbr_lr005_leaf15_l2_0` | 0.05 | 15 | 0.0 | 35.3259 | 35.3259 | 35.3259 | 35.3259 | 23.9019 / 23.9019 | 17.6601 / 17.6601 |
| `gbr_lr005_leaf15_l2_1` | 0.05 | 15 | 1.0 | 35.3155 | 35.3155 | 35.3155 | 35.3155 | 23.8389 / 23.8389 | 17.6220 / 17.6220 |
| `gbr_lr005_leaf31_l2_0` | 0.05 | 31 | 0.0 | 35.0396 | 35.0396 | 35.0396 | 35.0396 | 23.7042 / 23.7042 | 17.4870 / 17.4870 |
| `gbr_lr005_leaf31_l2_1` | 0.05 | 31 | 1.0 | 35.0503 | 35.0503 | 35.0503 | 35.0503 | 23.7225 / 23.7225 | 17.5144 / 17.5144 |
| `gbr_lr010_leaf15_l2_0` | 0.10 | 15 | 0.0 | 34.8016 | 34.8016 | 34.8016 | 34.8016 | 23.5186 / 23.5186 | 17.4725 / 17.4725 |
| `gbr_lr010_leaf15_l2_1` | 0.10 | 15 | 1.0 | 34.8398 | 34.8398 | 34.8398 | 34.8398 | 23.5593 / 23.5593 | 17.5161 / 17.5161 |
| **`gbr_lr010_leaf31_l2_0`** | **0.10** | **31** | **0.0** | **34.6613** | **34.6613** | **34.6613** | **34.6613** | **23.5134 / 23.5134** | **17.4840 / 17.4840** |
| `gbr_lr010_leaf31_l2_1` | 0.10 | 31 | 1.0 | 34.6730 | 34.6730 | 34.6730 | 34.6730 | 23.5147 / 23.5147 | 17.4913 / 17.4913 |

### 2.2 Selected GBR Configuration

- **Selected Configuration ID**: `gbr_lr010_leaf31_l2_0`
- **Selected Mean Validation RMSE**: `34.6613` cycles (34.66132808744305)
- **Selected Worst-Seed Validation RMSE**: `34.6613` cycles
- **Validation MAE Summary**: 23.5134 cycles across both seeds
- **Capped-RMSE Summary**: 17.4840 cycles across both seeds
- **Tie Detected**: `false` (clear minimum score; tie-breaking rules not invoked)
- **Artifacts**: Summary stored at `experiments/model_selection/FD002/gbr_selection.json`

---

## 3. LSTM Selection Results (8 Runs)

- **Candidate Configurations**: 4 fixed grid configurations (hidden size $\in \{32, 64\}$, learning rate $\in \{0.0003, 0.0010\}$)
- **Architecture**: Single-layer unidirectional LSTM (input size 17, lookback 30, hidden size $H$, linear output 1) with explicit dropout $p=0.20$
- **Training Configuration**: AdamW ($\beta_1=0.9, \beta_2=0.999$, weight decay $10^{-4}$), batch size 256, max epochs 100, gradient clipping norm 1.0, weighted batch MSE loss
- **Validation Early Stopping**: Monitored on frozen validation partition uncapped RMSE, patience 10, min delta 0.01 cycles; best checkpoint restored

### 3.1 Candidate Performance Summary

| Configuration ID | Hidden Size | Learning Rate | Seed 2026 Val RMSE | Seed 2027 Val RMSE | Mean Selection RMSE | Worst-Seed Val RMSE | Best Epoch (2026 / 2027) | Val MAE (2026 / 2027) | Capped RMSE (2026 / 2027) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `lstm_h32_lr0003` | 32 | 0.0003 | 47.9261 | 48.0658 | 47.9959 | 48.0658 | 15 / 17 | 31.8746 / 31.8886 | 26.9681 / 27.1111 |
| `lstm_h32_lr0010` | 32 | 0.0010 | 38.0069 | 38.6496 | 38.3283 | 38.6496 | 45 / 38 | 25.1091 / 25.3524 | 19.3879 / 19.5695 |
| `lstm_h64_lr0003` | 64 | 0.0003 | 36.9390 | 37.7008 | 37.3199 | 37.7008 | 91 / 93 | 24.6630 / 25.1792 | 18.8151 / 19.5587 |
| **`lstm_h64_lr0010`** | **64** | **0.0010** | **35.1934** | **35.3113** | **35.2523** | **35.3113** | **59 / 63** | **23.7970 / 23.8566** | **19.2489 / 19.6714** |

### 3.2 Selected LSTM Configuration

- **Selected Configuration ID**: `lstm_h64_lr0010`
- **Selected Mean Validation RMSE**: `35.2523` cycles (35.2523236139771)
- **Selected Worst-Seed Validation RMSE**: `35.3113` cycles (35.31126599937067)
- **Best Epochs per Selection Seed**:
  - Seed 2026: Epoch 59 (completed 69 epochs before early stopping)
  - Seed 2027: Epoch 63 (completed 73 epochs before early stopping)
- **Validation MAE Summary**: 23.7970 cycles (seed 2026) / 23.8566 cycles (seed 2027)
- **Capped-RMSE Summary**: 19.2489 cycles (seed 2026) / 19.6714 cycles (seed 2027)
- **Tie Detected**: `false` (clear minimum score; tie-breaking rules not invoked)
- **Artifacts**: Summary stored at `experiments/model_selection/FD002/lstm_selection.json`

---

## 4. Scientific Safeguards & Boundary Affirmation

1. **Strict Data Boundary Separation**:
   - `train` engines (130) were used exclusively for parameter optimization (22,923 windows).
   - `val` engines (26) were used exclusively for configuration ranking and early-stopping checkpoint selection (4,669 windows).
   - `cal` engines (52) were strictly untouched (no predictions, no evaluation, no conformal fitting).
   - `test` engines (52) were strictly untouched (reserved for confirmatory evaluation).
2. **Deterministic Reproducibility**:
   - Exact seed sequences set across `random`, `numpy`, and PyTorch (CPU deterministic algorithm flags enabled).
   - Checkpoints persisted and verified loadable on CPU (`map_location="cpu"`).
3. **Scope Clarification**:
   - These are base-predictor development results only.
   - They do **NOT** constitute confirmatory evidence for RQ1–RQ4.
   - They do **NOT** evaluate condition-adaptive conformal calibration or maintenance cost policies.
