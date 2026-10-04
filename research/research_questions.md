# Formal Research Questions and Hypotheses

> **Important Notice on Scientific Status**:
> Research Gap and RQ1–RQ4 have been formally formulated and locked for the research project.
> 
> **Governance Status Policy**: **Locked for the current research iteration, but subject to revision if later evidence or methodological constraints invalidate the formulation.**
> 
> "Locked" indicates pre-specification prior to experimental testing to prevent post-hoc hypothesis redefinition based on favorable results.
> 
> Detailed research formulation, metrics, target leakage constraints, statistical uncertainty framework, decision rules, and no-post-hoc-change governance are recorded in [`research/research_design/research_gap.md`](research_design/research_gap.md), [`research/hypotheses/hypothesis_framework.yaml`](hypotheses/hypothesis_framework.yaml), [`research/research_design/experiment_map.md`](research_design/experiment_map.md), and [`research/research_design/evaluation_criteria.md`](research_design/evaluation_criteria.md).

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
- **Evaluation Criteria & Decision Rules**:
  - **Primary Outcome**: Total simulated maintenance cost per engine
  - **Secondary / Supporting Outcomes**: Late/failure intervention rate; required prediction-interval coverage
  - **Outcome Hierarchy Meaning**: The primary outcome determines the main maintenance-utility conclusion. Favorable secondary metrics cannot compensate for failure on the primary outcome or violation of required coverage.
  - **Primary Comparators**: Global conformal calibration; standard condition-aware calibration
  - **Threshold Status**: Deferred until after maintenance simulator validation
  - **Statistical Framework**: 95% engine-level paired/cluster bootstrap confidence interval (engine is the independent statistical unit)
  - **Supported Rule**: Practically meaningful reduction in total maintenance cost per engine supported by 95% engine-level CI while maintaining required coverage reliability.
  - **Unsupported Rule**: No practically meaningful maintenance-cost improvement over strongest baseline, baseline performs better, or lower cost is achieved by violating coverage constraints.
  - **Inconclusive Rule**: Estimated improvement is favorable but 95% CI overlaps future practical threshold, or comparator evidence is mixed.
  - *(Full details in [`research/research_design/evaluation_criteria.md`](research_design/evaluation_criteria.md)).*

---

### Research Question 2 (RQ2)

- **Status**: **Locked**
- **Question**: *Can the proposed method improve reliability across operating regimes and degradation conditions without excessively widening prediction intervals?*
- **Null Hypothesis ($H_{0,2}$)**:
  > The proposed method does not improve worst-group or conditional coverage, or any improvement is primarily obtained through substantially wider intervals.
- **Alternative Hypothesis ($H_{1,2}$)**:
  > The proposed method improves worst-group or conditional coverage while maintaining practically useful interval sharpness.
- **Primary Experimental Evaluation**: **Experiment B** — Evaluate whether the proposed method improves conditional coverage and worst-group reliability without making prediction intervals excessively wide.
- **Evaluation Criteria & Decision Rules**:
  - **Primary Outcome**: Worst-group conditional coverage error
  - **Secondary / Supporting Outcomes**: Mean Prediction Interval Width (MPIW); interval score
  - **Outcome Hierarchy Meaning**: The primary outcome determines the main reliability conclusion. MPIW and interval score verify that reliability gains do not materially degrade interval sharpness/quality.
  - **Primary Comparators**: Global conformal calibration; standard condition-aware calibration
  - **Threshold Status**: Deferred until after maintenance simulator validation
  - **Statistical Framework**: 95% engine-level paired/cluster bootstrap confidence interval (engine is the independent statistical unit)
  - **Supported Rule**: Practically meaningful improvement in worst-group conditional coverage error supported by 95% engine-level CI without materially degrading interval sharpness.
  - **Unsupported Rule**: No practically meaningful worst-group reliability improvement, worst-group reliability degrades, or coverage gain requires materially wider/poorer-quality intervals.
  - **Inconclusive Rule**: Worst-group reliability appears to improve but 95% CI overlaps future threshold, or reliability-vs-sharpness trade-off is ambiguous.
  - *(Full details in [`research/research_design/evaluation_criteria.md`](research_design/evaluation_criteria.md)).*

---

### Research Question 3 (RQ3)

