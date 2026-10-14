# Proposed Methodology and Technical Architecture

**Document Version**: `1.0`  
**Governing ADRs**: `ADR-011`, `ADR-012`, `ADR-013`, `ADR-018`, `ADR-019`, `ADR-020`, `ADR-021`, `ADR-022`, `ADR-023`  
**Target Codebase**: `src/intellitwin/{data, models, uncertainty, decision, simulator, evaluation}`  
**Status**: Authoritative Technical Specification and Research Draft

---

## 1. Overview of the Predictive Maintenance Pipeline

The IntelliTwin methodology integrates five interconnected layers:
1. **Data Curation & Causal Windowing**: Strict engine-level partition isolation, training-only fitted scaling, zero-leakage causal temporal windowing, and dual-horizon target construction across C-MAPSS FD001, FD002, and FD004.
2. **Frozen Point Predictor Matrix**: High-capacity non-neural (Histogram Gradient Boosting Regressor) and deep recurrent (unidirectional LSTM) architectures trained across 5 official seeds on training engines under validation-only checkpoint selection.
3. **Engine-Weighted Conformal Calibration**: Multi-regime hierarchical conformal calibration implementing exact engine-weighted quantiles, finite-score mass bounding ($m/(m+1)$), and candidate configuration selection.
4. **Decision-Aware Asymmetric Score Inversion**: Dynamic modulation of interval width and asymmetry near the critical end-of-life decision boundary.
5. **Sequential Maintenance Simulation**: Discrete-event trace-driven simulation of operational replacement policies under transparent, pre-registered economic cost scenarios.

```
Raw C-MAPSS Run-to-Failure Telemetry (FD001, FD002, FD004)
                     │
                     ▼
  [Engine-Level Partitioning: Train (50%) / Cal (20%) / Val (10%) / Test (20%)]
                     │
                     ▼
  [Training-Only Preprocessing: 17 Features, Zero-Variance Removal, Robust Scaling]
                     │
                     ▼
  [Causal Sliding Windowing: W=30 Cycles, Stride=1, No Padding]
       ├── LSTM: 30 × 17 Sequential Tensors
       └── GBR:  510-Dimensional Flattened Vectors
                     │
                     ▼
  [Frozen Base Point Predictors: Capped RUL (max 125 cycles), 5 Seeds (2026-2030)]
       └── Predictions p_it >= 0.0
                     │
                     ▼
  [Conformal Calibration Layer (Reserved Calibration Partition)]
       ├── Global Hierarchical Calibration (global_hcp)
       ├── Condition-Aware Hierarchical Calibration (regime_hcp)
       └── Decision-Aware Asymmetric Calibration (decision_aware_hcp: gamma2_betam1)
                     │
                     ▼
  [Prediction Intervals: [L_it, U_it] calibrated against True Uncapped RUL]
                     │
                     ▼
  [Sequential Maintenance Simulator: lower_bound_one_cycle_policy]
       └── Output: Maintenance Cost, Failure Rate, Wasted Life, Inefficient Early PM
```

---

## 2. Dataset Partitioning, Preprocessing, and Causal Windowing

### 2.1 Qualified C-MAPSS Datasets and Operating Characteristics
Under ADR-011, three subsets of the NASA C-MAPSS benchmark are qualified:
- **FD001**: Single sea-level operating condition, single fault mode (High-Pressure Compressor [HPC] degradation). Serves as the baseline single-regime control. Total 100 engines.
- **FD002**: Six discrete operating conditions (combinations of altitude, Mach number, and throttle resolver angles), single fault mode (HPC degradation). Serves as the primary confirmatory dataset for complex multi-regime evaluation. Total 260 engines.
- **FD004**: Six discrete operating conditions, two complex fault modes (HPC degradation and fan degradation). Serves as the extended multi-fault robustness benchmark. Total 249 engines.
- *(Note: FD003 contains 1 operating condition and 2 fault modes; it is excluded from the active evaluation matrix to keep cell weighting balanced across multi-regime complexity).*

