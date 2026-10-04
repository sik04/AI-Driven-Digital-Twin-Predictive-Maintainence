# Research Gap and Research Problem Formulation

> **Document Status**: **Locked Research Problem**  
> **Authors**: Mayank Singh, Shiksha Pandey, Ruchi Gupta  
> **Date**: 2026-10-04  
> **Governance Policy**: Pre-specification prior to experimental testing prevents post-hoc hypothesis redefinition.  

---

## 1. Context and Research Problem

### 1.1 Context and Scope Boundaries
In industrial prognostic health management (PHM) and digital twin frameworks for turbofan engines:
- **Deterministic RUL prediction** using deep neural networks, recurrent architectures, and transformers is well-established in current literature.
- **Calibrated RUL prediction intervals** and distribution-free uncertainty estimation techniques (e.g., split conformal prediction, quantile regression) are established on benchmark datasets such as NASA C-MAPSS.
- **Uncertainty-aware maintenance decision support** linking interval bounds to maintenance scheduling heuristics or risk bounds has been previously explored in isolated settings.

### 1.2 Final Research Problem Statement

> **Existing RUL research has separately studied conformal uncertainty calibration, condition/regime-aware calibration, and uncertainty-aware maintenance decision-making. What remains insufficiently established is a RUL-specific method that jointly adapts calibration to operating conditions and downstream sequential maintenance consequences while preserving reliable uncertainty coverage. Our study will therefore investigate whether decision-aware, condition-adaptive conformal calibration can improve maintenance utility without sacrificing subgroup reliability or merely becoming more conservative.**

---

## 2. Research Questions Overview

The research gap is investigated through four locked research questions:

1. **RQ1**: *Can a decision-aware, condition-adaptive conformal RUL calibration method improve sequential maintenance utility while preserving reliable prediction-interval coverage?*
2. **RQ2**: *Can the proposed method improve reliability across operating regimes and degradation conditions without excessively widening prediction intervals?*
3. **RQ3**: *Are the maintenance benefits of the proposed method attributable to decision-aware uncertainty calibration rather than simply more conservative prediction intervals or earlier maintenance?*
4. **RQ4**: *Does the proposed method retain its calibration and maintenance-decision benefits across operating conditions, base RUL predictors, datasets, and repeated experimental runs?*

*(The complete formal hypotheses, planned comparisons, and authoritative registry are specified in [`research/hypotheses/hypothesis_framework.yaml`](../hypotheses/hypothesis_framework.yaml) and [`research/research_questions.md`](../research_questions.md)).*

---

## 3. Supporting Scientific Motivations

While the central novelty claim is focused on method-level integration of decision-aware, condition-adaptive conformal calibration with sequential maintenance consequences, the following supporting scientific motivations remain relevant:
- **Conditional Miscalibration**: Nominally calibrated prediction intervals can still conceal localized reliability failures across specific degradation stages or operating regimes.
- **Marginal vs. Conditional Coverage**: Marginal coverage alone can obscure worst-group failures, providing rationale for subgroup reliability evaluations.
- **Comparative Baseline Controls**: Evaluating condition-aware calibration against global calibration and simple conservative policies establishes whether observed decision gains stem from decision-aware uncertainty or simple over-conservatism.

---

## 4. Candidate Metrics Suite

### 4.1 Calibration & Reliability Metrics
- **Marginal Prediction Interval Coverage Probability (PICP)**:
  $$PICP = \frac{1}{N} \sum_{i=1}^{N} \mathbb{1}(y_i \in [L_i, U_i])$$
- **Conditional PICP ($PICP_g$)**:
  $$PICP_g = \frac{1}{N_g} \sum_{i \in g} \mathbb{1}(y_i \in [L_i, U_i])$$
- **Conditional Coverage Error ($CE_g$)**:
  $$CE_g = \left| PICP_g - (1-\alpha) \right|$$
- **Worst-Group Coverage (WGC)**:
  $$WGC = \min_{g \in \mathcal{G}} PICP_g$$
- **Maximum Conditional Calibration Gap (MCG)**:
  $$MCG = \max_{g \in \mathcal{G}} \left| PICP_g - (1-\alpha) \right|$$

### 4.2 Sharpness & Efficiency Metrics
- **Mean Prediction Interval Width (MPIW)**:
  $$MPIW = \frac{1}{N} \sum_{i=1}^{N} (U_i - L_i)$$
- **Interval Score (Winkler Score)**: Evaluates trade-off between coverage penalty and interval width.

### 4.3 Maintenance Decision Metrics
- Sequential maintenance utility
- Total simulated maintenance cost ($C_{\text{total}} = C_{\text{failure}} + C_{\text{preventive}} + C_{\text{wasted}}$)
- Late interventions / unscheduled failure count
- Premature maintenance interventions & wasted Remaining Useful Life ($RUL_{\text{wasted}}$)
- Failure-related cost vs. premature-replacement cost ratio

---

## 5. Methodological & Statistical Constraints

### 5.1 Target Leakage Constraint
- **Post-hoc Evaluation**: True RUL ($y_i$) may be used *retrospectively* during offline scientific auditing to assign predictions to degradation stages.
- **Deployable Policy Constraint**: True RUL must **NEVER** be used as an input feature for any online calibration method, adaptive thresholding scheme, or deployable maintenance decision policy.
- Online condition-aware calibration methods must rely strictly on inference-time-observable data (sensor settings, sequence history, predicted RUL $\hat{y}_i$, or inferred regime state).

### 5.2 Unit of Independence Constraint
- Sequential time windows extracted from the same physical engine unit exhibit strong autocorrelation and cannot be assumed independent.
- Statistical inference, confidence intervals, bootstrap resampling, and hypothesis testing must be structured at the **engine unit level** rather than treating individual temporal windows as independent samples.

---

## 6. Guiding Research Principle

> **The objective is to test whether decision-aware, condition-adaptive conformal calibration can improve sequential maintenance utility without sacrificing subgroup reliability or merely becoming more conservative.**
