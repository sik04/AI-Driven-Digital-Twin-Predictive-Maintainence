# Comprehensive Experimental Evaluation and Statistical Inference Plan

**Document Version**: `2.0 (v4 Audit Alignment)`  
**Reviewed Repository Baseline**: `c163bb279e7427b8f1b6e75955af4969ff9370fd`  
**Committed Readiness Evidence**: `experiments/pretest_verification_v4/` (Audit Execution Commit: `550a7994d5746d3bcbfa28c26e7ed4f1a26a6153`, `git_dirty: false`, readiness: `PRETEST_READY`, held-out execution: `NOT_STARTED`, RQ outcomes: `PENDING`)  
**Governing ADRs**: `ADR-010`, `ADR-018`, `ADR-023`  
**Authoritative Protocol**: `research/research_design/statistical_inference_protocol.md`  
**Target Codebase**: `src/intellitwin/evaluation/{metrics, bootstrap, decisions, inference}.py`  
**Status**: Authoritative Experimental Evaluation Contract

> **Status Statement**: Base predictors and conformal calibrators are implemented and frozen. The committed v4 pre-test audit reports PASS and PRETEST_READY. Held-out execution has not started, and RQ1–RQ4 outcomes remain pending. Development validation and audit results do not establish confirmatory maintenance benefit, subgroup reliability, or robustness.

---

## 1. Evaluation Hierarchy and Estimand Structure

The IntelliTwin evaluation framework enforces a strict hierarchy between confirmatory claims, descriptive sensitivity analyses, and exploratory diagnostics.

### 1.1 The Statistical Unit and Equal-Engine Weighting
- **The Independent Statistical Sample Unit**: The **engine unit** ($i \in \{1, \dots, N\}$). Individual operational cycles ($t$) within an engine trajectory are auto-correlated and must never be treated as independent observations.
- **Equal-Engine Weighting**: To prevent survivor bias (where long-lived engines dominate aggregate metrics), all cycle-level metrics are computed within engine across qualified prediction endpoints ($V_i = \{30, \dots, T_i\}$), averaged across model seeds within that engine, and then averaged equally across the evaluated engines:
  $$\bar{m}_i = \frac{1}{5} \sum_{s=1}^5 m_{i, s}, \quad \bar{m} = \frac{1}{N} \sum_{i=1}^N \bar{m}_i$$
- **Seed Averaging Rule**: The five training seeds (`2026, 2027, 2028, 2029, 2030`) represent fixed stochastic replicates of model parameter initialization. They are **averaged within each engine** to estimate expected model performance; they are **never pooled as independent sample units**.
- **Point-Prediction RMSE Definition**: For each seed, compute within-engine mean squared errors, average those engine MSEs equally across test engines, then take the square root. Do not average individual-engine RMSE values and label that the primary equal-engine RMSE.

### 1.2 Coverage Levels
- **Primary Confirmatory Coverage Target**: **90% nominal coverage** ($\alpha = 0.10$). All formal hypothesis tests and decision interval evaluations for RQ1–RQ4 are conducted strictly at 90% nominal coverage.
- **Secondary Sensitivity Coverage Levels**: **80%** ($\alpha = 0.20$) and **95%** ($\alpha = 0.05$). Evaluated to characterize interval width and coverage behavior under relaxed and tightened risk tolerance. These analyses are pre-specified descriptive sensitivities and do not carry confirmatory hypothesis claims.

---

## 2. Subgroup Reliability Auditing Protocol

### 2.1 Subgroup Families
Conditional reliability is evaluated across two separate subgroup families (which may contain overlapping observations):
1. **Operating Regimes Family ($G_{\text{regime}}$)**: Discrete operational environmental clusters ($C_1$–$C_6$ in FD002 and FD004) identified by K-Means clustering ($k=6$) on standardized operating settings. They represent algorithmic clusters, not named physical flight conditions.
2. **Degradation Lifecycle Stages Family ($G_{\text{stage}}$)**: Retrospective division of each engine's lifetime $T_i$ into thirds:
   - Early Stage: cycles $t \in [30, \; \lfloor T_i/3 \rfloor]$
   - Mid Stage: cycles $t \in [\lfloor T_i/3 \rfloor + 1, \; \lfloor 2T_i/3 \rfloor]$
   - Late Stage: cycles $t \in [\lfloor 2T_i/3 \rfloor + 1, \; T_i]$

