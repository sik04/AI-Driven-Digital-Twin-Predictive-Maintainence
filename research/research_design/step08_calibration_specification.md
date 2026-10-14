# Step 8 Specification: Engine-Weighted Decision-Aware Hierarchical Conformal Calibration

- **Protocol Version**: `step08-v1`
- **Schema Version**: `step08-calibrator-v1`
- **Status**: Completed & Reverified (Protocol step08-v1; ADR-021 & ADR-022)
- **Governing ADR**: ADR-021 and ADR-022 in `research/decision_log.md`
- **Target Subsystem**: `src/intellitwin/uncertainty/`, `src/intellitwin/decision/`
- **Scope**: Multi-dataset, two-family, five-seed conformal calibration matrix (3 datasets x 2 families x 5 seeds x 3 methods = 90 calibrator bundles; 270 coverage configurations).

---

## 1. Executive Summary & Research Context

Following the freeze and verification of the 30 base predictors in Step 7 (ADR-020), Step 8 establishes the formal conformal calibration methodology. The objective is to construct finite-sample valid prediction intervals for remaining useful life (RUL) under clustered, sequential industrial degradation data, while adapting interval asymmetry to downstream maintenance decisions.

This specification prespecifies:
1. **Three Conformal Methods**:
   - `global_hcp`: Global engine-weighted hierarchical conformal prediction baseline.
   - `regime_hcp`: Condition-aware (operating-regime-stratified) hierarchical conformal prediction baseline.
   - `decision_aware_hcp`: Proposed asymmetric, state-dependent decision-aware conformal calibration.
2. **Exact Nine-Candidate Parameter Space**: A restricted grid over scaling ($\gamma \in \{0, 1, 2\}$) and asymmetry ($\beta_{\text{code}} \in \{-1, 0, 1\}$).
3. **Validation-Only Selection**: Leave-one-engine-out cross-validation diagnostics on validation engines across five fixed seeds to select exactly one configuration per dataset/model-family cell.
4. **Authoritative Selection Freeze Gate**: Mandatory commit of selection manifests prior to final calibration fitting on reserved calibration engines.
5. **Exact Rational Engine-Weighted Quantiles**: Exact hierarchical quantile computation with engine weighting and finite/infinite boundary support based on Lee et al. (2023).
6. **Shared Downstream Maintenance Rule**: `lower_bound_one_cycle_policy` operating under `primary_reference` cost scenario.

---

## 2. Mathematical Formulations of the Three Methods

Let $p \ge 0$ denote the frozen base model point prediction, and $y = \text{rul\_true} \ge 0$ denote the ground-truth uncapped RUL. Let $g \in \mathcal{G}$ denote the discrete operating regime observed at cycle $t$.

### 2.1 Global Hierarchical Conformal Prediction (`global_hcp`)
- **Nonconformity Score**: Absolute residual:
  $$s(p, y) = |y - p|$$
- **Threshold**: Fit a single global engine-weighted hierarchical threshold $q$ for nominal coverage $1 - \alpha \in \{0.80, 0.90, 0.95\}$.
- **Prediction Interval**:
  $$L = \max(0, p - q), \quad U = p + q$$

### 2.2 Condition-Aware Hierarchical Conformal Prediction (`regime_hcp`)
- **Nonconformity Score**: Absolute residual:
  $$s(p, y) = |y - p|$$
- **Threshold**: Fit separate regime-specific hierarchical thresholds $q_g$ for each operating regime $g$. Fit a global threshold $q_{\text{global}}$ for fallback routing.
- **Prediction Interval**:
  $$L = \max(0, p - q_g), \quad U = p + q_g$$
- **FD001 Equivalence**: FD001 contains exactly one operating regime. When no fallback distinction is needed, `regime_hcp` and `global_hcp` are mathematically and numerically identical.

