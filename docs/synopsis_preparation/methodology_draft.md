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
  [Training-Only Preprocessing: 17 Features, Z-Score Normalization (ddof=0)]
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
Preprocessing uses training-only z-score normalization. Means and population standard deviations are estimated with `ddof=0`. An exactly zero standard deviation is replaced by an effective scale of 1.0, while the mean is still subtracted:
$$x_{\text{normalized}} = \frac{x - \mu_{\text{train}}}{s_{\text{train}}}$$
where:
$$s_{\text{train}} = \begin{cases} \sigma_{\text{train}}, & \text{when } \sigma_{\text{train}} > 0 \\ 1.0, & \text{otherwise} \end{cases}$$

Dataset-specific processing is structured as follows:
- **FD001**: Operates under a single operating condition; fitted with global training-only normalization across all engines.
- **FD002 and FD004**: Operating settings are standardized using training data. Six operating regimes ($C_1$ to $C_6$) are learned from standardized training settings via K-Means clustering ($k=6, \text{random\_state}=2026, \text{n\_init}=10$). Canonical regime labels are preserved based on lexicographic centroid ordering. Sensor normalization parameters are fitted separately within each training regime.
- Preprocessing transformations are computed and applied prior to window construction.

The pipeline enforces the exact frozen 17-feature selection order:
$$\text{setting1, setting2, setting3, s2, s3, s4, s7, s8, s9, s11, s12, s13, s14, s15, s17, s20, s21}$$
This is a frozen 17-feature selection supported by the recorded qualification procedure. The seven excluded sensors (s1, s5, s6, s10, s16, s18, s19) are omitted under this frozen protocol; they are not claimed to be mathematically constant or universally uninformative across all possible datasets and regimes.

### 2.4 Causal Temporal Windowing and Identical Information Horizons
- **Window Size**: Fixed causal window length $W = 30$ operating cycles.
- **Stride & Padding**: Stride $= 1$ cycle. **Zero padding is strictly prohibited**; engines must execute for at least 30 cycles before the first prediction is emitted.
- **Qualified Endpoints**: For an engine with run-to-failure lifetime $T_i$, qualified endpoints are $V_i = \{30, 31, \dots, T_i\}$, yielding exactly $n_i = T_i - 29$ valid predictions without crossing engine boundaries.
- **Identical Information Horizon**:
  - The LSTM consumes a sequential tensor of shape $(30, 17)$ representing the exact chronological sequence $t-29 \dots t$.
  - The GBR consumes a flattened vector of shape $(510,)$ constructed in C-order by unrolling the identical 30 cycles $\times$ 17 features.
  - This guarantees that differences in predictive performance between GBR and LSTM reflect representational capacity rather than differing temporal information horizons.

### 2.5 Dual-Horizon RUL Target Construction
Under ADR-012, a rigorous distinction is maintained between training and evaluation targets:
- **Capped Training Targets**: To prevent deep models from overfitting to non-informative sensor plateaus during early life, training targets are capped at $RUL_{\text{max}} = 125$ cycles:
  $$y_{\text{train}}(t) = \min(125, \; T_i - t)$$
  The 125-cycle target cap is a modeling convention; it is not a physical proof that early-life degradation is physically absent.
- **Uncapped Evaluation & Calibration Targets**: Calibration nonconformity scores and evaluation metrics are computed strictly against true, uncapped RUL:
  $$y_{\text{true}}(t) = T_i - t$$
  This ensures that prediction intervals reflect physical component longevity and that maintenance replacement decisions are penalized based on actual discarded life.
- **Non-Negative Point Post-Processing**: Evaluated point predictions are clipped at zero:
  $$p = \max(0.0, \; \text{raw\_prediction})$$
  No upper clipping at 125 cycles is applied to evaluated predictions.

---

## 3. Frozen Base Predictor Production Matrix

Under ADR-019 and ADR-020, two distinct point-predictor model families were specified, tuned on validation data, and frozen across five official research seeds (`2026, 2027, 2028, 2029, 2030`), forming a complete 30-model production matrix:

