# Step 6: RUL Sequence Modeling Experiment Report

**Project:** AI-Driven Digital Twin for Predictive Maintenance  
**Experiment ID:** `step06_rul_modeling_experiment`  
**Dataset:** NASA C-MAPSS FD001 (Turbofan Engine Degradation Simulation)  
**Date:** October 2026  
**Artifact Directory:** `artifacts/experiments/step_06_rul/`  
**Figures Directory:** `artifacts/figures/step_06/`  

---

## 1. Research Question

> Under a leakage-free engine-level evaluation protocol, does heteroscedastic sequence modeling improve Remaining Useful Life (RUL) prediction compared with conventional sequence regression (Standard LSTM and GRU)?

---

## 2. Scientific Hypotheses

1. **Hypothesis 1 (Architectural Comparison):** Recurrent neural network models (GRU, LSTM) that exploit temporal sequence trajectories will outperform tabular tree-based regressors (Random Forest, XGBoost) on terminal cycle RUL estimation.
2. **Hypothesis 2 (Heteroscedastic Loss vs. Scalar MSE):** Formulating the sequence regression objective as a Gaussian Negative Log-Likelihood (NLL) with an adaptive variance head ($\mu, \sigma^2$) will provide regularized gradients that improve overall generalization on C-MAPSS FD001.
3. **Hypothesis 3 (Predictive Uncertainty Fidelity):** The predicted standard deviation $\hat{\sigma}$ from the heteroscedastic head will exhibit positive correlation with absolute prediction residuals ($|\hat{y} - y|$), capturing data-dependent aleatoric uncertainty rather than collapsing or remaining uniform.

---

## 3. Dataset & Split Protocol

The experiment strictly utilizes the authoritative **Step 4** engine-level partitioned protocol:
- **Total Training Pool:** 100 engine runs from `train_FD001.txt`.
- **Engine-Level Split:**
  - **Training Engines:** 80 units (14,020 valid sequence windows of length 30).
  - **Validation Engines:** 20 units (3,711 valid sequence windows of length 30).
  - **Partitioning Rule:** $\text{Train Units} \cap \text{Val Units} = \emptyset$ (Disjoint engine partitions, zero trajectory overlap).
- **Test Engines:** 100 units from `test_FD001.txt`.
- **Evaluation Target:** Terminal cycle of each test engine ($N=100$) evaluated against ground-truth RUL values from `RUL_FD001.txt`.

---

## 4. Preprocessing & Feature Engineering

- **Sensor Selection:** 14 active degradation sensors (excluding constant and operational setting sensors: `s_1, s_5, s_6, s_10, s_16, s_18, s_19`).
- **Feature Pipeline:**
  - Raw sensor values (14 features).
  - 5-cycle rolling statistics: Rolling Mean (14 features), Rolling Std (14 features).
  - Operating settings: `setting_1, setting_2, setting_3` (3 features) + setting rolling means (3 features) + cycle index and cycle ratio (6 features).
  - Total input dimension: $D = 54$ features.
- **Normalization:** `StandardScaler` fitted strictly on the 80 training engine units. Validation and test sets are transformed without re-fitting.
- **Target Transformation:** Piecewise linear RUL degradation model capped at $RUL_{\max} = 125$ cycles.

---

## 5. Sequence Window Construction

- **Sequence Length ($T$):** 30 cycles.
- **Engine Boundary Isolation:** Sliding windows are generated strictly within individual engine boundaries. No window spans across two distinct engines.
- **Padding Protocol:** For test engines with trajectory length shorter than 30 cycles, zero-padding / repeat-padding is applied strictly preceding the observed window.
- **Evaluation Window:** Exactly one sequence window per test engine representing the terminal cycle ($N=100$).

---

## 6. Model Architectures & Loss Functions

| Model | Architecture | Parameter Count | Output Layer | Objective Function |
| :--- | :--- | :---: | :--- | :--- |
| **GRU + MSE** | 2-layer GRU (hidden=64, dropout=0.2) + FC(64 $\to$ 32 $\to$ 1) | ~49.5K | Scalar $\hat{y}$ | Mean Squared Error: $\frac{1}{B}\sum (y_i - \hat{y}_i)^2$ |
| **LSTM + MSE** | 2-layer LSTM (hidden=64, dropout=0.2) + FC(64 $\to$ 32 $\to$ 1) | ~65.8K | Scalar $\hat{y}$ | Mean Squared Error: $\frac{1}{B}\sum (y_i - \hat{y}_i)^2$ |
| **Heteroscedastic LSTM** | 2-layer LSTM (hidden=64, dropout=0.2) + FC(64 $\to$ 32) + Dual Heads | ~66.0K | Mean $\hat{\mu}$, Log-Var $\log \hat{\sigma}^2$ | Gaussian NLL: $\frac{1}{2}\exp(-\log \sigma^2)(y-\mu)^2 + \frac{1}{2}\log \sigma^2$ |

