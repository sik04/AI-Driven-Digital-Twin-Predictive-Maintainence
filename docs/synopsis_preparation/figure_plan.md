# Experimental Figure Plan and Visual Evidence Specifications

**Document Version**: `2.0 (v4 Audit Alignment)`  
**Reviewed Repository Baseline**: `c163bb279e7427b8f1b6e75955af4969ff9370fd`  
**Governing Standard**: Strict visual specifications for all publication figures (F1–F7). Native TikZ diagrams implemented for F1 and F2. No synthetic "result" curves or fabricated plots are created prior to verified experimental execution.

> **Status Statement**: Base predictors and conformal calibrators are implemented and frozen. The committed v4 pre-test audit reports PASS and PRETEST_READY. Held-out execution has not started, and RQ1–RQ4 outcomes remain pending. Development validation and audit results do not establish confirmatory maintenance benefit, subgroup reliability, or robustness.

---

## Figure F1: End-to-End Data, Model, Calibration, and Decision Architecture

- **Figure Identifier**: `FIG-01`
- **Caption Title**: Architecture of the IntelliTwin Prognostic Calibration and Sequential Maintenance Pipeline.
- **Scientific Purpose**: Illustrate the complete information flow from raw C-MAPSS multi-sensor telemetry, training-only preprocessor fitting, causal window construction ($w=30$), base model families (GBR and LSTM), reserved hierarchical conformal calibration, asymmetric decision-aware nonconformity inversion, and discrete-event sequential maintenance simulation.
- **Visual Design**: Native TikZ multi-tier block diagram (`latex/shared/figures/architecture.tex`):
  1. *Tier 1 (Data Layer)*: Raw run-to-failure trajectories partitioned by engine unit (50/20/10/20 train/cal/val/test: FD001 50/20/10/20, FD002 130/52/26/52, FD004 124/50/25/50). Training-only fitted z-score scalers ($s_{\text{train}}=\sigma_{\text{train}}$ if $\sigma > 0$ else $1.0$, `ddof=0`).
  2. *Tier 2 (Prognostic Layer)*: 30-cycle causal sliding windows ($t-29 \dots t$) mapped to flattened 510-dim vectors in C order (GBR) and $30 \times 17$ tensors (LSTM), producing point predictions $p = \max(0, \hat{y})$.
  3. *Tier 3 (Calibration Layer)*: Nonconformity score computation against uncapped $y_{\text{true}}$, exact engine-weighted quantiles with $m/(m+1)$ finite mass bounding, and asymmetric candidate parameter modulation ($\sigma(p), z(p), a(p), b(p)$).
  4. *Tier 4 (Decision Layer)*: Sequential evaluation of `lower_bound_one_cycle_policy` triggering `MAINTAIN_NOW` when $L(t) \le 1.0$ under the `primary_reference` scenario.
  5. *Held-Out Boundary*: Explicit visual demarcation indicating held-out test trajectories are isolated; true failure times are revealed only to offline evaluation routines.
- **Required Inputs**: Architectural specifications from `research/research_design/`.
- **Target Partition**: Architecture schematic (cross-partition).
- **Physical Units**: Operational cycles (time), sensor measurement units, Simulated Cost Units (SCU).
- **Current Status**: `IMPLEMENTED` (Compiled native TikZ figure in `latex/shared/figures/architecture.tex`, embedded in paper and thesis).

---

## Figure F2: Causal Temporal Windowing and Information Horizon Alignment

- **Figure Identifier**: `FIG-02`
- **Caption Title**: Causal Sliding-Window Formulation and RUL Target Definitions.
- **Scientific Purpose**: Clarify how temporal sequence windows are extracted causally without future data leakage, demonstrate the exact alignment between the LSTM sequential tensor ($30 \times 17$) and GBR flattened vector ($510$), and illustrate the critical distinction between capped training targets ($y_{\text{train}} = \min(y_{\text{true}}, 125)$) and uncapped evaluation targets ($y_{\text{true}} = T_i - t$).
- **Visual Design**: Native TikZ horizontal degradation timeline (`latex/shared/figures/causal_window.tex`):
  - Horizontal timeline from cycle 1 to failure cycle $T_i$.
  - Cycles 1–29 labeled as initialization/warm-up; zero padding is strictly prohibited (first prediction occurs at $t=30$).
  - An inspection window of length $w=30$ cycles ending at time $t$ showing sensor telemetry history $[t-29, \dots, t]$.
  - Information representations: $30 \times 17$ causal tensor for LSTM, flattened 510-dimensional vector in C order for GBR.
  - Target curves comparing the piecewise-linear capped training target (clamped at 125 cycles) against the true uncapped linear degradation slope reaching 0 at $T_i$.