1. **Histogram Gradient Boosting Regressor (GBR)**:
   - Implemented via `sklearn.ensemble.HistGradientBoostingRegressor`.
   - Input: C-order flattened $30 \times 17$ causal window, forming 510 tabular features.
   - The project's model is not LightGBM or XGBoost; it relies strictly on scikit-learn's native histogram gradient boosting regressor.
   - Evaluated over hyperparameter search grid of learning rates ($\{0.05, 0.10\}$), max leaf nodes ($\{15, 31, 63\}$), and L2 regularization ($\{0.0, 1.0\}$) across selection seeds 2026 and 2027.
   - *Frozen winning configuration on FD001*: `gbr_lr010_leaf15_l2_0` (learning rate 0.10, max leaf nodes 15, L2 regularization 0.0).
   - *Frozen winning configuration on FD002 and FD004*: `gbr_lr010_leaf31_l2_0` (learning rate 0.10, max leaf nodes 31, L2 regularization 0.0).
   - Execution across the five seeds (2026–2030) reflects seed replication for protocol completeness; the repeated seeds are not five independent stochastic experiments, nor is random subsampling invented as a cause of variation. Universal deterministic behavior beyond the recorded runs is not asserted.
2. **Unidirectional Long Short-Term Memory (LSTM)**:
   - PyTorch unidirectional recurrent network with one recurrent layer (`num_layers=1`, `bidirectional=False`, `batch_first=True`, `input_size=17`).
   - Internal LSTM dropout is $0.0$.
   - The network extracts the final sequence output, applies an explicit separate `nn.Dropout(p=0.20)`, and passes it to an output projection `nn.Linear(64, 1)`.
   - Selected configuration across all datasets: `lstm_h64_lr0010` (hidden dimension $H=64$, Adam optimizer with learning rate $\eta = 0.0010$, batch size 128).
   - Early stopping uses validation uncapped-RUL RMSE.
   - Two selection seeds (2026 and 2027) were used for hyperparameter validation selection; five final model seeds (2026–2030) form the frozen production matrix.

All 30 checkpoints are cryptographically hashed and immutably indexed in `experiments/base_models/model_registry.json`. Numerical validation and test performance metrics are reported in designated results tables rather than explanatory method text.

---

## 4. Conformal Calibration Methodology

### 4.1 Exact Engine-Weighted Quantiles and Boundary Mass
Standard split conformal prediction pools all calibration residuals into a single empirical distribution. In industrial degradation, this violates exchangeability because engines vary in run-to-failure length. 

IntelliTwin implements **hierarchical engine-weighted conformal calibration** based on the theoretical framework of Lee, Barber, and Willett (2023):
- Let $m$ denote the number of calibration engines contributing valid endpoints.
- Engine $i$ contains $n_i$ valid temporal windows ($n_i = T_i - 29$).
- For final calibration with $m$ contributing engines, the empirical cumulative distribution function is:
  $$F_{\text{final}}(q) = \frac{1}{m + 1} \sum_{i=1}^m \left[ \frac{1}{n_i} \sum_{t=1}^{n_i} \mathbb{I}(\text{score}_{it} \le q) \right]$$
- In this final calibration distribution, the probability mass assigned to each finite observed score endpoint $(i, t)$ is:
  $$\text{mass}(i, t) = \frac{1}{(m + 1) n_i}$$
- The total finite probability mass is $\frac{m}{m+1}$. The remaining probability mass of $\frac{1}{m+1}$ is placed at $+\infty$.
- The nonconformity threshold $q$ is the smallest observed score whose cumulative probability reaches $1 - \alpha$. If no finite score reaches $1 - \alpha$, $q = +\infty$.
- *(Note: During validation leave-one-engine-out candidate selection, a development empirical CDF with normalized $\frac{1}{m}$ engine weighting is evaluated separately over the validation engines).*
- For regime-specific calibration, $m_g$ counts distinct engines contributing to that regime, and $n_{ig}$ counts their eligible endpoints in that regime.
- All quantile boundaries are computed and verified using exact rational arithmetic (`fractions.Fraction`) to eliminate floating-point representation errors.

### 4.2 Mathematical Formulations of the Three Evaluated Methods
Let $p \ge 0$ denote the base model point prediction (in cycles), $y = y_{\text{true}} \ge 0$ denote ground-truth uncapped RUL, and $g \in \{C_1, \dots, C_6\}$ denote the discrete operating regime observed at cycle $t$.

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
At fixed $p$, $q$, and $\gamma$, negative $\beta$ decreases $a$ relative to $\beta=0$ and increases $b$. The lower bound is nondecreasing and the upper bound is nondecreasing. This does not establish improved maintenance utility or earlier intervention; thresholds are fitted separately and utility must be evaluated.

