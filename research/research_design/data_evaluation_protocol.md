# Data & Evaluation Protocol — Step 5

This document serves as the authoritative specification for data preprocessing, label construction, feature engineering, sequence windowing, dataset splits, subgroup definitions, target evaluation, and reproducibility protocols for the IntelliTwin research platform.

---

## 1. RUL Target Construction

### 1.1 Mathematical Definition of `rul_true`

For a full run-to-failure engine trajectory $i$, let $T_{\text{failure}}(i)$ denote the final observed operational cycle of that engine, and let $t$ denote the current cycle number ($1 \le t \le T_{\text{failure}}(i)$).

The uncapped ground-truth Remaining Useful Life (RUL) for engine $i$ at cycle $t$ is defined as:

$$\text{RUL}_{\text{true}}(i, t) = T_{\text{failure}}(i) - t$$

- **Meaning**: `rul_true` represents the exact, uncapped actual number of remaining operational cycles until functional failure.
- **Role in Research Pipeline**: `rul_true` is retained for offline ground-truth scientific evaluation, primary conformal prediction interval calibration responses, post-hoc error metrics, degradation-stage labeling, wasted RUL calculations, and post-hoc maintenance simulator consequence analysis.
- **Observed Calibration Response**: Uncapped `rul_true` is permitted as an observed calibration response on designated calibration engines. It remains strictly prohibited as a predictive model feature, calibration conditioning variable, or deployed policy input.

### 1.2 Mathematical Definition of `rul_target`

The primary target used for supervised training of base RUL prediction models is defined as:

$$\text{RUL}_{\text{target}}(i, t) = \min\left(\text{RUL}_{\text{true}}(i, t), 125\right)$$

- **Fixed Cap Value**: The maximum training target value is strictly locked at $125$ cycles.
- **Piecewise-Linear Target**: The training target is constant ($125$) during early operational cycles when $\text{RUL}_{\text{true}}(i, t) \ge 125$, and decreases linearly with a slope of $-1$ as the engine approaches failure once $\text{RUL}_{\text{true}}(i, t) < 125$.

### 1.3 Modeling Convention of the Capped Training Target

1. **Selected Modeling Convention**: The 125-cycle cap reflects a selected modeling convention to stabilize supervised model fitting by capping early-life targets where RUL prediction has high variance across units. It is not an assertion that engines universally experience zero early-life wear.
2. **Standard Benchmark Protocol**: A piecewise-linear cap of 125 cycles aligns with the benchmark convention in turbofan prognostic literature (e.g., Zheng et al., 2017; Diao et al., 2026), standardizing point prediction task formulation.
3. **No-Tuning Rule**: The cap value of 125 cycles is strictly fixed by research decision. It must **NOT** be tuned, optimized, or altered based on validation error, test set performance, or hyperparameter sweeps.

### 1.4 Distinction Between Training Target and Ground-Truth Evaluation

`rul_true` and `rul_target` represent distinct scientific quantities and must **NEVER** be treated as interchangeable:

- **Supervised Training**: Base RUL model architectures (e.g., linear baselines, temporal neural networks, GBR) are trained strictly using `rul_target` as the scalar regression target.
- **Conformal Interval Calibration & Primary Evaluation**: All primary conformal prediction intervals target uncapped `rul_true`. Prediction intervals are **NOT** capped at 125. All final evaluation metrics (MAE, RMSE, PICP, MPIW, interval score) and maintenance simulator consequences must use uncapped `rul_true` as the ground-truth benchmark. Capped-target coverage is evaluated as a secondary diagnostic only.

### 1.5 Model Output Interpretation & Maintenance Consequence Analysis

- **Early-Life Point Prediction Saturation**: Because base point predictors are trained against $\min(\text{RUL}_{\text{true}}, 125)$, point predictions during early engine life saturate near 125 cycles. However, primary conformal prediction intervals target uncapped `rul_true`.
- **Reporting Rule**: The capped prediction target `rul_target` must **NEVER** be reported or interpreted as if it were the engine's actual uncapped remaining operational lifetime.
- **Wasted Useful Life Rule**: Wasted useful life resulting from premature maintenance interventions must be calculated strictly from uncapped `rul_true` ($\text{RUL}_{\text{wasted}} = \text{RUL}_{\text{true}}(i, t_{\text{replacement}})$), **NEVER** from `rul_target`.

### 1.6 Inference-Time Input Leakage Restrictions

Consistent with Step 4 leakage governance rules (ADR-011):

1. Neither `rul_true`, `rul_target`, engine failure cycle $T_{\text{failure}}(i)$, nor any future-cycle information may be used as predictive model inputs at inference time.
2. Failure cycle $T_{\text{failure}}(i)$ may be used strictly to construct supervised labels for offline training on full run-to-failure trajectories.
3. `rul_true` is strictly prohibited from being used as:
   - A deployed model feature input
   - An operating-condition feature or regime identification input
   - A conformal calibration condition variable
   - A maintenance policy decision input
   - Information assumed to be available at prediction time

