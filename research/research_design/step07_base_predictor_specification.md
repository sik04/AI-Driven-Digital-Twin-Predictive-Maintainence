# Step 7.1 — Base Predictor Specification

> **Document Status**: **Frozen Specification (ADR-019)**  
> **Authors**: Mayank Singh, Shiksha Pandey, Ruchi Gupta  
> **Protocol Reference**: `step06-v2` / ADR-018 / ADR-019  
> **Scientific Role**: Supporting Point-RUL Base Predictors  
> **Implementation Scope**: Base predictor implementation, model selection, matrix training, and formal freeze completed under ADR-019 and ADR-020 (Step 7 Complete).

---

## 1. Executive Summary & Scientific Positioning

This document defines the exact, frozen specification for the point-RUL base predictors in the IntelliTwin research framework.

In accordance with ADR-002, ADR-018, and ADR-019:
- **Base predictors serve as supporting infrastructure**: They provide foundational point remaining useful life (RUL) estimates for subsequent conformal uncertainty calibration.
- **Novelty boundary**: The core scientific contribution of IntelliTwin is **decision-aware, condition-adaptive conformal calibration linked to sequential maintenance utility**, NOT a novel point-prediction neural network architecture or a broad benchmark of standard regression algorithms.
- **Frozen scope**: Only two established model families are evaluated:
  1. **GBR**: Histogram Gradient Boosting Regressor (`sklearn.ensemble.HistGradientBoostingRegressor`).
  2. **LSTM**: Single-layer unidirectional Long Short-Term Memory network (`torch.nn.LSTM`).
  No additional predictor families (e.g., SVR, Random Forest, MLP, GRU, Transformers) form part of this frozen design.

---

## 2. Dataset Scope, Inputs, and Preprocessing

### 2.1 Datasets
- **FD002 (Primary)**: 6 operating regimes, 1 fault mode. Primary multi-operating-condition benchmark for RQ1–RQ3.
- **FD001 (Control)**: 1 operating regime, 1 fault mode (HPC). Single-condition control benchmark for RQ4.
- **FD004 (Robustness)**: 6 operating regimes, 2 fault modes (HPC + Fan). Complex multi-condition robustness benchmark for RQ4.
- *FD003 remains optional/inactive.*

### 2.2 Sequence Windowing and Input Geometry
- **Causal Lookback**: Fixed window length $W = 30$ cycles.
- **Stride**: Stride 1 (every consecutive valid cycle window $t \ge 30$).
- **Padding**: Strictly **NO** zero-padding or synthetic head padding. Engines with lifetime $T < 30$ cannot form valid 30-cycle causal windows and are ineligible.
- **Feature Schema**: 17 frozen features (3 operating settings + 14 non-constant degradation sensors), in exact canonical order established in Step 5 (`data_evaluation_protocol.md`).
- **GBR Input**: Flattened 2D array of shape `(batch_size, 510)` ($30 \times 17 = 510$ flattened features).
- **LSTM Input**: 3D tensor of shape `(batch_size, 30, 17)` (`batch_first=True`).

### 2.3 Preprocessing Scaling
- Z-score standard scaling fitted **strictly on training engines only**. Zero-variance features across training engines are left unscaled (scale factor 1.0, mean subtracted) to prevent division by zero.
- Validation, calibration, and test engines are transformed using the fitted training scaler parameters.

---

## 3. Data Partition Roles and Information Boundaries

In accordance with the authoritative data protocol:
- **Training Data**: Used for preprocessing scaler fitting and model parameter estimation (tree splits / network weights).
- **Validation Data**: Used for hyperparameter selection, checkpoint selection, matched-control parameter selection, maintenance-policy development, and protocol debugging.
- **Calibration Data**: Strictly reserved for fitting the subsequent conformal calibration mechanism (Step 8). **Must NOT be touched or used for model selection, hyperparameter tuning, or matched-control optimization during Step 7.**
- **Held-Out Test Data**: Strictly reserved for final confirmatory hypothesis evaluation (Step 9+). **Must NEVER be inspected, transformed, or evaluated during Step 7.**

---

## 4. Targets, Weighting, and Evaluation Metrics

