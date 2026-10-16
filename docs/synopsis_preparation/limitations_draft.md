# Research Limitations and Threats to Validity

**Document Version**: `1.0`  
**Purpose**: Comprehensive audit of methodological, statistical, experimental, and operational boundaries governing the IntelliTwin research framework.

---

## 1. Benchmark Simulation and Synthetic Degradation Dynamics

The empirical evaluation of IntelliTwin is conducted entirely on the NASA Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) benchmark datasets (FD001, FD002, FD004). While C-MAPSS is the standard academic benchmark in prognostics:
- **Simulation Fidelity**: C-MAPSS models physics-based thermo-aerodynamic engine simulations rather than empirical flight telemetry recorded from operational commercial airliners. Degradation dynamics (exponential degradation with injected Gaussian noise) represent idealized failure trajectories.
- **Absence of Maintenance Reversibility**: In C-MAPSS, engine health strictly degrades monotonically until total failure. Real-world turbofan operations involve minor corrective actions (e.g., compressor water washes, turbine blade dressing, sensor recalibration) that temporarily restore operating margins without a full shop overhaul.
- **Sensor Fault Absence**: C-MAPSS assumes degradation is reflected in gas path sensors; it does not model acute sensor failures (e.g., drift, freezing, or open-circuit dropouts) independent of engine degradation.

---

## 2. Synthetic Economic Cost Scenarios

All maintenance utility evaluations rely on normalized **Simulated Cost Units (SCU)** parameterized by planned replacement cost ($C_{\text{PM}} = 1.0$), in-service failure penalty ($C_{\text{FAIL}}$), and wasted useful life penalty ($C_{\text{WASTE}}$):
- **Benchmark Preferences, Not Airline Constants**: These cost scenarios are transparent academic benchmark preferences prespecified under ADR-018. They do not represent empirical accounting figures derived from commercial airline financial records.
- **Stylized Linear Wasted Life**: The economic penalty for discarded life is modeled as linear ($C_{\text{WASTE}} \cdot W$). In actual airline fleet management, engine replacement scheduling depends on flight network scheduling, spare parts inventory, hangar slot availability, and regulatory flight hour thresholds.
- **Sensitivity Scenarios**: While the `failure_sensitive` ($C_{\text{FAIL}} = 10.0$) and `waste_sensitive` ($C_{\text{WASTE}} = 0.40$) scenarios evaluate sensitivity to cost ratios, they remain stylized mathematical benchmarks.

---

## 3. Limited Fleet Sizes and Dataset Generalization

The total physical engine fleet across all three evaluated datasets comprises 609 engines:
- FD001: 100 engines (20 held-out test engines)
- FD002: 260 engines (52 held-out test engines)
- FD004: 249 engines (50 held-out test engines)

### Threats to Statistical Power
- **Small Test Clusters**: While 52 test engines in FD002 provide adequate statistical power for primary fleet-level cost contrasts, evaluating localized subgroup coverage (such as 6 discrete operating regimes and 3 lifecycle stages) divides engines into smaller subsets.
- **Subgroup Support Threshold**: The protocol enforces an eligibility threshold requiring $\ge 10$ distinct engines. While this prevents extreme single-engine distortion, empirical coverage estimates in 10-engine subgroups possess wider confidence bands.
- **Inactive Dataset FD003**: C-MAPSS FD003 (single operating condition, two fault modes) was excluded from the active evaluation matrix to keep cell weighting balanced across operating complexity. Consequently, claims do not generalize to FD003.

---

## 4. Conformal Assumptions and Temporal Dependence

Standard inductive conformal prediction guarantees valid finite-sample marginal coverage under the assumption of **data exchangeability**:
$$P(y_{n+1} \in C(x_{n+1})) \ge 1 - \alpha$$

### Violations in Degradation Time Series
1. **Intra-Engine Autocorrelation**: Telemetry observations extracted from successive operational cycles within the same physical engine are strongly autocorrelated and non-exchangeable. Hierarchical conformal theory provides marginal predictive coverage under its stated sampling and exchangeability assumptions. IntelliTwin uses an engine-weighted construction motivated by that theory. Applicability of those assumptions to ordered, lifetime-stratified degradation trajectories is not established merely by weighting engines equally; reliability is therefore evaluated empirically under the frozen protocol.
2. **Non-Exchangeable Stopping Times**: In sequential maintenance simulation, the stopping time $t_{\text{stop}}$ (when $L(t) \le 1.0$) is a state-dependent random variable that depends on past prediction intervals. Conformal prediction does not theoretically guarantee valid coverage at sequential stopping times or under adaptive stopping rules.
3. **No Exact Pointwise Conditional Guarantees**: Conformal calibration provides marginal coverage. It does not provide theoretical guarantees of exact 90% coverage for every individual cycle, wear stage, or localized state. Subgroup reliability across operating regimes and stages is an empirical diagnostic, not a mathematically guaranteed property.

---

## 5. Dual-Horizon Target Asymmetry (Capped Training vs. Uncapped Evaluation)

Under ADR-012, base point predictors are trained on capped RUL targets ($y_{\text{train}} = \min(125, T_i - t)$), whereas conformal calibration and evaluation are executed against true, uncapped RUL ($y_{\text{true}} = T_i - t$):
- **Early-Life Residual Distortion**: During early operational cycles where true RUL exceeds 125 (e.g., cycle 30 of an engine that survives 350 cycles), point predictors emit predictions near 125, creating large positive residuals ($y_{\text{true}} - p \approx 225 - 125 = 100$ cycles).
- **Interval Expansion in Early Life**: The calibration mechanism must absorb these early-life residuals, which can result in wide upper bounds ($U(t)$) during early operation. While the lower bound $L(t)$ is clipped at zero and remains safe, interval width is inflated during healthy operation.

---

## 6. Rare-Group Support and Fallback Routing

In complex operating environments (FD002 and FD004), certain flight condition clusters occur infrequently:
- If a calibration split contains fewer than $m_g = 10$ engines in a specific operating regime, the calibrator cannot fit a regime-specific threshold and must route to the global fallback threshold ($q_{\text{global}}$).
- While fallback routing preserves operational execution without crashing, fallback intervals do not provide condition-tailored adaptation.
- When evaluating worst-group error in cluster-bootstrap replicates, missing subgroups require conservative bound propagation ($[0.0, 0.90]$), which widens decision intervals.

---

## 7. Fixed Policy Assumptions and Single-Asset Scope

1. **Fixed Policy Contract**: The entire evaluation uses a fixed decision threshold: `MAINTAIN_NOW` iff $L(t) \le 1.0$. The study does not evaluate dynamically optimized or reinforcement-learned replacement policies that adjust the decision threshold as a function of fleet capacity.
2. **Single-Asset Isolated Decisions**: The maintenance simulator models each engine in isolation. It does not model fleet-level constraints, such as limited maintenance technician crews, spare engine supply chain delays, or concurrent opportunistic replacement of multiple engines on the same aircraft.
3. **No Operational Flight Integration**: The system does not interface with live avionics, flight data recorders, or ground-station communication networks. All conclusions apply strictly to offline trace-driven simulation replay.