- **Required Inputs**: Data specifications from `src/intellitwin/data/windowing.py` and ADR-012/ADR-013.
- **Target Partition**: Illustrative schematic based on training partition telemetry.
- **Physical Units**: Time (operational flight cycles), sensor values (standardized), RUL (cycles).
- **Current Status**: `IMPLEMENTED` (Compiled native TikZ figure in `latex/shared/figures/causal_window.tex`, embedded in paper and thesis).

---

## Figure F3: Representative Prediction Interval Trajectories Across Degradation Stages

- **Figure Identifier**: `FIG-03`
- **Caption Title**: Run-to-Failure Prediction Interval Trajectories for Global, Condition-Aware, and Proposed Decision-Aware Calibration.
- **Scientific Purpose**: Contrast the temporal evolution of prediction intervals $[L(t), U(t)]$ across the lifetime of a representative held-out test engine on FD002. Demonstrate how global conformal intervals have displayed width $p + q - \max(0, p-q)$ ($=2q$ only when $p \ge q$), how condition-aware intervals adjust with flight regime changes, and how the proposed decision-aware method ($\beta = -\ln 2 \approx -0.693147$, $\beta_{\text{code}} = -1$) modulates asymmetry.
- **Visual Design**: Three stacked subplots sharing the horizontal time axis ($t = 30 \dots T_i$):
  - *Top Subplot*: Global Conformal Calibration (`global_hcp`) showing point prediction $\hat{y}(t)$, symmetric error bounds $[L, U]$ (symmetric before clipping at zero), and ground-truth $y_{\text{true}}(t)$.
  - *Middle Subplot*: Condition-Aware Hierarchical Calibration (`regime_hcp`) showing regime-stratified step changes in interval width as operating regimes shift.
  - *Bottom Subplot*: Proposed Decision-Aware Calibration (`decision_aware_hcp`: $\gamma=2, \beta=-\ln 2$) illustrating the nondecreasing lower and upper endpoints relative to $\beta=0$ and the resulting replacement trigger at $L(t) \le 1.0$.
- **Interpretation Note**: At fixed $p$, $q$, and $\gamma$, negative $\beta$ decreases $a(p)$ and increases $b(p)$. The lower and upper endpoints are therefore nondecreasing relative to $\beta=0$. This does not establish earlier intervention or better maintenance utility because calibration thresholds are refitted and policy outcomes depend on the resulting trajectories.
- **Required Inputs**: Evaluated cycle-by-cycle prediction CSVs from held-out test engines under `UPD-02`.
- **Target Partition**: Held-out Test Partition (FD002 test engines).
- **Physical Units**: Horizontal axis: Operating Cycles ($t$); Vertical axis: Remaining Useful Life (cycles).
- **Current Status**: `PENDING_EXPERIMENT` (Plotted upon completion of held-out test execution).

---

## Figure F4: Subgroup Conditional Reliability Profiles (Regimes and Wear Stages)

- **Figure Identifier**: `FIG-04`
- **Caption Title**: Empirical Prediction Interval Coverage and Error across Operating Regimes and Lifecycle Wear Stages.
- **Scientific Purpose**: Evaluate Research Question 2 (RQ2) by exposing localized coverage vulnerabilities across the 6 C-MAPSS operating regimes ($C_1$–$C_6$, derived via K-means clustering on standardized operating settings, not named physical flight conditions) and 3 degradation lifecycle stages (Early, Mid, Late thirds).
- **Visual Design**: Two side-by-side grouped bar charts with horizontal dashed reference line at 90% nominal coverage and shaded gray bands indicating the $\pm 5\%$ descriptive reference band ($[0.85, 0.95]$):
  - *Panel A (Operating Regimes)*: Six clusters ($C_1$ to $C_6$) comparing empirical coverage across `global_hcp`, `regime_hcp`, and `decision_aware_hcp`.
  - *Panel B (Lifecycle Stages)*: Early, Mid, and Late stages comparing empirical coverage across the three methods.
  - *Decision Rule Note*: The shaded $[0.85, 0.95]$ region is a descriptive reference band; formal hypothesis decisions strictly require the upper 98.75% bootstrap decision interval bound of absolute coverage error to satisfy $E_{\text{worst}} < 0.05$.
- **Required Inputs**: Aggregated subgroup metrics output by `src/intellitwin/evaluation/metrics.py` under `UPD-02`.
- **Target Partition**: Held-out Test Partition (FD002 test engines).
- **Physical Units**: Horizontal axis: Subgroups; Vertical axis: Empirical Coverage Probability (PICP, %).
- **Current Status**: `PENDING_EXPERIMENT`.

---

## Figure F5: Maintenance Cost, In-Service Failure, and Wasted Life Trade-offs

