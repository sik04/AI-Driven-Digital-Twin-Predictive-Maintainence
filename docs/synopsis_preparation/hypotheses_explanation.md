# Authoritative Hypothesis Framework and Decision Logic Explanation

**Document Version**: `1.0`  
**Governing ADR**: `ADR-018` (Step 6 Numerical Freeze Decision, 2026-10-11)  
**Authoritative Specifications**: `research/hypotheses/hypothesis_framework.yaml` & `research/research_design/statistical_inference_protocol.md`  
**LaTeX Counterpart**: `latex/shared/hypotheses.tex` & `latex/hypotheses/main.tex`  
**Status**: Frozen for Confirmatory Evaluation — All inequalities, thresholds, and decision rules are preserved without modification.

---

## 1. Governance Rules on Hypothesis Testing and Evaluation

The IntelliTwin hypothesis framework is governed by five mandatory principles established under ADR-018:

1. **Success Criteria Governance**: The historical percentage-based thresholds (e.g., arbitrary 5% or 10% cost reductions) are permanently superseded. Each research question possesses a pre-specified primary outcome metric, a defined comparator set, an immutable numerical practical-effect threshold, and an engine-cluster bootstrap decision rule that classifies results into a three-way outcome: **Supported**, **Unsupported**, or **Inconclusive**.
2. **Outcome Hierarchy Rule**: For each research question, the pre-specified **primary outcome** determines the confirmatory scientific claim. Supporting and secondary outcomes verify operational constraints, reliability trade-offs, and failure safeguards. A favorable secondary outcome cannot compensate for failure on the primary outcome.
3. **No Post-Hoc Modification Rule**: Primary metrics, comparator sets, subgroup definitions, practical-effect thresholds, statistical decision rules, and outcome hierarchies are frozen prior to inspecting held-out test data. Any post-hoc modification is prohibited; any unplanned secondary analysis must be explicitly designated as exploratory.
4. **Nature of Numerical Margins**: Numerical practical-effect thresholds (e.g., 0.20 SCU cost improvement, 0.01 coverage error reduction) are transparent, study-defined benchmark preferences. They represent pre-specified minimum interesting effects for the academic evaluation, not universal engineering constants or empirical airline economic parameters.
5. **Statistical Sample Unit**: The independent statistical unit is the **engine unit** ($i \in \{1, \dots, N\}$). Individual operational cycles ($t$) and sliding time windows within an engine trajectory are autocorrelated time series and must never be treated as independent observations.

---

## 2. Global Statistical Inference Protocol

### 2.1 Resampling Structure
- **Resampling Method**: Stratified engine-cluster bootstrap with replacement ($B = 10,000$ resamples).
- **Stratification**: Within each dataset, resampling is stratified by the lifetime quartiles ($Q_1, Q_2, Q_3, Q_4$) defined during split generation. The exact engine count per stratum in the held-out split is strictly preserved.
- **Quartile Provenance**: Fixed from split-generation metadata (for FD001/FD004 from `quartile_membership` in the manifest; for FD002 from `data/splits/fd002_lifetime_quartile_provenance.json`).
- **Paired Trajectory Consistency**: When an engine is drawn in a bootstrap replicate, all of its cycles, endpoints, models, predictions across all five random seeds, and comparator states are drawn simultaneously to maintain strict pairing.
- **Pseudo-Random Number Generator**: `numpy.random.Generator` backed by `PCG64` with seed sequence `SeedSequence([2026, 6, dataset_number])` (where `dataset_number` is 1 for FD001, 2 for FD002, and 4 for FD004).

### 2.2 Decision Confidence Intervals vs. Descriptive Intervals
- **Multiplicity Control**: Family-Wise Error Rate (FWER) across the four primary research questions is controlled at $\alpha = 0.05$ via Bonferroni correction:
  $$\alpha_{\text{per-RQ}} = \frac{0.05}{4} = 0.0125$$
- **Confirmatory Decision Intervals**: Evaluated at **98.75% confidence** using the empirical percentile method:
  $$\text{CI}_{\text{decision}} = \left[\text{Quantile}(0.00625), \; \text{Quantile}(0.99375)\right]$$
- **Descriptive Confidence Intervals**: 95% intervals ($\alpha = [0.025, 0.975]$) are reported for context and descriptive reporting only; they do not determine confirmatory hypothesis support.
- **Intersection-Union Principle (IUT)**: Each research question encompasses multiple component criteria (e.g., both model architectures, multiple comparators, and error ceilings). In accordance with IUT, an RQ is Supported if and only if **every single required component condition passes** at the 98.75% decision interval level.

### 2.3 Three-Way Decision Rules
For any condition evaluated against a frozen practical-effect margin:

