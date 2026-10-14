# Experimental Figure Plan and Visual Evidence Specifications

**Document Version**: `1.0`  
**Governing Standard**: Strict visual specifications for all publication figures (F1–F7). No synthetic "result" curves or fabricated plots are created prior to verified experimental execution.

---

## Figure F1: End-to-End Data, Model, Calibration, and Decision Architecture

- **Figure Identifier**: `FIG-01`
- **Caption Title**: Architecture of the IntelliTwin Prognostic Calibration and Sequential Maintenance Pipeline.
- **Scientific Purpose**: Illustrate the complete information flow from raw C-MAPSS multi-sensor telemetry, training-only preprocessor fitting, causal window construction ($W=30$), dual model families (GBR and LSTM), reserved hierarchical conformal calibration, asymmetric decision-aware nonconformity inversion, and discrete-event sequential maintenance simulation.
- **Visual Design**: Multi-tier block diagram:
  1. *Tier 1 (Data Layer)*: Raw run-to-failure trajectories partitioned by engine unit (50/20/10/20) into Training, Calibration, Validation, and Held-Out Test sets.
  2. *Tier 2 (Prognostic Layer)*: 30-cycle causal sliding windows mapped to flattened 510-dim vectors (GBR) and 30×17 tensors (LSTM), producing point predictions $\hat{y} \ge 0$.
  3. *Tier 3 (Calibration Layer)*: Nonconformity score computation against uncapped $y_{\text{true}}$, exact engine-weighted quantiles with $m/(m+1)$ finite mass bounding, and asymmetric candidate parameter modulation ($\sigma(p), z(p), a(p), b(p)$).
  4. *Tier 4 (Decision Layer)*: Sequential evaluation of `lower_bound_one_cycle_policy` triggering `MAINTAIN_NOW` when $L(t) \le 1.0$ under the `primary_reference` scenario.
- **Required Inputs**: Architectural specifications from `research/research_design/`.
- **Target Partition**: Architecture schematic (cross-partition).
- **Physical Units**: Operational cycles (time), sensor measurement units, Simulated Cost Units (SCU).
- **Current Status**: Complete conceptual and TikZ diagram specification in `latex/paper/sections/methodology.tex`.

---

## Figure F2: Causal Temporal Windowing and Information Horizon Alignment

- **Figure Identifier**: `FIG-02`
- **Caption Title**: Causal Sliding-Window Formulation and Dual-Horizon Target Construction.
- **Scientific Purpose**: Clarify how temporal sequence windows are extracted causally without future data leakage, demonstrate the exact alignment between the LSTM sequential tensor $(30 \times 17)$ and GBR flattened vector $(510,)$, and illustrate the critical distinction between capped training targets ($y_{\text{train}} \le 125$) and uncapped evaluation targets ($y_{\text{true}} = T_i - t$).
- **Visual Design**:
  - Horizontal degradation timeline from cycle 1 to failure cycle $T_i$.
  - An inspection window of length $W=30$ cycles ending at time $t$ showing sensor telemetry history $[t-29, \dots, t]$.
  - Callout illustrating that zero padding is prohibited (first prediction occurs at $t=30$).
  - Target curves comparing the piecewise-linear capped target (clamped at 125 cycles during healthy operation) against the true uncapped linear degradation slope reaching 0 at $T_i$.
- **Required Inputs**: Data loader specifications from `src/intellitwin/data/window.py` and ADR-012/ADR-013.
- **Target Partition**: Illustrative schematic based on training partition telemetry.
- **Physical Units**: Time (operational flight cycles), sensor values (standardized), RUL (cycles).
- **Current Status**: Complete diagram specification in `latex/paper/sections/problem_formulation.tex`.

---

## Figure F3: Representative Prediction Interval Trajectories Across Degradation Stages

- **Figure Identifier**: `FIG-03`
- **Caption Title**: Run-to-Failure Prediction Interval Trajectories for Global, Condition-Aware, and Proposed Decision-Aware Calibration.
- **Scientific Purpose**: Contrast the temporal evolution of prediction intervals $[L(t), U(t)]$ across the lifetime of a representative held-out test engine on FD002. Demonstrate how global conformal intervals maintain constant width regardless of wear, how condition-aware intervals fluctuate with flight envelope shifts, and how the proposed decision-aware method ($\beta = -1$) dynamically alters asymmetry near end of life.
- **Visual Design**: Three stacked subplots sharing the horizontal time axis ($t = 30 \dots T_i$):
  - *Top Subplot*: Global Conformal Calibration (`global_hcp`) showing point prediction $\hat{y}(t)$, symmetric error bounds $[L, U]$, and ground-truth $y_{\text{true}}(t)$.
  - *Middle Subplot*: Condition-Aware Hierarchical Calibration (`regime_hcp`) showing regime-stratified step changes in interval width as flight envelopes shift.
  - *Bottom Subplot*: Proposed Decision-Aware Calibration (`decision_aware_hcp`: $\gamma=2, \beta=-1$) illustrating the narrowing of the lower-side margin $q \cdot a(p)$ as $p \to 0$ and the resulting replacement trigger at $L(t) \le 1.0$.