### 2.3 Proposed Decision-Aware Conformal Prediction (`decision_aware_hcp`)
The proposed method modulates interval width and asymmetry as a function of the point prediction $p$:
$$\sigma(p) = \left(1 + \frac{p}{125}\right)^\gamma$$
$$z(p) = \exp\left(-\frac{p}{20}\right)$$
$$a(p) = \sigma(p) \exp\left(\beta z(p)\right)$$
$$b(p) = \sigma(p) \exp\left(-\beta z(p)\right)$$
where $\beta = \beta_{\text{code}} \ln(2)$ with $\beta_{\text{code}} \in \{-1, 0, 1\}$ and $\gamma \in \{0, 1, 2\}$.

- **Nonconformity Score**:
  $$\text{score}(p, y) = \max\left(\frac{p - y}{a(p)}, \frac{y - p}{b(p)}, 0\right)$$
- **Score Inversion / Prediction Interval**:
  $$L = \max\left(0, p - q_g \cdot a(p)\right), \quad U = p + q_g \cdot b(p)$$
  where $q_g$ is the regime-specific hierarchical threshold (with global fallback $q_{\text{global}}$).
- **Asymmetry Mechanics ($\beta < 0$)**: Holding $p$, $q$, and $\gamma$ fixed, when $\beta < 0$:
  - $a(p)$ decreases, and $b(p)$ increases.
  - The lower bound $L = \max(0, p - q \cdot a(p))$ rises or remains at zero after clipping.
  - The upper bound $U = p + q \cdot b(p)$ rises.
  - This mathematical fact does not justify claiming earlier preventive maintenance or protection against late failure; refitted $q$ affects empirical comparisons between candidates, and observed outcomes must be reported from measured results.
- **Identity Candidate Equivalence**: When $\gamma = 0$ and $\beta_{\text{code}} = 0$, $a(p) = 1$ and $b(p) = 1$, yielding $\text{score}(p, y) = |y - p|$. Thus, candidate `gamma0_beta0` reproduces `regime_hcp` numerically.
- **Reference Scales**: The constants $125$ and $20$ are prespecified reference scales ($125$ is the standard training RUL cap scale; $20$ is the characteristic end-of-life decision transition scale). The $20$-cycle scale is not a maintenance threshold or an asserted optimal replacement cycle.

---

## 3. Nine Candidate Parameter Grid

The candidate grid is strictly restricted to exactly 9 combinations:

| Candidate ID | $\gamma$ | $\beta_{\text{code}}$ | $\beta = \beta_{\text{code}} \ln(2)$ | Description |
| :--- | :---: | :---: | :---: | :--- |
| `gamma0_beta0` | 0 | 0 | $0.000000$ | Identity candidate (matches `regime_hcp`) |
| `gamma0_betam1` | 0 | -1 | $-0.693147$ | Constant scale, asymmetric conservative upper |
| `gamma0_betap1` | 0 | +1 | $+0.693147$ | Constant scale, asymmetric conservative lower |
| `gamma1_beta0` | 1 | 0 | $0.000000$ | Linear scale, symmetric |
| `gamma1_betam1` | 1 | -1 | $-0.693147$ | Linear scale, asymmetric conservative upper |
| `gamma1_betap1` | 1 | +1 | $+0.693147$ | Linear scale, asymmetric conservative lower |
| `gamma2_beta0` | 2 | 0 | $0.000000$ | Quadratic scale, symmetric |
| `gamma2_betam1` | 2 | -1 | $-0.693147$ | Quadratic scale, asymmetric conservative upper |
| `gamma2_betap1` | 2 | +1 | $+0.693147$ | Quadratic scale, asymmetric conservative lower |

No neural calibration networks, extra features, regime-specific candidate parameters, or additional search rounds are permitted.

---

## 4. Exact Engine-Weighted Quantiles & Rational Boundary Arithmetic

### 4.1 Engine Weighting Principle
To account for unequal trajectory lengths across engines, calibration mass is balanced equally across contributing engines rather than individual time windows. For $m$ contributing engines:
- Engine $i$ contains $n_i$ valid endpoints.
- Each endpoint within engine $i$ receives mass $\frac{1}{m \cdot n_i}$.

