# Sequential Maintenance Simulator — Step 6

This document serves as the authoritative specification for the sequential maintenance simulator used by the IntelliTwin platform to evaluate downstream operational decisions under predicted remaining useful life (RUL) and calibrated uncertainty intervals.

---

## 1. Purpose and Operational Boundary

### 1.1 Purpose of the Simulator
The sequential maintenance simulator evaluates the operational consequences of acting on RUL point predictions and calibrated prediction intervals under an explicit decision policy.

### 1.2 Explicit Non-Scope Declarations
The maintenance simulator is strictly an algorithmic decision-evaluation framework under a stylized cost model. It is **NOT**:
- A physical engine degradation simulator or aerothermal cycle solver.
- A fleet-level scheduling or route assignment optimizer.
- A component repair, overhaul, or rejuvenation simulator.
- Empirical evidence of real-world commercial airline financial cost savings.

### 1.3 Terminology and Attribution Standard
Because NASA C-MAPSS supplies run-to-failure degradation trajectories without actual physical maintenance interventions or financial cost records, all experimental results produced by this simulator MUST be described as:

> *"Simulated sequential maintenance utility under a pre-specified maintenance cost model."*

---

## 2. Chronological Event Contract

### 2.1 Engine-Level Independent Replay
Each engine trajectory is replayed independently in strict chronological order ($t = 1, 2, \dots$). No information from future cycles or from other engine units may influence the decision at cycle $t$.

### 2.2 Per-Cycle Decision Loop
For each eligible decision cycle $t$ of engine $i$:

1. **Information Revelation**: Reveal observations only through cycle $t$.
   $$\mathcal{H}(i, t) = \{\text{observed telemetry and settings for engine } i \text{ for cycles } \le t\}$$
2. **Preprocessing**: Apply the frozen Step 5 preprocessing pipeline (training-derived setting standardization and regime-aware sensor z-score normalization).
3. **Window Construction**: Construct the causal feature sequence window using observations through cycle $t$.
4. **Model Inference & Uncertainty Estimation**: Generate the RUL point prediction $\hat{y}(i, t)$ and prediction interval $[\hat{L}(i, t), \hat{U}(i, t)]$.
5. **Information Boundary Check**: Supply only permitted, observable information to the maintenance policy.
6. **Action Selection**: The maintenance policy selects exactly one action $a_t \in \{\text{CONTINUE}, \text{MAINTAIN\_NOW}\}$.
7. **Consequence Execution**:
   - If $a_t = \text{MAINTAIN\_NOW}$ before failure, execute preventive maintenance, record outcomes, and **terminate the engine episode immediately**.
   - If $a_t = \text{CONTINUE}$, advance to the next event step in chronological sequence.

---

## 3. Failure Event Ordering and Boundary Convention

### 3.1 Failure Cycle Definition
Let $T_{\text{failure}}(i)$ denote the final observed failure cycle of engine $i$ in the benchmark dataset.

### 3.2 Actionable Pre-Failure State
The final preventive-maintenance decision opportunity occurs at:

$$t = T_{\text{failure}}(i) - 1$$

At cycle $t = T_{\text{failure}}(i) - 1$, the true remaining life is $\text{RUL}_{\text{true}} = 1$. This represents the final actionable state prior to functional failure.

### 3.3 Terminal Failure Boundary
If the maintenance policy selects $a_t = \text{CONTINUE}$ at cycle $t = T_{\text{failure}}(i) - 1$:
- The engine transitions immediately to **FAILURE** at cycle $T_{\text{failure}}(i)$ ($\text{RUL}_{\text{true}} = 0$).
- The engine replay episode terminates immediately with a failure outcome.
- The policy is **NOT** evaluated at cycle $T_{\text{failure}}(i)$, and no retroactive preventive action is permitted using failure-cycle data.

This strict ordering prevents lookahead bias and ensures that the policy cannot observe a failure event and retroactively claim to have prevented it.

---

## 4. Action Space

### 4.1 Approved Action Set
The action space per decision cycle $t$ is strictly restricted to two discrete actions:

$$\mathcal{A} = \{\text{CONTINUE}, \text{MAINTAIN\_NOW}\}$$