> **Critical Methodological Boundary**: Lifecycle stages are defined retrospectively based on total lifetime $T_i$ and are used **strictly for offline diagnostic evaluation**. They are never used as online features or conditioning inputs during real-time prediction or calibration fitting.

### 2.2 Subgroup Eligibility Criteria
A subgroup $g$ is eligible for evaluation if and only if it contains at least **10 distinct physical engines** with at least one qualified endpoint in the observed split:
$$\text{Eligible}(g) \iff |\text{Engines}(g)| \ge 10$$
Subgroup eligibility is frozen from original qualified endpoints before resampling and never dynamically re-evaluated using duplicated bootstrap draws. The worst eligible group is recomputed within each bootstrap replicate.

### 2.3 Subgroup Coverage and Error Contrasts
For each eligible subgroup $g$, coverage is computed within contributing engines across seeds, then averaged across contributing engines:
$$\overline{\text{cov}}(g) = \frac{1}{N_g} \sum_{i \in \text{Engines}(g)} \left(\frac{1}{5} \sum_{s=1}^5 \text{cov}_{i, s}(g)\right)$$
$$\text{Err}(g) = |\overline{\text{cov}}(g) - 0.90|$$
The maximum worst-group error is evaluated separately for regimes and stages:
$$\text{WorstErr}_{\text{regime}} = \max_{g \in G_{\text{regime, eligible}}} \text{Err}(g), \quad \text{WorstErr}_{\text{stage}} = \max_{g \in G_{\text{stage, eligible}}} \text{Err}(g)$$

The contrast between baseline ($B$) and proposed ($P$) calibration is:
$$\Delta_{\text{error}} = \text{WorstErr}_B - \text{WorstErr}_P$$
where positive $\Delta_{\text{error}}$ represents error reduction (improved reliability).

---

## 3. Matched-Conservatism Control Protocol (RQ3)

To disambiguate true decision-aware calibration utility from trivial interval expansion or naive early intervention, RQ3 evaluates **four named control configurations** across **three prespecified control families**:

| Control Family | Control ID | Method / Parameter Rule | Selection Parameter Grid | Frozen Selected Value (FD002 Validation) |
| :--- | :--- | :--- | :--- | :--- |
| **Widened Interval** | `matched_width_interval` | Scaled baseline interval: $L = \max(0, p - \lambda q), U = p + \lambda q$. Minimizes $|MPIW_{\text{control}} - MPIW_{\text{proposed}}|$. | $\lambda \in \{0.01..4.00, 5, 6, 8, 12, 16\}$ | **GBR**: $\lambda = 0.92$ (`global_hcp`, diff: 0.255 cycles)<br>**LSTM**: $\lambda = 0.90$ (`regime_hcp`, diff: 0.058 cycles) |
| **Widened Interval** | `widened_interval` | Scaled baseline interval minimizing validation maintenance cost subject to $\lambda \ge 1.0$. | $\lambda \in \{1.00..4.00, 5, 6, 8, 12, 16\}$ | **GBR**: $\lambda = 1.00$ (`regime_hcp`, unscaled baseline width)<br>**LSTM**: $\lambda = 1.00$ (`global_hcp`, unscaled baseline width) |
| **Point Safety Margin** | `point_safety_margin` | Replaces interval lower bound with point prediction offset: PM triggered iff $p \le 1 + m$. | $m \in \{0, 1, \dots, 250\}$ cycles | **GBR**: $m = 5$ cycles<br>**LSTM**: $m = 4$ cycles |
| **Earlier Intervention**| `earlier_intervention` | Replaces standard policy with elevated replacement threshold: PM triggered iff $L \le h$. | $h \in \{1, 2, \dots, 251\}$ cycles | **GBR**: $h = 1$ cycle (`regime_hcp`, matches baseline threshold)<br>**LSTM**: $h = 1$ cycle (`global_hcp`, matches baseline threshold) |

*(Note: $\lambda=1.00$ corresponds to unscaled baseline width, not actual expansion beyond baseline; $h=1$ matches the baseline threshold, not an empirically earlier intervention.)*

### Strict Selection Isolation Gate
Under ADR-023:
- Control parameter tuning was performed strictly on FD002 validation engines across seeds 2026–2030 jointly under the `primary_reference` scenario.
- Calibration engines and test engines were strictly untouched during control selection.
- All selected parameters were committed to `experiments/pretest_verification_v4/control_selection.json` before test data was prepared.

---