- **Required Inputs**: Evaluated cycle-by-cycle prediction CSVs from held-out test engines under `UPD-02`.
- **Target Partition**: Held-out Test Partition (FD002 test engines).
- **Physical Units**: Horizontal axis: Operating Cycles ($t$); Vertical axis: Remaining Useful Life (cycles).
- **Current Status**: `PENDING_EXPERIMENT` (Plotted upon completion of held-out test execution).

---

## Figure F4: Subgroup Conditional Reliability Profiles (Regimes and Wear Stages)

- **Figure Identifier**: `FIG-04`
- **Caption Title**: Empirical Prediction Interval Coverage and Error across Operating Regimes and Lifecycle Wear Stages.
- **Scientific Purpose**: Evaluate Research Question 2 (RQ2) by exposing localized coverage vulnerabilities across the 6 C-MAPSS operating regimes ($C_1$–$C_6$) and 3 degradation lifecycle stages (Early, Mid, Late thirds).
- **Visual Design**: Two side-by-side grouped bar charts with horizontal dashed reference line at 90% nominal coverage and shaded gray bands indicating the $\pm 5\%$ acceptance ceiling ($[0.85, 0.95]$):
  - *Panel A (Operating Regimes)*: Six clusters ($C_1$ to $C_6$) comparing empirical coverage across `global_hcp`, `regime_hcp`, and `decision_aware_hcp`.
  - *Panel B (Lifecycle Stages)*: Early, Mid, and Late stages comparing empirical coverage across the three methods.
- **Required Inputs**: Aggregated subgroup metrics output by `src/intellitwin/evaluation/metrics.py` under `UPD-02`.
- **Target Partition**: Held-out Test Partition (FD002 test engines).
- **Physical Units**: Horizontal axis: Subgroups; Vertical axis: Empirical Coverage Probability (PICP, %).
- **Current Status**: `PENDING_EXPERIMENT`.

---

## Figure F5: Maintenance Cost, In-Service Failure, and Wasted Life Trade-offs

- **Figure Identifier**: `FIG-05`
- **Caption Title**: Operational Cost Trade-offs: Comparing Preventive Replacement Cost, Failure Penalties, and Wasted Useful Life.
- **Scientific Purpose**: Evaluate Research Questions 1 and 3 (RQ1, RQ3) by decomposing total simulated maintenance expenditure into its constituent components: planned maintenance base cost ($C_{\text{PM}}$), unplanned in-service failure penalties ($C_{\text{FAIL}}$), and discarded useful life costs ($C_{\text{WASTE}} \cdot W$).
- **Visual Design**: Stacked bar chart comparing:
  1. Reactive Maintenance Baseline (run-to-failure).
  2. Point-Prediction Deterministic Policy ($\hat{y} \le 1$).
  3. Global Conformal Baseline (`global_hcp`).
  4. Condition-Aware Baseline (`regime_hcp`).
  5. Proposed Decision-Aware Calibration (`decision_aware_hcp`).
  6. The four Matched-Conservatism Controls (matched width, widened interval, point safety margin, earlier intervention).
- **Required Inputs**: Simulator event logs generated by `src/intellitwin/simulator/engine.py` under `UPD-03`.
- **Target Partition**: Held-out Test Partition (FD002, `primary_reference` scenario).
- **Physical Units**: Vertical axis: Average Cost per Engine in Simulated Cost Units (SCU).
- **Current Status**: `PENDING_EXPERIMENT`.

---

## Figure F6: Confirmatory Effect-Size Decision Intervals (RQ1–RQ4)

- **Figure Identifier**: `FIG-06`
- **Caption Title**: Multiplicity-Adjusted Confirmatory Decision Intervals (98.75% Cluster Bootstrap) and Practical-Effect Thresholds.
- **Scientific Purpose**: Visualize the formal confirmatory hypothesis test decisions for RQ1, RQ2, RQ3, and RQ4. Demonstrate whether the empirical bootstrap distribution clears the frozen practical-effect margins ($\Delta_{\text{cost}} > 0.20$ SCU, $\Delta_{\text{error}} > 0.01$).
- **Visual Design**: Forest plot with horizontal error bars:
  - Outer thin bar: 98.75% confirmatory decision interval (Bonferroni $\alpha = 0.0125$).
  - Inner thick bar: 95% descriptive confidence interval.
  - Central marker: Observed paired contrast from the evaluation output.
  - Vertical red dashed lines: Frozen practical-effect thresholds ($+0.20$ SCU for cost, $+0.01$ for error reduction, $-0.20$ for non-harm).
  - Explicit outcome badges indicating `Supported`, `Unsupported`, or `Inconclusive`.
- **Required Inputs**: Bootstrap quantiles from `src/intellitwin/evaluation/bootstrap.py` under `UPD-04`.
- **Target Partition**: Held-out Test Partitions across all 6 cells.
- **Physical Units**: Horizontal axis: Effect Size Contrast ($\Delta_{\text{cost}}$ in SCU; $\Delta_{\text{error}}$ in percentage points).
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
