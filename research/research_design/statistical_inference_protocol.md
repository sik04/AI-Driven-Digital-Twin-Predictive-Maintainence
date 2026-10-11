# Authoritative Statistical Inference and Decision Protocol

**Protocol Version**: `step06-v2`  
**Approval Reference**: `ADR-018` (Date: 2026-10-11)  
**Status**: Frozen for Confirmatory Evaluation  

This document defines the frozen statistical inference contract, cluster-bootstrap resampling procedure, multiplicity-adjusted decision rules, and evaluation criteria for IntelliTwin's confirmatory research questions (RQ1–RQ4).

---

## 1. Estimands and Comparison Directions

### 1.1 Statistical Unit and Seed Aggregation
- **Independent Statistical Unit**: The engine ($i \in \{1, \dots, N\}$). Individual operational cycles ($t$) and time windows are correlated measurements within an engine trajectory and must not be treated as independent observations.
- **Model Seeds**: Five prespecified base model training seeds: `[2026, 2027, 2028, 2029, 2030]`.
- **Primary Estimand**: Performance averaged over the five fixed trained runs across the evaluated engines. Repeated model seeds and stochastic runs are not additional independent engines. Individual seed results must be reported separately as descriptive diagnostics.
- **Additive Metric Computation**:
  1. For each evaluated engine $i$ and seed $s$, compute the engine-level metric over qualified endpoints $V_i = \{30, \dots, T_i\}$ ($n_i = T_i - 29$).
  2. Average across the five seeds within engine $i$:
     $$\bar{m}_i = \frac{1}{5} \sum_{s=1}^5 m_{i, s}$$
  3. Average equally across evaluated engines:
     $$\bar{m} = \frac{1}{N} \sum_{i=1}^N \bar{m}_i$$

### 1.2 Subgroup Coverage Estimands
- For each evaluated engine $i$, seed $s$, and eligible subgroup $g \in G$:
  $$\text{cov}_{i, s}(g) = \frac{1}{|V_i \cap g|} \sum_{t \in V_i \cap g} \mathbf{1}\{L_{it} \le y_{it} \le U_{it}\}$$
- Average across seeds, then equally across engines contributing at least one qualified endpoint to subgroup $g$:
  $$\overline{\text{cov}}(g) = \frac{1}{N_g} \sum_{i \in \text{Engines}(g)} \left(\frac{1}{5} \sum_{s=1}^5 \text{cov}_{i, s}(g)\right)$$
- Absolute coverage error from the 90% nominal target ($\alpha = 0.10$):
  $$\text{Err}(g) = |\overline{\text{cov}}(g) - 0.90|$$
- The maximum worst-group error is evaluated separately for the operating regimes family ($G_{\text{regime}}$, $C_1$–$C_6$) and the lifecycle stages family ($G_{\text{stage}}$, Early/Mid/Late thirds):
  $$\text{WorstErr}_{\text{regime}} = \max_{g \in G_{\text{regime}}} \text{Err}(g), \quad \text{WorstErr}_{\text{stage}} = \max_{g \in G_{\text{stage}}} \text{Err}(g)$$
  Their union maximum $\max(\text{WorstErr}_{\text{regime}}, \text{WorstErr}_{\text{stage}})$ is also reported.

### 1.3 Comparison Directions and Contrasts
For comparisons between a baseline method ($B$) and the proposed method ($P$):
- **Cost Improvement Contrast**:
  $$\Delta_{\text{cost}} = \overline{\text{Cost}}_B - \overline{\text{Cost}}_P$$
  *Positive $\Delta_{\text{cost}}$ favors the proposed method (cost reduction).*
- **Worst-Group Coverage Error Contrast**:
  $$\Delta_{\text{error}} = \text{WorstErr}_B - \text{WorstErr}_P$$
  *Positive $\Delta_{\text{error}}$ favors the proposed method (error reduction).*
- **Interval Width Noninferiority Contrast**:
  $$D_{\text{width}} = \overline{\text{MPIW}}_P - \overline{\text{MPIW}}_B$$
  *Positive $D_{\text{width}}$ indicates interval widening / deterioration by the proposed method.*
- **Interval Score Noninferiority Contrast**:
  $$D_{\text{score}} = \overline{\text{IS}}_P - \overline{\text{IS}}_B$$
  *Positive $D_{\text{score}}$ indicates interval quality degradation by the proposed method.*
- **Tail-Miss Rates**:
  - Optimistic misses: fraction of qualified endpoints with $y_{it} < L_{it}$ (actual RUL shorter than lower bound).
  - Pessimistic misses: fraction of qualified endpoints with $y_{it} > U_{it}$ (actual RUL longer than upper bound).

