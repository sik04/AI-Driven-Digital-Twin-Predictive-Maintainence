# Master Experiment Map (Version 1)

> **Document Status**: **Locked for Current Research Iteration**
> **Authors**: Mayank Singh, Shiksha Pandey, Ruchi Gupta
> **Date**: 2026-10-04
> **Governance Policy**: Locked for the current research iteration, but subject to revision if later evidence or methodological constraints justify a documented research-design revision.

---

## 1. Overview and Experimental Dependency Flow

The IntelliTwin experimental methodology is structured into four sequential, hypothesis-driven experiments (Experiments A through D). Each experiment directly maps to a pre-specified research question (RQ1 through RQ4) and its corresponding formal hypotheses defined in the hypothesis registry [`research/hypotheses/hypothesis_framework.yaml`](../hypotheses/hypothesis_framework.yaml).

### 1.1 Experimental Dependency Cascade

```text
Experiment A: Conditional Reliability Audit (RQ1)
  │
  ├─► Does conditional reliability failure exist?
  │     │
  │     ├── YES (Outcome A/B) ──► Proceed to Experiment B & C
  │     └── NO  (Outcome C)   ──► Reconsider central research direction
  ▼
Experiment B: Condition-Aware Calibration Evaluation (RQ2)
  │
  ├─► Can the problem be reduced without destroying interval usefulness?
  ▼
Experiment C: Maintenance Decision Impact (RQ3)
  │
  ├─► Does reducing the problem produce better downstream maintenance decisions?
  ▼
Experiment D: Robustness and Generalization (RQ4)
  │
  └─► Are those findings robust rather than dataset- or model-specific?
```

*Critical Methodological Safeguard*: If Experiment A does not reveal practically or statistically meaningful conditional reliability failure (Outcome C), Experiments B and C must be formally reconsidered and adapted rather than executed unchanged.

---

## 2. Detailed Experiment Specifications

### 2.1 Experiment A — Conditional Reliability Audit

- **Primary Research Question**: **RQ1** (*Conditional RUL Interval Reliability*)
- **Formal Hypotheses**: $H_{0,1}$ vs. $H_{1,1}$ (defined in [`hypothesis_framework.yaml`](../hypotheses/hypothesis_framework.yaml))
- **Primary Purpose**: Determine whether prediction intervals that achieve satisfactory marginal coverage can nevertheless exhibit severe conditional undercoverage across degradation stages or operating regimes.
- **Datasets (Locked v1)**: Primary: **C-MAPSS FD002** (multi-regime); Control: **C-MAPSS FD001** (single-condition).
- **Base Models (Locked v1)**: **Gradient Boosting Regressor (GBR)** and **LSTM** (representing tree-based and temporal deep learning families).
- **High-Level Calibration Strategy (Locked v1)**: **Global conformal calibration** (exact nonconformity score and conformal variant TBD).
- **Audit Axes**: Primary: **Operating Regime** (derived from setting variables); Secondary: **Degradation Stage** (post-hoc scientific audit using true RUL).
- **Primary Metrics**: Marginal PICP, Conditional PICP ($PICP_g$), Worst-Group Coverage ($WGC$), Conditional Coverage Error ($CE_g$), Maximum Calibration Gap ($MCG$), $MPIW$, Winkler Interval Score, Engine-Level Confidence Intervals.
- **Detailed Protocol Reference**: See [`experiment_a_design.md`](experiment_a_design.md) for full protocol specifications.

---

### 2.2 Experiment B — Condition-Aware Calibration Evaluation

- **Primary Research Question**: **RQ2** (*Condition-Aware Calibration Efficacy*)
- **Formal Hypotheses**: $H_{0,2}$ vs. $H_{1,2}$ (defined in [`hypothesis_framework.yaml`](../hypotheses/hypothesis_framework.yaml))
- **Primary Purpose**: Determine whether condition-aware calibration methods can reduce or eliminate conditional reliability failures identified in Experiment A without making prediction intervals excessively wide.
- **Conceptual Comparison**:
  $$\text{Global Calibration (Baseline)} \quad \text{vs.} \quad \text{Condition-Aware Calibration (Proposed Candidate)}$$