### 2.2 Strict Engine-Level Partitioning
To prevent cross-trajectory data leakage, all dataset splits are constructed strictly at the **engine level**. The entire run-to-failure trajectory of any physical engine belongs exclusively to exactly one partition:
- **Training (approx. 50%)**: Used exclusively for fitting preprocessors, training base point predictors, and fitting K-Means regime clusterers.
- **Calibration (approx. 20%)**: Reserved strictly for fitting conformal calibration nonconformity thresholds. Never inspected during base-model hyperparameter selection.
- **Validation (approx. 10%)**: Used for hyperparameter tuning, checkpoint early stopping, candidate calibrator selection, and matched-control parameter selection.
- **Held-Out Test (approx. 20%)**: Immutably sealed until confirmatory evaluation. Never touched during model development.

#### Exact Partition Engine Counts
| Dataset | Total Engines | Training Engines | Calibration Engines | Validation Engines | Held-Out Test Engines | Split Manifest Path |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **FD001** | 100 | 50 | 20 | 10 | 20 | `data/splits/fd001_engine_split_seed_2026.json` |
| **FD002** | 260 | 130 | 52 | 26 | 52 | `data/splits/fd002_engine_split_seed_2026.json` |
| **FD004** | 249 | 124 | 50 | 25 | 50 | `data/splits/fd004_engine_split_seed_2026.json` |
| **Total Fleet** | **609** | **304** | **122** | **61** | **122** | Reconstructed provenance in `data/splits/` |

### 2.3 Training-Only Preprocessing & Sensor Schema
Under ADR-013, a frozen 17-feature schema is enforced across all three datasets:
- **Sensor Pruning**: Raw C-MAPSS logs contain 3 operational settings and 21 sensors (24 columns total). Sensors showing zero or near-zero variance across operating regimes (sensors 1, 5, 6, 10, 16, 18, 19) are permanently removed, leaving 14 degradation sensors plus the 3 operational settings (altitude, Mach number, TRA), totaling **17 input features per cycle**.
- **Training-Only Normalization**: All scaling parameters (medians, interquartile ranges, and K-Means regime centroids) are fit strictly on the training partition. Calibration, validation, and test engines are transformed using frozen training scalers. If an operational feature in training has zero variance, a unit scale is assigned to prevent division-by-zero errors.
- **K-Means Operating Regime Clustering**: For FD002 and FD004, the 3 operational settings are clustered into $K=6$ operating regimes using a frozen K-Means model fit on training data. For FD001, a single static regime ($C_1$) is assigned.

### 2.4 Causal Temporal Windowing and Identical Information Horizons
- **Window Size**: Fixed causal window length $W = 30$ operating cycles.
- **Stride & Padding**: Stride $= 1$ cycle. **Zero padding is strictly prohibited**; engines must execute for at least 30 cycles before the first prediction is emitted.
- **Qualified Endpoints**: For an engine with run-to-failure lifetime $T_i$, qualified endpoints are $V_i = \{30, 31, \dots, T_i\}$, yielding exactly $n_i = T_i - 29$ valid predictions.
- **Identical Information Horizon**:
  - The LSTM consumes a sequential tensor of shape $(30, 17)$ representing the exact chronological sequence $t-29 \dots t$.
  - The GBR consumes a flattened vector of shape $(510,)$ constructed by unrolling the identical 30 cycles $\times$ 17 features.
  - This guarantees that differences in predictive performance between GBR and LSTM reflect representational capacity rather than differing temporal information horizons.

### 2.5 Dual-Horizon RUL Target Construction
Under ADR-012, a rigorous distinction is maintained between training and evaluation targets:
- **Capped Training Targets**: To prevent deep models from overfitting to flat, non-informative sensor plateaus during early life, training targets are capped at $RUL_{\text{max}} = 125$ cycles:
  $$y_{\text{train}}(t) = \min(125, \; T_i - t)$$
- **Uncapped Evaluation & Calibration Targets**: Calibration nonconformity scores and evaluation metrics are computed strictly against true, uncapped RUL:
  $$y_{\text{true}}(t) = T_i - t$$
  This ensures that prediction intervals reflect physical component longevity and that maintenance replacement decisions are penalized based on actual discarded life.
- **Non-Negative Point Post-Processing**: All base model predictions are clipped at zero ($\hat{y} = \max(0.0, p)$) to guarantee physical feasibility.

---

## 3. Frozen Base Predictor Production Matrix

Under ADR-019 and ADR-020, two distinct point-predictor model families were specified, tuned on validation data, and frozen across five official research seeds (`2026, 2027, 2028, 2029, 2030`), forming a complete 30-model production matrix:

