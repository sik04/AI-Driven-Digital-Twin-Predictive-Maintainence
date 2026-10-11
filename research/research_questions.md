# Formal Research Questions and Hypotheses

> **Important Notice on Scientific Status**:
> Research Gap and RQ1–RQ4 have been formally formulated and locked for the research project.
> 
> **Governance Status Policy**: **Frozen for confirmatory evaluation under ADR-018.**
> 
> Detailed research formulation, metrics, target leakage constraints, statistical uncertainty framework, frozen numerical thresholds, decision rules, and no-post-hoc-change governance are recorded in [`research/research_design/research_gap.md`](research_design/research_gap.md), [`research/hypotheses/hypothesis_framework.yaml`](hypotheses/hypothesis_framework.yaml), [`research/research_design/statistical_inference_protocol.md`](research_design/statistical_inference_protocol.md), [`research/research_design/experiment_map.md`](research_design/experiment_map.md), and [`research/research_design/evaluation_criteria.md`](research_design/evaluation_criteria.md).

---

## Final Research Problem Statement

> **Existing RUL research has separately studied conformal uncertainty calibration, condition/regime-aware calibration, and uncertainty-aware maintenance decision-making. What remains insufficiently established is a RUL-specific method that jointly adapts calibration to operating conditions and downstream sequential maintenance consequences while preserving reliable uncertainty coverage. Our study will therefore investigate whether decision-aware, condition-adaptive conformal calibration can improve maintenance utility without sacrificing subgroup reliability or merely becoming more conservative.**

---

## Formal Research Questions and Hypotheses

### Research Question 1 (RQ1)

- **Status**: **Frozen (ADR-018)**
- **Question**: *Can a decision-aware, condition-adaptive conformal RUL calibration method improve sequential maintenance utility while preserving reliable prediction-interval coverage?*
- **Null Hypothesis ($H_{0,1}$)**:
  > The proposed method does not improve sequential maintenance utility by at least 0.20 SCU per engine over both global and standard condition-aware calibration, or fails to maintain required coverage reliability.
- **Alternative Hypothesis ($H_{1,1}$)**:
  > The proposed method improves maintenance utility by at least 0.20 SCU per engine over both global and standard condition-aware calibration while maintaining the required coverage reliability.
- **Primary Experimental Evaluation**: **Experiment A** — Evaluate the proposed decision-aware, condition-adaptive conformal RUL calibration method against global conformal calibration and standard condition-aware calibration baselines on FD002 under the `primary_reference` scenario ($C_{\text{PM}}=1.0, C_{\text{FAIL}}=5.0, C_{\text{WASTE}}=0.20$) at 90% nominal coverage.
- **Evaluation Criteria & Decision Rules**:
  - **Primary Outcome**: Total simulated maintenance cost per engine contrast ($\Delta_{\text{cost}} = \overline{\text{Cost}}_B - \overline{\text{Cost}}_P$)
  - **Secondary / Supporting Outcomes**: Marginal absolute coverage error; worst-group operating regime error; worst-group lifecycle stage error; fleet failure rate
  - **Outcome Hierarchy Meaning**: The primary outcome determines the main maintenance-utility conclusion. Favorable secondary metrics cannot compensate for failure on the primary outcome or violation of required coverage.
  - **Primary Comparators**: Global conformal calibration; standard condition-aware calibration (both GBR and LSTM base models required)
  - **Frozen Practical-Effect Threshold**: $\Delta_{\text{cost}} > 0.20$ SCU per engine (equal to the cost of one discarded cycle); absolute coverage error ceiling $E < 0.05$
  - **Statistical Framework**: 98.75% engine-level cluster-bootstrap percentile decision interval (10,000 resamples, Bonferroni family-wise control $\alpha = 0.05 / 4 = 0.0125$)
  - **Supported Rule**: For both GBR and LSTM, lower CI of $\Delta_{\text{cost}} > 0.20$ SCU against both baselines, upper CI of marginal, worst-regime, and worst-stage coverage error $< 0.05$, and observed fleet failure rate increase $\le 0.0$ against both baselines.
  - **Unsupported Rule**: For either model, upper CI of $\Delta_{\text{cost}} < 0.20$ SCU against either baseline, lower CI of any coverage error $> 0.05$, or observed fleet failure rate increases over either baseline.
  - **Inconclusive Rule**: No condition fails, but at least one decision interval covers its boundary, or inference is degenerate.
  - *(Full details in [`research/research_design/statistical_inference_protocol.md`](research_design/statistical_inference_protocol.md)).*

---

### Research Question 2 (RQ2)