- **Figure Identifier**: `FIG-05`
- **Caption Title**: Operational Cost Trade-offs: Comparing Preventive Replacement Cost, Failure Penalties, and Wasted Useful Life.
- **Scientific Purpose**: Evaluate Research Questions 1 and 3 (RQ1, RQ3) by decomposing total simulated maintenance expenditure into its constituent components: planned maintenance base cost ($C_{\text{PM}}$), unplanned in-service failure penalties ($C_{\text{FAIL}}$), and discarded useful life costs ($C_{\text{WASTE}} \cdot W$).
- **Visual Design**: Stacked bar chart comparing the three registered calibration methods and four frozen controls on FD002 under `primary_reference`:
  1. Global Conformal Baseline (`global_hcp`).
  2. Condition-Aware Baseline (`regime_hcp`).
  3. Proposed Decision-Aware Calibration (`decision_aware_hcp`).
  4. Matched-Width Interval Control (`matched_width_interval`: GBR $\lambda=0.92$, LSTM $\lambda=0.90$).
  5. Widened-Interval Control (`widened_interval`: $\lambda=1.00$, unscaled baseline width).
  6. Point Safety Margin Control (`point_safety_margin`: GBR $m=5$, LSTM $m=4$).
  7. Earlier-Intervention Control (`earlier_intervention`: $h=1$, matching baseline threshold).
  *(Note: Reactive and untuned point-threshold policies are excluded from the confirmatory comparator plot.)*
- **Required Inputs**: Simulator event logs generated by `src/intellitwin/simulator/engine.py` under `UPD-03`.
- **Target Partition**: Held-out Test Partition (FD002, `primary_reference` scenario).
- **Physical Units**: Vertical axis: Average Cost per Engine in Simulated Cost Units (SCU).
- **Current Status**: `PENDING_EXPERIMENT`.

---

## Figure F6: Confirmatory Effect-Size Decision Intervals (RQ1–RQ4)

- **Figure Identifier**: `FIG-06`
- **Caption Title**: Multiplicity-Adjusted Confirmatory Decision Intervals (98.75% Cluster Bootstrap) and Practical-Effect Thresholds.
- **Scientific Purpose**: Visualize the formal confirmatory hypothesis test decisions for RQ1, RQ2, RQ3, and RQ4. Demonstrate whether the empirical bootstrap distribution clears the frozen practical-effect margins ($\Delta_{\text{cost}} > 0.20$ SCU, $\Delta_{\text{error}} > 0.01$).
- **Visual Design**: Forest plot with separate panels for cost and coverage-error contrasts:
  - *Panel A (Cost Contrasts)*: Evaluates $\Delta_{\text{cost}}$ in SCU per engine. Practical threshold line at $+0.20$ SCU (RQ1, RQ3, RQ4) and non-harm threshold at $-0.20$ SCU (RQ4).
  - *Panel B (Coverage Error Contrasts)*: Evaluates $\Delta_{\text{error}}$ as a fraction (where $0.01 = 1.0$ percentage point). Practical threshold line at $+0.01$ (RQ2, RQ4) and non-harm threshold at $-0.01$ (RQ4).
  - *Bar Styling*:
    - Outer thin bar: 98.75% confirmatory decision interval (Bonferroni $\alpha = 0.0125$, quantiles $0.00625$ and $0.99375$).
    - Inner thick bar: 95% descriptive confidence interval (quantiles $0.025$ and $0.975$).
    - Central marker: Observed paired contrast estimate.
  - Explicit outcome badges indicating `Supported`, `Unsupported`, or `Inconclusive`.
- **Required Inputs**: Bootstrap quantiles from `src/intellitwin/evaluation/bootstrap.py` under `UPD-04`.
- **Target Partition**: Held-out Test Partitions across all 6 cells.
- **Physical Units**: Panel A: SCU per engine; Panel B: coverage error fraction (with percentage-point secondary labeling).
- **Current Status**: `PENDING_EXPERIMENT`.

---

## Figure F7: Interactive Demonstrator User Interface and Trajectory Replay

- **Figure Identifier**: `FIG-07`
- **Caption Title**: IntelliTwin Interactive Digital Twin Simulation Interface.
- **Scientific Purpose**: Illustrate the software demonstrator interface (Phase 9 milestone), demonstrating how the underlying research pipeline provides actionable decision-support to fleet maintenance engineers.
- **Visual Design**: High-resolution UI layout showing:
  - Fleet navigation sidebar selecting engine ID and dataset partition.
  - Real-time degradation trajectory chart rendering live cycle replay with calibrated conformal prediction bounds.
  - Flight envelope regime indicators showing current operating conditions ($C_1$–$C_6$).
  - Decision banner indicating whether the policy triggers `CONTINUE` or `MAINTAIN_NOW`.
  - Cumulative maintenance cost and wasted life summary gauge.
- **Required Inputs**: Demonstrator frontend execution and screenshot captures under `UPD-06`.
- **Target Partition**: Software demonstrator prototype.
- **Physical Units**: UI display units (cycles, SCU, normalized sensor readings).
- **Current Status**: `PENDING_DEVELOPMENT` (Tracked under `UPD-06`).