1. **Histogram Gradient Boosting Regressor (GBR)**:
   - Scikit-learn `HistGradientBoostingRegressor` evaluated over hyperparameter search grid of learning rates ($\{0.05, 0.10\}$), max leaf nodes ($\{15, 31, 63\}$), and L2 regularization ($\{0.0, 1.0\}$).
   - *Winning Configuration FD001*: `gbr_lr010_leaf15_l2_0` (Validation RMSE: 28.42 cycles).
   - *Winning Configuration FD002*: `gbr_lr010_leaf31_l2_0` (Validation RMSE: 34.66 cycles).
   - *Winning Configuration FD004*: `gbr_lr010_leaf31_l2_0` (Validation RMSE: 48.83 cycles).
   - *Properties*: Deterministic execution yielding identical outputs across seeds ($\sigma_{\text{RMSE}} = 0.0000$).
2. **Unidirectional Long Short-Term Memory (LSTM)**:
   - PyTorch unidirectional LSTM with hidden dimension $H=64$, dropout rate $0.20$, Adam optimizer with learning rate $\eta = 0.0010$, batch size 128, and early stopping on validation uncapped RMSE.
   - *Winning Configuration across all datasets*: `lstm_h64_lr0010` (Validation RMSE: FD001 = 30.08, FD002 = 35.25, FD004 = 48.25 cycles).
   - *Properties*: Highly stable stochastic convergence ($\sigma \le 0.36$ cycles across all seeds).

All 30 checkpoints are cryptographically hashed and immutably indexed in `experiments/base_models/model_registry.json`.

---

## 4. Conformal Calibration Methodology

### 4.1 Exact Engine-Weighted Quantiles and Boundary Mass
Standard split conformal prediction pools all calibration residuals into a single empirical distribution. In industrial degradation, this violates exchangeability because engines vary in run-to-failure length. 

IntelliTwin implements **hierarchical engine-weighted conformal calibration** based on the theoretical framework of Lee, Barber, and Willett (2023):
- Let $m$ denote the number of calibration engines contributing valid endpoints.
- Engine $i$ contains $n_i$ valid temporal windows ($n_i = T_i - 29$).
- Each individual endpoint $(i, t)$ within engine $i$ receives mass:
  $$w_{it} = \frac{1}{m \cdot n_i}$$
  ensuring that each physical engine contributes exactly $\frac{1}{m}$ of total finite calibration weight.
- To guarantee finite-sample marginal coverage for a new, unseen engine, total finite probability mass is bounded by $\frac{m}{m+1}$, with the remaining $\frac{1}{m+1}$ probability mass placed at $+\infty$:
  $$F_{\text{hierarchical}}(q) = \frac{1}{m + 1} \sum_{i=1}^m \frac{1}{n_i} \sum_{t=1}^{n_i} \mathbb{I}(s_{it} \le q)$$
- The nonconformity threshold $q^*$ for nominal coverage $1 - \alpha$ is the smallest score satisfying:
  $$q^* = \inf \left\{ q \in \mathbb{R} : F_{\text{hierarchical}}(q) \ge 1 - \alpha \right\}$$
- All quantile boundaries are computed and verified using exact rational arithmetic (`fractions.Fraction`) to eliminate floating-point representation errors.

### 4.2 Mathematical Formulations of the Three Evaluated Methods
Let $p \ge 0$ denote the base model point prediction, $y = y_{\text{true}} \ge 0$ denote ground-truth uncapped RUL, and $g \in \{C_1, \dots, C_6\}$ denote the discrete operating regime observed at cycle $t$.

#### Method 1: Global Hierarchical Conformal Prediction (`global_hcp`)
- **Nonconformity Score**: Symmetric absolute residual:
  $$s(p, y) = |y - p|$$
- **Threshold**: A single global engine-weighted hierarchical threshold $q_{\text{global}}$ fitted across all calibration engines.
- **Prediction Interval**:
  $$L = \max(0, \; p - q_{\text{global}}), \quad U = p + q_{\text{global}}$$

#### Method 2: Condition-Aware Hierarchical Conformal Prediction (`regime_hcp`)
- **Nonconformity Score**: Symmetric absolute residual:
  $$s(p, y) = |y - p|$$