---

## 2. Sensor Diagnostic Historical Context

### 2.1 Historical Diagnostic Note
A training-only exploratory diagnostic was executed for FD002 sensors $s1$ through $s21$ using [`scripts/audit_fd002_sensors.py`](../../scripts/audit_fd002_sensors.py). This diagnostic preceded the final feature schema lock in Section 3.

- **Data Partitioning**: The diagnostic script loaded `train_FD002.txt` and filtered rows strictly to the 130 training partition engines defined in `data/splits/fd002_engine_split_seed_2026.json`. All reported diagnostic statistics reflect strictly the designated 130 training engines.
- **Statistical Conventions**: The historical diagnostic CSV (`fd002_training_sensor_diagnostic.csv`) uses sample standard deviation ($N-1$ denominator) for descriptive reporting. This is distinguished from feature preprocessing normalization, which uses population variance ($N$ denominator, `ddof=0`).
- **Interpretation of Low Variance**: Low within-regime variance in telemetry is descriptive empirical evidence of near-constant sensor output, not mathematical proof that an excluded sensor contains zero predictive information under all possible non-linear feature interactions.

---

## 3. Final Sensor and Input Policy

### 3.1 Engine Identifier Role (`unit`)
- **Role**: Engine identifier, partition assignment, engine-level grouping, chronology validation, and unit-of-independence statistical analysis.
- **Predictive Constraint**: `unit` MUST NOT be used as a predictive feature in any model.

### 3.2 Operational Cycle Role (`cycle`)
- **Role**: Temporal ordering, sequence window construction, RUL label construction, chronological replay, and trajectory indexing.
- **Predictive Constraint**: `cycle` is strictly excluded from predictive model inputs as a controlled modeling choice to force predictors to learn health status from sensor telemetry rather than operational age shortcuts. Cycle is excluded by protocol design, not because it constitutes future-information leakage.

### 3.3 Operating Settings (`setting1`, `setting2`, `setting3`)
- **Retained Features**: All three operating settings (`setting1`, `setting2`, `setting3`) are retained as predictive inputs.
- **Regime Identification Role**: Operating settings remain the **ONLY** variables used to assign operating-condition regimes ($k=6$ K-means clustering fit on training settings).

### 3.4 Final Retained Sensor Set (14 Sensors)
The following 14 sensors are strictly locked as predictive inputs:
`["s2", "s3", "s4", "s7", "s8", "s9", "s11", "s12", "s13", "s14", "s15", "s17", "s20", "s21"]`

### 3.5 Final Excluded Sensor Set (7 Sensors)
The following 7 sensors are strictly locked as excluded from predictive inputs:
`["s1", "s5", "s6", "s10", "s16", "s18", "s19"]`

- **Exclusion Rationale**: Excluded as a controlled feature selection policy due to zero or near-zero within-regime variation.

### 3.6 Common Sensor Schema (17 Features Total)
The identical 17-feature predictive schema (3 operating settings + 14 retained sensors) is enforced across **FD001**, **FD002**, and **FD004**.

**Canonical Feature Vector Order**:
`["setting1", "setting2", "setting3", "s2", "s3", "s4", "s7", "s8", "s9", "s11", "s12", "s13", "s14", "s15", "s17", "s20", "s21"]`

---

## 4. Normalization and Preprocessing Strategy

### 4.1 Population Variance and Zero-Variance Scaling Rule
Preprocessing parameters are fit on training partition engines ONLY.

- **Statistics Calculation**: Means $\mu_{\text{train}}$ and population variances $\sigma^2_{\text{train}}$ are computed using `ddof=0`.
- **Zero-Standard-Deviation Rule**: For any feature $j$ where training population variance is exactly zero ($\sigma_{\text{train}, j} = 0$):
  - Use effective scale $s_j = 1.0$.
  - Center normally: $x_{\text{normalized}, j} = (x_j - \mu_{\text{train}, j}) / 1.0 = 0.0$ for all training observations.
  - Preserve all 17 features in the predictive schema.
  - Store mean $\mu_j$, variance $\sigma^2_j$, effective scale $s_j$, and a boolean zero-variance mask.
  - Pipelines MUST NOT introduce epsilon scaling ($+1e-8$), automatic feature removal, clipping, or winsorization.
- **Input Validation**: Pipelines MUST reject missing values (NaN/null) and non-finite inputs (inf/-inf) with an explicit ValueError.

