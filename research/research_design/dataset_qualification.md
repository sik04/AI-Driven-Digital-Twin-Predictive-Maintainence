# C-MAPSS Dataset Qualification & Feasibility Specification (Step 4)

This document formalizes the dataset selection, qualification, engine-level split governance, operating-condition clustering rules, input leakage rules, and reproducible split manifest for the IntelliTwin prognostic research project.

---

## 1. Locked Final Dataset Roles Summary

| Dataset | Feasibility Status | Operating Conditions | Fault Modes | Role | Primary Scientific Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FD002** | **PASS** | 6 regimes | 1 mode | **PRIMARY DATASET** | Provides operating-condition heterogeneity required for testing condition-adaptive conformal calibration without introducing multiple fault modes into the primary experiment. |
| **FD001** | **PASS** | 1 condition | 1 mode | **CONTROL DATASET** | Single-condition baseline for evaluating whether benefits attributed to condition adaptation diminish when operating-condition heterogeneity is absent. |
| **FD004** | **PASS** | 6 regimes | 2 modes | **REQUIRED ROBUSTNESS DATASET** | Reserved for RQ4 robustness evaluation across combined operating-condition and multi-fault-mode heterogeneity. |
| **FD003** | **PASS** | 1 condition | 2 modes | **OPTIONAL EXPLORATORY EXTENSION** | Secondary control/robustness dataset (optional; not required for primary confirmatory study). |

---

## 2. Dataset Feasibility and Characteristics

### FD002 — Primary Dataset (PASS)
- **Training Trajectories**: 260 run-to-failure engines, 53,759 total cycle records.
- **Engine Lifetimes**: Range approximately 128 to 378 cycles per engine.
- **Operating Regimes**: 6 distinct operating regimes identified from operating settings (`setting1`, `setting2`, `setting3`).
- **Regime Sample Counts**: Substantial observation counts across all 6 regimes (~8,000–13,500 observations each).
- **Regime Exposure**: 100% of training engines (260/260) encounter all 6 operating regimes during their lifecycles.
- **Official NASA Test Set**: 259 engines, 33,991 total observations, all 6 operating regimes represented.
- **NASA Test Set Limitation**: Official NASA FD002 test trajectories are truncated prior to failure. Therefore, final sequential maintenance evaluation will use a held-out run-to-failure subset (52 engines) of the FD002 training dataset. The official NASA test set remains available as a secondary standard RUL benchmark.

### FD001 — Control Dataset (PASS)
- **Training Trajectories**: 100 run-to-failure engines, 20,631 total cycle records.
- **Engine Lifetimes**: Range approximately 128 to 362 cycles per engine.
- **Operating Conditions**: 1 single operating condition (setting 1 ≈ 0, setting 2 ≈ 0, setting 3 ≈ 100).
- **Official NASA Test Set**: 100 engines, 13,096 observations.
- **Usage Rule**: FD001 is treated strictly as a single-operating-condition dataset. K-means clustering with $k=6$ is **NOT** applied to FD001.

### FD004 — Required Robustness Dataset (PASS)
- **Training Trajectories**: 249 run-to-failure engines, 61,249 total cycle records.
- **Engine Lifetimes**: Range approximately 128 to 543 cycles per engine.
- **Operating Conditions**: 6 operating regimes.
- **Fault Modes**: 2 underlying degradation/fault modes (mixed-fault degradation setting).
- **Official NASA Test Set**: 248 engines, 41,214 observations.
- **Metadata / File Count Discrepancy**: The included NASA C-MAPSS README text metadata and actual parsed dataset files disagree on engine counts. The parsed dataset files used by our executable pipeline (249 train engines, 248 test engines) are the authoritative source of truth.
- **Fault-Mode Claim Boundary**: Standard C-MAPSS records do not provide per-cycle or per-engine fault-mode labels. We **MAY** claim that FD004 evaluates robustness under a complex mixed-fault setting, but we **MUST NOT** claim fault-mode-specific calibration, performance, or maintenance utility unless defensible per-cycle labels are later independently established.

### FD003 — Optional Exploratory Extension (PASS)
- **Training Trajectories**: 100 run-to-failure engines, 24,720 total cycle records.
- **Engine Lifetimes**: Range approximately 145 to 525 cycles per engine.
- **Operating Conditions**: 1 single operating condition, 2 fault modes.
- **Official NASA Test Set**: 100 engines, 16,596 observations.
- **Usage Rule**: Retained as an optional exploratory extension; not required for the primary confirmatory study.