- **Threshold**: Separate regime-specific hierarchical thresholds $q_g$ fitted using calibration residuals observed in operating regime $g$. A global threshold $q_{\text{global}}$ is fit concurrently for fallback routing.
- **Prediction Interval**:
  $$L = \max(0, \; p - q_g), \quad U = p + q_g$$
- *(Note: On single-regime FD001, `regime_hcp` and `global_hcp` are mathematically and numerically identical).*

#### Method 3: Proposed Decision-Aware Conformal Prediction (`decision_aware_hcp`)
The proposed method dynamically modulates nonconformity scaling and interval asymmetry as a function of the point prediction $p$:
$$\sigma(p) = \left(1 + \frac{p}{125}\right)^\gamma$$
$$z(p) = \exp\left(-\frac{p}{20}\right)$$
$$a(p) = \sigma(p) \exp\left(\beta z(p)\right)$$
$$b(p) = \sigma(p) \exp\left(-\beta z(p)\right)$$
where $\gamma \in \{0, 1, 2\}$ is the polynomial scaling exponent, $\beta = \beta_{\text{code}} \ln(2)$ with $\beta_{\text{code}} \in \{-1, 0, 1\}$ governs asymmetry, $125$ is the reference training cap scale, and $20$ cycles represents the characteristic end-of-life decision transition scale.

- **Nonconformity Score Function**:
  $$\text{score}(p, y) = \max\left(\frac{p - y}{a(p)}, \; \frac{y - p}{b(p)}, \; 0\right)$$
- **Score Inversion & Prediction Interval**:
  Inverting the score against the fitted regime-specific threshold $q_g$ yields:
  $$L = \max\left(0, \; p - q_g \cdot a(p)\right), \quad U = p + q_g \cdot b(p)$$

### 4.3 Mathematical Mechanics of Negative Beta ($\beta < 0$)
In the proposed formulation, when $\beta_{\text{code}} = -1$ ($\beta = -\ln(2) \approx -0.693147$):
- As an engine approaches end-of-life ($p \to 0$), the transition weight $z(p) \to 1$.
- Consequently, $\exp(\beta z(p)) \to \exp(-\ln 2) = 0.5$, while $\exp(-\beta z(p)) \to \exp(\ln 2) = 2.0$.
- Holding $p$, $q$, and $\gamma$ fixed, negative beta **decreases the lower-side scale $a(p)$ by half and doubles the upper-side scale $b(p)$**.
- Because $a(p)$ is reduced, the subtracted margin $q_g \cdot a(p)$ is smaller, which causes the unclipped lower bound $p - q_g \cdot a(p)$ to **rise** (or remain at zero after clipping). Simultaneously, the upper bound $U = p + q_g \cdot b(p)$ rises.

> **Critical Scientific Clarification**: Negative beta **does not necessarily lower the lower bound or trigger earlier maintenance**. At fixed $p$, $q$, and $\gamma$, negative beta scales down the lower-side deduction. However, in empirical calibration, fitting the asymmetric score function alters the empirical nonconformity distribution, leading to a refitted threshold $q^*$. Whether this mathematical structure reduces total operational maintenance costs is an empirical hypothesis that must be measured through simulation, not claimed a priori.

### 4.4 Nine-Candidate Parameter Space & Validation Selection
The parameter space was prespecified as a strict $3 \times 3$ grid:

| Candidate ID | $\gamma$ | $\beta_{\text{code}}$ | $\beta$ | Description |
| :--- | :---: | :---: | :---: | :--- |
| `gamma0_beta0` | 0 | 0 | $0.0000$ | Identity candidate (matches `regime_hcp`) |
| `gamma0_betam1` | 0 | -1 | $-0.6931$ | Constant scale, asymmetric upper expansion |
| `gamma0_betap1` | 0 | +1 | $+0.6931$ | Constant scale, asymmetric lower expansion |
| `gamma1_beta0` | 1 | 0 | $0.0000$ | Linear scale, symmetric |
| `gamma1_betam1` | 1 | -1 | $-0.6931$ | Linear scale, asymmetric upper expansion |
| `gamma1_betap1` | 1 | +1 | $+0.6931$ | Linear scale, asymmetric lower expansion |
| `gamma2_beta0` | 2 | 0 | $0.0000$ | Quadratic scale, symmetric |
| `gamma2_betam1` | 2 | -1 | $-0.6931$ | Quadratic scale, asymmetric upper expansion |
| `gamma2_betap1` | 2 | +1 | $+0.6931$ | Quadratic scale, asymmetric lower expansion |

