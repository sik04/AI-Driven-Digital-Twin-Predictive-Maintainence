# IntelliTwin Data Splitting & Preprocessing Protocol
**Version:** 2.1.0-authoritative  
**Date:** October 3, 2026  
**Auditor / Architect:** Senior Machine Learning Engineer & Research Reviewer  
**Status:** Approved & Implemented Protocol  
**Scope:** Step 4 — Data Splitting, Temporal Isolation, and Feature Engineering Protocol

---

## 1. Dataset Identity & Structural Characteristics

The primary benchmark dataset utilized across this research program is the **NASA Commercial Modular Aero-Propulsion System Simulation (C-MAPSS)** turbofan engine degradation dataset, specifically subset **FD001**.

| Attribute | Specification |
|---|---|
| **Dataset Source** | NASA Prognostics Center of Excellence (PCoE) |
| **Asset Type** | High-bypass commercial turbofan jet engines |
| **Operating Condition** | Single sea-level condition (nominal ambient flight) |
| **Fault Mode** | High-Pressure Compressor (HPC) degradation |
| **Operational Variables** | 3 operational settings (`setting_1`, `setting_2`, `setting_3`) |
| **Sensor Channels** | 21 continuous telemetry sensors (`sensor_1` through `sensor_21`) |
| **Total Columns** | 26 numeric columns (unit, cycle, 3 settings, 21 sensors) |
| **Training Engines** | 100 run-to-failure engine fleets (20,631 total cycle observations) |
| **Test Engines** | 100 fleet engines truncated prior to system failure (13,096 cycles) |
| **Ground-Truth RUL** | Exact vector of true final cycle RULs for all 100 test engines |

---

## 2. NASA C-MAPSS FD001 Experimental Protocol

### Piecewise Linear RUL Target Formulation
In industrial turbofan engines, physical wear does not accumulate linearly from the initial flight cycle. During early operational life, components operate within their nominal design envelope. Wear manifests and accelerates only after an initial degradation threshold is reached.

To prevent models from attempting to predict arbitrary degradation trajectories during the healthy phase, the Remaining Useful Life (RUL) target is parameterized via a **piecewise linear degradation model**:
$$
y_{i}(t) = \min\left( RUL_{\max}, \, T_{i} - t \right)
$$
where:
- $T_{i}$ is the cycle of physical destruction (end-of-life) for engine $i$.
- $t$ is the current operational cycle index ($1 \le t \le T_{i}$).
- $RUL_{\max} = 125 \text{ cycles}$ is the standard literature saturation threshold.

### Discrete Health State Class Labeling
For cyber-physical digital twin health monitoring, continuous RUL values are discretized into three actionable structural states:
- **Class 0 (Healthy):** $y_{i}(t) > 60 \text{ cycles}$ — Standard continuous operation; standard inspection cadence.
- **Class 1 (Degrading):** $20 < y_{i}(t) \le 60 \text{ cycles}$ — Pre-emptive maintenance alert; logistics dispatch.
- **Class 2 (Critical):** $y_{i}(t) \le 20 \text{ cycles}$ — Severe risk / catastrophic failure avoidance zone; mandatory emergency intervention.

---

## 3. Deterministic Engine-Level Splitting

### Methodological Vulnerability Eliminated
Traditional machine learning pipelines frequently partition tabular time-series data using random sample shuffling (`train_test_split(df, shuffle=True)`). In equipment prognostics, row-level shuffling leaks temporal trajectory segments and asset-specific manufacturing variations across partitions. 

Furthermore, temporal truncation splits (e.g. training on early cycles and testing on late cycles across all engines) invalidate trajectory dynamics and catastrophic warning evaluations.

### Authoritative Protocol
The IntelliTwin framework enforces a strict **asset-level (engine-level) deterministic partition**:
1. All 100 training engines from `train_FD001.txt` are treated as atomic assets.
2. The engine IDs $\mathcal{U} = \{1, 2, \dots, 100\}$ are shuffled using a deterministic local pseudo-random number generator:
   $$\text{rng} = \text{RandomState}(\text{seed}=42)$$
3. With an 80/20 split ratio ($\text{val\_ratio} = 0.20$):
   - **Training Set ($\mathcal{U}_{\text{train}}$):** 80 complete engine trajectories ($N_{\text{train}} = 16,340 \text{ cycles}$).
   - **Validation Set ($\mathcal{U}_{\text{val}}$):** 20 complete run-to-failure engine trajectories ($N_{\text{val}} = 4,291 \text{ cycles}$).
   - **Independent Benchmark Test Set ($\mathcal{U}_{\text{test}}$):** 100 complete test engines from `test_FD001.txt` ($N_{\text{test}} = 13,096 \text{ cycles}$).

### Formal Mathematical Guarantees
$$
\mathcal{U}_{\text{train}} \cap \mathcal{U}_{\text{val}} = \emptyset, \quad \mathcal{U}_{\text{train}} \cup \mathcal{U}_{\text{val}} = \{1, 2, \dots, 100\}
$$
$$
|\mathcal{U}_{\text{train}}| = 80, \quad |\mathcal{U}_{\text{val}}| = 20, \quad |\mathcal{U}_{\text{test}}| = 100
$$