---

## 3. FD002 Operating-Condition Identification Rule

Operating conditions for FD002 must be identified using **ONLY** the three operating-setting variables (`setting1`, `setting2`, `setting3`).

### Standardization & K-Means Clustering Procedure
1. Extract `setting1`, `setting2`, and `setting3` from observation rows.
2. Fit an operating-setting scaler using **TRAINING ENGINES ONLY**.
3. Standardize operating settings using parameters learned from training engines only.
4. Fit a K-means clustering algorithm on standardized training-engine setting observations with **$k = 6$**.
5. Freeze the scaler parameters and the six fitted cluster centers.
6. Calibration, validation, and held-out test cycles must **NOT** refit scaling or clustering; their cycles are assigned to the nearest frozen training-derived cluster center.

### Descriptive Physical Setting Clusters
The six approximate physical operating-setting clusters observed in FD002 are:
- **C1**: setting 1 ≈ 0, setting 2 ≈ 0.00, setting 3 ≈ 100
- **C2**: setting 1 ≈ 10, setting 2 ≈ 0.25, setting 3 ≈ 100
- **C3**: setting 1 ≈ 20, setting 2 ≈ 0.70, setting 3 ≈ 100
- **C4**: setting 1 ≈ 25, setting 2 ≈ 0.62, setting 3 ≈ 60
- **C5**: setting 1 ≈ 35, setting 2 ≈ 0.84, setting 3 ≈ 100
- **C6**: setting 1 ≈ 42, setting 2 ≈ 0.84, setting 3 ≈ 100

*(Note: These numerical values are descriptive. The standardized training-derived K-means procedure is the executable assignment rule.)*

### Strict Leakage Rule
Operating-condition identification must **NEVER** use:
- true RUL
- degradation-stage labels
- future cycles
- failure-time knowledge
- future sensor values
- test labels
- maintenance outcomes

Sensor measurements are **NOT** used to define operating regimes.

---

## 4. Input and Target Leakage Governance

### Candidate Model Inputs
- **Predictive Inputs**: Operating settings (`setting1`, `setting2`, `setting3`) and sensor measurements (`s1`–`s21`).
- **Engine Identifier**: Engine/unit ID is an identifier and must **NEVER** be used as a predictive feature encoding engine identity.
- **Preprocessing Isolation**: All learned preprocessing, normalization, feature-selection statistics, scaling parameters, or sequence transforms must be fit using training engines **ONLY**.

### Ground-Truth RUL Usage
- **Permitted Uses**: Supervised training targets, post-hoc evaluation metrics, and post-hoc wasted-RUL calculations.
- **Prohibited Uses**: True RUL must **NEVER** be used as an inference-time feature, a condition variable for the deployed calibrator, a maintenance-policy input, or information available to the model at prediction time.

---

## 5. RQ2 Subgroup Scope & Worst-Group Analysis Rule

### Predefined Subgroup Families
RQ2 evaluates conditional reliability across **TWO** predefined subgroup families:
1. **Operating-Condition Groups**: The six FD002 operating regimes (C1–C6).
2. **Degradation-Stage Groups**: Predefined degradation stages (e.g., early life, mid life, late life). Exact degradation-stage boundaries are intentionally deferred to Step 5 (Data & Evaluation Protocol) and must be frozen before confirmatory testing.

### Ground-Truth Usage for Subgroups
True RUL / known failure time may be used to construct degradation-stage groups **ONLY** for post-hoc evaluation. They must **NEVER** become inference-time features, calibration inputs, condition-adaptive features, or maintenance policy inputs.

### Worst-Group Reliability Rule
- **Primary Subgroup Families**: Operating regimes and degradation stages.
- **Primary Reliability Metric**: Worst-group conditional coverage error across predefined eligible groups from these two families.
- **Secondary Diagnostic Analysis**: Regime × degradation-stage intersections are treated as **secondary diagnostic analysis only** due to potential limited sample sizes in intersection cells.
- **Subgroup Eligibility**: Minimum subgroup-size rules are deferred to Step 5 and must be fixed before confirmatory testing. No post-hoc subgroup creation is permitted based on observed results.

---

## 6. Engine-Level Split Governance & Manifest

The independent statistical and experimental unit is the **ENGINE**. Individual cycles, time steps, or sequence windows must never be split independently across partitions.

### FD002 Partition Breakdown

