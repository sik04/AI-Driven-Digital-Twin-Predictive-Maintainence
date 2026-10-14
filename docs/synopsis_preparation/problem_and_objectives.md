# Formal Research Problem Statement and Objectives

**Document Version**: `1.0`  
**Governance Reference**: Locked under ADR-006, ADR-007, and ADR-018  
**Authoritative Protocol**: `research/research_questions.md` & `research/hypotheses/hypothesis_framework.yaml`  
**Status**: Frozen for Confirmatory Evaluation — Objectives framed as hypotheses to be tested, not pre-claimed successes.

---

## 1. Context and Problem Statement

The prognostics and health management (PHM) community has made extensive progress in developing deep learning architectures for Remaining Useful Life (RUL) estimation. In parallel, the statistical learning community has advanced distribution-free uncertainty quantification through conformal prediction. Concurrently, operational research has modeled risk-averse predictive maintenance optimization.

However, these three disciplines have evolved largely in isolation:
1. **Conformal RUL prediction** studies (e.g., Javanmardi & Hüllermeier, 2023) have established that inductive split conformal prediction can guarantee marginal coverage on aero-engine benchmarks, but they evaluate statistical metrics (coverage and interval width) without measuring whether calibrated intervals improve downstream replacement scheduling.
2. **Conditional reliability diagnostics** (e.g., Yang et al., 2026; BenAbdennour, 2026) have audited localized coverage under operating-regime shifts and lifecycle wear stages, demonstrating that global marginal coverage routinely masks acute localized undercoverage. However, they do not integrate condition-adaptive calibration with prescriptive maintenance policies.
3. **Uncertainty-aware maintenance optimization** literature (e.g., Chen et al., 2022; Zhu et al., 2025; Walia & Kumar, 2026) models replacement policies under predicted uncertainty, but typically relies on heuristic or uncalibrated variance estimates (such as Monte Carlo dropout or uncalibrated quantile regression) that lack distribution-free finite-sample coverage guarantees.

This fragmentation leaves a critical scientific gap unaddressed. In sequential maintenance systems where replacements are triggered by prediction lower bounds, naive attempts to improve reliability through broader intervals can induce severe operational inefficiency, replacing serviceable assets prematurely. Conversely, tightening intervals without valid calibration risks catastrophic uncontained failures.

### The Authoritative Research Problem Statement
As formally locked under ADR-006 and recorded in `research/research_questions.md`:

> **Existing RUL research has separately studied conformal uncertainty calibration, condition/regime-aware calibration, and uncertainty-aware maintenance decision-making. What remains insufficiently established is a RUL-specific method that jointly adapts calibration to operating conditions and downstream sequential maintenance consequences while preserving reliable uncertainty coverage. Our study will therefore investigate whether decision-aware, condition-adaptive conformal calibration can improve maintenance utility without sacrificing subgroup reliability or merely becoming more conservative.**

---

## 2. Formal Research Questions

To systematically evaluate this problem statement, IntelliTwin defines four pre-specified, confirmatory research questions. Each question addresses a distinct scientific requirement:

### Research Question 1 (RQ1): Sequential Maintenance Utility and Coverage Reliability
* *Primary Question*: **Can a decision-aware, condition-adaptive conformal RUL calibration method improve sequential maintenance utility while preserving reliable prediction-interval coverage?**
* *Scientific Scope*: Evaluate whether tailoring conformal nonconformity score inversion to operational replacement consequences reduces average maintenance expenditure per engine compared to standard global and condition-aware conformal calibration baselines, without exceeding pre-specified absolute coverage error ceilings ($E < 0.05$) or increasing observed fleet failure rates.
* *Confirmatory Benchmark*: Evaluated on the NASA C-MAPSS FD002 held-out test split under the frozen `primary_reference` cost scenario ($C_{\text{PM}}=1.0, C_{\text{FAIL}}=5.0, C_{\text{WASTE}}=0.20$ SCU per engine) at 90% nominal coverage across both GBR and LSTM base model architectures.