### 4.2 Prohibited Actions and Extensions
No additional actions or policy mechanics are approved:
- No inspection or diagnostic actions.
- No partial repair, component rejuvenation, or variable repair levels.
- No choice of replacement parts or maintenance procedures.
- No maintenance cancellation or deferral queues.
- No crew, shop-visit, or spare-parts inventory scheduling.
- No multi-asset fleet interaction or resource competition.
- No repeated maintenance cycles within the same engine unit.

Once $\text{MAINTAIN\_NOW}$ is selected, the engine episode ends permanently.

---

## 5. Policy Information Boundary

### 5.1 Permitted Policy Inputs
A deployable maintenance decision policy MAY consume:
- Observed feature history $\mathcal{H}(i, t)$ up to cycle $t$.
- Current normalized operating settings ($\text{setting1}, \text{setting2}, \text{setting3}$).
- Current frozen operating-regime assignment $g \in \{1 \dots 6\}$.
- Current point RUL prediction $\hat{y}(i, t)$.
- Current lower prediction interval bound $\hat{L}(i, t)$.
- Current upper prediction interval bound $\hat{U}(i, t)$.
- Observable policy/simulator state from prior cycles that contains no future or ground-truth information.

### 5.2 Prohibited Policy Inputs (Strict Leakage Restrictions)
A deployable maintenance decision policy MUST NOT consume:
- True remaining useful life $\text{RUL}_{\text{true}}(i, t)$.
- Piecewise-linear target $\text{RUL}_{\text{target}}(i, t)$.
- Engine failure cycle $T_{\text{failure}}(i)$.
- Future sensor observations, operating settings, or regime assignments ($t' > t$).
- Future point predictions or interval bounds.
- Test-set outcomes or post-hoc error statistics.
- Financial cost parameter values during online execution (unless explicitly part of a pre-specified decision-theoretic utility policy).
- Engine ID `unit` (identifier/metadata only) or raw `cycle` count as direct predictive features or policy shortcuts.

---

## 6. Uniform Simulator Interface Across All Methods

All experimental baselines and proposed methods MUST interact with the exact same simulator interface, event ordering, information boundary, and cost structure:
1. Point-prediction maintenance baseline
2. Global conformal calibration baseline
3. Standard condition-aware conformal calibration baseline
4. Proposed decision-aware condition-adaptive conformal calibration method
5. Matched-conservatism control baselines

No method may receive privileged information, custom event ordering, or a favorable cost function.

---

## 7. Maintenance Cost Structure

### 7.1 Cost Components
The financial consequence model contains exactly three cost components:
- $C_{\text{PM}}$: Fixed cost of preventive maintenance intervention.
- $C_{\text{FAIL}}$: Cost of unmitigated functional failure.
- $C_{\text{WASTE}}$: Cost per unused remaining operational cycle discarded at preventive intervention.

### 7.2 Preventive Maintenance Cost
If the policy selects $a_{\tau_i} = \text{MAINTAIN\_NOW}$ at cycle $\tau_i < T_{\text{failure}}(i)$:
- Uncapped wasted useful life is defined as:
  $$W_i = T_{\text{failure}}(i) - \tau_i = \text{RUL}_{\text{true}}(i, \tau_i)$$
- Total simulated cost for engine $i$ is:
  $$C_i = C_{\text{PM}} + C_{\text{WASTE}} \cdot W_i$$

### 7.3 Unmitigated Failure Cost
If the policy selects $a_t = \text{CONTINUE}$ through cycle $T_{\text{failure}}(i) - 1$, resulting in failure at $T_{\text{failure}}(i)$:
- Wasted useful life is $W_i = 0$.
- Total simulated cost for engine $i$ is:
  $$C_i = C_{\text{FAIL}}$$

### 7.4 Prohibited Cost Additions
No additional cost terms (e.g., downtime penalties, inspection fees, repair severity multipliers, fuel consumption, shop labor, inventory holding, passenger disruption, or currency conversion) are approved at this stage.

---

## 8. Cost Parameter Governance

### 8.1 Deferred Numerical Parameterization
Numerical values for $C_{\text{PM}}$, $C_{\text{FAIL}}$, and $C_{\text{WASTE}}$ remain intentionally **DEFERRED**. The mathematical structure is locked, but numerical parameters will be defined in pre-specified validation scenarios in Step 6.

### 8.2 Parameter Constraints
All cost parameter scenarios MUST satisfy:
$$C_{\text{PM}} > 0, \quad C_{\text{FAIL}} > C_{\text{PM}}, \quad C_{\text{WASTE}} \ge 0$$

### 8.3 Cost Unit and Evaluation Governance
- All cost metrics are expressed in **Simulated Cost Units**.
- The identical frozen cost scenario MUST be applied to every method within a comparison.
- Cost scenarios MUST be frozen before confirmatory experimental testing.
- Cost scenarios MUST NOT be tuned post-hoc to favor any specific method.

---

## 9. Per-Engine Outcome Record Protocol

For every engine replay episode, the simulator MUST output a structured outcome record containing:

| Field | Type | Description |
|---|---|---|
| `engine_id` | integer | Engine unit identifier |
| `terminal_event` | string | `PREVENTIVE_MAINTENANCE` or `FAILURE` |
| `intervention_cycle` | integer / null | Cycle $\tau_i$ if PM, else `null` if failure |
| `failure_indicator` | binary (0/1) | 1 if engine reached failure, else 0 |
| `preventive_maintenance_indicator` | binary (0/1) | 1 if PM executed, else 0 |
| `wasted_rul` | integer | $W_i = T_{\text{failure}}(i) - \tau_i$ if PM, else 0 |
| `total_simulated_cost` | float | $C_i$ under active cost scenario |

### Decision Provenance Metadata
Each record MUST include decision provenance: model version, calibration method, policy version, decision cycle $t$, point prediction $\hat{y}$, lower bound $\hat{L}$, upper bound $\hat{U}$, and action selected $a_t$.

---

## 10. Premature / Late Outcome Governance

- **Continuous Wasted RUL**: Wasted useful life $W_i$ is preserved as a continuous outcome quantity. No arbitrary binary threshold for "premature maintenance" is imposed at this stage.
- **Failure Boundary**: Reaching the failure boundary without prior preventive maintenance ($t = T_{\text{failure}}(i)$) is the locked definition of an unmitigated failure / late intervention event.

---

## 11. Primary Simulator Evaluation Metric

### 11.1 Primary Metric: Mean Simulated Cost per Engine
The primary simulator outcome metric evaluating RQ1 is the **Mean Simulated Maintenance Cost per Engine**:

$$\bar{C} = \frac{1}{N} \sum_{i=1}^N C_i$$

where $N$ is the number of evaluation engines in the partition.

### 11.2 Independent Unit of Analysis
The **ENGINE** is the fundamental independent unit of statistical evaluation ($N$ = engine count). Individual operational cycles or windows are non-independent time-series observations and MUST NOT be treated as independent statistical samples.

### 11.3 Supporting Secondary Outcomes
Supporting engine-level outcomes include:
- Unmitigated failure rate ($\frac{1}{N} \sum \text{failure\_indicator}$)
- Preventive maintenance rate ($\frac{1}{N} \sum \text{preventive\_maintenance\_indicator}$)
- Mean wasted useful life ($\frac{1}{N} \sum \text{wasted\_rul}$)
- Mean intervention timing ($\bar{\tau}$)

The evaluation hierarchy locked in Step 3 (ADR-010) remains authoritative: secondary outcomes cannot override failure on the primary metric $\bar{C}$.

---

## 12. No Post-Maintenance Trajectory Policy

C-MAPSS supplies unmaintained run-to-failure degradation trajectories.
- When preventive maintenance occurs at $\tau_i$, the simulator stops reading engine $i$'s trajectory immediately.
- Telemetry rows after $\tau_i$ in the raw benchmark file MUST NOT be interpreted as data from a repaired or overhauled engine.
- The simulator does NOT model post-maintenance state restoration, sensor reset, or subsequent degradation cycles.

---

## 13. Simulator Implementation Contract

The Python implementation of the sequential maintenance simulator resides in `src/intellitwin/simulator/` and is strictly structured as follows:

- **`types.py`**: Defines immutable enums `MaintenanceAction` (`CONTINUE`, `MAINTAIN_NOW`) and `TerminalEvent` (`PREVENTIVE_MAINTENANCE`, `FAILURE`), dataclasses `PredictionState`, `MaintenanceDecision`, `DecisionRecord`, `EngineSimulationResult`, and protocol `MaintenancePolicy`. `PredictionState` strictly isolates ground-truth metrics (such as true RUL or failure cycle) from the policy.
- **`costs.py`**: Defines `MaintenanceCostConfig` and cost evaluation routines `preventive_maintenance_cost` and `failure_maintenance_cost`. Config parameters enforce $C_{\text{PM}} > 0$, $C_{\text{FAIL}} > C_{\text{PM}}$, and $C_{\text{WASTE}} \ge 0$.
- **`engine.py`**: Implements deterministic single-engine replay `simulate_engine_trajectory`, fleet simulation `simulate_fleet`, and outcome aggregation `compute_fleet_metrics`. Trajectories are validated for strict monotonicity and non-empty sequences. Decisions occur strictly for $t < T_{\text{failure}}$.

---

## 14. Deterministic Validation Protocol

The simulator core is validated by an automated, deterministic test suite in `tests/test_maintenance_simulator.py`. The suite validates:
1. **Perfect / Correct Timing**: Engine replayed until $t = T_{\text{failure}} - 1$, preventive maintenance triggers $W_i = 1$.
2. **Never Maintain**: Policy always chooses `CONTINUE`, resulting in `FAILURE` at $T_{\text{failure}}$ with zero decision evaluated at $T_{\text{failure}}$.
3. **Early Maintenance**: Policy chooses `MAINTAIN_NOW` at $t \ll T_{\text{failure}}$, engine terminates immediately with $W_i = T_{\text{failure}} - t$.
4. **Final Opportunity**: Policy maintains at $T_{\text{failure}} - 1$, yielding `PREVENTIVE_MAINTENANCE`.
5. **Continue at Final Opportunity**: Policy chooses `CONTINUE` at $T_{\text{failure}} - 1$, leading directly to `FAILURE`.
6. **Optimistic Prediction Stream**: Overestimating RUL leads to `CONTINUE` at final opportunity and `FAILURE`.
7. **Pessimistic Prediction Stream**: Underestimating RUL causes premature `MAINTAIN_NOW` and positive wasted RUL.
8. **Cost Arithmetic**: Cost functions accurately compute $C_{\text{PM}} + C_{\text{WASTE}} \cdot W_i$ and $C_{\text{FAIL}}$.
9. **Policy Information Isolation**: Policy receives only `PredictionState` without access to ground truth.
10. **Invalid Input Enforcement**: Duplicate cycles, non-monotonic timestamps, or invalid bounds raise explicit exceptions.
11. **Fleet Aggregation**: Correct calculation of per-engine mean cost, failure rate, PM rate, and wasted RUL metrics.

---

## 15. Maintenance Cost Scenario Families

The cost infrastructure defines three scenario families in `research/research_design/maintenance_cost_scenarios.yaml`:
- **`primary_balanced`**: Primary confirmatory maintenance scenario balancing failure avoidance and unnecessary early replacement.
- **`failure_sensitive`**: Sensitivity scenario assigning greater relative importance to avoiding failure events ($C_{\text{FAIL}} \gg C_{\text{PM}}$).
- **`waste_sensitive`**: Sensitivity scenario assigning greater relative importance to discarding usable remaining life ($C_{\text{WASTE}}$ weighted higher).

> **Governance Notice**:
> The scenario **FAMILY definitions** are locked.
> The **NUMERICAL VALUES** ($C_{\text{PM}}, C_{\text{FAIL}}, C_{\text{WASTE}}$) are intentionally **DEFERRED / UNLOCKED** pending researcher review of the Step 6.7 validation-only decision pilot (`step06_numerical_freeze_decision.md`). Held-out test evaluation results MUST NOT be used to tune or select these numerical parameters.

