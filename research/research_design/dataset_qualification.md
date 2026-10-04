# C-MAPSS Dataset Qualification & Feasibility Specification (Step 4)

This document formalizes the dataset selection, feasibility qualification, engine-level split governance, input leakage rules, and reproducible split manifest for the IntelliTwin prognostic research project.

---

## 1. Locked Dataset Roles

| Dataset | Operating Conditions | Fault Modes | Role | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **FD002** | 6 regimes | 1 mode | **Primary Dataset** | Provides operating-condition heterogeneity required for testing condition-adaptive conformal calibration without introducing multiple fault modes into the primary experiment. |
| **FD001** | 1 condition | 1 mode | **Control Dataset** | Single-condition baseline for evaluating whether benefits attributed to condition adaptation diminish when operating-condition heterogeneity is absent. |
| **FD004** | 6 regimes | 2 modes | **Robustness Dataset** | Reserved for RQ4 robustness evaluation across combined operating-condition and multi-fault-mode heterogeneity. |
| **FD003** | 1 condition | 2 modes | **Optional Extension** | Secondary control/robustness dataset (optional; not required for main confirmatory experiment). |

---

## 2. Dataset Qualification and Feasibility (FD002)

- **Feasibility Status**: **PASS**
- **Training Trajectories**: 260 run-to-failure engines, 53,759 total cycle records.
- **Engine Lifetimes**: Approximately 128 to 378 cycles per engine.
- **Operating Regimes**: 6 distinct operating regimes identified from operating-setting variables (`setting1`, `setting2`, `setting3`).
- **Regime Sample Counts**: Substantial observation counts across all 6 regimes (~8,000–13,500 observations each).
- **Regime Exposure**: 100% of training engines (260/260) encounter all 6 operating regimes during their lifecycles.
- **Official NASA Test Set**: 259 engines, 33,991 total observations, all 6 operating regimes represented.
- **NASA Test Set Limitation**: Official NASA FD002 test trajectories are truncated prior to failure. Therefore, final sequential maintenance evaluation will use a held-out run-to-failure subset (52 engines) of the FD002 training dataset. The official NASA test set remains available as a secondary standard RUL benchmark.

---

## 3. Input and Leakage Governance Rules

### Candidate Model Inputs
- **Predictive Inputs**: Operating settings (`setting1`, `setting2`, `setting3`) and sensor measurements (`s1`–`s21`).
- **Engine Identifier**: Engine/unit ID is an identifier and must **NEVER** be used as a predictive feature encoding engine identity.
- **Preprocessing Isolation**: All learned preprocessing, normalization, feature-selection statistics, scaling parameters, or sequence transforms must be fit using training engines **ONLY**.

### Operating-Condition Definition
- Operating regimes/conditions must be derived **ONLY** from operating-setting variables.
- Conditions must **NEVER** be derived using true RUL, future cycles, test labels, future sensor information, or failure-time knowledge.

### Ground-Truth RUL Usage
- **Permitted Uses**: Supervised training targets, post-hoc evaluation metrics, and post-hoc wasted-RUL calculations.
- **Prohibited Uses**: True RUL must **NEVER** be used as an inference-time feature, a condition variable for the deployed calibrator, a maintenance-policy input, or information available to the model at prediction time.

---

## 4. Engine-Level Split Governance

The independent statistical and experimental unit is the **ENGINE**. Individual cycles, time steps, or sequence windows must never be split independently across partitions.

### FD002 Partition Breakdown

| Partition | Engines | Percentage | Role & Purpose |
| :--- | :--- | :--- | :--- |
| **Train** | 130 | 50% | Base RUL predictor training & preprocessing parameter fitting |
| **Calibration** | 52 | 20% | Conformal prediction interval calibration |
| **Validation** | 26 | 10% | Model selection, policy tuning, protocol debugging, and allowed bounded pilots |
| **Held-out Test** | 52 | 20% | Final confirmatory evaluation (untouched until final testing) |
| **Total** | **260** | **100%** | Full run-to-failure FD002 dataset |

---

## 5. Split-Generation Procedure & Reproducible Manifest

- **Random Seed**: `2026` (fixed, pre-specified; must not be re-rolled after inspecting downstream results).
- **Stratification Method**: Engine-level stratified random sampling based on engine-lifetime quartiles (Q1–Q4) to prevent lifetime distribution concentration bias.
- **Partition Disjointness**: 100% disjoint engine isolation (0 engine overlap between any partitions).
- **Regime Representation**: All 6 operating regimes are present in all 4 partitions.
- **Machine-Readable Manifest**: Saved at [`data/splits/fd002_engine_split_seed_2026.json`](../../data/splits/fd002_engine_split_seed_2026.json).

---

## 6. Maintenance-Simulation Scope Limitation

- **Simulation Context**: Benchmark datasets (C-MAPSS) contain simulated sensor degradation trajectories but do **NOT** contain real-world maintenance actions or empirical cost logs.
- **Reporting Scope**: Downstream operational claims must strictly refer to *"simulated sequential maintenance utility under a pre-specified maintenance cost model"* rather than demonstrated real-world maintenance savings.
- **Workflow Boundary**: The maintenance simulator itself belongs to Step 6 of the governing research workflow and is **NOT** implemented in Step 4.