### 4.2 Normalization by Dataset
- **FD001**: Global training-only setting and sensor normalization (no K-means regime clustering).
- **FD002**: Global training-only setting normalization, followed by regime-specific training-only sensor normalization using frozen K-means cluster centers ($k=6$).
- **FD004**: Global training-only setting normalization, followed by regime-specific training-only sensor normalization using its own training-fitted parameters and K-means cluster centers ($k=6$).

---

## 5. Sequence Windowing Specification (Step 5.4)

### 5.1 Window Construction Rules
- **Lookback Length ($L$)**: 30 cycles.
- **Stride**: 1 cycle.
- **Padding Policy**: NO padding.
- **Normalization Precedence**: Normalization occurs cycle-by-cycle BEFORE window assembly.
- **Causal Endpoint Alignment**: Window for endpoint cycle $t$ contains normalized cycles $t-29$ through $t$ in chronological order (oldest cycle $t-29$ first, newest cycle $t$ last).
- **Boundary Restrictions**: Windows MUST NEVER cross engine boundaries or include future cycles ($> t$).
- **Warm-Up Cycles**: Cycles 1 through 29 are warm-up cycles and do NOT produce valid windows.

### 5.2 Predictor Model Input Shapes
- **LSTM / Temporal Architectures**: Tensor input shape $(30, 17)$ representing 30 time steps $\times$ 17 canonical features.
- **GBR / Tabular Baselines**: Flattened row-major feature vector of dimension $510 = 30 \times 17$ (cycles $t-29 \dots t$ flattened in order).
- **Metadata Attachment**: Engine ID `unit`, cycle $t$, `rul_target`, `rul_true`, failure cycle $T_{\text{failure}}$, and stage label are attached as window metadata, NOT model features.
- **Window Operating Regime**: The operating regime of a window is defined strictly by its endpoint cycle $t$, even if earlier cycles in the window belong to different regimes.

### 5.3 Qualification and Short Trajectory Governance
- **Raw Trajectory Integrity**: Input records MUST have positive integer engine and cycle IDs, be duplicate-free, start at cycle 1, and be strictly consecutive without gaps.
- **Offline Prognostic Evaluation Scope**: Evaluates endpoints $t \in [30, T_{\text{failure}}(i)]$ inclusive, including terminal $t = T_{\text{failure}}(i)$ ($\text{RUL}_{\text{true}} = 0$).
- **Sequential Maintenance Decision Scope**: Evaluates decision opportunities $t \in [30, T_{\text{failure}}(i) - 1]$. No decision occurs at failure cycle $T_{\text{failure}}(i)$.
- **Short Trajectory Handling**:
  - Trajectories with $T_{\text{failure}} < 30$ produce 0 windows.
  - Trajectories with $T_{\text{failure}} = 30$ produce 1 offline prognostic endpoint ($t=30$), but 0 maintenance decision opportunities.
  - Any primary full-trajectory engine with $T_{\text{failure}} \le 30$ triggers an explicit dataset qualification failure for sequential evaluation. Pipelines MUST NOT silently drop engines or reroll splits.

---

## 6. Lifecycle Stages and Subgroup Definitions (Step 5.5)

### 6.1 Retrospective Lifecycle Stage Definitions
Lifecycle stages are defined retrospectively for offline evaluation based on endpoint cycle $t$ and total run-to-failure lifetime $T_{\text{failure}}(i)$:

- **Early Stage**: $3t \le T_{\text{failure}}(i)$
- **Mid Stage**: $T_{\text{failure}}(i) < 3t \le 2 T_{\text{failure}}(i)$
- **Late Stage**: $2 T_{\text{failure}}(i) < 3t \le 3 T_{\text{failure}}(i)$

*Governance Note*: Lifecycle thirds are retrospective evaluation proxies, not verified physical degradation phases. Stage labels MUST NEVER be used as model features, calibration conditions, or deployed policy inputs.

### 6.2 Subgroup Families and Worst-Group Reliability
Primary subgroup families are evaluated separately:
1. **Operating Regimes** (C1–C6 on FD002/FD004; 1 condition group on FD001)
2. **Lifecycle Stages** (Early, Mid, Late)

*Regime $\times$ Stage intersections are secondary diagnostic analyses only.*

### 6.3 Subgroup Eligibility and Metric Aggregation
- **Eligibility Threshold**: A subgroup is eligible for primary worst-group reliability analysis if at least **10 distinct engines** contribute at least 1 valid evaluation endpoint to that subgroup.
- **Engine-Weighted Subgroup Coverage**: Within an eligible subgroup $g$, compute empirical coverage for each contributing engine $i$, then take the simple unweighted average across all contributing engines $N_g$:
  $$\text{Coverage}(g) = \frac{1}{N_g} \sum_{i \in \mathcal{E}_g} \text{Coverage}(i, g)$$
- **Subgroup Coverage Error**:
  $$\text{CoverageError}(g) = \left| \text{Coverage}(g) - (1 - \alpha) \right|$$