---

## 2. Resampling & Cluster-Bootstrap Specification

### 2.1 Resampling Structure
- **Replicate Count**: $B = 10,000$ bootstrap resamples.
- **Resampling Unit**: Resample engines intact with replacement (engine-cluster bootstrap). When an engine is drawn, all of its cycles, endpoints, models, predictions across all 5 seeds, and comparator states are included simultaneously to preserve pairing and trajectory autocorrelation.
- **Stratification**: Resampling is stratified within dataset by the original lifetime quartiles ($Q_1, Q_2, Q_3, Q_4$) defined during split generation. The exact engine count per stratum in the held-out split is strictly preserved.
- **Original Quartile Membership**: Stratum memberships are fixed from the split generator manifest (`quartile_membership`), not re-derived from the held-out sample.
- **Paired Consistency**: The identical engine resample draws are used for every comparative method, comparator, metric, and contrast within a dataset.
- **Cross-Dataset Independence**: Resampling is conducted independently across datasets (FD001, FD002, FD004).

### 2.2 PRNG and Reproducibility
- Resampling must use Python `numpy.random.Generator` backed by the `PCG64` bit generator.
- Seed initialization:
  ```python
  from numpy.random import Generator, PCG64, SeedSequence
  rng = Generator(PCG64(SeedSequence([2026, 6, dataset_number])))
  ```
  where `dataset_number` is 1 for FD001, 2 for FD002, and 4 for FD004.
- Engine IDs within each stratum must be sorted in ascending order before index selection.
- Calibrators, base predictors, and hyperparameter selections are **never refit** inside bootstrap replicates. Uncertainty is conditional on the frozen training/calibration partitions, trained runs, split, and protocol.

---

## 3. Multiplicity Adjustment and Confidence Intervals

### 3.1 Interval Construction
- All confidence intervals are constructed using the empirical percentile method via `numpy.quantile(..., method="linear")`.
- **Descriptive Confidence Intervals**: 95% intervals computed with quantiles $\alpha_{\text{desc}} = [0.025, 0.975]$. Reported for descriptive and exploratory summaries only.
- **Confirmatory Decision Intervals**: 98.75% intervals computed with quantiles:
  $$\alpha_{\text{decision}} = [0.00625, 0.99375]$$
  This allocates $\alpha_{\text{fam}} = 0.05 / 4 = 0.0125$ error probability to each of the four primary research questions (Bonferroni family-wise error control across RQ1–RQ4).

### 3.2 Intersection-Union Decision Principle
- Each research question encompasses multiple component criteria (e.g., both model families, multiple baselines, coverage error ceilings, and noninferiority bounds).
- In accordance with the **intersection-union testing (IUT)** principle, an RQ is supported if and only if **every single required component condition** passes at the $\alpha = 0.0125$ level.
- Component intervals are decision bounds for component conditions; they do not constitute a simultaneous joint confidence region.
- Descriptive seed-level, subgroup-level, or secondary sensitivity outcomes do not carry separate multiplicity-adjusted significance claims. No supplementary p-value tests form part of this frozen protocol.

---

## 4. Worst-Group Handling and Missing-Group Bound Propagation

### 4.1 Replicate-Level Worst-Group Recomputation
- Subgroup eligibility is fixed from original endpoint metadata: groups containing at least 10 distinct engines with $\ge 1$ qualified endpoint are eligible.
- In every bootstrap replicate $b$, the worst group is recomputed dynamically across all eligible groups:
  $$\text{WorstErr}^{(b)} = \max_{g \in G_{\text{eligible}}} \text{Err}^{(b)}(g)$$
  The evaluator must not restrict the search to the group that was worst in the empirical sample.

### 4.2 Conservative Missing-Group Bound Propagation
- Because cluster resampling samples with replacement, an eligible subgroup may have zero contributing engines in a particular replicate $b$. An eligible subgroup is **never dropped** due to zero replicate representation.
- For a subgroup with zero engines in replicate $b$, its possible absolute coverage error is bounded by $[0.0, 0.90]$ (since nominal coverage is 0.90 and empirical coverage is bounded in $[0, 1]$).
- For a subgroup family $G$, the replicate lower and upper error bounds are constructed as:
  $$\text{WorstErr}_{\text{lower}}^{(b)} = \max_{g \in G_{\text{available}}^{(b)}} \text{Err}^{(b)}(g)$$
  $$\text{WorstErr}_{\text{upper}}^{(b)} = \max\left(\max_{g \in G_{\text{available}}^{(b)}} \text{Err}^{(b)}(g), \; 0.90 \cdot \mathbf{1}\{|G_{\text{missing}}^{(b)}| > 0\}\right)$$
