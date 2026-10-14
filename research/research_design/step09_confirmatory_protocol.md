# Step 9 Confirmatory Evaluation Protocol Specification (Roadmap Phase 7)

- **Protocol Version**: `step09-v1`
- **Schema Version**: `step09-protocol-v1`
- **Stage**: Pre-Test Confirmatory Protocol Freeze
- **Date**: 2026-10-13
- **Baseline Review SHA**: `f1edce7fdf48b45513ff90a680da49701451d9cb`
- **Status**: Complete — Pre-Test Confirmatory Machinery Frozen (Held-out execution strictly pending)

---

## 1. Scope, Purpose, and Preregistration Standard

This document establishes the definitive, immutable pre-test confirmatory protocol for **Step 9 (Roadmap Phase 7)** of the IntelliTwin predictive maintenance research project.

In accordance with confirmatory empirical standards:
1. **Pre-Test Lock**: All experimental matrices, model choices, calibration thresholds, benchmark control grids, control parameter choices, statistical inference procedures, hypothesis decision thresholds, and output file schemas are locked prior to accessing or processing held-out test trajectories.
2. **Strict Boundary**: This stage develops and validates evaluation software on the validation partition only. No official NASA test windows, held-out test trajectories, or unmitigated failure labels are prepared, processed, or evaluated in this stage.
3. **Numbering Convention**: This stage is designated **Step 9 / roadmap Phase 7** to eliminate historical step/phase numbering ambiguities.

---

## 2. Primary Method and Experiment Matrix

The primary evaluation matrix consists of 810 method/seed/coverage/scenario configurations:
- **Datasets (3)**: C-MAPSS sub-corpora `FD001`, `FD002`, `FD004`. (`FD003` is excluded from the primary scope).
- **Model Families (2)**: Gradient Boosted Regressor (`GBR`) and Long Short-Term Memory network (`LSTM`).
- **Seeds (5)**: `2026`, `2027`, `2028`, `2029`, `2030`.
- **Primary Methods (3)**:
  1. `global_hcp`: Global engine-weighted hierarchical conformal baseline.
  2. `regime_hcp`: Condition-aware hierarchical conformal baseline.
  3. `decision_aware_hcp`: Proposed asymmetric decision-aware hierarchical conformal method.
- **Calibrators**: Uses the existing 90 frozen calibrator bundles fitted in Step 8 (ADR-021 / ADR-022) without refitting or post-hoc adjustments.
- **Nominal Coverage Levels (3)**:
  - `0.90` (90%): **Confirmatory Primary Coverage** governing RQ1–RQ4 hypothesis decisions.
  - `0.80` (80%) and `0.95` (95%): **Descriptive Secondary Coverages** for sensitivity analysis.
- **Cost Scenarios (3)**:
  - `primary_reference` ($C_{\text{pm}}=1.0$, $C_{\text{fail}}=5.0$, $C_{\text{waste}}=0.20$, $r_{\text{equal}}=20.0$): **Confirmatory Primary Scenario** governing RQ1–RQ4 hypothesis decisions.
  - `failure_sensitive` ($C_{\text{pm}}=1.0$, $C_{\text{fail}}=10.0$, $C_{\text{waste}}=0.20$, $r_{\text{equal}}=45.0$): Descriptive sensitivity scenario.
  - `waste_sensitive` ($C_{\text{pm}}=1.0$, $C_{\text{fail}}=5.0$, $C_{\text{waste}}=0.40$, $r_{\text{equal}}=10.0$): Descriptive sensitivity scenario.
- **Maintenance Policy**:
  - `lower_bound_one_cycle_policy`: Decision policy triggers `MAINTAIN_NOW` if and only if $L \le 1.0$ cycle; otherwise `CONTINUE`.

$$\text{Total Primary Configurations} = 3 \text{ datasets} \times 2 \text{ models} \times 5 \text{ seeds} \times 3 \text{ methods} \times 3 \text{ coverages} \times 3 \text{ scenarios} = 810$$

---

## 3. Benchmark Control Families and Parameter Grids (RQ3)

To test Research Question 3 (RQ3)—whether proposed benefits stem from decision-awareness rather than general conservatism—four named benchmark controls spanning three control families are prespecified for dataset `FD002`:

### 3.1 Named Benchmark Controls
1. **`matched_width_interval`** (Interval-control family, Representative A):
   - Derives bounds from frozen baseline source: $q = U_{\text{source}} - p$, $L_\lambda = \max(0, p - \lambda q)$, $U_\lambda = p + \lambda q$.
   - Search grid: $\lambda = k/100$ for $k=1,\dots,400$ plus $\{5, 6, 8, 12, 16\}$.
   - Target: Proposed method's engine-weighted, 5-seed-averaged validation MPIW.
   - Selected candidate minimizes $| \text{MPIW}(\lambda) - \text{MPIW}_{\text{target}} |$ within $10^{-8}$ of the minimum error. Tie-breaking retains candidates with mean cost within $10^{-8}$ of minimum cost, then smaller $\lambda$, then `global_hcp` before `regime_hcp`.
   - Verified parameter selections: GBR $\lambda=0.92$ (`global_hcp`); LSTM $\lambda=0.90$ (`regime_hcp`).