- **Status**: **Frozen (ADR-018)**
- **Question**: *Can the proposed method improve reliability across operating regimes and degradation conditions without excessively widening prediction intervals?*
- **Null Hypothesis ($H_{0,2}$)**:
  > The proposed method does not improve worst-group conditional coverage error by at least 0.01 over both baselines, or causes interval width or interval score to deteriorate by 1.0 cycle or more.
- **Alternative Hypothesis ($H_{1,2}$)**:
  > The proposed method improves worst-group conditional coverage error by at least 0.01 over both baselines while restricting interval width and score deterioration to under 1.0 cycle.
- **Primary Experimental Evaluation**: **Experiment B** — Evaluate whether the proposed method improves conditional coverage and worst-group reliability without making prediction intervals excessively wide on FD002 at 90% nominal coverage.
- **Evaluation Criteria & Decision Rules**:
  - **Primary Outcome**: Worst-group conditional coverage error contrast ($\Delta_{\text{error}} = \text{WorstErr}_B - \text{WorstErr}_P$)
  - **Secondary / Supporting Outcomes**: Mean Prediction Interval Width contrast ($D_{\text{width}} = \overline{\text{MPIW}}_P - \overline{\text{MPIW}}_B$); Winkler interval score contrast ($D_{\text{score}} = \overline{\text{IS}}_P - \overline{\text{IS}}_B$); worst-group absolute coverage error
  - **Outcome Hierarchy Meaning**: The primary outcome determines the main reliability conclusion. MPIW and interval score verify that reliability gains do not materially degrade interval sharpness/quality.
  - **Primary Comparators**: Global conformal calibration; standard condition-aware calibration (both GBR and LSTM base models required; both regimes and stages required)
  - **Frozen Practical-Effect Threshold**: $\Delta_{\text{error}} > 0.01$ (1 percentage point); absolute worst-group error ceiling $E < 0.05$; $D_{\text{width}} < 1.0$ cycle; $D_{\text{score}} < 1.0$ cycle
  - **Statistical Framework**: 98.75% engine-level cluster-bootstrap percentile decision interval with conservative missing-group bound propagation
  - **Supported Rule**: For both models and both subgroup families, lower CI of $\Delta_{\text{error}} > 0.01$ against both baselines, upper CI of worst-group error $< 0.05$, upper CI of $D_{\text{width}} < 1.0$ cycle against both baselines, and upper CI of $D_{\text{score}} < 1.0$ cycle against both baselines.
  - **Unsupported Rule**: Upper CI of $\Delta_{\text{error}} < 0.01$, lower CI of worst-group error $> 0.05$, lower CI of $D_{\text{width}} > 1.0$ cycle, or lower CI of $D_{\text{score}} > 1.0$ cycle against either baseline.
  - **Inconclusive Rule**: No condition fails, but at least one decision interval covers its boundary, or inference is degenerate.
  - *(Full details in [`research/research_design/statistical_inference_protocol.md`](research_design/statistical_inference_protocol.md)).*

---

### Research Question 3 (RQ3)

- **Status**: **Frozen (ADR-018)**
- **Question**: *Are the maintenance benefits of the proposed method attributable to decision-aware uncertainty calibration rather than simply more conservative prediction intervals or earlier maintenance?*
- **Null Hypothesis ($H_{0,3}$)**:
  > The proposed method does not improve maintenance utility by at least 0.20 SCU per engine over every prespecified matched-conservatism control family, or violates coverage constraints.
- **Alternative Hypothesis ($H_{1,3}$)**:
  > The proposed method provides maintenance improvements beyond those achievable through matched-conservatism baselines, demonstrating useful decision information rather than simple over-conservatism.
