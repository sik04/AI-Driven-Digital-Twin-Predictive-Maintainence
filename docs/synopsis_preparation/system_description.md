# System Architecture and Digital Twin Simulation Description

**Document Version**: `1.0`  
**Governing Standard**: Strict demarcation between implemented production research modules and planned demonstration features  
**Source Commit Reviewed**: `bb9e34579343881a831e3f052608ee15e183df76` (Historical initial draft: `224c741f5f3da19821a708e0a6da417d4810e9da`)  
**Target Codebase**: `src/intellitwin/`

---

## 1. Architectural Philosophy and Scope Boundaries

The term "Digital Twin" has been broadly used in engineering literature to encompass diverse implementations ranging from 3D visual CAD models to real-time industrial IoT platforms. In the IntelliTwin research project, the system architecture is strictly defined around **computational prognostic decision-support**:

- **Implemented Research System**: A Python-based scientific research framework comprising data loaders, causal windowing pipelines, neural and gradient-boosted base models, conformal uncertainty calibrators, a discrete-event sequential maintenance simulator, and statistical bootstrap inference machinery.
- **Physical Integration Boundary**: There is **no physical turbofan engine connected to this system**, no real-time telemetry streaming protocol (MQTT, OPC UA, Kafka), and no bidirectional hardware control actuation. The framework operates on offline, trace-driven simulation replay of the NASA C-MAPSS degradation benchmark.
- **Planned Demonstration Subsystem**: An interactive demonstration interface (targeted for Phase 9 of the roadmap) designed to replay historical engine degradation trajectories cycle-by-cycle, displaying live sensor telemetry, point predictions, conformal uncertainty intervals, and simulated maintenance recommendations.

---

## 2. Implemented Subsystems and Code Architecture

The implemented codebase resides in `src/intellitwin/` and is organized into authoritative functional modules:

```text
src/intellitwin/
├── __init__.py                # Package version and metadata
├── provenance.py              # Cryptographic execution provenance and environment logging
├── data/                      # Data curation, regime clustering, and windowing
│   ├── schema.py              # C-MAPSS dataset schema, column definitions, and validation
│   ├── preprocessing.py       # Training-only z-score normalization and regime-aware scaling
│   └── windowing.py           # Causal sliding-window generator (W=30, stride=1, no padding)
├── models/                    # Point prognostic predictors
│   ├── gbr.py                 # sklearn HistGradientBoostingRegressor wrapper and grid specs
│   ├── lstm.py                # PyTorch unidirectional LSTM architecture and trainer
│   └── metrics.py             # Point prediction error metrics (RMSE, MAE, asymmetric score)
├── uncertainty/               # Conformal calibration machinery
│   ├── scores.py              # Nonconformity score functions (symmetric absolute and decision-aware)
│   ├── quantiles.py           # Exact engine-weighted rational quantile computation
│   ├── calibration.py         # Hierarchical conformal calibration engine (global, regime, decision-aware)
│   └── selection.py           # Leave-one-engine-out validation candidate selection
├── decision/                  # Maintenance decision logic
│   ├── policies.py            # lower_bound_one_cycle_policy and baseline policy contracts
│   └── controls.py            # RQ3 matched-conservatism control parameterizations
├── simulator/                 # Sequential maintenance simulation engine
│   ├── engine.py              # Discrete-event MaintenanceSimulator replay engine
│   └── costs.py               # MaintenanceCostModel supporting SCU cost scenarios
└── evaluation/                # Confirmatory statistical inference
    ├── schema.py              # Evaluation result data structures and serialization contracts
    ├── metrics.py             # PICP, MPIW, Winkler score, coverage error, and cost accounting
    ├── bootstrap.py           # Stratified engine-cluster bootstrap with PCG64 PRNG
    ├── inference.py           # Multiplicity adjustment and decision interval estimation
    ├── decisions.py           # Bonferroni FWER and Intersection-Union Testing decision aggregator
    └── runner.py              # End-to-end evaluation orchestration pipeline
```

### 2.1 Cryptographic Execution Provenance (`src/intellitwin/provenance.py`)
To guarantee end-to-end scientific traceability under ADR-022:
- `ExecutionEnvironment`: Captures machine architecture, operating system, Python runtime version, package dependencies (`torch`, `scikit-learn`, `numpy`, `pandas`), command-line arguments, UTC timestamps, and the exact Git commit SHA.
- `Git Dirty Checking`: Refuses execution of official audit or confirmatory runs if uncommitted modifications or untracked files are detected.

### 2.2 Data and Preprocessing Subsystem (`src/intellitwin/data/`)
- Preprocessing uses training-only z-score normalization: $x_{\text{normalized}} = (x - \mu_{\text{train}}) / s_{\text{train}}$, where means and population standard deviations are estimated with `ddof=0`, and $s_{\text{train}} = 1.0$ if $\sigma_{\text{train}} = 0$.
- Preserves the frozen 17-feature selection order: `setting1, setting2, setting3, s2, s3, s4, s7, s8, s9, s11, s12, s13, s14, s15, s17, s20, s21`.
- For FD002 and FD004, operating settings are standardized on training data and clustered into $k=6$ operating regimes via K-Means ($k=6, \text{random\_state}=2026, \text{n\_init}=10$), preserving lexicographic centroid ordering ($C_1$–$C_6$). Sensor normalization parameters are fitted within training regimes. Preprocessing occurs before window construction.
- Causal temporal windowing constructs 30-cycle causal windows ($t-29 \dots t$) with stride 1 without crossing engine boundaries. No padding ensures every prediction is backed by 30 true operational cycles.
- Outputs dual data representations: 2D sequential tensors $(30, 17)$ for LSTM and flattened 1D vectors $(510,)$ in C-order for GBR.

