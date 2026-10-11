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

- **Early-Life Point Prediction Behavior**: Capped-target training encourages early-life predictions near the cap; the model's output behavior is not mathematically guaranteed by the target cap. However, primary conformal prediction intervals target uncapped `rul_true`.
- **Reporting Rule**: The capped prediction target `rul_target` must **NEVER** be reported or interpreted as if it were the engine's actual uncapped remaining operational lifetime.
- **Wasted Useful Life Rule**: Wasted useful life resulting from premature maintenance interventions must be calculated strictly from uncapped `rul_true` ($\text{RUL}_{\text{wasted}} = \text{RUL}_{\text{true}}(i, t_{\text{replacement}})$), **NEVER** from `rul_target`.

### 1.6 Inference-Time Input Leakage Restrictions

Consistent with Step 4 leakage governance rules (ADR-011):

1. Neither `rul_true`, `rul_target`, engine failure cycle $T_{\text{failure}}(i)$, nor any future-cycle information may be used as predictive model inputs at inference time.
2. Failure cycle $T_{\text{failure}}(i)$ is available offline strictly for label construction, retrospective degradation stage labeling, and simulator consequence evaluation, but remains strictly prohibited as a deployed predictive or policy input.
3. `rul_true` is strictly prohibited from being used as:
   - A deployed model feature input
   - An operating-condition feature or regime identification input
   - A conformal calibration condition variable
   - A maintenance policy decision input
   - Information assumed to be available at prediction time

### 1.7 Nominal Coverage Levels and Interval Target Convention

- **Primary Nominal Coverage**: The primary coverage level is strictly locked at $1 - \alpha = 90\%$ ($\alpha = 0.10$). All primary hypothesis evaluations (RQ1, RQ2, RQ3, RQ4) evaluate against nominal 90% coverage.
- **Secondary Sensitivity Levels**: Secondary coverage levels are evaluated at $80\%$ ($\alpha = 0.20$) and $95\%$ ($\alpha = 0.05$) for sensitivity analysis. Secondary sensitivity levels cannot replace or override an unfavorable primary result.
- **Uncapped Response Calibration**: Base predictors are trained on $\min(\text{rul\_true}, 125)$, but primary interval calibration responses and interval evaluation use uncapped $\text{rul\_true}$.
- **Upper Bound Policy**: Upper interval bounds $U_{it}$ must **NOT** be capped at 125 cycles. Prediction intervals must be free to express genuine prognostic uncertainty above the training target cap.
- **Secondary Capped Diagnostic**: Evaluation of prediction interval coverage against the capped target $\text{rul\_target}$ is permitted strictly as a secondary diagnostic, never as primary coverage evidence.

### 1.8 Interpretation and Methodological Boundaries

- **Evaluation vs. Training Weighting**: Engine-weighted evaluation across trajectories does not itself define training-loss weighting or conformal quantile weighting.
- **Nonconformity Construction**: Exact nonconformity scores and dependence-aware calibration construction remain later research decisions.
- **Guarantees Scope**: Empirical marginal coverage does not establish conditional coverage, simultaneous-trajectory validity, or stopping-time guarantees.
- **No-Tuning Restrictions**: Calibration set outcomes must not be used to select base-model hyperparameters. Held-out test outcomes must never be inspected or used for model tuning.

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

### 6.3 Subgroup Eligibility and Metric Aggregation Governance
- **Eligibility Threshold**: A subgroup is eligible for primary worst-group reliability analysis if at least **10 distinct engines** contribute at least 1 valid evaluation endpoint to that subgroup.
- **Fixed Endpoint Metadata Derivation**: Subgroup membership and eligibility are determined strictly from fixed offline endpoint metadata.
- **Identical Eligibility Rule**: Identical subgroup membership and eligibility definitions are enforced across all compared methods and random seeds.
- **No Reselection in Bootstrap**: Subgroup eligibility is not reselected within bootstrap resamples; eligibility remains fixed at the dataset partition level.
- **Reporting Counts**: Evaluation reports must provide distinct engine counts and total evaluation endpoint counts for each subgroup.
- **Ineligible Group Transparency**: Ineligible groups ($< 10$ contributing engines) remain visible in summary tables marked *descriptive-only*.
- **Family Availability**: If a required family has no eligible subgroup, mark that component as unavailable and do not claim full empirical support for RQ2.
- **Frozen Bootstrap Missing-Group Specification**: The handling of bootstrap replicates with unavailable subgroup estimates is frozen under ADR-018/ADR-019 and the statistical inference protocol (`statistical_inference_protocol.md`). If an eligible group is absent from a bootstrap replicate, conservative error propagation bounds it into $[ \text{WorstErr}_{\text{lower}}^{(b)}, \max(\text{WorstErr}_{\text{lower}}^{(b)}, 0.90) ]$; if all eligible groups are absent ($|G_{\text{available}}^{(b)}| = 0$), the conservative interval is exactly $[0.0, 0.90]$. Replicates are never discarded or redrawn.
- **Engine-Weighted Subgroup Coverage**: Within an eligible subgroup $g$, compute empirical coverage for each contributing engine $i$, then take the simple unweighted average across all contributing engines $N_g$:
  $$\text{Coverage}(g) = \frac{1}{N_g} \sum_{i \in \mathcal{E}_g} \text{Coverage}(i, g)$$