## 4. Stratified Cluster-Bootstrap Resampling Protocol

### 4.1 Resampling Algorithm
1. **Replicate Count**: $B = 10,000$ bootstrap resamples.
2. **Cluster Drawing**: Resample engines intact with replacement within each lifetime quartile stratum ($Q_1$–$Q_4$) defined during split generation.
3. **Paired Structure**: The identical engine resample index vector is applied simultaneously to the proposed method, baseline methods, and all matched controls within that dataset replicate.
4. **Independent Dataset Draws**: Resampling is executed independently across datasets (FD001, FD002, FD004) using `numpy.random.Generator(PCG64(SeedSequence([2026, 6, dataset_number])))`.
5. **Calibrators are Never Refit**: Base models and conformal nonconformity thresholds are never re-estimated within bootstrap loops. Resampling quantifies test evaluation sampling variance conditional on frozen trained models and fitted calibrators.

### 4.2 Dynamic Worst-Group Recomputation & Conservative Missing-Group Bound Propagation
Because cluster resampling draws engines with replacement, an eligible subgroup $g$ may have zero represented engines in a specific replicate $b$.
- An eligible group is **never dropped** or ignored due to absence in replicate $b$.
- If group $g$ is absent in replicate $b$, its empirical coverage error is mathematically bounded within $[0.0, \; 0.90]$ (since nominal coverage is 0.90 and empirical coverage is bounded in $[0, 1]$).
- Recompute the worst eligible group within each bootstrap replicate.
- For replicate $b$ and subgroup family $G$:
  $$\text{WorstErr}_{\text{lower}}^{(b)} = \begin{cases} \max_{g \in G_{\text{available}}^{(b)}} \text{Err}^{(b)}(g), & \text{if } |G_{\text{available}}^{(b)}| > 0 \\ 0.0, & \text{if } |G_{\text{available}}^{(b)}| = 0 \end{cases}$$
  $$\text{WorstErr}_{\text{upper}}^{(b)} = \begin{cases} \max\left(\text{WorstErr}_{\text{lower}}^{(b)}, \; 0.90\right), & \text{if } |G_{\text{missing}}^{(b)}| > 0 \\ \text{WorstErr}_{\text{lower}}^{(b)}, & \text{if } |G_{\text{missing}}^{(b)}| = 0 \end{cases}$$
- For contrast $\Delta_{\text{error}} = \text{WorstErr}_B - \text{WorstErr}_P$, bounds propagate conservatively:
  $$\Delta_{\text{error, lower}}^{(b)} = \text{WorstErr}_{B, \text{lower}}^{(b)} - \text{WorstErr}_{P, \text{upper}}^{(b)}$$
  $$\Delta_{\text{error, upper}}^{(b)} = \text{WorstErr}_{B, \text{upper}}^{(b)} - \text{WorstErr}_{P, \text{lower}}^{(b)}$$
- Decision intervals are derived from the quantiles of replicate lower and upper bounds:
  $$\text{CI}_{\text{lower}} = \text{Quantile}(\Delta_{\text{error, lower}}, \; 0.00625), \quad \text{CI}_{\text{upper}} = \text{Quantile}(\Delta_{\text{error, upper}}, \; 0.99375)$$

---

## 5. Statistical Inference Protocol: Bonferroni FWER & IUT Decision Rules

### 5.1 Multiplicity Adjustment
To maintain family-wise error rate across the four confirmatory research questions at nominal $\alpha_{\text{total}} \le 0.05$, Bonferroni correction allocates $\alpha = 0.0125$ to each research question:
$$\text{Confidence Level} = 1 - 0.0125 = 98.75\%$$
$$\text{Lower Quantile} = \frac{0.0125}{2} = 0.00625, \quad \text{Upper Quantile} = 1 - 0.00625 = 0.99375$$
The Bonferroni adjustment is a prespecified nominal familywise adjustment. Percentile bootstrap inference is approximate; it does not claim exact finite-sample error control.

### 5.2 Intersection-Union Testing (IUT)
An RQ encompasses multiple required criteria. Under IUT, an RQ is Supported if and only if **every required condition passes at the 98.75% decision interval level**:

