# Data & Evaluation Protocol — Step 5

This document serves as the authoritative specification for data preprocessing, label construction, feature engineering, sequence windowing, and experimental evaluation protocols for the IntelliTwin research platform.

---

## 1. RUL Target Construction

### 1.1 Mathematical Definition of `rul_true`

For a full run-to-failure engine trajectory $i$, let $T_{\text{failure}}(i)$ denote the final observed operational cycle of that engine, and let $t$ denote the current cycle number ($1 \le t \le T_{\text{failure}}(i)$).

The uncapped ground-truth Remaining Useful Life (RUL) for engine $i$ at cycle $t$ is defined as:

$$\text{RUL}_{\text{true}}(i, t) = T_{\text{failure}}(i) - t$$

- **Meaning**: `rul_true` represents the exact, uncapped actual number of remaining operational cycles until functional failure.
- **Role in Research Pipeline**: `rul_true` is retained exclusively for offline ground-truth scientific evaluation, post-hoc error metrics, degradation-stage labeling (to be specified in later Step 5 protocol sections), wasted RUL calculations, and post-hoc maintenance simulator consequence analysis.

### 1.2 Mathematical Definition of `rul_target`

The primary target used for supervised training of all RUL prediction models is defined as:

$$\text{RUL}_{\text{target}}(i, t) = \min\left(\text{RUL}_{\text{true}}(i, t), 125\right)$$

- **Fixed Cap Value**: The maximum target value is strictly locked at $125$ cycles.
- **Piecewise-Linear Target**: The training target is constant ($125$) during early operational cycles when $RUL_{\text{true}}(i, t) \ge 125$, and decreases linearly with a slope of $-1$ as the engine approaches failure once $RUL_{\text{true}}(i, t) < 125$.

### 1.3 Purpose of the Capped Training Target

1. **Physical Degradation Saturation**: Turbofan engines exhibit negligible component wear during early operational cycles. Prior to degradation onset, attempting to regress exact initial engine lifetimes (which vary across units) introduces noise into function approximators without physical basis.
2. **Standard Benchmark Protocol**: A piecewise-linear cap of 125 cycles reflects the standard benchmark convention in turbofan prognostic literature (e.g., Zheng et al., 2017; Diao et al., 2026), standardizing point prediction task formulation.
3. **No-Tuning Rule**: The cap value of 125 cycles is strictly fixed by research decision. It must **NOT** be tuned, optimized, or altered based on validation error, test set performance, or hyperparameter sweeps.

### 1.4 Distinction Between Training Target and Ground-Truth Evaluation

`rul_true` and `rul_target` represent distinct scientific quantities and must **NEVER** be treated as interchangeable:

- **Supervised Training**: All base RUL model architectures (e.g., linear baselines, temporal neural networks) are trained strictly using `rul_target` as the scalar regression target.
- **Scientific Evaluation & Maintenance Decision Analysis**: All final scientific evaluation metrics (e.g., MAE, RMSE, prediction interval coverage, conditional miscalibration auditing) and downstream maintenance simulator consequence metrics (e.g., wasted useful life $RUL_{\text{wasted}}$, late/failure intervention rates, total operational cost per engine) must use uncapped `rul_true` as the ground-truth benchmark.

### 1.5 Model Output Interpretation & Maintenance Consequence Analysis

- **Early-Life Saturation**: Because the base RUL predictor is trained against $\min(\text{RUL}_{\text{true}}, 125)$, point predictions and prediction intervals during early engine life are expected to saturate near the cap value of 125 cycles.
- **Reporting Rule**: The capped prediction target `rul_target` must **NEVER** be reported or interpreted as if it were the engine's actual uncapped remaining operational lifetime.
- **Wasted Useful Life Rule**: Wasted useful life resulting from premature maintenance interventions must be calculated strictly from uncapped `rul_true` ($\text{RUL}_{\text{wasted}} = \text{RUL}_{\text{true}}(i, t_{\text{replacement}})$), **NEVER** from `rul_target`.

### 1.6 Inference-Time Input Leakage Restrictions

Consistent with the Step 4 leakage governance rules (ADR-011):

1. Neither `rul_true`, `rul_target`, engine failure cycle $T_{\text{failure}}(i)$, nor any future-cycle information may be used as predictive model inputs at inference time.
2. Failure cycle $T_{\text{failure}}(i)$ may be used strictly to construct supervised labels for offline training on full run-to-failure trajectories.
3. `rul_true` is strictly prohibited from being used as:
   - A deployed model feature input
   - An operating-condition feature or regime identification input
   - A conformal calibration condition variable
   - A maintenance policy decision input
   - Information assumed to be available at prediction time

### 1.7 Summary Comparison of Target Quantities