### 4.2 Development Empirical CDF & Threshold
For leave-one-engine-out validation development:
$$F_{\text{dev}}(q) = \frac{1}{m} \sum_{i=1}^m \frac{\sum_{t=1}^{n_i} \mathbb{I}(s_{it} \le q)}{n_i}$$
The development threshold is the smallest observed score $q$ satisfying $F_{\text{dev}}(q) \ge 1 - \alpha$.

### 4.3 Final Hierarchical Finite-Score Mass & Threshold
Following Lee, Barber, & Willett (arXiv:2306.06342v4), to establish hierarchical exchangeability guarantees for a new unseen engine, total finite mass is bounded by $\frac{m}{m+1}$, with remaining mass $\frac{1}{m+1}$ placed at $+\infty$:
$$F_{\text{final}}(q) = \frac{1}{m + 1} \sum_{i=1}^m \frac{\sum_{t=1}^{n_i} \mathbb{I}(s_{it} \le q)}{n_i}$$
The final threshold is the smallest score $q$ satisfying $F_{\text{final}}(q) \ge 1 - \alpha$. If no finite score satisfies this condition, the mathematical threshold is $+\infty$.

### 4.4 Exact Rational Arithmetic Verification
To eliminate floating-point representation error:
- Exact coverage targets: $80\% = \frac{4}{5}$, $90\% = \frac{9}{10}$, $95\% = \frac{19}{20}$.
- Cumulative mass is computed and verified using `fractions.Fraction`.
- The chosen threshold $q^*$ must satisfy $F(q^*) \ge \text{target}$ while the preceding distinct score $q_{\text{prev}}$ satisfies $F(q_{\text{prev}}) < \text{target}$.
- This ensures exact boundary determination (e.g., $m=19$ engines at $95\%$ coverage).

---

## 5. Fallback Routing & Insufficient Support

### 5.1 Regime Support Rules
For final hierarchical calibration at coverage level $1 - \alpha$, regime $g$ requires:
$$m_g \ge \max\left(10, \left\lceil \frac{1}{\alpha} \right\rceil - 1\right)$$
- At $80\%$ ($\alpha = 0.20$): $m_g \ge \max(10, 4) = 10$ engines.
- At $90\%$ ($\alpha = 0.10$): $m_g \ge \max(10, 9) = 10$ engines.
- At $95\%$ ($\alpha = 0.05$): $m_g \ge \max(10, 19) = 19$ engines.

If this support requirement fails or the regime is unobserved in calibration:
- Fall back to the global threshold of the same method at the same coverage level.
- Record `fallback_used = True`, requested regime, engine count, and fallback reason.
- Never claim regime-specific coverage for fallback intervals.
- An invalid regime outside the dataset vocabulary is rejected with `ValueError`.

### 5.2 Global Support Failure
If the global pool lacks sufficient support (threshold $= +\infty$):
- The final bundle fitter raises `InsufficientCalibrationSupport`.
- Infinite bounds are never emitted to the maintenance simulator or downstream consumers.
- No artificial capping at $125$ is applied to upper bounds.

---

## 6. Shared Maintenance Benchmark Policy

- **Policy**: `lower_bound_one_cycle_policy`
- **Decision Rule**:
  $$\text{Action}(t) = \begin{cases} \text{MAINTAIN\_NOW} & \text{if } \text{lower\_rul} \le 1.0 \\ \text{CONTINUE} & \text{otherwise} \end{cases}$$
- **Operational Window**: Evaluated strictly at cycles $t \in [30, T-1]$. At terminal cycle $T$, failure occurs if not maintained earlier.
- **Episode Termination**: Episode stops immediately upon maintenance action.
- **Cost Scenario**: Frozen `primary_reference` scenario:
  - $C_{\text{PM}} = 1.0$ (Planned Replacement Cost)
  - $C_{\text{FAIL}} = 5.0$ (Unplanned Failure Penalty)
  - $C_{\text{WASTE}} = 0.20$ (Cost per unused cycle of true RUL)
