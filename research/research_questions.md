# Formal Research Questions and Hypotheses

> **Important Notice on Scientific Status**:
> Research Gap and RQ1–RQ4 have been formally formulated and locked for the research project.
> 
> **Governance Status Policy**: **Locked for the current research iteration, but subject to revision if later evidence or methodological constraints invalidate the formulation.**
> 
> "Locked" indicates pre-specification prior to experimental testing to prevent post-hoc hypothesis redefinition based on favorable results.
> 
> Detailed research formulation, metrics, target leakage constraints, and falsification criteria are recorded in [`research/research_design/research_gap.md`](research_design/research_gap.md), [`research/hypotheses/hypothesis_framework.yaml`](hypotheses/hypothesis_framework.yaml), and [`research/research_design/experiment_map.md`](research_design/experiment_map.md).

---

## Final Research Problem Statement

> **Existing RUL research has separately studied conformal uncertainty calibration, condition/regime-aware calibration, and uncertainty-aware maintenance decision-making. What remains insufficiently established is a RUL-specific method that jointly adapts calibration to operating conditions and downstream sequential maintenance consequences while preserving reliable uncertainty coverage. Our study will therefore investigate whether decision-aware, condition-adaptive conformal calibration can improve maintenance utility without sacrificing subgroup reliability or merely becoming more conservative.**

---

## Formal Research Questions and Hypotheses

### Research Question 1 (RQ1)

- **Status**: **Locked**
- **Question**: *Can a decision-aware, condition-adaptive conformal RUL calibration method improve sequential maintenance utility while preserving reliable prediction-interval coverage?*
- **Null Hypothesis ($H_{0,1}$)**:
  > The proposed method does not significantly improve maintenance utility over standard global or condition-aware calibration while maintaining comparable coverage.
- **Alternative Hypothesis ($H_{1,1}$)**:
  > The proposed method improves maintenance utility over standard global and condition-aware calibration while maintaining the required coverage reliability.
- **Primary Experimental Evaluation**: **Experiment A** — Evaluate the proposed decision-aware, condition-adaptive conformal RUL calibration method against global conformal calibration and standard condition-aware calibration baselines.

---

### Research Question 2 (RQ2)

- **Status**: **Locked**
- **Question**: *Can the proposed method improve reliability across operating regimes and degradation conditions without excessively widening prediction intervals?*
- **Null Hypothesis ($H_{0,2}$)**:
  > The proposed method does not improve worst-group or conditional coverage, or any improvement is primarily obtained through substantially wider intervals.
- **Alternative Hypothesis ($H_{1,2}$)**:
  > The proposed method improves worst-group or conditional coverage while maintaining practically useful interval sharpness.
- **Primary Experimental Evaluation**: **Experiment B** — Evaluate whether the proposed method improves conditional coverage and worst-group reliability without making prediction intervals excessively wide.

---

### Research Question 3 (RQ3)

- **Status**: **Locked**
- **Question**: *Are the maintenance benefits of the proposed method attributable to decision-aware uncertainty calibration rather than simply more conservative prediction intervals or earlier maintenance?*
- **Null Hypothesis ($H_{0,3}$)**:
  > Any maintenance improvement can be matched by simpler conservative baselines such as widened intervals or safety margins.
- **Alternative Hypothesis ($H_{1,3}$)**:
  > The proposed method provides maintenance improvements beyond those achievable through matched-conservatism baselines, demonstrating useful decision information rather than simple over-conservatism.
- **Primary Experimental Evaluation**: **Experiment C** — Evaluate decision-value attribution by comparing the proposed method against matched-conservatism baselines, widened intervals, point-prediction safety margins, and earlier-intervention conservative policies.

---

### Research Question 4 (RQ4)

- **Status**: **Locked**
- **Question**: *Does the proposed method retain its calibration and maintenance-decision benefits across operating conditions, base RUL predictors, datasets, and repeated experimental runs?*
- **Null Hypothesis ($H_{0,4}$)**:
  > The observed benefits are specific to particular datasets, operating conditions, model families, or random seeds.
- **Alternative Hypothesis ($H_{1,4}$)**:
  > The principal reliability and maintenance-utility improvements persist across multiple operating conditions, model families, datasets, and repeated experimental runs.
- **Primary Experimental Evaluation**: **Experiment D** — Evaluate whether the main calibration and maintenance decision benefits remain robust across operating conditions, base RUL model families, datasets, and repeated random seeds/runs.

---

## Authoritative Registry & Reference

The authoritative source of truth for all hypotheses, planned comparisons, and experimental mappings is:
- [`research/hypotheses/hypothesis_framework.yaml`](hypotheses/hypothesis_framework.yaml)
- [`research/hypotheses/hypothesis_framework.tex`](hypotheses/hypothesis_framework.tex)