| Research Question | Required Pass Conditions for Supported Classification |
| :--- | :--- |
| **RQ1** | For **both** GBR and LSTM:<br>1. $\text{CI}_{\text{lower}}(\Delta_{\text{cost}}) > 0.20$ SCU vs. `global_hcp`<br>2. $\text{CI}_{\text{lower}}(\Delta_{\text{cost}}) > 0.20$ SCU vs. `regime_hcp`<br>3. $\text{CI}_{\text{upper}}(E_{\text{marginal}}) < 0.05$<br>4. $\text{CI}_{\text{upper}}(E_{\text{regime}}) < 0.05$<br>5. $\text{CI}_{\text{upper}}(E_{\text{stage}}) < 0.05$<br>6. Observed fleet failure rate increase $\Delta_{\text{fail}} \le 0.0$ vs. both baselines (empirical gate) |
| **RQ2** | For **both** models and **both** subgroup families (regimes & stages):<br>1. $\text{CI}_{\text{lower}}(\Delta_{\text{error}}) > 0.01$ vs. `global_hcp`<br>2. $\text{CI}_{\text{lower}}(\Delta_{\text{error}}) > 0.01$ vs. `regime_hcp`<br>3. $\text{CI}_{\text{upper}}(E_{\text{worst}}) < 0.05$<br>4. $\text{CI}_{\text{upper}}(D_{\text{width}}) < 1.0$ cycle vs. both baselines<br>5. $\text{CI}_{\text{upper}}(D_{\text{score}}) < 1.0$ cycle vs. both baselines |
| **RQ3** | For **both** GBR and LSTM:<br>1. $\text{CI}_{\text{lower}}(\Delta_{\text{cost}}) > 0.20$ SCU vs. `matched_width_interval`<br>2. $\text{CI}_{\text{lower}}(\Delta_{\text{cost}}) > 0.20$ SCU vs. `widened_interval`<br>3. $\text{CI}_{\text{lower}}(\Delta_{\text{cost}}) > 0.20$ SCU vs. `point_safety_margin`<br>4. $\text{CI}_{\text{lower}}(\Delta_{\text{cost}}) > 0.20$ SCU vs. `earlier_intervention`<br>5. $\text{CI}_{\text{upper}}(E) < 0.05$ across marginal, regime, and stage coverage<br>6. Observed fleet failure rate increase $\Delta_{\text{fail}} \le 0.0$ vs. all 4 controls (empirical gate) |
| **RQ4** | 1. Weighted aggregate $\text{CI}_{\text{lower}}(\Delta_{\text{cost, agg}}) > 0.20$ SCU vs. both baselines<br>2. Weighted aggregate $\text{CI}_{\text{lower}}(\Delta_{\text{error, agg}}) > 0.01$ for regimes and stages vs. both baselines<br>3. Cell non-harm: $\text{CI}_{\text{lower}}(\Delta_{\text{cost}, k}) > -0.20$ SCU in all 6 cells vs. both baselines<br>4. Cell non-harm: $\text{CI}_{\text{lower}}(\Delta_{\text{error}, k}) > -0.01$ for regimes and stages in all 6 cells vs. both baselines<br>5. All cell-level safeguards (coverage ceilings, interval width/score noninferiority, failure safeguard) hold across all 6 cells |

### 5.3 Classification Definitions
- **Supported**: Every single required component condition passes.
- **Unsupported**: At least one required component condition fails (e.g., upper CI falls below margin or failure rate increases).
- **Inconclusive**: No condition fails, but at least one decision interval covers its practical-effect margin boundary, or inference is degenerate (zero-width interval). Boundary equality is classified as indeterminate. Observed failure rate equality passes its empirical safeguard.

---

## 6. Critical Methodological Boundaries

1. **Bootstrap Intervals are Asymptotic Approximations**: Cluster-bootstrap percentile intervals are asymptotic approximations. They do not constitute exact finite-sample confidence guarantees, particularly in small subgroup samples ($N_g \approx 10$) or non-smooth max operators.
2. **Point Estimate Traps**: Observing that a point estimate exceeds the margin ($\hat{\Delta} > 0.20$) while excluding zero ($\text{CI}_{\text{lower}} > 0.0$) is **NOT sufficient** to claim support. Support requires the lower bound of the 98.75% decision interval to strictly clear the margin ($\text{CI}_{\text{lower}} > 0.20$).
3. **No Secondary P-Values**: The confirmatory protocol relies exclusively on decision intervals evaluated against practical-effect margins. No supplementary p-value hypothesis tests form part of the confirmatory findings.
4. **Empirical Gate**: The observed failure safeguard ($\Delta_{\text{fail}} \le 0.0$) is an empirical gate, not a confidence-interval proof of population safety.
