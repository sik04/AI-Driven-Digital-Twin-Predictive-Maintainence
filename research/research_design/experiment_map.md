# High-Level Experiment Map

This document establishes the high-level mapping between the formal research questions (RQ1–RQ4) and planned experimental evaluation suites (Experiment A–D).

---

## 1. High-Level Experiment Suite Mapping

### Experiment A → RQ1: Proposed Method Evaluation

- **Associated RQ**: **RQ1** (*Can a decision-aware, condition-adaptive conformal RUL calibration method improve sequential maintenance utility while preserving reliable prediction-interval coverage?*)
- **Associated Hypotheses**: $H_{0,1}$ / $H_{1,1}$
- **Purpose**: Evaluate the proposed decision-aware, condition-adaptive conformal RUL calibration method to determine whether it improves sequential maintenance utility while preserving reliable prediction-interval coverage.
- **High-Level Comparison**:
  - Proposed method (decision-aware, condition-adaptive conformal calibration)
  - Global conformal calibration
  - Standard condition-aware calibration
- **Primary Type of Evidence Expected**: Sequential maintenance utility scores, total maintenance costs, and marginal coverage probability ($PICP$).
- **Decisions Deferred**: Exact algorithmic loss functions, nonconformity score definitions, optimization objectives, and operational cost ratios ($C_{\text{failure}} / C_{\text{preventive}}$).

---

### Experiment B → RQ2: Conditional Reliability & Sharpness Evaluation

- **Associated RQ**: **RQ2** (*Can the proposed method improve reliability across operating regimes and degradation conditions without excessively widening prediction intervals?*)
- **Associated Hypotheses**: $H_{0,2}$ / $H_{1,2}$
- **Purpose**: Evaluate whether the proposed method improves conditional coverage and worst-group reliability across operating regimes and wear conditions without making prediction intervals excessively wide.
- **High-Level Comparison**:
  - Proposed method vs. relevant global and condition-aware calibration baselines.
- **Primary Type of Evidence Expected**: Worst-Group Coverage ($WGC$), Conditional Coverage Error ($CE_g$), Maximum Conditional Gap ($MCG$), Mean Prediction Interval Width ($MPIW$), and Winkler Interval Score.
- **Decisions Deferred**: Exact subgroup partitioning boundaries, clustering cutoffs, and numerical sharpness trade-off parameters.

---

### Experiment C → RQ3: Decision-Value Attribution vs. Matched-Conservatism Baselines

- **Associated RQ**: **RQ3** (*Are the maintenance benefits of the proposed method attributable to decision-aware uncertainty calibration rather than simply more conservative prediction intervals or earlier maintenance?*)
- **Associated Hypotheses**: $H_{0,3}$ / $H_{1,3}$
- **Purpose**: Disambiguate true decision-aware calibration utility from trivial interval expansion or naive early intervention by comparing against matched-conservatism baselines.
- **High-Level Comparison**:
  - Proposed method vs. simple conservative controls:
    - Matched-width / widened prediction intervals
    - Point-prediction safety margins
    - Earlier-intervention conservative policies
- **Primary Type of Evidence Expected**: Comparative utility curves, lead-time distributions, wasted RUL statistics, and failure rate reductions relative to matched-conservatism baselines.
- **Decisions Deferred**: Exact baseline implementation details, safety margin tuning steps, and policy parameterizations.

---

### Experiment D → RQ4: Robustness & Generalization

- **Associated RQ**: **RQ4** (*Does the proposed method retain its calibration and maintenance-decision benefits across operating conditions, base RUL predictors, datasets, and repeated experimental runs?*)
- **Associated Hypotheses**: $H_{0,4}$ / $H_{1,4}$
- **Purpose**: Evaluate whether the principal reliability and maintenance-utility benefits persist across diverse operating conditions, model families, datasets, and repeated stochastic runs.
- **High-Level Comparison**:
  - Proposed method performance consistency across multiple configurations vs. baseline models across datasets and random seeds.
- **Primary Type of Evidence Expected**: Multi-dataset reliability scores, cross-architecture maintenance utility distributions, and statistical hypothesis test results across repeated runs.
- **Decisions Deferred**: Exact benchmark datasets, base model architectures, random seed counts, and statistical testing packages.

---

## 2. Experimental Boundaries and Deferred Parameters

The exact specification of the following parameters is explicitly deferred to Phase 3–4 protocol definition and Phase 5–7 experimental design:
- Exact calibration algorithms and loss equations
- Exact numerical decision thresholds and cost ratios
- Exact subgroup partitioning cutoffs
- Exact statistical test procedures and seed counts

These parameters will be pre-specified in Phase 3–4 prior to confirmatory model training and testing.