- When evaluating the difference $\Delta_{\text{error}} = \text{WorstErr}_B - \text{WorstErr}_P$, bounds propagate conservatively:
  $$\Delta_{\text{error, lower}}^{(b)} = \text{WorstErr}_{B, \text{lower}}^{(b)} - \text{WorstErr}_{P, \text{upper}}^{(b)}$$
  $$\Delta_{\text{error, upper}}^{(b)} = \text{WorstErr}_{B, \text{upper}}^{(b)} - \text{WorstErr}_{P, \text{lower}}^{(b)}$$
- The final decision interval endpoints are obtained from the specified quantiles of the replicate lower and upper bounds:
  $$\text{CI}_{\text{lower}} = \text{Quantile}(\Delta_{\text{error, lower}}, 0.00625), \quad \text{CI}_{\text{upper}} = \text{Quantile}(\Delta_{\text{error, upper}}, 0.99375)$$
- The evaluator must record and report the exact number of replicates that required missing-group bound propagation. Replicates are never discarded, redrawn, or rerolled.

---

## 5. Decision Rules: Supported, Unsupported, Inconclusive

All confirmatory decisions use the 98.75% decision intervals ($[\text{CI}_{\text{lower}}, \text{CI}_{\text{upper}}]$) evaluated against prespecified margins:

### 5.1 Required Improvement Condition ($\Delta > \text{margin}$)
Applies to cost reductions ($\Delta_{\text{cost}} > 0.20$ SCU) and coverage error reductions ($\Delta_{\text{error}} > 0.01$):
- **Pass**: $\text{CI}_{\text{lower}} > \text{margin}$ (entire decision interval clears the margin).
- **Fail**: $\text{CI}_{\text{upper}} < \text{margin}$ (entire decision interval falls below the margin).
- **Indeterminate**: $\text{CI}_{\text{lower}} \le \text{margin} \le \text{CI}_{\text{upper}}$ (interval covers the margin).
*Exact boundary equality ($\text{CI}_{\text{lower}} = \text{margin}$ or $\text{CI}_{\text{upper}} = \text{margin}$) is classified as Indeterminate.*

### 5.2 Required Noninferiority Condition ($D < \text{margin}$)
Applies to interval width ($D_{\text{width}} < 1.0$ cycle) and interval score ($D_{\text{score}} < 1.0$ cycle):
- **Pass**: $\text{CI}_{\text{upper}} < \text{margin}$ (entire decision interval rules out deterioration $\ge \text{margin}$).
- **Fail**: $\text{CI}_{\text{lower}} > \text{margin}$ (entire decision interval indicates deterioration $\ge \text{margin}$).
- **Indeterminate**: $\text{CI}_{\text{lower}} \le \text{margin} \le \text{CI}_{\text{upper}}$.

### 5.3 Error Ceiling Condition ($E < 0.05$)
Applies to absolute coverage error ($\text{WorstErr} < 0.05$):
- **Pass**: $\text{CI}_{\text{upper}} < 0.05$ (error is bounded within 5 percentage points of nominal 90% coverage).
- **Fail**: $\text{CI}_{\text{lower}} > 0.05$.
- **Indeterminate**: $\text{CI}_{\text{lower}} \le 0.05 \le \text{CI}_{\text{upper}}$.

### 5.4 Finite-Benchmark Failure Safeguard
- In every required comparison, the proposed method's observed engine- and seed-averaged fleet failure rate must not exceed that of the comparator:
  $$\overline{\text{FailRate}}_P \le \overline{\text{FailRate}}_B \quad (\Delta_{\text{fail}} \le 0.0)$$
- Exact equality ($\Delta_{\text{fail}} = 0.0$) satisfies this finite-benchmark constraint.
- Any observed increase ($\overline{\text{FailRate}}_P > \overline{\text{FailRate}}_B$) fails this safeguard.
- *Notice*: This is a finite-sample empirical gate, not mathematical proof of population failure-rate noninferiority or operational safety. Zero observed failures in a finite test set does not imply zero true operational risk.

### 5.5 Research Question Classification
- **Supported**: Every prespecified component condition for the RQ passes under its decision interval and failure safeguard.
- **Unsupported**: At least one required component condition fails.
- **Inconclusive**: No required condition fails, but at least one condition is indeterminate (e.g., CI covers the boundary), or inference is degenerate.
- *Critical Principle*: "Point estimate exceeds margin and CI excludes zero" is **not** sufficient to claim support; the lower CI must strictly exceed the margin.
  - *Example*: An observed $\Delta_{\text{cost}} = 0.25$ SCU with 98.75% CI $[0.01, 0.49]$ is **Inconclusive** against a $0.20$ margin, because the interval includes values below $0.20$.