2. **`widened_interval`** (Interval-control family, Representative B):
   - Uses same formulation with $\lambda \ge 1.0$: $\lambda = k/100$ for $k=100,\dots,400$ plus $\{5, 6, 8, 12, 16\}$.
   - Minimizes validation maintenance cost under `primary_reference`.
   - Verified parameter selections: GBR $\lambda=1.00$ (`regime_hcp`); LSTM $\lambda=1.00$ (`global_hcp`).
3. **`point_safety_margin`** (Point-prediction safety buffer family):
   - Grid: $m \in \{0, 1, \dots, 250\}$ cycles.
   - Policy: `MAINTAIN_NOW` iff $p \le 1 + m$.
   - Operates strictly on point prediction $p$; does not fabricate conformal coverage.
   - Verified parameter selections: GBR $m=5$; LSTM $m=4$.
4. **`earlier_intervention`** (Earlier intervention threshold family):
   - Grid: $h \in \{1, 2, \dots, 251\}$ cycles.
   - Policy: `MAINTAIN_NOW` iff $L_{\text{source}} \le h$.
   - Verified parameter selections: GBR $h=1$ (`regime_hcp`); LSTM $h=1$ (`global_hcp`).

$$\text{Total RQ3 Control Configurations} = 1 \text{ dataset (FD002)} \times 2 \text{ models} \times 5 \text{ seeds} \times 4 \text{ controls} \times 1 \text{ coverage (0.90)} \times 3 \text{ scenarios} = 120$$

---

## 4. Sequential Simulator Adapter and Output Contracts

1. **Trajectory Continuity**:
   - Endpoints run from cycle 30 through terminal lifetime $T$.
   - Maintenance decisions occur on observable endpoints 30 through $T-1$.
   - Terminal cycle $T$ is reserved for the unmitigated failure event (if no PM was executed by $T-1$). No maintenance action occurs at $T$.
2. **Observability Safeguard**:
   - The decision policy receives `PredictionState(engine_id, cycle, point_rul, lower_rul, upper_rul, regime)` only.
   - True RUL, terminal lifetime $T$, future cycles, lifecycle stage, and cost oracle information are strictly inaccessible to the policy.
3. **Early PM Diagnostic**:
   - Cost-inefficient early PM is flagged when PM occurs and wasted RUL $W > r_{\text{equal}}$ ($r_{\text{equal}} \in \{20, 45, 10\}$). Equality does not count.

---

## 5. Statistical Inference Protocol

1. **Stratified Engine-Cluster Bootstrap**:
   - Replicates: $B = 10,000$.
   - Stratification: Lifetime-quartile strata (Q1, Q2, Q3, Q4) fixed from frozen split manifests.
   - Engine sorting: Ascending by engine ID within each stratum.
   - PRNG: `np.random.Generator(PCG64(SeedSequence([2026, 6, dataset_number])))`.
   - Multiplicity: Duplicate sampled engines retain multiplicity; never deduplicated into sets.
   - Shared streams: Replicate draws are reused across all models, seeds, methods, and metrics within each dataset.
2. **Confidence Intervals**:
   - Method: `numpy.quantile(..., method="linear")`.
   - Descriptive intervals: $[0.025, 0.975]$ (95% CI).
   - Decision intervals: $[0.00625, 0.99375]$ (Bonferroni-adjusted decision intervals).
3. **Missing-Group Bounds Propagation**:
   - Eligible subgroups require $\ge 10$ distinct engines with evaluated endpoints in the partition.
   - Missing groups in a replicate contribute conservative bound $[0, 0.90]$.
   - Propagated through contrasts: $\Delta_{\text{lower}} = B_{\text{lower}} - P_{\text{upper}}$, $\Delta_{\text{upper}} = B_{\text{upper}} - P_{\text{lower}}$.
   - Number of affected replicates is explicitly recorded.
4. **RQ Component Decision Rules**:
   - Improvement ($\Delta > \text{margin}$): `PASS` if lower bound $> \text{margin}$; `FAIL` if upper bound $< \text{margin}$; otherwise `INDETERMINATE`.
   - Noninferiority ($\text{Metric} < \text{margin}$): `PASS` if upper bound $< \text{margin}$; `FAIL` if lower bound $> \text{margin}$; otherwise `INDETERMINATE`.
   - Boundary equality or degenerate zero-width interval: `INDETERMINATE`.
   - Observed Failure Safeguard: Exact counts over identical grid; proposed $\le$ baseline passes (`PASS`), increase fails (`FAIL`).
   - Intersection-Union Testing (IUT): Any `FAIL` $\implies \text{UNSUPPORTED}$; none fail and any `INDETERMINATE` $\implies \text{INCONCLUSIVE}$; all `PASS` $\implies \text{SUPPORTED}$.
