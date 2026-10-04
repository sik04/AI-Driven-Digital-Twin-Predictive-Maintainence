# Experiment A v1 — Conditional Reliability Audit Protocol Design

> **Document Status**: **Provisional v1 — Locked for Current Research Iteration**
> **Authors**: Mayank Singh, Shiksha Pandey, Ruchi Gupta
> **Date**: 2026-10-04
> **Governance Policy**: Locked for the current research iteration, but subject to revision if later evidence or methodological constraints invalidate the formulation.

---

## 1. Primary Research Question Alignment

Experiment A directly addresses **RQ1**:

> **RQ1: To what extent can nominally calibrated RUL prediction intervals conceal conditional reliability failures across degradation stages and operating regimes in turbofan prognostics?**

---

## 2. Dataset Selection (LOCKED v1)

Experiment A is restricted to two specific datasets from the NASA C-MAPSS benchmark suite:

### 2.1 Primary Dataset: C-MAPSS FD002
- **Role**: **Primary Experiment A Dataset**
- **Characteristics**: Multiple operating conditions (6 operational regimes, 1 fault mode).
- **Research Purpose**: Serves as the primary benchmark for the **operating-regime conditional reliability audit**. It allows testing whether prediction intervals that achieve nominal aggregate coverage over a multi-regime fleet systematically fail within specific operating regimes.

### 2.2 Control Dataset: C-MAPSS FD001
- **Role**: **Secondary / Control Dataset**
- **Characteristics**: Single operating condition (1 operational regime, 1 fault mode).
- **Research Purpose**: Serves as a controlled environment where operating-regime shifts are absent. It isolates the **degradation-stage conditional reliability audit** from regime-shift confounding.

### 2.3 Excluded Datasets
- **FD003** and **FD004** are explicitly excluded from Experiment A.
- They are reserved for downstream robustness evaluation in **Experiment D**.

---

## 3. Base Predictor Model Families (LOCKED v1)

To ensure that observed conditional calibration failures reflect intrinsic prognostic properties rather than artifacts of a single network architecture, Experiment A will evaluate two distinct model families:

1. **Gradient Boosting Regressor (GBR)**: Represents non-recurrent, tree-based ensemble algorithms.
2. **Long Short-Term Memory Network (LSTM)**: Represents recurrent temporal deep learning architectures.

*Methodological Rule*: The objective is **not** to conduct an exhaustive model comparison benchmark, but to verify whether conditional calibration failures persist across fundamentally different model families. Model implementation and hyperparameter tuning will occur in later phases.

---

## 4. High-Level Calibration Strategy (LOCKED AT HIGH LEVEL)

Experiment A will implement:

> **Global Conformal Calibration**

- **Purpose**: First achieve or target valid global/marginal coverage ($P(Y \in C(X)) \approx 1-\alpha$) across the overall test set, and subsequently audit whether this marginal validity masks severe subgroup conditional undercoverage.

### Deferred Calibration Details (TBD)
The exact conformal prediction implementation details are deliberately deferred and will be finalized during the detailed calibration protocol design:
- Standard split conformal prediction vs. normalized conformal prediction vs. conformalized quantile regression (CQR)
- Exact nonconformity score definition
- Exact calibration set partitioning scheme

*Rule*: No calibration code will be implemented in Phase 2.

---

## 5. Conditional Audit Group Definitions

### 5.1 Primary Audit Axis: Operating Regime
- **Status**: **Primary Conditional Audit Axis**
- **Definition Rule**: Operating regimes must be derived strictly from inference-time-observable C-MAPSS operating setting variables (e.g., altitude, Mach number, throttle setting).
- **Leakage Constraint**: True future RUL ($y_i$) must **NEVER** be used to define deployable operating regimes.
- **Implementation Status**: Exact regime-identification methodology (canonical C-MAPSS settings vs. unsupervised setting clustering fit on training engines) remains TBD.

### 5.2 Secondary Audit Axis: Degradation Stage
- **Status**: **Secondary Conditional Audit Axis (Post-Hoc Scientific Audit Only)**
- **Definition Rule**: Degradation-stage conditional coverage will be evaluated purely as an offline scientific audit.
- **Leakage Constraint**: True RUL ($y_i$) may be used *retrospectively* to group evaluation predictions into wear stages. True RUL must **NEVER** be used as an online feature for calibration, model prediction, maintenance policy, or state identification.
- **Implementation Status**: Exact degradation-stage boundaries remain TBD and will be pre-specified based on reproducible criteria (e.g., normalized lifetime fractions) prior to test set evaluation.

---

## 6. Metrics Suite (LOCKED v1)

Experiment A will evaluate predictions using the following pre-specified metrics:

- **Marginal Prediction Interval Coverage Probability (PICP)**: Aggregate coverage across all test samples.
- **Conditional PICP ($PICP_g$)**: Subgroup coverage across operating regimes and degradation stages.
- **Worst-Group Coverage (WGC)**: $\min_g PICP_g$ across defined groups.
- **Conditional Coverage Error ($CE_g$)**: $|PICP_g - (1-\alpha)|$.
- **Maximum Conditional Calibration Gap (MCG)**: $\max_g |PICP_g - (1-\alpha)|$.
- **Mean Prediction Interval Width (MPIW)**: Measures interval sharpness.
- **Interval Score (Winkler Score)**: Evaluates joint coverage accuracy and width penalty.
- **Engine-Level Confidence Intervals**: Uncertainty bounds computed at the engine unit level.

*Sharpness Interpretation Rule*: Coverage metrics must always be evaluated alongside interval sharpness ($MPIW$). A calibration approach must not be considered superior merely because it produces excessively wide, uninformative prediction intervals.

---

## 7. Core Experiment Pipeline

```text
C-MAPSS FD002 (Primary) & FD001 (Control)
                   │
                   ▼
     Base Models: GBR & LSTM
                   │
                   ▼
     Global Conformal Calibration
                   │
                   ▼
 Globally Calibrated RUL Prediction Intervals
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
Operating-Regime        Degradation-Stage
Conditional Audit       Post-Hoc Audit
(Primary Axis)          (Secondary Axis)
       │                       │
       └───────────┬───────────┘
                   ▼
 Marginal vs. Conditional Reliability Comparison
```

---

## 8. Primary Scientific Test & Falsification Logic

### Central Scientific Test Question
> *Can globally calibrated RUL prediction intervals satisfy nominal overall coverage while substantially under-covering specific operating regimes or degradation stages?*

### Falsification & Negative Result Criteria
Experiment A shall be considered to provide **weak or no support** for RQ1 if:
1. Global coverage matches nominal target ($PICP \approx 1-\alpha$).
2. Subgroup coverages ($PICP_g$) across all operating regimes and degradation stages remain consistently near nominal.
3. Worst-Group Coverage ($WGC$) remains operationally acceptable.
4. Observed subgroup coverage variations fall within expected sampling uncertainty under engine-level bootstrap testing.

---

## 9. Experimental Dependency & Next Steps

Experiment A must be fully executed, audited, and interpreted before Experiment B is finalized.

- **If Experiment A confirms conditional failure (Outcomes A/B)**: Experiment B will investigate whether condition-aware calibration can mitigate the subgroup coverage gaps identified in Experiment A.
- **If Experiment A falsifies conditional failure (Outcome C)**: Experiment B and downstream decision policies must be formally reconsidered and adapted rather than executed unchanged.