- "Unsupported" indicates that the prespecified research claim is not demonstrated; it does not necessarily imply that the proposed method is inferior or harmful.

---

## 6. Detailed Requirements for Each Research Question

### 6.1 RQ1 — Primary Maintenance Utility
- **Dataset**: FD002 test split (260 engines total: 52 held-out test engines).
- **Scenario**: `primary_reference` ($C_{\text{PM}}=1.0, C_{\text{FAIL}}=5.0, C_{\text{WASTE}}=0.20$).
- **Nominal Coverage**: 90% ($\alpha = 0.10$).
- **Base Models**: Both GBR and LSTM must be evaluated separately; both must pass all conditions for full RQ1 support.
- **Comparators**: Proposed method must be compared against **BOTH** Global Conformal Calibration and Standard Condition-Aware Calibration.
- **Required Conditions**:
  1. $\Delta_{\text{cost}} > 0.20$ SCU per engine against Global Conformal ($\text{CI}_{\text{lower}} > 0.20$).
  2. $\Delta_{\text{cost}} > 0.20$ SCU per engine against Standard Condition-Aware ($\text{CI}_{\text{lower}} > 0.20$).
  3. Marginal coverage error $E_{\text{marginal}} < 0.05$ ($\text{CI}_{\text{upper}} < 0.05$).
  4. Worst-regime coverage error $E_{\text{regime}} < 0.05$ ($\text{CI}_{\text{upper}} < 0.05$).
  5. Worst-stage coverage error $E_{\text{stage}} < 0.05$ ($\text{CI}_{\text{upper}} < 0.05$).
  6. Observed failure safeguard: $\overline{\text{FailRate}}_P \le \overline{\text{FailRate}}_B$ against both baselines.

### 6.2 RQ2 — Subgroup Reliability Without Material Interval Deterioration
- **Dataset**: FD002 test split.
- **Nominal Coverage**: 90%.
- **Base Models**: Both GBR and LSTM required.
- **Subgroup Families**: Both operating regimes ($C_1$–$C_6$) and degradation lifecycle stages (Early/Mid/Late) required.
- **Comparators**: Proposed method compared against **BOTH** Global Conformal and Standard Condition-Aware Calibration.
- **Required Conditions**:
  1. $\Delta_{\text{error}} > 0.01$ (1 percentage point error reduction) against Global Conformal ($\text{CI}_{\text{lower}} > 0.01$) for regimes and stages.
  2. $\Delta_{\text{error}} > 0.01$ against Standard Condition-Aware ($\text{CI}_{\text{lower}} > 0.01$) for regimes and stages.
  3. Absolute worst-group error ceiling $E < 0.05$ ($\text{CI}_{\text{upper}} < 0.05$) for regimes and stages.
  4. Interval width noninferiority: $D_{\text{width}} < 1.0$ cycle against both baselines ($\text{CI}_{\text{upper}} < 1.0$).
  5. Interval score noninferiority: $D_{\text{score}} < 1.0$ cycle against both baselines ($\text{CI}_{\text{upper}} < 1.0$).
  *Note*: MPIW and interval score safeguards are explicit numerical conditions; they cannot be replaced by vague claims of "no statistically significant widening."

### 6.3 RQ3 — Decision-Value Attribution vs. Matched-Conservatism Controls
- **Dataset**: FD002 test split.
- **Scenario**: `primary_reference`.
- **Base Models**: Both GBR and LSTM required.
- **Control Families**: All three prespecified control families must be evaluated:
  1. Widened / matched-width prediction intervals.
  2. Tuned point-prediction safety margins.
  3. Earlier-intervention conservative policies.
- **Required Conditions**:
  1. $\Delta_{\text{cost}} > 0.20$ SCU per engine against **EVERY** prespecified control family ($\text{CI}_{\text{lower}} > 0.20$). This guarantees benefit over the strongest control family without cherry-picking.
  2. Coverage ceilings: $E < 0.05$ on marginal, worst-regime, and worst-stage coverage.
  3. Observed failure safeguard: $\overline{\text{FailRate}}_P \le \overline{\text{FailRate}}_{\text{control}}$ against every control family.
- *Notice*: Control parameter tuning will be pre-specified in the later method-design phase using training/calibration data only. Confirmatory RQ3 evaluation cannot be run until that tuning protocol is frozen.

