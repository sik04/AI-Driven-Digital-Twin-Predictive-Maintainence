# System Architecture and Digital Twin Simulation Description

**Document Version**: `1.0`  
**Governing Standard**: Strict demarcation between implemented production research modules and planned demonstration features  
**Source Commit**: `224c741f5f3da19821a708e0a6da417d4810e9da`  
**Target Codebase**: `src/intellitwin/`

---

## 1. Architectural Philosophy and Scope Boundaries

The term "Digital Twin" has been broadly used in engineering literature to encompass diverse implementations ranging from 3D visual CAD models to real-time industrial IoT platforms. In the IntelliTwin research project, the system architecture is strictly defined around **computational prognostic decision-support**:

- **Implemented Research System**: A Python-based scientific research framework comprising data loaders, causal windowing pipelines, neural and gradient-boosted base models, conformal uncertainty calibrators, a discrete-event sequential maintenance simulator, and statistical bootstrap inference machinery.
- **Physical Integration Boundary**: There is **no physical turbofan engine connected to this system**, no real-time telemetry streaming protocol (MQTT, OPC UA, Kafka), and no bidirectional hardware control actuation. The framework operates on offline, trace-driven simulation replay of the NASA C-MAPSS degradation benchmark.
- **Planned Demonstration Subsystem**: An interactive demonstration interface (targeted for Phase 9 of the roadmap) designed to replay historical engine degradation trajectories cycle-by-cycle, displaying live sensor telemetry, point predictions, conformal uncertainty intervals, and simulated maintenance recommendations.

---

## 2. Implemented Subsystems and Code Architecture

The implemented codebase resides in `src/intellitwin/` and is organized into six functional modules:

```text
src/intellitwin/
├── __init__.py                # Package version and metadata
├── provenance.py              # Cryptographic execution provenance and environment logging
├── data/                      # Data curation, regime clustering, and windowing
│   ├── loader.py              # C-MAPSS dataset parser and schema validator
│   ├── preprocessor.py        # Training-only robust scaling and zero-variance pruning
│   ├── regime.py              # K-Means operational regime clustering (k=6)
│   └── window.py              # Causal sliding-window generator (W=30, stride=1, no padding)
├── models/                    # Point prognostic predictors
│   ├── base.py                # Abstract base model contract
│   ├── gbr.py                 # Scikit-learn HistGradientBoostingRegressor wrapper
│   └── lstm.py                # PyTorch unidirectional LSTM architecture and trainer
├── uncertainty/               # Conformal calibration machinery
│   ├── calibrator.py          # Abstract calibrator contract
│   ├── conformal.py           # HierarchicalConformalCalibrator with exact rational quantiles
│   └── scores.py              # Asymmetric decision-aware nonconformity score functions
├── decision/                  # Maintenance decision logic
│   └── policies.py            # lower_bound_one_cycle_policy and baseline policy rules
├── simulator/                 # Sequential maintenance simulation engine
│   ├── engine.py              # Discrete-event MaintenanceSimulator replay engine
│   └── cost.py                # MaintenanceCostModel supporting SCU cost scenarios
└── evaluation/                # Confirmatory statistical inference
    ├── metrics.py             # PICP, MPIW, Winkler score, coverage error, and cost metrics
    ├── bootstrap.py           # Stratified engine-cluster bootstrap with PCG64 PRNG
    └── decision_rules.py      # Bonferroni FWER and Intersection-Union Testing aggregator
```

### 2.1 Cryptographic Execution Provenance (`src/intellitwin/provenance.py`)
To guarantee end-to-end scientific traceability under ADR-022:
- `ExecutionEnvironment`: Captures machine architecture, operating system, Python runtime version, package dependencies (`torch`, `scikit-learn`, `numpy`, `pandas`), command-line arguments, UTC timestamps, and the exact Git commit SHA.
- `Git Dirty Checking`: Refuses execution of official audit or confirmatory runs if uncommitted modifications or untracked files are detected.

### 2.2 Data and Preprocessing Subsystem (`src/intellitwin/data/`)
- Strict C-MAPSS loader enforcing the 17-feature schema (3 operational settings + 14 degradation sensors).
- Preprocessing fit strictly on training engines; frozen medians and scales applied to calibration, validation, and test engines.
- Causal temporal windowing constructing 30-cycle windows ($t-29 \dots t$) with stride 1. No padding ensures every prediction is backed by 30 true operational cycles.
- Outputs dual data representations: 2D sequential tensors $(30, 17)$ for LSTM and flattened 1D vectors $(510,)$ for GBR.

### 2.3 Base Prognostic Model Subsystem (`src/intellitwin/models/`)
- Encapsulates point-prediction architectures adhering to a common interface (`fit`, `predict`).
- GBR: High-capacity tree-based gradient boosting operating over flattened 510-dimensional causal windows.
- LSTM: Deep recurrent neural network operating over sequential 30-step tensors, utilizing dropout regularization and early stopping on validation RMSE.
- Enforces non-negative point-prediction post-processing ($\hat{y} \ge 0.0$).

### 2.4 Conformal Uncertainty Subsystem (`src/intellitwin/uncertainty/`)
- Implements `HierarchicalConformalCalibrator`:
  - Computes exact rational nonconformity weights balancing mass equally across contributing engines ($w_{it} = \frac{1}{m \cdot n_i}$).
  - Enforces Lee et al. (2023) hierarchical boundary mass bounding finite scores by $\frac{m}{m+1}$ and assigning remaining mass to $+\infty$.
  - Supports global thresholding (`global_hcp`), regime-stratified thresholding (`regime_hcp`), and proposed decision-aware asymmetric thresholding (`decision_aware_hcp`).
  - Implements fallback routing to global thresholds when an operating regime contains fewer than $m_g$ calibration engines.

### 2.5 Sequential Maintenance Simulator (`src/intellitwin/simulator/`)
- Implements `MaintenanceSimulator`: a deterministic, trace-driven discrete-event simulation engine.
- Replays qualified engine operational cycles from cycle 30 to cycle $T_i - 1$.
- Evaluates the policy `MAINTAIN_NOW` iff $L(t) \le 1.0$.
- Terminates trajectory immediately upon maintenance trigger, recording cycle $t_{\text{stop}}$, wasted useful life $W = T_i - t_{\text{stop}}$, and simulated cost units.
- Evaluates in-service failure if an engine reaches cycle $T_i$ without maintaining, recording failure cost $C_{\text{FAIL}}$.

### 2.6 Statistical Inference Engine (`src/intellitwin/evaluation/`)
- Executes 10,000 stratified engine-cluster bootstrap resamples with replacement.
- Stratifies draws by original split lifetime quartiles ($Q_1$–$Q_4$).
- Evaluates empirical 98.75% decision intervals and 95% descriptive intervals using linear quantile interpolation.
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