| Partition | Engines | Percentage | Role & Purpose |
| :--- | :--- | :--- | :--- |
| **Train** | 130 | 50% | Base RUL predictor training & preprocessing parameter fitting |
| **Calibration** | 52 | 20% | Conformal prediction interval calibration |
| **Validation** | 26 | 10% | Model selection, policy tuning, protocol debugging, and allowed bounded pilots |
| **Held-out Test** | 52 | 20% | Final confirmatory evaluation (untouched until final testing) |
| **Total** | **260** | **100%** | Full run-to-failure FD002 dataset |

### Reproducible Split Manifest
- **Random Seed**: `2026` (fixed, pre-specified).
- **Stratification Method**: Engine-level stratified random sampling based on engine-lifetime quartiles (Q1–Q4).
- **Disjointness**: 100% disjoint engine isolation (0 engine overlap between any partitions).
- **Regime Representation**: All 6 operating regimes are present in all 4 partitions.
- **Manifest Location**: Saved at [`data/splits/fd002_engine_split_seed_2026.json`](../../data/splits/fd002_engine_split_seed_2026.json).

---

## 7. Maintenance-Simulation Scope Limitation

- **Simulation Context**: Benchmark datasets (C-MAPSS) contain simulated sensor degradation trajectories but do **NOT** contain real-world maintenance actions or empirical cost logs.
- **Reporting Scope**: Downstream operational claims must strictly refer to *"simulated sequential maintenance utility under a pre-specified maintenance cost model"* rather than demonstrated real-world maintenance savings.
- **Workflow Boundary**: The maintenance simulator itself belongs to Step 6 of the governing research workflow and is **NOT** implemented in Step 4.

---

## 8. Step 4 Completion Audit

| Audit Item | Status | Verification Detail |
| :--- | :--- | :--- |
| FD002 = Primary Dataset | **PASS** | Multi-condition 6-regime benchmark for condition adaptation |
| FD001 = Control Dataset | **PASS** | Single-condition baseline for condition adaptation control |
| FD004 = Required Robustness Dataset | **PASS** | Multi-condition, 2-fault-mode robustness benchmark |
| FD003 = Optional Exploratory Extension | **PASS** | Single-condition, 2-fault-mode optional extension |
| FD002 Feasibility | **PASS** | 260 train engines, 53,759 cycles, lifetimes 128–378 cycles |
| FD001 Qualification | **PASS** | 100 train engines, 20,631 cycles, lifetimes 128–362 cycles |
| FD004 Qualification | **PASS** | 249 train engines, 61,249 cycles, lifetimes 128–543 cycles |
| FD002 Run-to-Failure Engines | **PASS** | 260 full run-to-failure training engines used for split |
| FD002 Split Breakdown | **PASS** | 130 Train / 52 Cal / 26 Val / 52 Test |
| Split Seed | **PASS** | Fixed pre-specified seed `2026` |
| Engine-Level Splitting | **PASS** | Unit of independence is Engine |
| Lifetime-Quartile Stratification | **PASS** | Q1–Q4 engine lifetime stratification applied |
| Disjoint Engine Isolation | **PASS** | Zero engine overlap across partitions |
| Leakage Rule | **PASS** | Preprocessing parameters fit on train engines only |
| Ground-Truth RUL Governance | **PASS** | True RUL restricted from inference/calibration inputs |
| FD002 Regime Identification | **PASS** | Derived only from 3 operating settings using train K-means ($k=6$) |
| Cluster Center Freezing | **PASS** | Scaler and cluster centers frozen after train fit |
| Nearest Frozen Center Assignment | **PASS** | Non-train cycles assigned to frozen cluster centers |
| RQ2 Subgroup Scope | **PASS** | Operating regimes + degradation stages |
| Degradation Stage Deferral | **PASS** | Stage boundaries deferred to Step 5 |
| Worst-Group Primary Scope | **PASS** | Regimes and stages primary; intersections secondary diagnostic |
| NASA Test Set Limitation | **PASS** | Truncated test set recognized; held-out train subset used for sequential utility |
| Simulated Utility Boundary | **PASS** | Claims specified as simulated utility under cost model |
| C-MAPSS Maintenance Limitation | **PASS** | No empirical maintenance action/cost history in C-MAPSS |
| FD004 Claim Boundary | **PASS** | Fault-mode-specific claims prohibited without explicit labels |
| FD004 Metadata Discrepancy | **PASS** | Parsed files (249 train / 248 test) documented as source of truth |