*(Note: It is not claimed that $a(p) < 1$ or $b(p) > 1$ for every $p$, because the scaling factor $\sigma(p)$ also modulates their absolute magnitude).*

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
Therefore:
- **80% coverage** ($\alpha = 0.20$): requires at least $\max(10, 4) = 10$ distinct engines.
- **90% coverage** ($\alpha = 0.10$): requires at least $\max(10, 9) = 10$ distinct engines.
- **95% coverage** ($\alpha = 0.05$): requires at least $\max(10, 19) = 19$ distinct engines.

If a regime contains fewer than $m_g$ distinct engines in the calibration split, the calibrator automatically routes to the global threshold $q_{\text{global}}$ for the same method and coverage level, records the fallback occurrence, and logs the rationale. Fallback does not depend on an observation count of 100.

---

## 5. Sequential Maintenance Simulator and Policy Execution

Under ADR-014 and ADR-015, the downstream operational impact of calibrated intervals is evaluated via a discrete-event sequential maintenance simulation engine (`src/intellitwin/simulator/engine.py`).

### 5.1 Shared Benchmark Replacement Policy
All conformal methods and controls are evaluated using an identical, pre-registered maintenance policy:
$$\text{Policy}: \quad \text{Action}(t) = \begin{cases} \text{MAINTAIN\_NOW}, & \text{if } L(t) \le 1.0 \text{ cycle} \\ \text{CONTINUE}, & \text{otherwise} \end{cases}$$
- **Operational Window**: Actions occur at cycles $t \in [30, T_i - 1]$.
- **Immediate Preventive Maintenance**: If `MAINTAIN_NOW` is triggered at cycle $t_{\text{stop}} < T_i$, a planned preventive maintenance (PM) event occurs immediately and terminates the episode. There is no intervention lead time; the one-cycle decision threshold ($L(t) \le 1.0$) must not be confused with an intervention lead time.
- **Unplanned Failure**: If an engine reaches terminal cycle $T_i$ without triggering PM, an unplanned in-service failure occurs at cycle $T_i$, incurring cost $C_{\text{FAIL}}$ and zero wasted life ($W=0$).
- **Offline Interval Evaluation**: Offline prediction interval evaluation still includes all qualified endpoints $30$ through $T_i$, independently of policy stopping.

### 5.2 Economic Cost Structure
Under ADR-018, maintenance costs are quantified in synthetic Simulated Cost Units (SCU):
- $C_{\text{PM}}$ and $C_{\text{FAIL}}$ are synthetic cost units per event.
- $C_{\text{WASTE}}$ is synthetic cost units per unused cycle of true RUL.

The cost and wasted life $W$ are defined as:
$$\text{Cost} = \begin{cases} C_{\text{PM}} + C_{\text{WASTE}} \cdot (T_i - t_{\text{stop}}), & \text{if PM occurred at } t_{\text{stop}} < T_i \\ C_{\text{FAIL}}, & \text{if in-service failure occurred at } T_i \end{cases}$$
$$W = \begin{cases} T_i - t_{\text{stop}}, & \text{if PM occurred at } t_{\text{stop}} < T_i \\ 0, & \text{if in-service failure occurred at } T_i \end{cases}$$

#### Frozen Synthetic Cost Scenarios
1. **Primary Reference Scenario (`primary_reference`)**:
   - $C_{\text{PM}} = 1.0$ SCU per event (Planned Replacement Cost)
   - $C_{\text{FAIL}} = 5.0$ SCU per event (Unplanned Failure Penalty)
   - $C_{\text{WASTE}} = 0.20$ SCU per unused cycle
   - *Cost Equality Horizon*: $r_{\text{equal}} = \frac{C_{\text{FAIL}} - C_{\text{PM}}}{C_{\text{WASTE}}} = \frac{5.0 - 1.0}{0.20} = 20$ cycles.
2. **Failure-Sensitive Sensitivity Scenario (`failure_sensitive`)**:
   - $C_{\text{PM}} = 1.0, \; C_{\text{FAIL}} = 10.0, \; C_{\text{WASTE}} = 0.20$ ($r_{\text{equal}} = 45$ cycles).
3. **Waste-Sensitive Sensitivity Scenario (`waste_sensitive`)**:
   - $C_{\text{PM}} = 1.0, \; C_{\text{FAIL}} = 5.0, \; C_{\text{WASTE}} = 0.40$ ($r_{\text{equal}} = 10$ cycles).

*(Note: The cost equality values of 20, 45, and 10 cycles compare preventive-plus-waste cost with failure cost; they are economic breakeven reference points and are not policy decision thresholds or optimal replacement times).*