1. **Improvement Condition ($\Delta > \text{margin}$)**:
   - **Pass**: $\text{CI}_{\text{lower}} > \text{margin}$ (entire 98.75% interval clears the practical-effect threshold).
   - **Fail**: $\text{CI}_{\text{upper}} < \text{margin}$ (entire 98.75% interval falls below the threshold).
   - **Indeterminate**: $\text{CI}_{\text{lower}} \le \text{margin} \le \text{CI}_{\text{upper}}$ (interval covers the boundary). Boundary equality is classified as Indeterminate.
2. **Noninferiority / Safeguard Condition ($D < \text{margin}$)**:
   - **Pass**: $\text{CI}_{\text{upper}} < \text{margin}$ (entire 98.75% interval rules out deterioration $\ge \text{margin}$).
   - **Fail**: $\text{CI}_{\text{lower}} > \text{margin}$ (entire 98.75% interval indicates deterioration $\ge \text{margin}$).
   - **Indeterminate**: $\text{CI}_{\text{lower}} \le \text{margin} \le \text{CI}_{\text{upper}}$.
3. **Finite-Benchmark Failure Safeguard**:
   - In every comparison, the proposed method's observed fleet failure rate must not exceed that of the comparator:
     $$\Delta_{\text{fail}} = \overline{\text{FailRate}}_P - \overline{\text{FailRate}}_{\text{comparator}} \le 0.0$$
   - Any observed increase ($\Delta_{\text{fail}} > 0.0$) constitutes an immediate failure of the safeguard.

---

## 3. Detailed Hypothesis Specifications (RQ1–RQ4)

### Research Question 1 (RQ1): Sequential Maintenance Utility and Coverage Reliability
* **Experiment Mapping**: Experiment A (C-MAPSS FD002 held-out test split, 52 engines, `primary_reference` scenario: $C_{\text{PM}}=1.0, C_{\text{FAIL}}=5.0, C_{\text{WASTE}}=0.20$ SCU, nominal coverage 90%).
* **Null Hypothesis ($H_{0,1}$)**:
  > The proposed method does not improve sequential maintenance utility by at least 0.20 SCU per engine over both global and standard condition-aware calibration, or fails to maintain required coverage reliability.
* **Alternative Hypothesis ($H_{1,1}$)**:
  > The proposed method improves maintenance utility by at least 0.20 SCU per engine over both global and standard condition-aware calibration while maintaining required coverage reliability.
* **Primary Outcome Metric**: Total simulated maintenance cost per engine contrast:
  $$\Delta_{\text{cost}} = \overline{\text{Cost}}_B - \overline{\text{Cost}}_P$$
  (where $B$ denotes baseline calibration and $P$ denotes the proposed decision-aware calibration; positive $\Delta_{\text{cost}}$ represents cost reduction).
* **Primary Comparators**:
  1. `global_hcp`: Global engine-weighted hierarchical conformal calibration.
  2. `regime_hcp`: Standard condition-aware (operating-regime-stratified) hierarchical conformal calibration.
* **Required Models**: Both Histogram Gradient Boosting Regressor (GBR) and Long Short-Term Memory (LSTM) base models must pass all criteria.
* **Frozen Practical-Effect Threshold**: $\Delta_{\text{cost}} > 0.20$ SCU per engine (equivalent to the economic cost of exactly one discarded cycle of usable life under $C_{\text{WASTE}}=0.20$).
* **Reliability & Safeguard Criteria**:
  - Marginal absolute coverage error ceiling: $E_{\text{marginal}} < 0.05$ ($\text{CI}_{\text{upper}} < 0.05$).
  - Worst operating-regime absolute coverage error ceiling: $E_{\text{regime}} < 0.05$ ($\text{CI}_{\text{upper}} < 0.05$).
  - Worst degradation lifecycle stage absolute coverage error ceiling: $E_{\text{stage}} < 0.05$ ($\text{CI}_{\text{upper}} < 0.05$).
  - Observed fleet failure rate safeguard: $\overline{\text{FailRate}}_P \le \overline{\text{FailRate}}_B$ against both baselines.
* **Decision Classification Logic**:
  - **Supported**: For **both** GBR and LSTM, $\text{CI}_{\text{lower}}(\Delta_{\text{cost}}) > 0.20$ SCU against both baselines, $\text{CI}_{\text{upper}}(E) < 0.05$ across marginal, worst-regime, and worst-stage coverage, and observed fleet failure rate increase $\le 0.0$.
  - **Unsupported**: For either model, $\text{CI}_{\text{upper}}(\Delta_{\text{cost}}) < 0.20$ SCU against either baseline, $\text{CI}_{\text{lower}}(E) > 0.05$ on any coverage metric, or observed fleet failure rate increases over either baseline.
  - **Inconclusive**: No required condition fails, but at least one decision interval covers its boundary, or inference is degenerate.

---