- **Candidate Outputs & Metrics**:
  - Worst-Group Coverage ($WGC$)
  - Conditional Coverage Error ($CE_g$)
  - Maximum Conditional Calibration Gap ($MCG$)
  - Overall PICP ($PICP$)
  - Mean Prediction Interval Width ($MPIW$)
  - Winkler Interval Score
- **Coverage–Sharpness Trade-off Constraint**: A method that achieves nominal subgroup coverage solely by generating excessively wide intervals does not constitute desirable calibration performance (pre-specified thresholds in [`hypothesis_framework.yaml`](../hypotheses/hypothesis_framework.yaml)).
- **Non-Goal Declarations**: Do NOT define the specific condition-aware calibration algorithm yet.

---

### 2.3 Experiment C — Maintenance Decision Impact

- **Primary Research Question**: **RQ3** (*Maintenance Decision Utility*)
- **Formal Hypotheses**: $H_{0,3}$ vs. $H_{1,3}$ (defined in [`hypothesis_framework.yaml`](../hypotheses/hypothesis_framework.yaml))
- **Primary Purpose**: Determine whether improvements in conditional RUL calibration translate into better downstream maintenance decisions under simulated operational conditions.
- **Conceptual Policy Comparison**:
  1. **Point-Estimate Maintenance Policy**: Traditional thresholding on predicted point RUL ($\hat{y}_i \le \tau$).
  2. **Globally Calibrated Uncertainty-Aware Policy**: Maintenance scheduling based on lower bound $L_i$ from global calibration.
  3. **Conditionally Calibrated Uncertainty-Aware Policy**: Maintenance scheduling based on lower bound $L_i$ from condition-aware calibration.
- **Candidate Outputs & Metrics**:
  - Late interventions / catastrophic failure events (missed safe-intervention opportunities)
  - Premature interventions / wasted Remaining Useful Life
  - Intervention lead time distribution
  - Preventive maintenance frequency
  - Total simulated maintenance cost ($C_{\text{total}} = C_{\text{failure}} + C_{\text{preventive}} + C_{\text{wasted}}$)
  - Decision utility / risk-adjusted cost
- **Non-Goal Declarations**: Do NOT define exact cost ratios, decision threshold equations, or simulator code yet.

---

### 2.4 Experiment D — Robustness and Generalization

- **Primary Research Question**: **RQ4** (*Robustness and Generalization*)
- **Formal Hypotheses**: $H_{0,4}$ vs. $H_{1,4}$ (defined in [`hypothesis_framework.yaml`](../hypotheses/hypothesis_framework.yaml))
- **Primary Purpose**: Determine whether the principal conditional calibration failures and decision consequences identified in Experiments A–C remain consistent across diverse experimental settings.
- **Potential Robustness Dimensions**:
  - Dataset variations (e.g., C-MAPSS FD001 vs. FD002 vs. FD003 vs. FD004)
  - Operating-condition complexity (single-condition vs. multi-condition operational regimes)
  - Fault-mode complexity (single fault mode vs. dual failure modes)
  - Base RUL predictors (linear/tree baselines, recurrent temporal architectures, transformers)
  - Multiple random seeds and initialization sets
- **Statistical Evaluation Framework (Planned)**:
  - Engine-level bootstrap confidence intervals
  - Effect size estimation
  - Appropriate non-parametric statistical tests (e.g., Wilcoxon signed-rank tests)
- **Non-Goal Declarations**: Do NOT finalize exact datasets, models, or specific statistical test packages yet.

---

## 3. Governance and Non-Redefinition Rule

All four experiments are pre-specified before conducting model development or dataset processing. Results will be evaluated against pre-specified metrics and falsification criteria in [`hypothesis_framework.yaml`](../hypotheses/hypothesis_framework.yaml) to ensure that hypotheses are not retroactively redefined post-experimentation.
