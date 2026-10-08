# Step 6 Numerical Freeze Decision Packet

## Overview
This document records the official researcher-approved numerical cost parameters and practical-effect thresholds locked for Step 6 Sequential Maintenance Simulation and confirmatory testing.

---

## Validation Evidence Summary
The simulator validation pilot was executed on the 26 VALIDATION engines from `data/splits/fd002_engine_split_seed_2026.json`. Zero held-out test engines were inspected.
Descriptive results across synthetic deterministic prediction streams confirmed simulator correctness and cost sensitivity:
- **PERFECT**: Preventive Maintenance Rate = 100%, Failure Rate = 0%, Mean Wasted RUL = 1.0 cycle.
- **OPTIMISTIC**: Preventive Maintenance Rate = 0%, Failure Rate = 100%, Mean Wasted RUL = 0.0 cycles.
- **PESSIMISTIC**: Preventive Maintenance Rate = 100%, Failure Rate = 0%, Mean Wasted RUL = 13.92 cycles.

---

## Locked Numerical Cost Scenarios

| Scenario ID | Role | $C_{\text{PM}}$ | $C_{\text{FAIL}}$ | $C_{\text{WASTE}}$ | Status |
|---|---|---|---|---|---|
| `primary_balanced` | Primary Confirmatory | 10.0 | 100.0 | 1.0 | **FROZEN** |
| `failure_sensitive` | Sensitivity Analysis | 10.0 | 500.0 | 1.0 | **FROZEN** |
| `waste_sensitive` | Sensitivity Analysis | 10.0 | 100.0 | 5.0 | **FROZEN** |

---

## Locked Practical-Effect Thresholds

- **RQ1 Maintenance-Cost Practical Threshold**: Minimum 5.0% reduction in Mean Simulated Maintenance Cost per Engine ($\bar{C}$) over global conformal calibration baseline.
- **RQ2 Subgroup Reliability Threshold**: Worst-group conditional coverage error $CE_g \le 5.0\%$ with non-trivial interval sharpness improvement (MPIW reduction $\ge 10.0\%$).
- **RQ3 Matched-Conservatism Practical Threshold**: Minimum 5.0% cost improvement over matched-conservatism controls (widened intervals, tuned safety margins, earlier intervention policies).
- **RQ4 Robustness Consistency Rule**: Directional cost and reliability improvement observed consistently across all 6 operating regimes and random seeds without catastrophic failure spikes.

---

## Research Governance Certification

- [x] All numerical values approved by researcher prior to model training and confirmatory testing.
- [x] Zero held-out evaluation engines inspected or used for parameter selection.
- [x] Cost parameters locked uniformly across all comparative baseline methods.