- **Status**: This policy is a prespecified operational benchmark, not an asserted optimal policy or absolute safety guarantee.

---

## 7. Validation-Only Candidate Selection Protocol

Candidate selection is performed strictly on validation data across all five model seeds:
1. **Leave-One-Engine-Out Fitting**: For each held-out validation engine $j$, compute empirical thresholds using the remaining validation engines (requiring $\ge 10$ other engines for regime thresholds).
2. **Sequential Maintenance Replay**: Evaluate `lower_bound_one_cycle_policy` over cycles $30 \dots T-1$.
3. **Metric Aggregation**:
   - Aggregate metrics per engine across seeds, then equally across engines.
   - Regime coverage is averaged across seeds for contributing engines, then averaged across contributing engines ($\ge 10$ validation engines required for regime eligibility).
4. **Feasibility Filters**:
   - $0.85 \le \text{marginal PICP} \le 0.95$
   - $0.85 \le \text{PICP}(g) \le 0.95$ for all eligible regimes
   - $\text{MPIW}_{\text{cand}} - \text{MPIW}_{\text{regime}} \le 1.0$ cycle
   - $\text{IS}_{\text{cand}} - \text{IS}_{\text{regime}} \le 1.0$ cycle
   - $\text{Failure Rate} \le \text{Failure Rate}(\text{global\_hcp})$
   - $\text{Failure Rate} \le \text{Failure Rate}(\text{regime\_hcp})$
5. **Optimization & Tie-Breaking**:
   - Minimize mean maintenance cost under `primary_reference`.
   - Ties within $10^{-8}$ SCU broken by: (1) identity candidate, (2) smaller $\gamma$, (3) smaller $|\beta|$, (4) smaller signed $\beta$.
6. **Fallback if No Feasible Candidate**:
   - Select `gamma0_beta0` with status `fallback_no_feasible_candidate`.

---

## 8. Selection Freeze Gate & Immutability

1. Candidate selection writes 6 cell-level selection records and a consolidated `selection_freeze.json`.
2. The selection-freeze artifact is committed to Git before final calibration.
3. The final calibration runner verifies Git commit status and artifact hashes, refusing execution if uncommitted or modified.

---

## 9. Limitations & Scientific Claim Boundaries

- **Exchangeability**: Hierarchical conformal guarantees rely on exchangeability across engines. Sequential degradation windows within an engine are autocorrelated and non-exchangeable.
- **Stratification**: Lifetime-stratified splitting does not theoretically guarantee exchangeability.
- **No Pointwise Guarantees**: No claim of exact coverage at individual cycles, lifecycle stages, or stopping times is made.
- **Development vs. Confirmatory**: Validation diagnostics are developmental and must not be reported as confirmatory proof of generalization or superiority.
- **Zero Failures**: Zero observed simulation failures in validation does not imply zero risk in general operations.
- **Step Completion**: Completion of Step 8 requires rigorous implementation and auditing, not favorable experimental outcomes.

---

## 10. Literature Citations

1. Yonghoon Lee, Rina Foygel Barber, Rebecca Willett, "Distribution-free inference with hierarchical data," *arXiv:2306.06342v4*, 2023. [https://arxiv.org/html/2306.06342v4](https://arxiv.org/html/2306.06342v4)
2. "Utility-Directed Conformal Prediction: A Decision-Aware Framework for Actionable Uncertainty Quantification," *ICLR 2025*. [https://proceedings.iclr.cc/paper_files/paper/2025/hash/0c6b452f1bbfb6905f6bac957d73b321-Abstract-Conference.html](https://proceedings.iclr.cc/paper_files/paper/2025/hash/0c6b452f1bbfb6905f6bac957d73b321-Abstract-Conference.html)
3. Robinson et al., "Risk-aware remaining useful life prediction," *International Journal of Prognostics and Health Management*, 2023. [https://www.papers.phmsociety.org/index.php/ijphm/article/view/4724](https://www.papers.phmsociety.org/index.php/ijphm/article/view/4724)