The exact split IDs are:
- **Validation Engines (20 units):** `[2, 3, 15, 21, 22, 24, 30, 38, 52, 53, 61, 64, 72, 75, 83, 85, 87, 88, 92, 93]`
- **Training Engines (80 units):** `[1, 4, 5, 6, 7, 8, 9, 10, 11, 12, ...]` (all remaining 80 units).

---

## 4. Strict Train / Validation / Test Isolation Protocol

### The Previous Data Leakage Defect
In the pre-Step-04 repository baseline, data was prepared following the flawed paradigm:
```text
ALL 100 TRAIN ENGINES (Train + Validation)
                     ↓
        fit StandardScaler parameters (μ, σ)
                     ↓
         Engine-level Train/Validation Split
```
Because the validation engines' 4,291 observations contributed to the computation of $\mu$ and $\sigma$, the standardization parameters were biased by validation telemetry (shifting feature means by up to $0.8466$ and scales by up to $0.4138$).

### The Corrected Zero-Leakage Architecture
The Step 4 protocol guarantees complete operational isolation:
```text
ALL AVAILABLE TRAINING ENGINES
              ↓
      ENGINE-LEVEL SPLIT (seed=42)
         /          \
        /            \
 TRAIN ENGINES    VALIDATION ENGINES
(80 units, 16340)  (20 units, 4291)
      ↓                 ↓
Feature Selection  Apply Selected Columns
(std >= 1e-4)           ↓
      ↓            Transform Only
Fit StandardScaler (scaler.transform)
(scaler.fit)            ↓
      ↓            Unseen Validation
Transform Train    Sequences & Metrics
(scaler.transform)
```

The independent NASA C-MAPSS test set (`test_FD001.txt`, 100 engines) is transformed using the fitted training scaler and is reserved strictly for final model evaluation.

---

## 5. Preprocessing Parameter Fitting (Zero-Leakage Guarantee)

All parameters learned from data are estimated **exclusively from $\mathcal{U}_{\text{train}}$**:

1. **Feature Selection (Low-Variance Filtering):**
   Sensors with operational variance $\text{Var}(s) < 10^{-4}$ across $\mathcal{U}_{\text{train}}$ are identified as uninformative. In FD001, exactly 7 sensors are identified as constant:
   $$\text{Constant Sensors} = \{\text{sensor\_1, sensor\_5, sensor\_6, sensor\_10, sensor\_16, sensor\_18, sensor\_19}\}$$
   The remaining 14 informative sensors are retained.
2. **StandardScaler Standardization:**
   $$\mu_{j} = \frac{1}{|\mathcal{D}_{\text{train}}|} \sum_{i \in \mathcal{D}_{\text{train}}} x_{i,j}, \quad \sigma_{j} = \sqrt{\frac{1}{|\mathcal{D}_{\text{train}}|} \sum_{i \in \mathcal{D}_{\text{train}}} (x_{i,j} - \mu_{j})^2}$$
   StandardScaler is fitted strictly on `train_df[train_mask, feature_cols]`.
   Validation and test features are normalized using $\hat{x}_{j} = \frac{x_{j} - \mu_{j}}{\sigma_{j}}$.
3. **Condition Clustering & Environmental Baseline:**
   The `EnvironmentalConditionHandler` (KMeans clustering and Ridge regressions) is fitted strictly on training engines:
   `env_handler.fit(train_df[train_mask, setting_cols], train_df[train_mask, sensor_cols])`.
4. **Unsupervised Anomaly Detector:**
   The `AnomalyDetector` (PCA projection and Isolation Forest) is fitted strictly on the healthy operational regime ($y \ge 60$) of training engines $\mathcal{U}_{\text{train}}$.

---

## 6. Engine-Safe Temporal Feature Engineering

To capture dynamic rates of deterioration, rolling window statistics (mean and standard deviation) are extracted over an authoritative window size $W = 5$ cycles.

### Engine Boundary Protection
If rolling statistics are computed on a global dataframe without grouping, the rolling window for the first $W-1$ cycles of Engine $k$ will ingest the terminal cycles of Engine $k-1$, creating severe cross-asset contamination.

The IntelliTwin implementation enforces strict asset encapsulation:
```python
rolling_dfs = []
for unit, group in df.groupby("unit"):
    group_sorted = group.sort_values("cycle")
    rm = group_sorted[sensor_cols].rolling(window=5, min_periods=1).mean().add_suffix("_mean5")
    rs = group_sorted[sensor_cols].rolling(window=5, min_periods=1).std().fillna(0).add_suffix("_std5")
    rolling_dfs.append(pd.concat([rm, rs], axis=1))
```
- Each engine trajectory is sorted monotonically by `cycle`.
- The rolling window is initialized with `min_periods=1` independently for cycle 1 of each asset.
- No rolling window observation ever crosses an engine boundary.