### 4.1 Supervised Training Target
- Piecewise linear RUL target capped at $R_{\text{max}} = 125$ cycles:
  $$\text{rul\_target} = \min(\text{rul\_true}, 125)$$
- The 125-cycle cap encourages stability in early engine life where degradation is undetectable. It is strictly an engineering training cap, not a post-processing clamp on outputs.

### 4.2 Evaluation Target for Model Selection
- Model selection on validation data targets **uncapped true RUL** ($\text{rul\_true}$).
- Predictions are post-processed solely by non-negativity truncation:
  $$\hat{y} = \max(0.0, \hat{y}_{\text{raw}})$$
- Predictions are **NOT** capped at 125 cycles during validation or evaluation.

### 4.3 Engine-Weighted Training Loss Weighting
To prevent engines with long run-to-failure lifetimes from dominating gradient updates or tree splits, training samples are weighted so that every engine contributes equal total training weight:
- For engine $i$ with $n_i$ valid training windows, total training windows $M = \sum_{k=1}^N n_k$, and $N$ training engines:
  $$w_{i,t} = \frac{M}{N \cdot n_i}$$
- This ensures $\sum_{t=1}^{n_i} w_{i,t} = \frac{M}{N}$, giving each engine equal total mass in the loss objective.

### 4.4 Model Selection Metric
- **Primary Selection Metric**: Equal-engine-weighted uncapped-RUL Root Mean Squared Error (RMSE) on validation engines:
  $$\text{MSE}_i = \frac{1}{n_i} \sum_{t=30}^{T_i} (\hat{y}_{it} - y_{it})^2, \quad \text{RMSE}_{\text{engine}} = \sqrt{\frac{1}{N_{\text{val}}} \sum_{i=1}^{N_{\text{val}}} \text{MSE}_i}$$
  where $y_{it}$ is uncapped $\text{rul\_true}$.
- **Supporting Metrics**:
  - Engine-weighted Mean Absolute Error (MAE) against uncapped RUL.
  - Engine-weighted RMSE against capped target $\min(\text{rul\_true}, 125)$.

---

## 5. Model Specifications and Hyperparameter Search Grids

### 5.1 GBR (HistGradientBoostingRegressor)

Implemented via `sklearn.ensemble.HistGradientBoostingRegressor`.

#### Fixed Parameters
- `loss`: `"squared_error"`
- `early_stopping`: `False` (all configurations run to `max_iter` with fixed regularization)
- `validation_fraction`: `None`
- `min_samples_leaf`: `20`
- `max_bins`: `255`
- `max_features`: `1.0`
- `categorical_features`: `None`
- `warm_start`: `False`
- `random_state`: `run_seed`
- `max_iter`: `300`

#### Hyperparameter Search Grid (Exactly 8 Configurations)
- `learning_rate`: `[0.05, 0.10]`
- `max_leaf_nodes`: `[15, 31]`
- `l2_regularization`: `[0.0, 1.0]`

No other GBR hyperparameters may be tuned or adjusted.

---

### 5.2 LSTM (Unidirectional Single-Layer)

Implemented via PyTorch (`torch.nn.LSTM`).

#### Architecture
- Input: `(batch_size, 30, 17)`
- `LSTM(input_size=17, hidden_size=H, num_layers=1, batch_first=True, bidirectional=False, bias=True, dropout=0.0)`
- Slice final sequence step: `out = lstm_out[:, -1, :]` (shape `(batch_size, H)`)
- Explicit Dropout: `nn.Dropout(p=0.20)`
- Linear Projection: `nn.Linear(H, 1)`
- Output shape: `(batch_size, 1)`

#### Fixed Training Hyperparameters
- `optimizer`: `AdamW`
- `weight_decay`: `1e-4`
- `betas`: `(0.9, 0.999)`
- `eps`: `1e-8`
- `batch_size`: `256`
- `max_epochs`: `100`
- `gradient_clip_norm`: `1.0` (via `torch.nn.utils.clip_grad_norm_`)
- `early_stopping_patience`: `10` epochs
- `early_stopping_min_delta`: `0.01` RMSE cycles

#### Hyperparameter Search Grid (Exactly 4 Configurations)
- `hidden_size`: `[32, 64]`
- `learning_rate`: `[0.0003, 0.001]`