### Research Question 2 (RQ2): Conditional Subgroup Reliability and Interval Sharpness
* **Experiment Mapping**: Experiment B (C-MAPSS FD002 held-out test split, nominal coverage 90%).
* **Null Hypothesis ($H_{0,2}$)**:
  > The proposed method does not improve worst-group conditional coverage error by at least 0.01 over both baselines, or causes interval width or interval score to deteriorate by 1.0 cycle or more.
* **Alternative Hypothesis ($H_{1,2}$)**:
  > The proposed method improves worst-group conditional coverage error by at least 0.01 over both baselines while restricting interval width and score deterioration to under 1.0 cycle.
* **Primary Outcome Metric**: Worst-group conditional coverage error contrast:
  $$\Delta_{\text{error}} = \text{WorstErr}_B - \text{WorstErr}_P$$
  (positive $\Delta_{\text{error}}$ represents error reduction; 0.01 represents 1 percentage point improvement).
* **Required Subgroup Families**:
  1. *Operating Regimes Family* ($G_{\text{regime}}$): The 6 discrete operating clusters ($C_1$–$C_6$).
  2. *Degradation Lifecycle Stages Family* ($G_{\text{stage}}$): Early, Mid, and Late operating thirds of run-to-failure lifetime.
* **Dynamic Worst-Group & Missing-Group Bound Propagation**:
  In each bootstrap replicate $b$, the worst group is dynamically recomputed across eligible groups ($\ge 10$ engines). If a group is absent in replicate $b$, error bounds propagate conservatively as $[0.0, 0.90]$ per Section 4 of the statistical inference protocol. Replicates are never discarded.
* **Secondary Interval Quality Safeguards**:
  - Mean Prediction Interval Width (MPIW) contrast: $D_{\text{width}} = \overline{\text{MPIW}}_P - \overline{\text{MPIW}}_B < 1.0$ cycle.
  - Winkler Interval Score contrast: $D_{\text{score}} = \overline{\text{IS}}_P - \overline{\text{IS}}_B < 1.0$ cycle.
  - Worst-group absolute coverage error ceiling: $E_{\text{worst}} < 0.05$.
* **Decision Classification Logic**:
  - **Supported**: For **both** models and **both** subgroup families, $\text{CI}_{\text{lower}}(\Delta_{\text{error}}) > 0.01$ against both baselines, $\text{CI}_{\text{upper}}(E_{\text{worst}}) < 0.05$, $\text{CI}_{\text{upper}}(D_{\text{width}}) < 1.0$ cycle, and $\text{CI}_{\text{upper}}(D_{\text{score}}) < 1.0$ cycle.
  - **Unsupported**: For either model or subgroup family, $\text{CI}_{\text{upper}}(\Delta_{\text{error}}) < 0.01$ against either baseline, $\text{CI}_{\text{lower}}(E_{\text{worst}}) > 0.05$, $\text{CI}_{\text{lower}}(D_{\text{width}}) > 1.0$ cycle, or $\text{CI}_{\text{lower}}(D_{\text{score}}) > 1.0$ cycle.
  - **Inconclusive**: No required condition fails, but at least one decision interval covers its boundary, or inference is degenerate.

---

### Research Question 3 (RQ3): Decision-Value Attribution vs. Matched-Conservatism Controls
* **Experiment Mapping**: Experiment C (C-MAPSS FD002 held-out test split, `primary_reference` scenario, nominal coverage 90%).
* **Null Hypothesis ($H_{0,3}$)**:
  > The proposed method does not improve maintenance utility by at least 0.20 SCU per engine over every prespecified matched-conservatism control family, or violates coverage constraints.
* **Alternative Hypothesis ($H_{1,3}$)**:
  > The proposed method provides maintenance improvements beyond those achievable through matched-conservatism baselines, demonstrating useful decision information rather than simple over-conservatism.
* **Primary Outcome Metric**: Maintenance cost improvement over matched-conservatism controls:
  $$\Delta_{\text{cost}} = \overline{\text{Cost}}_{\text{control}} - \overline{\text{Cost}}_P$$
* **Prespecified Matched-Conservatism Control Taxonomy**:
  The evaluation evaluates **four named control configurations** spanning **three control families**, frozen under ADR-023:
  1. *Widened Prediction Intervals Family*:
     - Control 1 (`matched_width_interval`): Interval scaled by $\lambda$ to match proposed validation MPIW within $\le 1.0$ cycle (achieved: GBR $\lambda=0.92$, diff 0.255 cycles; LSTM $\lambda=0.90$, diff 0.058 cycles).
     - Control 2 (`widened_interval`): Parameterized expansion $\lambda \in [1.0, 16.0]$ minimizing validation cost (achieved: GBR $\lambda=1.00$; LSTM $\lambda=1.00$).
  2. *Point-Prediction Safety Margins Family*:
     - Control 3 (`point_safety_margin`): Replaces lower bound with offset point prediction $p \le 1 + m$ (achieved: GBR $m=5$; LSTM $m=4$).
  3. *Earlier-Intervention Conservative Policies Family*:
     - Control 4 (`earlier_intervention`): Replaces standard policy with elevated lower-bound threshold $L \le h$ (achieved: GBR $h=1$; LSTM $h=1$).