Under ADR-021, candidate selection was executed exclusively on validation engines across seeds 2026–2030 using leave-one-engine-out cross-validation. Candidate `gamma2_betam1` was selected as the optimal feasible configuration across **all six mandatory cells** (`FD001_GBR`, `FD001_LSTM`, `FD002_GBR`, `FD002_LSTM`, `FD004_GBR`, `FD004_LSTM`) and frozen in `experiments/calibration/selection/selection_freeze.json`.

### 4.5 Fallback Routing Rules for Insufficient Subgroup Support
For regime-specific calibration at nominal coverage $1 - \alpha$, regime $g$ requires a minimum sample support of:
$$m_g \ge \max\left(10, \; \left\lceil \frac{1}{\alpha} \right\rceil - 1\right)$$
- At 90% coverage ($\alpha = 0.10$): $m_g \ge \max(10, 9) = 10$ calibration engines.
- At 95% coverage ($\alpha = 0.05$): $m_g \ge \max(10, 19) = 19$ calibration engines.

If a regime contains fewer than $m_g$ calibration engines in the partition, the calibrator automatically routes to the global threshold $q_{\text{global}}$ for that coverage level, flags `fallback_used = True`, and records the exact fallback rationale.

---

## 5. Sequential Maintenance Simulator and Policy Execution

Under ADR-014 and ADR-015, the downstream operational impact of calibrated intervals is evaluated via a discrete-event sequential maintenance simulation engine (`src/intellitwin/simulator/engine.py`).

### 5.1 Shared Benchmark Replacement Policy
All conformal methods and controls are evaluated using an identical, pre-registered maintenance policy:
$$\text{Policy}: \quad \text{Action}(t) = \begin{cases} \text{MAINTAIN\_NOW}, & \text{if } L(t) \le 1.0 \\ \text{CONTINUE}, & \text{otherwise} \end{cases}$$
- **Operational Window**: Evaluated at cycles $t \in [30, T_i - 1]$.
- **Episode Termination**: If `MAINTAIN_NOW` is triggered at cycle $t_{\text{stop}} < T_i$, a planned preventive maintenance (PM) event occurs, and the episode terminates.
- **Unplanned Failure**: If an engine reaches terminal cycle $T_i$ without triggering PM, an unplanned in-service failure occurs at cycle $T_i$.

### 5.2 Economic Cost Structure
Under ADR-018, maintenance costs are quantified in normalized **Simulated Cost Units (SCU)**, where the preventive replacement cost defines the base unit ($C_{\text{PM}} = 1.0$):
$$\text{Cost} = \begin{cases} C_{\text{PM}} + C_{\text{WASTE}} \cdot (T_i - t_{\text{stop}}), & \text{if PM occurred at } t_{\text{stop}} < T_i \\ C_{\text{FAIL}}, & \text{if in-service failure occurred at } T_i \end{cases}$$

#### Frozen Cost Scenarios
1. **Primary Reference Scenario (`primary_reference`)**:
   - $C_{\text{PM}} = 1.0$ (Planned Replacement Cost)
   - $C_{\text{FAIL}} = 5.0$ (Unplanned Failure Penalty)
   - $C_{\text{WASTE}} = 0.20$ SCU per unused cycle of true RUL
   - *Economic Equivalence Horizon*: $r_{\text{equal}} = \frac{C_{\text{FAIL}} - C_{\text{PM}}}{C_{\text{WASTE}}} = \frac{5.0 - 1.0}{0.20} = 20$ cycles. (Replacing an engine with $> 20$ cycles remaining is more expensive than an in-service failure).
2. **Failure-Sensitive Sensitivity Scenario (`failure_sensitive`)**:
   - $C_{\text{PM}} = 1.0, \; C_{\text{FAIL}} = 10.0, \; C_{\text{WASTE}} = 0.20$ ($r_{\text{equal}} = 45$ cycles).
3. **Waste-Sensitive Sensitivity Scenario (`waste_sensitive`)**:
   - $C_{\text{PM}} = 1.0, \; C_{\text{FAIL}} = 5.0, \; C_{\text{WASTE}} = 0.40$ ($r_{\text{equal}} = 10$ cycles).