- **Reported Worst-Group Metrics**:
  - Maximum coverage error among eligible operating regimes
  - Maximum coverage error among eligible lifecycle stages
  - Overall worst-group coverage error across the union of eligible groups
- Ineligible groups ($< 10$ contributing engines) remain visible in reports marked *descriptive-only*.

---

## 7. Dataset Splits and Official NASA Benchmark Protocol (Step 5.6)

### 7.1 Split Manifest Protocol
- **FD002**: `data/splits/fd002_engine_split_seed_2026.json` (130 / 52 / 26 / 52) is preserved byte-for-byte.
- **FD001**: `data/splits/fd001_engine_split_seed_2026.json` (50 / 20 / 10 / 20) generated via `scripts/generate_engine_splits.py`.
- **FD004**: `data/splits/fd004_engine_split_seed_2026.json` (124 / 50 / 25 / 50) generated via `scripts/generate_engine_splits.py`.

### 7.2 Official NASA Test Set Protocol
- NASA official test trajectories (`test_FD001.txt`–`test_FD004.txt`) are truncated prior to failure and supply terminal RUL labels in `RUL_FD00x.txt`.
- Official NASA test data serves as a secondary terminal-RUL benchmark only.
- Excluded from sequential maintenance simulation and primary RQ1–RQ4 confirmatory inference.
- Official test evaluation uses the final 30 observed cycles of each test trajectory transformed with frozen training preprocessing.
- Trajectories shorter than 30 cycles are excluded and reported as an eligible-subset benchmark.
- Official test set labels MUST NEVER be used to tune preprocessing parameters, model architectures, or decision thresholds.

---

## 8. Target Metric Aggregation & Bootstrap Governance (Step 5.7)

### 8.1 Primary Engine-Weighted Metric Aggregation
All primary prognostic metrics are aggregated by computing engine-level mean statistics first, then averaging across engines $N$:

- **Engine MAE**: $\bar{\text{MAE}} = \frac{1}{N} \sum_{i=1}^N \left( \frac{1}{T_i} \sum_{t=1}^{T_i} |\hat{y}_{i,t} - y_{i,t}| \right)$
- **Engine RMSE**: $\bar{\text{RMSE}} = \sqrt{\frac{1}{N} \sum_{i=1}^N \left( \frac{1}{T_i} \sum_{t=1}^{T_i} (\hat{y}_{i,t} - y_{i,t})^2 \right)}$ *(Note: Root of average engine MSEs; engine-specific RMSEs are NOT averaged).*
- **Engine PICP**: $\bar{\text{PICP}} = \frac{1}{N} \sum_{i=1}^N \left( \frac{1}{T_i} \sum_{t=1}^{T_i} \mathbb{I}(y_{i,t} \in [\hat{L}_{i,t}, \hat{U}_{i,t}]) \right)$
- **Engine MPIW**: $\bar{\text{MPIW}} = \frac{1}{N} \sum_{i=1}^N \left( \frac{1}{T_i} \sum_{t=1}^{T_i} (\hat{U}_{i,t} - \hat{L}_{i,t}) \right)$
- **Engine Interval Score**: Engine-averaged central Winkler interval score at level $\alpha$.
- **Engine Maintenance Cost**: $\bar{C} = \frac{1}{N} \sum_{i=1}^N C_i$ (one terminal cost per engine).

### 8.2 Statistical Uncertainty Framework
- 95% engine-level paired/cluster-bootstrap confidence intervals ($B=1000$ resamples) with the **ENGINE** as the resampled unit of independence.
- Correlated time steps within an engine are non-independent time series; individual window samples MUST NOT be treated as independent bootstrap units.

---

## 9. Model Training Seeds & Reproducibility (Step 5.8)

### 9.1 Model Run Seeds
To evaluate training stability across random initializations, all model training pipelines must run across 5 fixed seeds:
`2026, 2027, 2028, 2029, 2030`

- Model run seeds evaluate weight initialization and stochastic optimization variance.
- Model run seeds MUST NOT alter engine partition split manifests or preprocessing parameters.
- Seeds are NOT additional independent engine units.

### 9.2 K-Means Regime Model Reproducibility
For FD002 and FD004 operating regime identification:
```python
KMeans(
    n_clusters=6,
    init="k-means++",
    n_init=10,
    max_iter=300,
    tol=1e-4,
    random_state=2026,
    algorithm="lloyd",
)
```
Fit on float64 training-setting rows sorted by engine and cycle. Centroids are lexicographically sorted by `(setting1, setting2, setting3)` to assign canonical C1–C6 labels. Save mapping, centroids, unscaled centroids, and scaler parameters. Assign new observations to nearest frozen centroid using squared Euclidean distance.