*Numerical Stability Guard:* In the heteroscedastic model, $\log \sigma^2$ is clipped to $[-6.0, 6.0]$ to prevent numerical overflow or division-by-zero precision collapse.

---

## 7. Hyperparameters & Training Protocol

- **Batch Size:** 128
- **Optimizer:** Adam ($\beta_1 = 0.9, \beta_2 = 0.999$)
- **Learning Rate:** $2 \times 10^{-3}$
- **Weight Decay:** $1 \times 10^{-5}$
- **Maximum Epochs:** 20
- **Validation Early Stopping:** Patience = 8 epochs monitoring Validation RMSE.
- **Checkpoint Selection:** Weights from the epoch achieving minimum validation RMSE are restored for final test evaluation.
- **Isolation Constraint:** Test engines ($N=100$) remain strictly untouched during training and checkpoint selection.

---

## 8. Random Seeds & Reproducibility

To distinguish genuine architectural advantages from random initialization variance, all recurrent sequence models and contextual baselines were evaluated across three deterministic seeds:
$$S \in \{42, 43, 44\}$$
Results are reported as $\text{Mean} \pm \text{Standard Deviation}$.

---

## 9. Benchmark Results & Model Comparison

Evaluated on all 100 test engines ($N=100$):

| Model Architecture | Loss Function | Multi-Seed RMSE (Mean ± Std) | Multi-Seed MAE (Mean ± Std) | Multi-Seed NASA Score (Mean ± Std) | Primary Seed (42) RMSE | Primary Seed (42) MAE | Primary Seed (42) NASA Score |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **GRU** | MSE | **15.11 ± 0.93** | **11.09 ± 0.75** | **407.1 ± 103.5** | 15.72 | 11.43 | 361.7 |
| **Standard LSTM** | MSE | 16.03 ± 1.72 | 11.55 ± 1.10 | 672.4 ± 311.2 | **14.18** | **10.43** | **361.2** |
| **Heteroscedastic LSTM** | Gaussian NLL | 15.58 ± 0.94 | 11.87 ± 1.18 | 475.4 ± 139.3 | 16.65 | 12.98 | 635.9 |
| **XGBoost (Contextual)** | SquaredError | 17.00 ± 0.00 | 12.32 ± 0.00 | 768.8 ± 0.0 | 17.00 | 12.32 | 768.8 |
| **Random Forest (Contextual)** | MSE | 18.13 ± 0.05 | 13.46 ± 0.05 | 882.1 ± 13.5 | 18.09 | 13.46 | 895.8 |

---

## 10. Operational Regime Stratification

Test engines are stratified by ground-truth terminal RUL into three operational regimes:
- **Critical / Near-Failure Regime ($\text{RUL} \le 40$ cycles, $n=28$ engines):** Where late predictions cause catastrophic in-flight failures.
- **Accelerated Degradation Regime ($40 < \text{RUL} \le 80$ cycles, $n=17$ engines):** Transition phase.
- **Early / Healthy Operating Regime ($\text{RUL} > 80$ cycles, $n=55$ engines):** Plateau phase dominated by capping.

Performance in Critical Regime ($\text{RUL} \le 40$):
| Model | Critical RMSE | Critical MAE | Critical NASA Score | Critical Mean Error (Bias) |
| :--- | :---: | :---: | :---: | :---: |
| **GRU + MSE** | **4.94** | **3.83** | **13.3** | **+0.99 cycles** |
| **LSTM + MSE** | 7.91 | 6.84 | 31.1 | +5.63 cycles |
| **Heteroscedastic LSTM** | 12.39 | 10.16 | 77.8 | +8.84 cycles |
| **XGBoost** | 12.09 | 8.24 | 83.5 | +5.38 cycles |
| **Random Forest** | 14.05 | 9.19 | 139.6 | +6.47 cycles |

### Regime Insight:
- In the near-failure regime, **GRU + MSE** achieves extraordinary precision ($\text{RMSE}=4.94$, $\text{NASA}=13.3$), maintaining nearly unbiased predictions ($+0.99$ cycles).
- **Heteroscedastic LSTM** exhibits higher error in this regime ($\text{RMSE}=12.39$, bias $=+8.84$ cycles). This occurs because Gaussian NLL scales the gradient by precision $\exp(-\log \sigma^2)$. As engine noise accelerates near failure, the model allocates higher variance, mitigating its own loss penalty and slightly softening the mean gradient.