* **Selection Isolation Gate**: All control parameters were selected strictly on FD002 validation engines across seeds 2026–2030 jointly. Calibration and test engines were strictly untouched.
* **Frozen Practical-Effect Threshold**: $\Delta_{\text{cost}} > 0.20$ SCU per engine against **EVERY** prespecified control family.
* **Decision Classification Logic**:
  - **Supported**: For **both** GBR and LSTM, $\text{CI}_{\text{lower}}(\Delta_{\text{cost}}) > 0.20$ SCU against **all four controls**, $\text{CI}_{\text{upper}}(E) < 0.05$ across marginal, regime, and stage coverage, and observed fleet failure rate increase $\le 0.0$ against all controls.
  - **Unsupported**: For either model, $\text{CI}_{\text{upper}}(\Delta_{\text{cost}}) < 0.20$ SCU against **any** control configuration, $\text{CI}_{\text{lower}}(E) > 0.05$, or fleet failure rate increases over any control.
  - **Inconclusive**: No condition fails, but at least one decision interval covers its boundary, or inference is degenerate.

---

### Research Question 4 (RQ4): Robustness and Generalization
* **Experiment Mapping**: Experiment D (Evaluation matrix of 6 mandatory cells across FD001, FD002, FD004 $\times$ GBR, LSTM, weighted equally at $w_k = 1/6$ per cell).
* **Null Hypothesis ($H_{0,4}$)**:
  > The proposed method fails to achieve aggregate improvements ($\Delta_{\text{cost}} > 0.20$ SCU, $\Delta_{\text{error}} > 0.01$) across the evaluation matrix, or exhibits material harm ($\Delta_{\text{cost}} < -0.20$ SCU or $\Delta_{\text{error}} < -0.01$) in any individual configuration cell.
* **Alternative Hypothesis ($H_{1,4}$)**:
  > The proposed method achieves aggregate improvements across the evaluation matrix without material harm in any individual configuration cell.
* **Primary Outcome Metrics**:
  - Weighted aggregate cost contrast: $\Delta_{\text{cost, agg}} = \sum_{k=1}^6 \frac{1}{6} \Delta_{\text{cost}, k}$
  - Weighted aggregate worst-group error contrast: $\Delta_{\text{error, agg}} = \sum_{k=1}^6 \frac{1}{6} \Delta_{\text{error}, k}$
  - Cell-level non-harm bounds: $\Delta_{\text{cost}, k}$ and $\Delta_{\text{error}, k}$ evaluated in each cell $k \in \{1, \dots, 6\}$.
* **Frozen Practical-Effect Margins**:
  - Aggregate Improvement: $\Delta_{\text{cost, agg}} > 0.20$ SCU, $\Delta_{\text{error, agg}} > 0.01$ (regimes and stages).
  - Cell Non-Harm: $\Delta_{\text{cost}, k} > -0.20$ SCU and $\Delta_{\text{error}, k} > -0.01$ in **every single cell**.
  - Cell Safeguards: Coverage ceilings ($E < 0.05$), interval noninferiority ($D_{\text{width}} < 1.0, D_{\text{score}} < 1.0$), and failure rate increase $\le 0.0$ must hold in all 6 cells.
* **Decision Classification Logic**:
  - **Supported**: Against both calibration baselines, $\text{CI}_{\text{lower}}(\Delta_{\text{cost, agg}}) > 0.20$ SCU, $\text{CI}_{\text{lower}}(\Delta_{\text{error, agg}}) > 0.01$ for regimes and stages, $\text{CI}_{\text{lower}}(\Delta_{\text{cost}, k}) > -0.20$ SCU in every cell, $\text{CI}_{\text{lower}}(\Delta_{\text{error}, k}) > -0.01$ in every cell, and all cell safeguards hold across all 6 cells.
  - **Unsupported**: Against either baseline, $\text{CI}_{\text{upper}}(\Delta_{\text{cost, agg}}) < 0.20$ SCU or $\text{CI}_{\text{upper}}(\Delta_{\text{error, agg}}) < 0.01$, or $\text{CI}_{\text{upper}}(\Delta_{\text{cost}, k}) < -0.20$ SCU or $\text{CI}_{\text{upper}}(\Delta_{\text{error}, k}) < -0.01$ in any individual cell, or any cell-level safeguard fails.
  - **Inconclusive**: No condition fails, but at least one decision interval covers its boundary, or inference is degenerate.
