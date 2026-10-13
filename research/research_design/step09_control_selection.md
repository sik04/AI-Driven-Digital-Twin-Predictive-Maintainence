# Step 9 Confirmatory Benchmark Control Parameter Selection Report

- **Protocol Version**: `step09-v1`
- **Schema Version**: `step09-controls-v1`
- **Scope**: Prespecified Benchmark Control Selection for RQ3
- **Dataset**: `FD002` (Validation Partition Exclusively; 26 engines)
- **Seeds**: `2026, 2027, 2028, 2029, 2030` (Joint 5-Seed Evaluation)
- **Status**: Complete — Validation Selection Frozen for Pre-Test Registration

---

## 1. Objectives and Methodology

Research Question 3 (RQ3) evaluates whether the operational maintenance advantages of `decision_aware_hcp` arise from its decision-aware asymmetric formulation or merely from generic conservatism (e.g. wider intervals or arbitrary safety buffers).

To test this hypothesis, four benchmark controls spanning three distinct control families were prespecified:
1. `matched_width_interval`: Rescaled baseline interval matched to proposed validation MPIW.
2. `widened_interval`: Cost-optimal baseline interval expansion ($\lambda \ge 1.0$).
3. `point_safety_margin`: Point-prediction maintenance buffer ($p \le 1 + m$).
4. `earlier_intervention`: Earlier interval lower bound intervention threshold ($L \le h$).

### Strict Methodological Safeguards
- **Validation Partition Only**: Selected strictly on the 26 validation engines of FD002 across all 5 seeds jointly. Training, calibration, and held-out test partitions were strictly excluded.
- **No Per-Seed Tuning**: Parameters are selected once per model family across all five seeds jointly.
- **Frozen Calibrators**: Uses existing Step 8 calibrators at 90% nominal coverage.
- **Development Status**: These parameter selections are development-set benchmarks. They do not constitute unbiased test estimates.

---

## 2. Selection Results and Parameter Freeze

### 2.1 FD002 / GBR Controls
- **Target Proposed MPIW**: 111.4749 cycles

| Control Identifier | Selected Parameter | Interval Source | Achieved MPIW (cycles) | Width Difference (cycles) | Mean Cost (SCU) | Failure Rate | PM Rate | Wasted RUL | Boundary Flag |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `matched_width_interval` | $\lambda = 0.92$ | `global_hcp` | 111.4883 | 0.0134 | 13.9923 | 0.0000 | 1.0000 | 64.96 | False |
| `widened_interval` | $\lambda = 1.00$ | `regime_hcp` | 120.3060 | 8.8311 | 14.9000 | 0.0000 | 1.0000 | 69.50 | True ($\lambda=\min$) |
| `point_safety_margin` | $m = 5$ | `regime_hcp`* | N/A | N/A | 2.7462 | 0.0000 | 1.0000 | 8.73 | False |
| `earlier_intervention` | $h = 1$ | `regime_hcp` | 120.3060 | N/A | 14.9000 | 0.0000 | 1.0000 | 69.50 | True ($h=\min$) |

*\*Logged for schema consistency; policy reads only point prediction $p$.*

### 2.2 FD002 / LSTM Controls
- **Target Proposed MPIW**: 110.0624 cycles

| Control Identifier | Selected Parameter | Interval Source | Achieved MPIW (cycles) | Width Difference (cycles) | Mean Cost (SCU) | Failure Rate | PM Rate | Wasted RUL | Boundary Flag |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `matched_width_interval` | $\lambda = 0.90$ | `regime_hcp` | 110.1584 | 0.0960 | 16.3985 | 0.0000 | 1.0000 | 76.99 | False |
| `widened_interval` | $\lambda = 1.00$ | `global_hcp` | 121.7377 | 11.6753 | 18.0523 | 0.0000 | 1.0000 | 85.26 | True ($\lambda=\min$) |
| `point_safety_margin` | $m = 4$ | `regime_hcp`* | N/A | N/A | 2.3846 | 0.0000 | 1.0000 | 6.92 | False |
| `earlier_intervention` | $h = 1$ | `global_hcp` | 121.7377 | N/A | 18.0523 | 0.0000 | 1.0000 | 85.26 | True ($h=\min$) |

---

## 3. Key Observations and Pre-Test Verification

1. **Width Match Tolerance**:
   - GBR achieved width error is $0.0134 \le 1.0$ cycle.
   - LSTM achieved width error is $0.0960 \le 1.0$ cycle.
   - Both satisfy the width-matching verification criterion.
2. **Boundary Flags**:
   - `widened_interval` selected $\lambda=1.00$ (lower boundary of $\lambda \ge 1.0$ grid), indicating that wider intervals only increase maintenance cost due to excessive wasted RUL.
   - `earlier_intervention` selected $h=1$ (lower boundary of $h \ge 1$ grid), confirming that intervening at lower thresholds minimizes premature maintenance costs.
   - In accordance with preregistration rules, boundary selections are preserved and flagged; grids are not modified or expanded.
3. **Artifact Integrity**:
   - Detailed candidate metrics, simulation outcome traces, and selection JSON files are preserved under `experiments/confirmatory_development/controls/FD002/{GBR,LSTM}/`.