- **Status**: **Locked**
- **Question**: *Are the maintenance benefits of the proposed method attributable to decision-aware uncertainty calibration rather than simply more conservative prediction intervals or earlier maintenance?*
- **Null Hypothesis ($H_{0,3}$)**:
  > Any maintenance improvement can be matched by simpler conservative baselines such as widened intervals or safety margins.
- **Alternative Hypothesis ($H_{1,3}$)**:
  > The proposed method provides maintenance improvements beyond those achievable through matched-conservatism baselines, demonstrating useful decision information rather than simple over-conservatism.
- **Primary Experimental Evaluation**: **Experiment C** — Evaluate decision-value attribution by comparing the proposed method against matched-conservatism baselines, widened intervals, point-prediction safety margins, and earlier-intervention conservative policies.
- **Evaluation Criteria & Decision Rules**:
  - **Primary Outcome**: Maintenance cost/utility improvement over the strongest pre-specified matched-conservatism baseline
  - **Secondary / Supporting Outcomes**: Wasted RUL; premature intervention rate
  - **Outcome Hierarchy Meaning**: The primary outcome determines whether the proposed method provides decision value beyond simple conservatism. Supporting metrics provide interpretation but cannot substitute for failure on the primary outcome.
  - **Primary Comparators**: Widened/matched-width prediction intervals; tuned point-prediction safety margins; earlier-intervention conservative policies
  - **Threshold Status**: Deferred until after maintenance simulator validation
  - **Statistical Framework**: 95% engine-level paired/cluster bootstrap confidence interval (engine is the independent statistical unit)
  - **Supported Rule**: Practically meaningful improvement in maintenance utility over strongest pre-specified matched-conservatism baseline, supported by 95% engine-level CI.
  - **Unsupported Rule**: Matched conservative controls reproduce or outperform proposed method's benefit, demonstrating that decision-aware calibration is unnecessary.
  - **Inconclusive Rule**: Proposed method appears superior but 95% CI overlaps future threshold, or matched controls yield mixed evidence.
  - *(Full details in [`research/research_design/evaluation_criteria.md`](research_design/evaluation_criteria.md)).*

---

### Research Question 4 (RQ4)

- **Status**: **Locked**
- **Question**: *Does the proposed method retain its calibration and maintenance-decision benefits across operating conditions, base RUL predictors, datasets, and repeated experimental runs?*
- **Null Hypothesis ($H_{0,4}$)**:
  > The observed benefits are specific to particular datasets, operating conditions, model families, or random seeds.
- **Alternative Hypothesis ($H_{1,4}$)**:
  > The principal reliability and maintenance-utility improvements persist across multiple operating conditions, model families, datasets, and repeated experimental runs.
- **Primary Experimental Evaluation**: **Experiment D** — Evaluate whether the main calibration and maintenance decision benefits remain robust across operating conditions, base RUL model families, datasets, and repeated random seeds/runs.
- **Evaluation Criteria & Decision Rules**:
  - **Primary Outcome**: Cross-configuration consistency of the proposed method's effect
  - **Secondary / Supporting Outcomes**: Effect size; engine-level confidence intervals
  - **Outcome Hierarchy Meaning**: The primary outcome determines robustness/generalization. Support requires consistent overall benefit across configurations without systematic failure (does not require positive effect in literally every single configuration).
  - **Primary Comparators**: Proposed-vs-baseline effects across predefined datasets/operating conditions, model families, and random seeds
  - **Threshold Status**: Deferred until after maintenance simulator validation
  - **Statistical Framework**: Engine-level confidence intervals across configurations (engine is the independent statistical unit)
  - **Supported Rule**: Consistently favorable and practically meaningful effect across predefined robustness configurations without systematic reversal across datasets, model families, or seeds.
  - **Unsupported Rule**: Benefit disappears, systematically reverses, or is restricted to specific datasets, model families, or seeds.
  - **Inconclusive Rule**: Mixed results across robustness configurations or statistical uncertainty is too large to confirm robustness.
  - *(Full details in [`research/research_design/evaluation_criteria.md`](research_design/evaluation_criteria.md)).*

---

## Authoritative Registry & Reference

The authoritative source of truth for all hypotheses, planned comparisons, and experimental mappings is:
- [`research/hypotheses/hypothesis_framework.yaml`](hypotheses/hypothesis_framework.yaml)
- [`research/hypotheses/hypothesis_framework.tex`](hypotheses/hypothesis_framework.tex)