| Quantity | Definition | Primary Purpose | Inference-Time Model Input? |
|---|---|---|---|
| `rul_true` | $T_{\text{failure}}(i) - t$ | Offline evaluation / post-hoc ground truth / maintenance consequences | **NO** (Strict Leakage Violation) |
| `rul_target` | $\min(\text{RUL}_{\text{true}}, 125)$ | Supervised model training target | **NO** (Strict Leakage Violation) |

---

## 2. Sensor Diagnostic — Pending Final Input Lock

### 2.1 Diagnostic Scope and Strict Partition Boundaries

A training-only exploratory diagnostic was executed for FD002 sensors $s1$ through $s21$ using the committed script [`scripts/audit_fd002_sensors.py`](../../scripts/audit_fd002_sensors.py).

- **Data Source**: `data/raw/cmapss/train_FD002.txt`
- **Engine Subset**: Restricted strictly to the **130 engines** defined in `partitions.train` of [`data/splits/fd002_engine_split_seed_2026.json`](../../data/splits/fd002_engine_split_seed_2026.json).
- **Observation Rows**: 26,693 training cycles.
- **Metrics Evaluated**: Row count, missing count, unique values, min, max, overall range, mean, std, variance, median absolute engine-cycle Pearson correlation, 6 per-regime std metrics (`regime_1_std`–`regime_6_std`), and 6 per-regime range metrics (`regime_1_range`–`regime_6_range`).
- **Zero-Leakage Assurance**: No calibration (52 engines), validation (26 engines), or held-out test (52 engines) partition data was loaded or inspected for any diagnostic statistic.

### 2.2 Summary of Diagnostic Findings

The full output is recorded in [`research/research_design/fd002_training_sensor_diagnostic.csv`](fd002_training_sensor_diagnostic.csv).

1. **Zero Within-Regime Variation (Constant within Regimes)**:
   - Sensors **s1**, **s5**, **s18**, and **s19** exhibit exactly 0.0 standard deviation and 0.0 range within each of the 6 operating regimes ($k=6$ K-means fit on training settings). Their overall variation is driven entirely by operating condition shifts.
   - Sensors **s6** and **s10** exhibit near-zero within-regime standard deviation (< 0.005) and negligible within-regime range ($\le 0.02$).
2. **Near-Constant / Low Variation**:
   - Sensor **s16** exhibits extremely low overall standard deviation (0.004709) and only 2 unique values across 26,693 training rows.
3. **Sensors with Clear Within-Regime Variability**:
   - Sensors **s2**, **s3**, **s4**, **s7**, **s8**, **s9**, **s11**, **s12**, **s13**, **s14**, **s15**, **s17**, **s20**, and **s21** exhibit non-zero within-regime variation and/or temporal degradation correlation.

### 2.3 Diagnostic-Only Threshold Governance

- **Descriptive Convenience**: The descriptive label threshold (`DIAGNOSTIC_NEAR_CONSTANT_STD_THRESHOLD = 0.01`) used in `scripts/audit_fd002_sensors.py` serves strictly as an exploratory labeling convenience.
- **Not a Locked Decision**: It is **NOT** a locked scientific research threshold and **NOT** an automated feature-selection rule.
- **Raw Statistics Preserved**: Modifying or removing the descriptive threshold does not alter the underlying raw statistics recorded in the diagnostic CSV.
- **Final Sensor Subset Unlocked**: Final sensor inclusion, exclusion, operating-setting retention, and cycle feature policies will be evaluated and decided separately in Step 5.2B.
- **No Automatic Removal**: Zero sensors have been removed from data pipelines or model input definitions.

---

## 3. Final Sensor and Input Policy

### 3.1 Engine Identifier Role (`unit`)
- **Role**: Engine identifier, partition assignment, engine-level grouping, chronology validation, and unit-of-independence statistical analysis.
- **Predictive Constraint**: `unit` MUST NOT be used as a predictive feature in any model.

### 3.2 Operational Cycle Role (`cycle`)
- **Role**: Temporal ordering, sequence/window construction, RUL label construction, chronological replay, and trajectory indexing.
- **Predictive Constraint**: `cycle` MUST NOT be used as a predictive feature.
- **Rationale**: The RUL predictor must learn component health and degradation status strictly from physical operating settings and sensor telemetry, rather than relying on direct operational age as a shortcut.

### 3.3 Operating Settings (`setting1`, `setting2`, `setting3`)
- **Retained Features**: All three operating settings (`setting1`, `setting2`, `setting3`) are retained as predictive inputs.
- **Regime Identification Role**: Operating settings remain the **ONLY** variables used to assign operating-condition regimes ($k=6$ K-means clustering fit on training settings).
- **Leakage Constraint**: No sensor, RUL label, cycle index, future observation, failure time, or engine ID may influence operating regime assignment.