- **Subgroup Coverage Error**:
  $$\text{CoverageError}(g) = \left| \text{Coverage}(g) - (1 - \alpha) \right|$$
- **Reported Worst-Group Metrics**:
  - Maximum coverage error among eligible operating regimes
  - Maximum coverage error among eligible lifecycle stages
  - Overall worst-group coverage error across the union of eligible groups

---

## 7. Dataset Splits and Benchmark Protocols (Step 5.6)

### 7.1 Split Manifest Protocol
- **FD002**: `data/splits/fd002_engine_split_seed_2026.json` (130 / 52 / 26 / 52) is preserved byte-for-byte.
- **FD001**: `data/splits/fd001_engine_split_seed_2026.json` (50 / 20 / 10 / 20) generated via `scripts/generate_engine_splits.py`.
- **FD004**: `data/splits/fd004_engine_split_seed_2026.json` (124 / 50 / 25 / 50) generated via `scripts/generate_engine_splits.py`.

### 7.2 Official NASA Test Set Protocol
- NASA official test trajectories (`test_FD001.txt`–`test_FD004.txt`) are truncated prior to failure and supply terminal RUL labels in `RUL_FD00x.txt`.
- Official NASA test data serves as a secondary terminal-RUL benchmark only.
- Excluded from sequential maintenance simulation and primary RQ1–RQ4 confirmatory inference.
- Official test evaluation requires explicit validation of engine-to-terminal-label alignment.
- Official test evaluation uses the final 30 observed cycles of each test trajectory transformed with frozen training preprocessing.
- Trajectories shorter than 30 cycles are excluded; reports must explicitly provide IDs and counts of excluded trajectories.
- Pipelines must not claim a full-test benchmark when only an eligible subset was evaluated.
- Official test set labels MUST NEVER be used to tune preprocessing parameters, model architectures, or decision thresholds.

### 7.3 Optional Dataset Status (FD003)
- **FD003 Status**: FD003 remains an optional and inactive dataset. No FD003 artifacts, split manifests, or experiments are introduced in this phase.

---

## 8. Target Metric Aggregation & Statistical Uncertainty (Step 5.7)

### 8.1 Primary Engine-Weighted Metric Aggregation

Let:
- $N$ denote the total number of evaluated engines in the partition.
- $T_i$ denote engine $i$'s final run-to-failure cycle.
- $V_i = \{30, 31, \dots, T_i\}$ denote the set of evaluated offline prognostic endpoints for engine $i$.
- $n_i = |V_i| = T_i - 29$ denote the number of qualified prediction endpoints for engine $i$ ($T_i \ge 30$).
- $y_{it} = \text{RUL}_{\text{true}}(i, t)$ denote the uncapped ground-truth RUL.
- $p_{it}$ denote the point prediction for engine $i$ at cycle $t$.
- $[L_{it}, U_{it}]$ denote the conformal prediction interval for engine $i$ at cycle $t$.

The primary prognostic metrics are defined as follows:

- **Mean Absolute Error (MAE)**:
  $$\text{MAE} = \frac{1}{N} \sum_{i=1}^N \left[ \frac{1}{n_i} \sum_{t \in V_i} |p_{it} - y_{it}| \right]$$

- **Root Mean Squared Error (RMSE)**:
  $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N \left[ \frac{1}{n_i} \sum_{t \in V_i} (p_{it} - y_{it})^2 \right]}$$
  *(Critical Governance Rule: The overall RMSE is the square root of the average engine-level mean squared errors. Engine-specific RMSE values must NOT be averaged).*

- **Prediction Interval Coverage Probability (PICP)**:
  $$\text{PICP} = \frac{1}{N} \sum_{i=1}^N \left[ \frac{1}{n_i} \sum_{t \in V_i} \mathbf{1}\{L_{it} \le y_{it} \le U_{it}\} \right]$$

- **Mean Prediction Interval Width (MPIW)**:
  $$\text{MPIW} = \frac{1}{N} \sum_{i=1}^N \left[ \frac{1}{n_i} \sum_{t \in V_i} (U_{it} - L_{it}) \right]$$