### 2.3 Base Prognostic Model Subsystem (`src/intellitwin/models/`)
- GBR: `sklearn.ensemble.HistGradientBoostingRegressor` operating over flattened 510-dimensional causal vectors. Selected winning configurations: `gbr_lr010_leaf15_l2_0` on FD001; `gbr_lr010_leaf31_l2_0` on FD002 and FD004.
- LSTM: One unidirectional recurrent layer (`input_size=17, hidden_size=64, num_layers=1, batch_first=True, bidirectional=False, dropout=0.0`), extracting the final sequence step, followed by `nn.Dropout(p=0.20)` and `nn.Linear(64, 1)`. Selected configuration: `lstm_h64_lr0010`. Early stopping uses validation uncapped-RUL RMSE.
- Enforces non-negative point-prediction post-processing ($p = \max(0.0, \; \text{raw\_prediction})$) without upper clipping at 125 cycles.

### 2.4 Conformal Uncertainty Subsystem (`src/intellitwin/uncertainty/`)
- Implements exact rational nonconformity quantile solver:
  - In final calibration with $m$ contributing engines, finite score endpoints carry mass $\frac{1}{(m+1)n_i}$.
  - Total finite probability mass is $\frac{m}{m+1}$, with the remaining $\frac{1}{m+1}$ placed at $+\infty$.
  - Threshold $q$ is the smallest observed score whose cumulative probability reaches $1 - \alpha$.
  - Implements fallback routing to global thresholds when an operating regime contains fewer than $m_g \ge \max(10, \lceil 1/\alpha \rceil - 1)$ calibration engines (10 for 80%/90%, 19 for 95%).
  - Supports global baseline (`global_hcp`), regime baseline (`regime_hcp`), and proposed decision-aware asymmetric calibration (`decision_aware_hcp`: $\sigma(p)=(1+p/125)^\gamma, z(p)=\exp(-p/20), a(p)=\sigma(p)\exp(\beta z(p)), b(p)=\sigma(p)\exp(-\beta z(p))$, candidate `gamma2_betam1`).

### 2.5 Sequential Maintenance Simulator (`src/intellitwin/simulator/`)
- Implements `MaintenanceSimulator`: a deterministic, trace-driven discrete-event simulation engine.
- Replays qualified engine operational cycles from cycle 30 to cycle $T_i - 1$.
- Evaluates the policy `MAINTAIN_NOW` iff $L(t) \le 1.0$ cycle.
- Preventive maintenance occurs immediately upon decision and terminates the episode (zero intervention lead time).
- If maintenance occurs at $t < T_i$: $\text{Cost} = C_{\text{PM}} + C_{\text{WASTE}} \cdot (T_i - t)$ and $W = T_i - t$.
- If an engine reaches terminal cycle $T_i$ without maintaining: in-service failure occurs, recording $\text{Cost} = C_{\text{FAIL}}$ and $W=0$.
- Offline prediction interval evaluation includes cycles 30 through $T_i$ independently of policy stopping.

### 2.6 Statistical Inference Engine (`src/intellitwin/evaluation/`)
- Executes 10,000 stratified engine-cluster bootstrap resamples with replacement.
- Stratifies draws by original split lifetime quartiles ($Q_1$–$Q_4$) using PCG64 PRNG (`SeedSequence([2026, 6, dataset_number])`).
- Evaluates empirical 98.75% decision intervals (Bonferroni FWER control $\alpha = 0.0125$) and 95% descriptive intervals using linear quantile interpolation.
- Recomputes worst-group error dynamically in each replicate across eligible subgroups ($\ge 10$ engines).
- Propagates conservative missing-group bounds ($[0.0, 0.90]$ per absent group).
- Aggregates component outcomes under intersection-union testing into three-way decision classifications (`Supported`, `Unsupported`, `Inconclusive`).

---

## 3. Planned Demonstrator Subsystem (Phase 9 Milestone)

The planned demonstrator (tracked in `update_register.csv` as `UPD-06`) is a software demonstration interface designed to showcase the research framework in seminar and presentation settings.

### Intended Functional Features
1. **Interactive Trajectory Replay**: Select any evaluated engine from the C-MAPSS fleet and replay its run-to-failure operational history cycle-by-cycle.
2. **Multi-Regime Sensor Telemetry Stream**: Visualize normalized degradation sensor trajectories alongside current flight envelope regimes ($C_1$–$C_6$).
3. **Comparative Predictive Bounds**: Render point predictions alongside prediction intervals from global conformal baseline, regime-aware baseline, and the proposed decision-aware method.
4. **Maintenance Action Trigger**: Visually highlight the exact cycle where $L(t) \le 1.0$, contrasting the proposed replacement cycle against baseline replacement cycles and true failure cycle $T_i$.
5. **Cost Accounting Dashboard**: Display accumulated maintenance cost, wasted useful life, and economic comparison against reactive and conservative baselines.

> **Development Notice**: The demonstrator is a visualization tool for presenting verified research outputs. It does not perform online hardware synchronization and does not alter the underlying frozen experimental protocols.
