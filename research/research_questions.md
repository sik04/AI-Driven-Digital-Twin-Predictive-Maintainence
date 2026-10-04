# Formal Research Questions Overview (Version 1)

> **Important Notice on Scientific Status**:
> Following the Phase 1 Literature Review, Research Gap v1 and Research Questions RQ1–RQ4 have been formally formulated and locked for the current research iteration.
> 
> **Governance Status Policy**: **Locked for the current research iteration, but subject to revision if later evidence or methodological constraints justify a documented research-design revision.**
> 
> "Locked" indicates pre-specification prior to experimental testing to prevent post-hoc hypothesis redefinition based on favorable empirical results. It does NOT mean research questions can never be revised if foundational assumptions are invalidated.

---

## Approved Research Gap Overview

> **Although recent turbofan prognostic studies provide well-calibrated and increasingly risk-aware RUL prediction intervals, their evaluation remains dominated by aggregate or marginal reliability metrics. Related prognostic research demonstrates that such aggregate calibration can conceal severe conditional undercoverage under changing degradation states or operating regimes. The operational significance of this conditional miscalibration—particularly its effect on late maintenance, premature intervention, wasted useful life, failure risk, and maintenance cost—remains insufficiently characterized for turbofan RUL decision support.**

*Detailed literature-grounded rationale, scope boundaries, non-claims, and statistical cautions are documented in [`research/research_design/research_gap.md`](research_design/research_gap.md).*

---

## Authoritative Hypothesis Registry Notice

The formal mathematical definitions of null ($H_0$) and alternative ($H_1$) hypotheses, pre-specified practical effect-size thresholds, primary evaluation metrics, decision rules, and falsification criteria for all four research questions are maintained in:

- **Authoritative Canonical Registry (Machine-Readable)**: [`research/hypotheses/hypothesis_framework.yaml`](hypotheses/hypothesis_framework.yaml)
- **Academic LaTeX Rendering (Human-Readable)**: [`research/hypotheses/hypothesis_framework.tex`](hypotheses/hypothesis_framework.tex)

*To avoid synchronization errors and post-hoc hypothesis redefinition, `hypothesis_framework.yaml` serves as the single source of truth for all formal hypothesis testing, while `hypothesis_framework.tex` provides a publication-ready academic rendering.*

---

## Summary of Locked Research Questions (v1)

### Research Question 1 (RQ1: Conditional RUL Interval Reliability)
- **Question**: *To what extent can nominally calibrated RUL prediction intervals conceal conditional reliability failures across degradation stages and operating regimes in turbofan prognostics?*
- **Primary Experiment**: **Experiment A** ([`research/research_design/experiment_a_design.md`](research_design/experiment_a_design.md))
- **Authoritative Framework**: See `RQ1` in [`hypothesis_framework.yaml`](hypotheses/hypothesis_framework.yaml).

---

### Research Question 2 (RQ2: Condition-Aware Calibration Efficacy)
- **Question**: *Can condition-aware calibration methods improve worst-group RUL reliability across degradation stages and operating regimes without making prediction intervals excessively wide?*
- **Primary Experiment**: **Experiment B** (described in [`research/research_design/experiment_map.md`](research_design/experiment_map.md))
- **Authoritative Framework**: See `RQ2` in [`hypothesis_framework.yaml`](hypotheses/hypothesis_framework.yaml).

---

### Research Question 3 (RQ3: Maintenance Decision Utility)
- **Question**: *Do improvements in conditional RUL calibration lead to better maintenance decisions than point-estimate and globally calibrated maintenance policies?*
- **Primary Experiment**: **Experiment C** (described in [`research/research_design/experiment_map.md`](research_design/experiment_map.md))
- **Authoritative Framework**: See `RQ3` in [`hypothesis_framework.yaml`](hypotheses/hypothesis_framework.yaml).

---

### Research Question 4 (RQ4: Robustness and Generalization)
- **Question**: *Are the observed conditional calibration failures and their maintenance-decision consequences consistent across different operating conditions, fault modes, base RUL models, and random seeds?*
- **Primary Experiment**: **Experiment D** (described in [`research/research_design/experiment_map.md`](research_design/experiment_map.md))
- **Authoritative Framework**: See `RQ4` in [`hypothesis_framework.yaml`](hypotheses/hypothesis_framework.yaml).

---

## Revision Protocol

1. All research questions (RQ1–RQ4) and hypotheses ($H_{0,1}$–$H_{0,4}$ / $H_{1,1}$–$H_{1,4}$) are pre-specified and locked prior to model development and experiments.
2. Every hypothesis maps strictly to pre-specified statistical metrics, unit-of-independence constraints, and falsification criteria in [`hypothesis_framework.yaml`](hypotheses/hypothesis_framework.yaml).
3. If empirical evaluation in Experiment A does not reveal meaningful conditional reliability failure, Experiments B and C will be formally reconsidered rather than executed unchanged.
4. All architectural and methodological decisions are logged in [`research/decision_log.md`](decision_log.md).