#### Validation Early Stopping Protocol
- Early stopping evaluates the frozen validation engines directly after every epoch.
- Predict all valid validation windows, compute per-engine MSE against uncapped $\text{rul\_true}$, average engine MSEs equally, and take the square root.
- A checkpoint is saved if and only if validation uncapped RMSE improves by at least $\Delta \ge 0.01$ cycles over the best observed epoch.
- Training terminates after 10 consecutive non-improving epochs. The best checkpoint is restored for final evaluation.
- Strictly **NO** random internal validation splitting inside the training script.

---

## 6. Selection Protocol, Seeds, and Artifact Counts

### 6.1 Hyperparameter Selection Seeds
- Candidate hyperparameter configurations are evaluated across seeds:
  $$\text{selection\_seeds} = [2026, 2027]$$
- For each candidate configuration $c$:
  $$\text{score}(c) = \frac{1}{2} \sum_{s \in \{2026, 2027\}} \text{RMSE}_{\text{val}}(c, s)$$
- The configuration with the lowest selection score is selected.

### 6.2 Deterministic Tie-Breaking
If the selection score difference between two candidate configurations is smaller than $1 \times 10^{-6}$ cycles, ties are resolved deterministically in order:
1. **Lower worst-seed validation RMSE**: $\min \max_{s \in \{2026, 2027\}} \text{RMSE}_{\text{val}}(c, s)$.
2. **Lower-complexity configuration**:
   - GBR: fewer `max_leaf_nodes` is simpler; if equal, smaller `l2_regularization` search tuple ordering; if equal, smaller `learning_rate`.
   - LSTM: smaller `hidden_size` is simpler; if equal, smaller `learning_rate`.
3. **Lexicographically smaller configuration identifier** (e.g., `"cfg_01"` before `"cfg_02"`).

### 6.3 Official Five-Seed Production Runs
After the optimal configuration is selected and frozen per (dataset, model family), the selected configuration is trained across all five official random seeds:
$$\text{model\_seeds} = [2026, 2027, 2028, 2029, 2030]$$

### 6.4 Total Final Model Artifacts
$$3 \text{ datasets (FD002, FD001, FD004)} \times 2 \text{ model families (GBR, LSTM)} \times 5 \text{ seeds} = 30 \text{ final model artifacts}$$

---

## 7. Provenance, Reproducibility, and Logging Fields

Every training run must record and persist a standardized metadata record containing:
- `dataset`: (`FD001`, `FD002`, `FD004`)
- `model_family`: (`GBR`, `LSTM`)
- `configuration_id`: (e.g., `gbr_lr0.05_leaf31_l20.0`)
- `run_seed`: integer
- `git_commit`: commit SHA
- `git_dirty`: boolean (`false` required for official artifacts)
- `raw_dataset_sha256`: SHA-256 of source raw C-MAPSS file
- `split_manifest_sha256`: SHA-256 of split manifest
- `preprocessing_scaler_sha256`: SHA-256 of saved scaler artifact
- `complete_hyperparameters`: full dict of fixed and tuned hyperparameters
- `software_versions`:
  - `python_version`
  - `numpy_version`
  - `pandas_version`
  - `scikit_learn_version`
  - `torch_version`
- `hardware_device`: CPU / CUDA device name
- `training_duration_seconds`: float
- `best_epoch`: int (for LSTM)
- `validation_uncapped_rmse`: float
- `validation_uncapped_mae`: float
- `validation_capped_rmse`: float
- `checkpoint_sha256`: SHA-256 of model checkpoint file
- `prediction_artifact_sha256`: SHA-256 of generated validation predictions

PyTorch execution must enforce reproducibility:
```python
import random
import numpy as np
import torch

random.seed(seed)
np.random.seed(seed)
torch.manual_seed(seed)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(seed)
torch.use_deterministic_algorithms(True, warn_only=True)
```

---

## 8. Boundary Constraints

- **Implementation Status**: GBR and LSTM base predictors, 24-run model selection, 30-model production matrix, and independent verification are COMPLETE and immutably frozen under ADR-020.
- All 30 model artifacts are registered in `experiments/base_models/model_registry.json`.
- Base predictor parameters, architectures, and weights are strictly frozen and may not be altered by downstream calibration or simulation steps.