- **Primary Experimental Evaluation**: **Experiment C** — Evaluate decision-value attribution by comparing the proposed method against three prespecified matched-conservatism control families: widened intervals, point-prediction safety margins, and earlier-intervention conservative policies.
- **Evaluation Criteria & Decision Rules**:
  - **Primary Outcome**: Maintenance cost improvement over matched-conservatism controls ($\Delta_{\text{cost}} = \overline{\text{Cost}}_{\text{control}} - \overline{\text{Cost}}_P$)
  - **Secondary / Supporting Outcomes**: Wasted RUL; cost-inefficient early PM rate; coverage error
  - **Outcome Hierarchy Meaning**: The primary outcome determines whether the proposed method provides decision value beyond simple conservatism. Supporting metrics provide interpretation but cannot substitute for failure on the primary outcome.
  - **Primary Comparators**: All three prespecified matched-conservatism control families
  - **Frozen Practical-Effect Threshold**: $\Delta_{\text{cost}} > 0.20$ SCU per engine against **EVERY** control family; coverage ceiling $E < 0.05$
  - **Statistical Framework**: 98.75% engine-level cluster-bootstrap percentile decision interval
  - **Supported Rule**: For both models, lower CI of $\Delta_{\text{cost}} > 0.20$ SCU against every prespecified control family, upper CI of coverage errors $< 0.05$, and observed fleet failure rate increase $\le 0.0$.
  - **Unsupported Rule**: Upper CI of $\Delta_{\text{cost}} < 0.20$ SCU against any control family, lower CI of coverage error $> 0.05$, or failure rate increases over any control family.
  - **Inconclusive Rule**: No condition fails, but at least one decision interval covers its boundary, or inference is degenerate.
  - *(Note: Control tuning and matching will be specified in the later method-design step using development data only; confirmatory RQ3 evaluation cannot run until that protocol is frozen).*

---

### Research Question 4 (RQ4)

- **Status**: **Frozen (ADR-018)**
- **Question**: *Does the proposed method retain its calibration and maintenance-decision benefits across operating conditions, base RUL predictors, datasets, and repeated experimental runs?*
- **Null Hypothesis ($H_{0,4}$)**:
  > The proposed method fails to achieve aggregate improvements ($\Delta_{\text{cost}} > 0.20$ SCU, $\Delta_{\text{error}} > 0.01$) across the evaluation matrix, or exhibits material harm ($\Delta_{\text{cost}} < -0.20$ SCU or $\Delta_{\text{error}} < -0.01$) in any individual configuration cell.
- **Alternative Hypothesis ($H_{1,4}$)**:
  > The proposed method achieves aggregate improvements across the evaluation matrix without material harm in any individual configuration cell.
- **Primary Experimental Evaluation**: **Experiment D** — Evaluate consistency across 6 mandatory cells: FD001 × GBR, FD001 × LSTM, FD002 × GBR, FD002 × LSTM, FD004 × GBR, FD004 × LSTM, weighted equally ($1/6$ each).
- **Evaluation Criteria & Decision Rules**:
  - **Primary Outcome**: Weighted aggregate contrasts and cell-level non-harm bounds
  - **Secondary / Supporting Outcomes**: Individual cell effect sizes; cell-level decision intervals
  - **Primary Comparators**: Global conformal calibration and standard condition-aware calibration across all 6 cells
  - **Frozen Practical-Effect Threshold**:
    - Weighted aggregate: $\Delta_{\text{cost}} > 0.20$ SCU, $\Delta_{\text{error}} > 0.01$ (regimes and stages)
    - Cell-level non-harm: $\Delta_{\text{cost}} > -0.20$ SCU, $\Delta_{\text{error}} > -0.01$ in every cell
    - Cell-level safeguards: coverage ceiling $E < 0.05$, $D_{\text{width}} < 1.0$ cycle, $D_{\text{score}} < 1.0$ cycle, failure increase $\le 0.0$
  - **Statistical Framework**: 98.75% engine-level cluster-bootstrap percentile decision intervals
  - **Supported Rule**: Lower CI of weighted aggregate $\Delta_{\text{cost}} > 0.20$ SCU, lower CI of weighted aggregate $\Delta_{\text{error}} > 0.01$ for regimes and stages, lower CI of $\Delta_{\text{cost}} > -0.20$ SCU in every cell, lower CI of $\Delta_{\text{error}} > -0.01$ in every cell, and all cell safeguards hold across all 6 cells.
  - **Unsupported Rule**: Upper CI of aggregate $\Delta_{\text{cost}} < 0.20$ SCU or aggregate $\Delta_{\text{error}} < 0.01$, or upper CI of cell $\Delta_{\text{cost}} < -0.20$ SCU or $\Delta_{\text{error}} < -0.01$ in any cell, or any cell safeguard fails.
  - **Inconclusive Rule**: No condition fails, but at least one decision interval covers its boundary, or inference is degenerate.
  - *(Full details in [`research/research_design/statistical_inference_protocol.md`](research_design/statistical_inference_protocol.md)).*

---

## Authoritative Registry & Reference

The authoritative source of truth for all hypotheses, planned comparisons, and experimental mappings is:
- [`research/hypotheses/hypothesis_framework.yaml`](hypotheses/hypothesis_framework.yaml)
- [`research/research_design/statistical_inference_protocol.md`](research_design/statistical_inference_protocol.md)
- [`research/hypotheses/hypothesis_framework.tex`](hypotheses/hypothesis_framework.tex)
