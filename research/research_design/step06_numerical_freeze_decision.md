# Step 6 Numerical Freeze Decision Packet

This document summarizes the validation-only pilot evidence generated for Step 6 and outlines the specific numerical cost parameters and practical-effect thresholds awaiting formal researcher approval.

---

## 1. Validation-Only Pilot Evidence Summary

A validation-only pilot was conducted on the **26 validation engines** defined in `partitions.validation` of [`data/splits/fd002_engine_split_seed_2026.json`](../../data/splits/fd002_engine_split_seed_2026.json) using the deterministic script [`scripts/run_step06_simulator_validation.py`](../../scripts/run_step06_simulator_validation.py).

> **NOTICE**: This pilot uses offline synthetic prediction streams on validation engines to test simulator mechanics. It is **NOT** model performance or research experimental findings. Zero held-out test engines were inspected.

### Pilot Results Across Synthetic Prediction Streams

| Synthetic Stream | Description | Engines | PM Count | Failure Count | PM Rate | Failure Rate | Mean Wasted RUL (PM) |
|---|---|---|---|---|---|---|---|
| **PERFECT** | Point = $RUL_{\text{true}}$, Interval = $[RUL_{\text{true}}, RUL_{\text{true}}]$ | 26 | 26 | 0 | 100.0% | 0.0% | 5.0 cycles |
| **OPTIMISTIC** | Point = $RUL_{\text{true}} + 20$, Interval = $[\text{Point} - 5, \text{Point} + 5]$ | 26 | 0 | 26 | 0.0% | 100.0% | 0.0 cycles |
| **PESSIMISTIC** | Point = $\max(RUL_{\text{true}} - 20, 0)$, Interval = $[\max(\text{Point} - 5, 0), \text{Point} + 5]$ | 26 | 26 | 0 | 100.0% | 0.0% | 30.0 cycles |

---

## 2. Locked Cost Scenario Families

The mathematical cost structure $C_i = C_{\text{PM}} + C_{\text{WASTE}} \cdot W_i$ (for PM) and $C_i = C_{\text{FAIL}}$ (for failure) is locked in [`research/research_design/maintenance_cost_scenarios.yaml`](maintenance_cost_scenarios.yaml). The three scenario families are:

1. **`primary_balanced`**: Primary confirmatory maintenance scenario balancing failure avoidance and unnecessary early replacement.
2. **`failure_sensitive`**: Sensitivity scenario assigning greater relative importance to avoiding unmitigated functional failure.
3. **`waste_sensitive`**: Sensitivity scenario assigning greater relative importance to avoiding premature discarding of usable remaining life.

---

## 3. Numerical Values Awaiting Researcher Approval

The numerical values for the three cost parameters in [`research/research_design/maintenance_cost_scenarios.yaml`](maintenance_cost_scenarios.yaml) are currently **UNLOCKED** (`null`) pending researcher decision:

- $C_{\text{PM}}$ (Fixed Preventive Maintenance Cost): **UNLOCKED**
- $C_{\text{FAIL}}$ (Unmitigated Failure Cost): **UNLOCKED**
- $C_{\text{WASTE}}$ (Cost per Wasted RUL Cycle): **UNLOCKED**

---

## 4. Practical-Effect Thresholds Awaiting Researcher Approval

In accordance with ADR-008, ADR-009, and ADR-010, the following research question numerical practical-effect thresholds remain **UNLOCKED** pending researcher decision:

- **RQ1 Maintenance-Cost Practical Threshold**: **UNLOCKED** (Target cost reduction required for $H_{1,1}$ support)
- **RQ2 Material Reliability/Sharpness Threshold**: **UNLOCKED** (Maximum allowable interval width penalty for worst-group coverage gain)
- **RQ3 Matched-Conservatism Practical Threshold**: **UNLOCKED** (Required cost/utility advantage over matched-conservatism controls)
- **RQ4 Robustness Consistency Rule**: **UNLOCKED** (Permitted performance variation across datasets, model families, and seeds)

---

## 5. Governance Declarations

1. **Researcher Authority**: Numerical cost parameters and practical-effect thresholds MUST be explicitly supplied by the research team after reviewing this decision packet.
2. **No Agent Optimization**: The coding assistant MUST NOT infer, tune, or optimize cost values or practical thresholds autonomously.
3. **Strict Test Isolation**: Held-out test partitions (`data/splits/fd002_engine_split_seed_2026.json` `partitions.test`) MUST NOT be inspected or evaluated prior to locking these numerical values.
4. **Pre-Experimental Freeze**: All numerical cost parameters and practical thresholds MUST be frozen in `maintenance_cost_scenarios.yaml` and `decision_log.md` prior to model training or confirmatory testing.