### 6.4 RQ4 — Robustness Across Configurations
- **Evaluation Matrix**: Six mandatory cells:
  - Cell 1: FD001 × GBR
  - Cell 2: FD001 × LSTM
  - Cell 3: FD002 × GBR
  - Cell 4: FD002 × LSTM
  - Cell 5: FD004 × GBR
  - Cell 6: FD004 × LSTM
- **Weighting**: Equal weight across datasets and model families (each cell carries weight $w_k = 1/6$ in aggregate metrics). Engines must **never** be pooled raw across datasets with unequal weights.
- **Scenario**: `primary_reference`, nominal coverage 90%.
- **Required Conditions**:
  1. **Aggregate Benefit**:
     - Weighted aggregate $\Delta_{\text{cost}} > 0.20$ SCU ($\text{CI}_{\text{lower}} > 0.20$) against both calibration baselines.
     - Weighted aggregate $\Delta_{\text{error}} > 0.01$ ($\text{CI}_{\text{lower}} > 0.01$) separately for regimes and stages against both baselines.
  2. **Cell-Level Non-Harm**: In **every one of the 6 individual cells** and against both baselines:
     - $\Delta_{\text{cost}} > -0.20$ SCU ($\text{CI}_{\text{lower}} > -0.20$).
     - $\Delta_{\text{error}} > -0.01$ ($\text{CI}_{\text{lower}} > -0.01$) separately for regimes and stages.
  3. **Cell-Level Safeguards**: In every cell, proposed coverage ceilings ($E < 0.05$), interval safeguards ($D_{\text{width}} < 1.0, D_{\text{score}} < 1.0$), and observed failure safeguards must hold.
- *Generalization Boundary*: RQ4 claims apply strictly to the evaluated C-MAPSS subsets (FD001, FD002, FD004), the two model families, and the fixed-seed-average estimand. Generalization to unseen engine architectures or arbitrary future seeds is not claimed. FD003 remains inactive.

---

## 7. Premature-Intervention Offline Diagnostic

To provide an interpretable operational timing metric alongside continuous wasted RUL, the binary premature intervention diagnostic is defined as:
$$\text{Cost-Inefficient Early PM} = \mathbf{1}\{\text{PM Occurred}\} \land (\text{Cost}_{\text{PM}} > \text{Cost}_{\text{FAIL}})$$

For positive wasted life cost ($C_{\text{WASTE}} > 0$):
$$\text{Cost}_{\text{PM}} = C_{\text{PM}} + C_{\text{WASTE}} \cdot W > C_{\text{FAIL}} \iff W > r_{\text{equal}} = \frac{C_{\text{FAIL}} - C_{\text{PM}}}{C_{\text{WASTE}}}$$

- **Horizon Values ($r_{\text{equal}}$)**:
  - `primary_reference`: $r_{\text{equal}} = (5.0 - 1.0) / 0.20 = 20$ cycles.
  - `failure_sensitive`: $r_{\text{equal}} = (10.0 - 1.0) / 0.20 = 45$ cycles.
  - `waste_sensitive`: $r_{\text{equal}} = (5.0 - 1.0) / 0.40 = 10$ cycles.
- Exact equality ($W = r_{\text{equal}}$) does not count as cost-inefficient early PM.
- **Reporting**:
  - Fleet rate: denominator is all evaluated engines in the split.
  - PM-only rate: denominator is engines that received PM intervention; returns `null` if zero engines received PM.
- *Notice*: This is an offline economic diagnostic relative to scenario costs. It is not an optimal replacement boundary or an operationally validated threshold for engine overhaul.

---

## 8. Protocol Boundaries & Methodological Limitations

1. **Approximate Inference**: Cluster-bootstrap percentile intervals are asymptotic approximations. In small sample subgroups (e.g., minimum 10 engines) and non-smooth statistics (e.g., worst-group max operator), empirical coverage of the interval itself may exhibit finite-sample error.
2. **Degenerate Intervals**: If an empirical bootstrap distribution produces a zero-width interval ($\text{CI}_{\text{lower}} = \text{CI}_{\text{upper}}$), it must be flagged as degenerate and cannot be used to establish a confirmatory pass. The affected condition is classified as **Indeterminate**.
3. **Data Integrity**: Missing predictions or missing seed runs are fatal evaluation errors. Silently dropping missing endpoints or averaging only available observations is prohibited.
4. **Conditional Guarantees**: Conformal calibration provides marginal exchangeable coverage. It does not provide pointwise conditional coverage guarantees, trajectory-wide simultaneous bounds, or stopping-time coverage under state-dependent sequential maintenance policies.