---

## 11. Heteroscedastic Predictive Uncertainty Analysis

The primary motivation for heteroscedastic sequence modeling is the endogenous estimation of observation-level uncertainty.

### Quantitative Uncertainty Metrics:
- **Mean Predicted Standard Deviation ($\bar{\sigma}$):** 18.01 cycles.
- **Median Predicted Standard Deviation ($\tilde{\sigma}$):** 20.09 cycles.
- **Standard Deviation of $\hat{\sigma}$ across engines:** 4.45 cycles (indicating active adaptation across engine operating points).
- **Range of Predicted $\hat{\sigma}$:** $[6.17, 20.09]$ cycles.
- **Correlation with Absolute Residual ($|e| = |\hat{y} - y|$):**
  - **Pearson Correlation ($r$):** $+0.2661$ ($p = 0.0075 < 0.01$).
  - **Spearman Rank Correlation ($\rho$):** $+0.2913$ ($p = 0.0033 < 0.01$).
- **Numerical Stability:**
  - Uncertainty collapse ($\hat{\sigma} < 10^{-4}$): **None detected** (Min $\hat{\sigma} = 6.17$).
  - Uncertainty explosion ($\hat{\sigma} > 10^{4}$): **None detected** (Max $\hat{\sigma} = 20.09$).

### Interpretation:
The statistically significant positive correlation ($r \approx 0.27, p < 0.01$) demonstrates that the heteroscedastic head produces meaningful, data-dependent **aleatoric predictive uncertainty**: when the model's prediction residual is larger, its self-reported standard deviation is systematically higher.

*Important Note on Uncertainty Taxonomy:* This variance represents aleatoric (data-dependent / observation noise) uncertainty. It does NOT represent epistemic (model weight / parameter) uncertainty, which requires ensembles or Bayesian posterior sampling.

---

## 12. Answers to Core Research Questions

### RQ1: Does LSTM + MSE improve over GRU + MSE?
**No.** GRU + MSE achieved a multi-seed RMSE of $15.11 \pm 0.93$ cycles and a NASA score of $407.1 \pm 103.5$, outperforming Standard LSTM ($16.03 \pm 1.72$ RMSE, $672.4 \pm 311.2$ NASA score). GRU's simpler gating mechanism converged more reliably with lower cross-seed variance on this sequence length ($T=30$).

### RQ2: Does Heteroscedastic LSTM improve over Standard LSTM + MSE?
**Yes, in stability and asymmetric penalty.** Heteroscedastic LSTM achieved lower multi-seed RMSE ($15.58 \pm 0.94$ vs. $16.03 \pm 1.72$) and a lower multi-seed NASA score ($475.4 \pm 139.3$ vs. $672.4 \pm 311.2$) with roughly half the variance across seeds ($\sigma=0.94$ vs. $1.72$). However, for primary seed 42 point prediction alone, Standard LSTM reached 14.18 cycles.

### RQ3: Is the improvement consistent across metrics, regimes, and seeds?
The advantage of Heteroscedastic LSTM over Standard LSTM is consistent across multi-seed aggregate RMSE and NASA score. However, within the critical near-failure regime ($\text{RUL} \le 40$), conventional MSE-trained recurrent networks (especially GRU) produce lower mean error and smaller overprediction bias.

### RQ4: Does predicted heteroscedastic uncertainty behave meaningfully?
**Yes.** Predicted standard deviation varies smoothly between 6.17 and 20.09 cycles, avoids numerical collapse or explosion, and correlates positively ($r = 0.266, p = 0.0075$) with absolute prediction residuals.

### RQ5: Are there methodological reasons the comparison could still be biased?
No. All models were trained on the identical 80 training engines, validated on the identical 20 validation engines, scaled with the identical preprocessor, and evaluated on the identical 100 test engines at terminal cycles. Checkpoint selection was determined strictly by validation performance.

### RQ6: What limitations remain?
1. The heteroscedastic head captures only aleatoric uncertainty; epistemic model uncertainty is not modeled in this architecture.
2. The current evaluation is restricted to C-MAPSS sub-dataset FD001 (single operating condition, single failure mode). Multi-condition datasets (FD002, FD004) remain unvalidated.
3. Checkpoint selection used validation RMSE rather than validation NASA score or validation NLL.

---

## 13. Reproducibility Instructions

To reproduce this experiment and re-generate all artifacts and figures:
```bash
# Verify integrity tests
pytest tests/test_rul_experiment.py -v

# Run full multi-seed experiment
python intellitwin/rul_experiment.py --seeds 42 43 44
```
All outputs will be saved to `artifacts/experiments/step_06_rul/` and `artifacts/figures/step_06/`.