- **Central Winkler Interval Score**:
  For nominal miscoverage level $\alpha$ (primary $\alpha = 0.10$):
  $$\text{IS}_\alpha(L, U; y) = (U - L) + \frac{2}{\alpha}(L - y)\mathbf{1}\{y < L\} + \frac{2}{\alpha}(y - U)\mathbf{1}\{y > U\}$$
  The metric is averaged within each engine, then equally across engines:
  $$\bar{\text{IS}}_\alpha = \frac{1}{N} \sum_{i=1}^N \left[ \frac{1}{n_i} \sum_{t \in V_i} \text{IS}_\alpha(L_{it}, U_{it}; y_{it}) \right]$$

- **Mean Simulated Maintenance Cost**:
  $$\bar{C} = \frac{1}{N} \sum_{i=1}^N C_i$$
  where $C_i$ is the single terminal cost realized by engine $i$ under sequential chronological replay.

### 8.2 Evaluation Scope Integrity Rules
- **Fixed Offline Endpoint Set**: The primary offline evaluation endpoint set $V_i$ is fixed across all evaluated models, calibration variants, and seeds.
- **No Policy Truncation**: The offline prognostic evaluation set $V_i$ is **NOT** truncated by an agent's maintenance policy intervention. Prognostic evaluation assesses model fidelity across the entire operational trajectory independently of maintenance decisions.
- **Missing Predictions**: Missing predictions at required endpoints in $V_i$ constitute a fatal evaluation error; pipelines are never permitted to silently drop endpoints or engines.
- **Maintenance Opportunities**: Sequential maintenance decision opportunities are strictly cycles 30 through $T_i - 1$. No maintenance decision occurs at terminal failure cycle $T_i$.

### 8.3 Statistical Uncertainty Framework
- **Unit of Independence**: Uncertainty is estimated via 95% engine-level paired/cluster-bootstrap confidence intervals with the **ENGINE** as the intact resampled unit.
- **Preserved Pairing**: Engine resampling preserves pairing between compared methods across identical resampled engine clusters.
- **Non-Independence of Windows**: Correlated time steps within an engine trajectory are non-independent observations; window-level resampling is strictly prohibited.
- **Statistical Specification (ADR-018)**: The statistical inference specification is frozen under ADR-018 and detailed in `research/research_design/statistical_inference_protocol.md`: 10,000 cluster-bootstrap replicates stratified by split quartiles, 98.75% decision intervals (Bonferroni family-wise control $\alpha = 0.05 / 4 = 0.0125$ across RQ1–RQ4), percentile construction (`method="linear"`), intersection-union testing across component criteria, missing-group conservative bound propagation, and frozen benchmark practical-effect margins ($\Delta_{\text{cost}} > 0.20$ SCU, $\Delta_{\text{error}} > 0.01$, coverage ceiling $E < 0.05$, noninferiority margins $< 1.0$ cycle for width and score).

---

## 9. Model Training Seeds & K-Means Reproducibility (Step 5.8)

### 9.1 Model Run Seeds
To evaluate training stability across random initializations, all model training pipelines must run across 5 fixed seeds:
`2026, 2027, 2028, 2029, 2030`

- Model run seeds evaluate weight initialization and stochastic optimization variance.
- Model run seeds MUST NOT alter engine partition split manifests or preprocessing parameters.
- Seeds are NOT additional independent engine units.

### 9.2 K-Means Regime Model Reproducibility
For FD002 and FD004 operating regime identification, the KMeans configuration is locked as:

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

**Reproducibility Specification**:
1. **Training Data Only**: Fitted strictly on standardized training partition settings in `float64` precision.
2. **Deterministically Sorted Rows**: Input rows must be sorted by `unit` and `cycle` prior to fitting.
3. **Single Row Contribution**: Each training observation row contributes exactly once.
4. **Canonical Label Assignment**: Canonical labels C1 through C6 are assigned by sorting fitted centroids lexicographically by `(setting1, setting2, setting3)`.
5. **Distance Assignment**: Observations are assigned to the nearest centroid using minimum squared Euclidean distance.
6. **Tie-Breaking Rule**: Exact distance ties are broken deterministically by selecting the lowest canonical regime index.
7. **Cluster Validity**: Pipelines must reject duplicate fitted centroids or empty fitted clusters with an explicit ValueError.
8. **Artifact Preservation**: Pipelines must persist the original-to-canonical cluster mapping, standardized centroids, unscaled original-unit centroids, and setting-scaler parameters.
9. **Dataset-Local Parameters**: FD004 fits its own regime model independently from FD002; regime cluster labels are dataset-local and not cross-dataset transferable.
10. **Scope Boundary**: No preprocessing implementation is added in this repair phase.