### Research Question 2 (RQ2): Conditional Subgroup Reliability and Interval Sharpness
* *Primary Question*: **Can the proposed method improve reliability across operating regimes and degradation conditions without excessively widening prediction intervals?**
* *Scientific Scope*: Investigate whether condition-adaptive calibration eliminates localized coverage failure across distinct operating regimes (the 6 C-MAPSS FD002 flight condition clusters) and degradation lifecycle stages (Early, Mid, and Late operating thirds). Simultaneously verify that localized reliability gains do not come at the expense of severe interval widening or quality degradation (bounding Mean Prediction Interval Width [MPIW] and Winkler interval score deterioration to under 1.0 cycle).
* *Confirmatory Benchmark*: Evaluated on C-MAPSS FD002 held-out test engines at 90% nominal coverage across both model architectures and both subgroup families using dynamic worst-group recomputation and conservative missing-group bounds propagation.

### Research Question 3 (RQ3): Decision-Value Attribution vs. Matched-Conservatism Controls
* *Primary Question*: **Are the maintenance benefits of the proposed method attributable to decision-aware uncertainty calibration rather than simply more conservative prediction intervals or earlier maintenance?**
* *Scientific Scope*: Disambiguate genuine decision-informative uncertainty calibration from trivial over-conservatism. In sequential maintenance simulation, any heuristic that broadens intervals or triggers earlier replacement can suppress failures at the cost of massive discarded useful life. RQ3 determines whether the proposed method outperforms four pre-specified matched-conservatism control configurations across three distinct families:
  1. *Widened Prediction Intervals* (parameterized width expansion $\lambda \ge 1.0$).
  2. *Matched-Width Prediction Intervals* (calibrated width matching minimizing $|MPIW_{\text{control}} - MPIW_{\text{proposed}}|$).
  3. *Point-Prediction Safety Margins* (offset thresholding $p \le 1 + m$).
  4. *Earlier-Intervention Conservative Policies* (elevated lower-bound thresholding $L \le h$).
* *Confirmatory Benchmark*: Evaluated on C-MAPSS FD002 held-out test engines under the `primary_reference` scenario, requiring the proposed method to outperform every single pre-specified control family by at least 0.20 SCU per engine.

### Research Question 4 (RQ4): Robustness, Architecture Invariance, and Generalization
* *Primary Question*: **Does the proposed method retain its calibration and maintenance-decision benefits across operating conditions, base RUL predictors, datasets, and repeated experimental runs?**
* *Scientific Scope*: Verify that the calibration mechanism is not an artifact of a specific neural architecture, a single random seed, or a single dataset split. Evaluate performance consistency across a balanced multi-dataset, multi-architecture evaluation matrix comprising six mandatory cells:
  1. FD001 $\times$ Histogram Gradient Boosting Regressor (GBR)
  2. FD001 $\times$ Long Short-Term Memory (LSTM) network
  3. FD002 $\times$ Histogram Gradient Boosting Regressor (GBR)
  4. FD002 $\times$ Long Short-Term Memory (LSTM) network
  5. FD004 $\times$ Histogram Gradient Boosting Regressor (GBR)
  6. FD004 $\times$ Long Short-Term Memory (LSTM) network
* *Confirmatory Benchmark*: Weighted aggregate contrasts ($1/6$ equal weight per cell) requiring aggregate cost reduction ($\Delta_{\text{cost}} > 0.20$ SCU) and aggregate worst-group error reduction ($\Delta_{\text{error}} > 0.01$), alongside strict cell-level non-harm constraints ($\Delta_{\text{cost}} > -0.20$ SCU and $\Delta_{\text{error}} > -0.01$ in every individual cell).

---

## 3. Explicit Research Boundaries

In accordance with preregistration ethics and research integrity:
1. **Questions to be Tested**: All research objectives are formally formulated as scientific hypotheses to be tested empirically. They are not assumed, asserted, or reported as achieved outcomes prior to held-out test evaluation.
2. **Immutable Criteria**: In accordance with the *No Post-Hoc Changes Rule* (ADR-018), primary outcomes, comparators, practical-effect thresholds, and statistical decision rules are permanently frozen and cannot be relaxed after observing test data.
3. **Transparent Decision Space**: Every research question produces an immutable classification:
   - **Supported**: Confirmatory lower decision interval strictly exceeds the practical-effect margin and all safeguards hold.
   - **Unsupported**: Confirmatory upper decision interval falls below the practical-effect margin, or any safeguard fails.
   - **Inconclusive**: Decision interval spans the margin or inference is degenerate.