---

## 7. Boundary-Safe Sequence Generation Protocol

For recurrent architectures (Heteroscedastic LSTM and GRU), multi-sensor telemetry is organized into 3D sequential sliding tensors of shape:
$$
\mathbf{X} \in \mathbb{R}^{N \times L \times D}
$$
where $L = 30 \text{ cycles}$ (sequence length) and $D = 54 \text{ features}$.

### Sequence Isolation Guarantee
Sequences are generated strictly within individual engine trajectories:
1. For an engine with trajectory length $T_{i}$, exactly $\max(1, T_{i} - L + 1)$ sequences are extracted.
2. For each sequence $\mathbf{x}_{k} = \mathbf{S}_{i}[t - L : t]$, all $L$ timesteps belong exclusively to engine $i$.
3. If an engine's operational duration is shorter than $L$ (which occurs in some test engines), zero-order edge padding (repeating cycle 1) is applied exclusively at the front of that specific engine's data.
4. **Sequence Unit Traceability:** Every generated sequence is explicitly tagged with its engine ID `seq_units[k] = unit_i`. Automated unit-isolation tests verify that $\text{unique}(\text{train\_seq\_units}) \subseteq \mathcal{U}_{\text{train}}$ and $\text{unique}(\text{val\_seq\_units}) \subseteq \mathcal{U}_{\text{val}}$.

### Resulting Dataset Dimensions
- **Training Sequential Tensor:** $\mathbf{X}_{\text{train}} \in \mathbb{R}^{14,020 \times 30 \times 54}$ across 80 training engines.
- **Validation Sequential Tensor:** $\mathbf{X}_{\text{val}} \in \mathbb{R}^{3,711 \times 30 \times 54}$ across 20 validation engines.
- **Test Sequential Tensor (Benchmark Last Cycles):** $\mathbf{X}_{\text{test}} \in \mathbb{R}^{100 \times 30 \times 54}$ across 100 test engines.

---

## 8. Test-Set Isolation & Benchmark Protocol

The independent NASA C-MAPSS test set is subject to strict blind evaluation:
1. **Zero Preprocessing Influence:** The test set plays zero role in sensor variance filtering, rolling standard deviation baselines, or scaler fitting.
2. **Standard C-MAPSS Benchmark Evaluation:** In accordance with the NASA PHM 2008 competition standard, prognostic RUL regression metrics (RMSE, MAE, NASA Asymmetric Score $S$) are evaluated at the final available cycle of each of the 100 test engines ($\mathbf{x}_{\text{test\_last}}$ against true $y_{\text{test\_last}}$).
3. **Trajectory-Wide Conformal Calibration:** Split conformal prediction intervals are calibrated on the held-out validation set $\mathcal{U}_{\text{val}}$, and interval coverage (PICP, MPIW, Winkler score) is independently verified on $\mathcal{U}_{\text{test}}$.

---

## 9. Authoritative Random Seeds & Determinism Specifications

To guarantee mathematical reproducibility across platforms:
- **Central Random Seed:** `42`
- **Data Splitting RNG:** `np.random.RandomState(42)`
- **KMeans Operating Regime Clusterer:** `KMeans(n_clusters=4, random_state=42, n_init=10)`
- **Random Forest Baseline Regressor:** `RandomForestRegressor(n_estimators=100, random_state=42)`
- **XGBoost Baseline Regressor:** `xgb.XGBRegressor(n_estimators=100, random_state=42)`
- **Deep Learning Initialization:** PyTorch random seed `torch.manual_seed(42)`

---

## 10. Reproducibility Procedure & Artifact Verification

The authoritative split is automatically persisted as a machine-readable JSON artifact:
[`artifacts/splits/fd001_split.json`](file:///c:/Users/shiks/Downloads/res%20paper/artifacts/splits/fd001_split.json)

### Automated Test Verification
Automated test suites under `tests/` verify every requirement of this protocol:
```bash
pytest -v
```
- `tests/test_data_split.py`: Verifies zero unit overlap, strict determinism, split artifact consistency, and tabular/sequential split synchronization.
- `tests/test_preprocessing_protocol.py`: Empirically proves that `StandardScaler` matches isolated ground truth and differs from leaky fitting, validates sequence single-engine membership, and verifies rolling window boundary isolation.

---

## 11. Known Methodological Limitations & Future Scope

1. **Homogeneous Operating Conditions in FD001:** Subset FD001 evaluates HPC degradation under a single nominal operating condition. Multi-condition environmental shifts (6 flight conditions with diurnal thermal/altitude shifts) are present in subset FD002. Extending this isolated protocol to FD002 multi-condition clustering is scheduled for subsequent project phases.
2. **Recomputation Notice for Downstream Benchmarks:**
   > **IMPORTANT RESEARCH NOTICE:** All empirical metrics reported in legacy files (prior to Step 4) were generated under the pre-isolation data pipeline. Formal re-training and re-evaluation under this corrected protocol must be executed in Step 5/6 before updating research paper tables or publication figures.