### 3.4 Final Retained Sensor Set (14 Sensors)
The following 14 sensors are strictly locked as predictive inputs:
`["s2", "s3", "s4", "s7", "s8", "s9", "s11", "s12", "s13", "s14", "s15", "s17", "s20", "s21"]`

### 3.5 Final Excluded Sensor Set (7 Sensors)
The following 7 sensors are strictly locked as excluded from predictive inputs:
`["s1", "s5", "s6", "s10", "s16", "s18", "s19"]`

- **Exclusion Rationale**:
  - `s1`, `s5`, `s18`, `s19`: Exhibit zero within-regime variation ($\text{std} = 0.0$, $\text{range} = 0.0$) across all six FD002 operating regimes.
  - `s6`, `s10`: Exhibit negligible within-regime variation ($\text{std} < 0.005$, $\text{range} \le 0.02$).
  - `s16`: Descriptively near-constant with extremely low variation ($\text{std} = 0.004709$) and only 2 unique values across 26,693 training cycles.
  - Because operating settings (`setting1`–`setting3`) explicitly provide operating-condition information to the predictor, these seven sensors are excluded to prevent redundant, uninformative feature inputs.

### 3.6 Common Sensor Schema
The identical 14-sensor schema (`s2`, `s3`, `s4`, `s7`, `s8`, `s9`, `s11`, `s12`, `s13`, `s14`, `s15`, `s17`, `s20`, `s21`) is enforced across:
- **FD001** (control dataset)
- **FD002** (primary multi-condition dataset)
- **FD004** (required robustness dataset)

Enforcing a common sensor schema across all benchmark datasets prevents dataset-specific feature cherry-picking and ensures consistent cross-dataset evaluation.

### 3.7 Canonical Per-Cycle Predictive Feature Vector (17 Features)
Each operational cycle is represented by a 17-dimensional predictive feature vector:
$$\text{Dimension} = 3 \text{ operating settings} + 14 \text{ sensors} = 17 \text{ features}$$

**Canonical Ordered List**:
`["setting1", "setting2", "setting3", "s2", "s3", "s4", "s7", "s8", "s9", "s11", "s12", "s13", "s14", "s15", "s17", "s20", "s21"]`

**Strict Exclusions**:
The following quantities are strictly excluded from predictive model inputs: `unit`, `cycle`, `s1`, `s5`, `s6`, `s10`, `s16`, `s18`, `s19`, `rul_true`, `rul_target`, engine failure time $T_{\text{failure}}$, and all future-cycle observations.

### 3.8 Summary of Variable Roles

| Variable Group | Model Input? | Purpose |
|---|---|---|
| `unit` | No | Engine identifier / grouping |
| `cycle` | No | Chronology / window construction |
| `setting1–3` | Yes | Operating state + regime assignment |
| Retained 14 sensors | Yes | Prognostic measurements |
| Excluded 7 sensors | No | Removed by locked input policy |
| `rul_target` | No | Supervised training label |
| `rul_true` | No | Offline ground truth |
| Future/failure information | No | Prohibited leakage |

---

## 4. Normalization and Preprocessing Strategy

### 4.1 FD002 Operating-Setting Normalization
- **Scaler Fitting**: A single `StandardScaler` is fit on `setting1`, `setting2`, and `setting3` using observations from the **130 FD002 training engines ONLY**.
$$\text{setting}_{k, \text{normalized}} = \frac{\text{setting}_k - \mu_{\text{train}, k}}{\sigma_{\text{train}, k}}$$
- **Frozen Application**: The fitted scaler parameters ($\mu_{\text{train}, k}$, $\sigma_{\text{train}, k}$) are frozen and applied identically to FD002 training, calibration, validation, and held-out test partitions. Calibration, validation, and test cycles MUST NOT refit or modify the setting scaler.

### 4.2 Relation to Operating Regime Identification
- The **SAME** training-fitted operating-setting scaler is used prior to FD002 operating regime identification.
- **Regime Identification Protocol**:
  1. Fit operating-setting `StandardScaler` on FD002 training engines only.
  2. Standardize training-engine operating settings.
  3. Fit K-means clustering with $k=6$ on standardized training-engine settings only.
  4. Freeze setting scaler parameters and the 6 K-means cluster centers.
  5. Assign calibration, validation, and test cycles to the nearest frozen training cluster center without refitting.
- The normalized setting values produced by this frozen scaler serve directly as the three operating-setting features supplied to the predictive model. No separate setting scaler is fit.

### 4.3 FD002 Sensor Normalization (Regime-Aware Z-Score)
For the 14 retained sensors on FD002, feature normalization employs **OPERATING-REGIME-AWARE Z-SCORE NORMALIZATION**:

$$x_{\text{normalized}} = \frac{x - \mu_{\text{train}}[g, j]}{\sigma_{\text{train}}[g, j]}$$

where $g \in \{1 \dots 6\}$ denotes the assigned operating regime, and $j$ denotes the retained sensor index.

- **Statistics Estimation**: For each regime $g$ and sensor $j$, the regime-specific mean $\mu_{\text{train}}[g, j]$ and standard deviation $\sigma_{\text{train}}[g, j]$ are estimated using observations from the **130 FD002 training engines ONLY**.
- **Frozen Pipeline Application**:
  1. Standardize cycle operating settings using the frozen training setting scaler.
  2. Assign cycle operating regime using the frozen training K-means cluster centers.
  3. Normalize the 14 retained sensor measurements using the frozen regime-specific statistics $(\mu_{\text{train}}[g, j], \sigma_{\text{train}}[g, j])$ corresponding to the assigned regime.
- Non-training partitions (calibration, validation, test) MUST NOT refit or adjust sensor normalization statistics.

### 4.4 FD001 Normalization Protocol
FD001 is the single-condition baseline control dataset. K-means regime clustering is **NOT** applied to FD001.
- **Operating Settings**: Fit a `StandardScaler` on FD001 training engines only; freeze and apply to later partitions.
- **Sensors**: Use global training-only z-score normalization across all 14 retained sensors:
$$x_{\text{normalized}} = \frac{x - \mu_{\text{train}}[j]}{\sigma_{\text{train}}[j]}$$
No regime-specific sensor normalization is required because FD001 operates under a single operating condition.

### 4.5 FD004 Normalization Protocol
FD004 contains multiple operating conditions and follows the same regime-aware normalization principle as FD002:
- Once the FD004 engine-level split is frozen in later Step 5 sub-steps:
  1. Fit operating-setting scaler on FD004 training engines only.
  2. Fit $k=6$ K-means regime model on FD004 training settings only.
  3. Freeze scaler parameters and cluster centers.
  4. Compute regime-specific sensor means and standard deviations on FD004 training engines only.
  5. Apply frozen transformations to FD004 calibration, validation, and test partitions.
- FD004 statistics MUST be learned from its own training engines and MUST NOT directly copy FD002 normalization values.

### 4.6 Missing-Value Policy
- **No Silent Imputation**: C-MAPSS telemetry files contain zero missing values. If an unexpected missing value occurs in settings, sensors, unit IDs, or cycles, preprocessing pipelines MUST raise an explicit data validation error requiring manual inspection.
- **Prohibited Methods**: Mean imputation, median imputation, forward fill, backward fill, linear interpolation, and KNN imputation are strictly prohibited.

### 4.7 Zero-Standard-Deviation Validation Rule
If a training-derived standard deviation for any retained feature is zero where division would be required:
- Preprocessing pipelines MUST NOT silently replace the std with 1.0.
- Preprocessing pipelines MUST NOT silently add an epsilon value.
- Preprocessing pipelines MUST NOT automatically drop the feature.
- The pipeline MUST raise a validation failure to halt execution and mandate explicit review.

### 4.8 Prohibited Feature Transformations
The following feature engineering and preconditioning methods are explicitly prohibited at this stage:
- Principal Component Analysis (PCA) or Independent Component Analysis (ICA)
- Polynomial feature expansion
- Temporal smoothing filters (moving average, exponential smoothing, Savitzky-Golay)
- Data clipping, winsorization, or test-set-derived outlier removal
- Learned feature selection or wrapper/filter selection using validation/test error
- Target encoding or RUL-derived predictive features

### 4.9 Training-Only Learning Rule
All learned preprocessing parameters—including setting means/stds, sensor means/stds, K-means cluster centers, and scaling parameters—MUST be fit strictly on the corresponding **TRAINING ENGINE PARTITION ONLY**. Calibration, validation, and test partitions may be transformed using frozen training parameters but MUST NEVER influence parameter estimation.

---

## 5. Unresolved Protocol Specifications (Pending Later Step 5 Parts)

The following data preprocessing, sequence windowing, and evaluation specifications remain explicitly unresolved and will be defined in subsequent Step 5 sub-steps:

- Step 5.4 — Sequence length, window stride, padding policy, and short-trajectory handling
- Step 5.5 — Degradation-stage boundary construction ($RUL_{\text{true}}$ thresholds for early/mid/late failure stages) and subgroup eligibility thresholds
- Step 5.6 — Dataset-specific split protocols for FD001 and FD004, and official NASA test trajectory evaluation protocol
- Step 5.7 — Nominal conformal coverage levels ($\alpha$ levels) and calibration framing
- Step 5.8 — Model architecture specifications and baseline model families


