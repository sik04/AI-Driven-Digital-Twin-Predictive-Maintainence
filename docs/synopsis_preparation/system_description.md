# System Architecture and Digital Twin Simulation Description

**Document Version**: `2.0 (v4 Audit Alignment)`  
**Reviewed Repository Baseline**: `c163bb279e7427b8f1b6e75955af4969ff9370fd`  
**Committed Readiness Evidence**: `experiments/pretest_verification_v4/` (Audit Execution Commit: `550a7994d5746d3bcbfa28c26e7ed4f1a26a6153`, `git_dirty: false`, readiness: `PRETEST_READY`, held-out execution: `NOT_STARTED`, RQ outcomes: `PENDING`)  
**Governing Standard**: Strict demarcation between implemented production research modules and planned demonstration features  
**Target Codebase**: `src/intellitwin/`

> **Status Statement**: Base predictors and conformal calibrators are implemented and frozen. The committed v4 pre-test audit reports PASS and PRETEST_READY. Held-out execution has not started, and RQ1–RQ4 outcomes remain pending. Development validation and audit results do not establish confirmatory maintenance benefit, subgroup reliability, or robustness.

---

## 1. Architectural Philosophy and Scope Boundaries

The term "Digital Twin" has been broadly used in engineering literature to encompass diverse implementations ranging from 3D visual CAD models to real-time industrial IoT platforms. In the IntelliTwin research project, the system architecture is strictly defined around an **offline, trace-driven prognostic decision-support research prototype**:

- **Implemented Research System**: A Python-based scientific research framework comprising data loaders, causal windowing pipelines, neural and gradient-boosted base models, conformal uncertainty calibrators, a discrete-event sequential maintenance simulator, and statistical bootstrap inference machinery.
- **Physical Integration Boundary**: There is **no physical turbofan engine connected to this system**, no real-time telemetry streaming protocol (MQTT, OPC UA, Kafka), and no bidirectional hardware control actuation. The framework operates on offline, trace-driven simulation replay of the NASA C-MAPSS degradation benchmark. Physical engine integration and operational airline validation have not been demonstrated.
- **Planned Demonstration Subsystem**: An interactive demonstration interface (targeted for Phase 9 of the roadmap) designed to replay historical engine degradation trajectories cycle-by-cycle, displaying live sensor telemetry, point predictions, conformal uncertainty intervals, and simulated maintenance recommendations.

---

## 2. Implemented Subsystems and Code Architecture

The implemented codebase resides in `src/intellitwin/` and is organized into authoritative functional modules:

```text
src/intellitwin/
├── __init__.py                # Package version and metadata
├── provenance.py              # capture_environment_metadata and get_git_info
├── data/                      # Data curation, regime clustering, and windowing
│   ├── schema.py              # C-MAPSS dataset schema, column definitions, and validation
│   ├── splits.py              # Immutable engine-level split manifests and loader
│   ├── preprocessing.py       # Training-only z-score normalization and regime-aware scaling
│   └── windowing.py           # Causal sliding-window generator (w=30, stride=1, no padding)
├── models/                    # Point prognostic predictors
│   ├── gbr.py                 # sklearn HistGradientBoostingRegressor wrapper and grid specs
│   ├── lstm.py                # PyTorch unidirectional LSTM architecture and AdamW trainer
│   └── metrics.py             # Point prediction metrics: uncapped RMSE, uncapped MAE, capped RMSE
├── uncertainty/               # Conformal calibration machinery
│   ├── scores.py              # Nonconformity score functions (symmetric absolute and decision-aware)
│   ├── quantiles.py           # Exact engine-weighted rational quantile computation
│   ├── calibration.py         # Split conformal calibration engine (global, regime, decision-aware)
│   └── selection.py           # Leave-one-engine-out validation candidate selection
├── decision/                  # Maintenance decision logic
│   ├── policies.py            # lower_bound_one_cycle_policy and baseline policy contracts
│   └── controls.py            # RQ3 matched-conservatism control parameterizations
├── simulator/                 # Sequential maintenance simulation engine
│   ├── engine.py              # simulate_engine_trajectory and simulate_fleet replay functions
│   └── costs.py               # MaintenanceCostConfig and preventive/failure cost functions
└── evaluation/                # Confirmatory statistical inference
    ├── evidence_schema.py     # Evaluation summary schemas and cell key generators
    ├── metrics.py             # PICP, MPIW, Winkler score, coverage error, and cost accounting
    ├── bootstrap.py           # Stratified engine-cluster bootstrap with PCG64 PRNG
    ├── inference.py           # Simulation-policy execution and repricing
    ├── decisions.py           # Bonferroni FWER and Intersection-Union Testing decision rules
    └── runner.py              # End-to-end evaluation orchestration pipeline
```

### 2.1 Cryptographic Execution Provenance (`src/intellitwin/provenance.py`)
To guarantee end-to-end scientific traceability under ADR-022:
- `capture_environment_metadata`: Captures machine architecture, operating system, Python runtime version, package dependencies (`torch`, `scikit-learn`, `numpy`, `pandas`), command-line arguments, UTC timestamps, and the exact Git commit SHA via `get_git_info`.
- `Git Dirty Checking`: Refuses execution of official audit or confirmatory runs if uncommitted modifications or untracked files are detected (`git_dirty: false`).
- **CI Configuration**: CI executes on Ubuntu with Python 3.10–3.13, alongside a targeted Windows Python 3.11 portability job. Passing local development tests does not establish that every CI environment passed.

### 2.2 Data and Preprocessing Subsystem (`src/intellitwin/data/`)
- Preprocessing uses training-only z-score normalization: $x_{\text{normalized}} = (x - \mu_{\text{train}}) / s_{\text{train}}$, where means and population standard deviations are estimated with `ddof=0`, and $s_{\text{train}} = 1.0$ if $\sigma_{\text{train}} = 0$.
- Preserves the frozen 17-feature selection order: `setting1, setting2, setting3, s2, s3, s4, s7, s8, s9, s11, s12, s13, s14, s15, s17, s20, s21`.
- For FD002 and FD004, operating settings are standardized on training data and clustered into $k=6$ operating regimes via K-Means ($k=6, \text{random\_state}=2026, \text{n\_init}=10$), preserving lexicographic centroid ordering ($C_1$–$C_6$). Sensor normalization parameters are fitted within training regimes. Preprocessing occurs before window construction.
- Causal temporal windowing constructs 30-cycle causal windows ($t-29 \dots t$) with stride 1 without crossing engine boundaries. Zero padding is strictly prohibited.
- Outputs dual data representations: 2D sequential tensors $(30, 17)$ for LSTM and flattened 1D vectors $(510,)$ in C-order for GBR.

### 2.3 Base Prognostic Model Subsystem (`src/intellitwin/models/`)
- GBR: `sklearn.ensemble.HistGradientBoostingRegressor` operating over flattened 510-dimensional causal vectors. Selected winning configurations: `gbr_lr010_leaf15_l2_0` on FD001; `gbr_lr010_leaf31_l2_0` on FD002 and FD004.
- LSTM: One unidirectional recurrent layer (`input_size=17, hidden_size=64, num_layers=1, batch_first=True, bidirectional=False, dropout=0.0`), extracting the final sequence step, followed by `nn.Dropout(p=0.20)` and `nn.Linear(64, 1)`. Optimizer: AdamW, learning rate 0.001, weight decay 0.0001, batch size 256, betas (0.9, 0.999), epsilon $10^{-8}$. Selected configuration: `lstm_h64_lr0010`. Early stopping uses validation uncapped-RUL RMSE.
- Metrics in `models/metrics.py`: Computes uncapped RMSE, uncapped MAE, and capped RMSE. It does not implement the asymmetric scoring function.
- Evaluated predictions are clipped below at zero: $p = \max(0.0, \; \text{raw\_prediction})$, without an upper clip at 125 cycles.

### 2.4 Conformal Uncertainty Subsystem (`src/intellitwin/uncertainty/`)
- Implements exact rational nonconformity quantile solver:
  - In final calibration with $m$ contributing engines, finite score endpoints carry mass $\frac{1}{(m+1)n_i}$.
  - Total finite probability mass is $\frac{m}{m+1}$, with the remaining $\frac{1}{m+1}$ placed at $+\infty$.
  - Threshold $q$ is the smallest observed score whose cumulative probability reaches $1 - \alpha$.
  - Implements fallback routing to global thresholds when an operating regime contains fewer than $m_g \ge \max(10, \lceil 1/\alpha \rceil - 1)$ calibration engines (10 for 80%/90%, 19 for 95%).
  - Supports global baseline (`global_hcp`), regime baseline (`regime_hcp`), and proposed decision-aware asymmetric calibration (`decision_aware_hcp`: $\sigma(p)=(1+p/125)^\gamma, z(p)=\exp(-p/20), a(p)=\sigma(p)\exp(\beta z(p)), b(p)=\sigma(p)\exp(-\beta z(p))$, candidate `gamma2_betam1`, $\gamma=2, \beta=-\ln 2 \approx -0.693147$).

### 2.5 Sequential Maintenance Simulator (`src/intellitwin/simulator/`)
- Implements `simulate_engine_trajectory` and `simulate_fleet` in `engine.py`: deterministic, trace-driven discrete-event simulation routines.
- Evaluates the policy `MAINTAIN_NOW` iff $L(t) \le 1.0$ cycle for $t \in [30, T_i - 1]$.
- Preventive maintenance occurs immediately upon trigger with zero intervention lead time, terminating the episode.
- Cost configuration governed by `MaintenanceCostConfig` in `costs.py`. Costs are expressed in synthetic Simulated Cost Units (SCU), which represent synthetic benchmark preferences rather than validated airline economics.
- Offline prediction interval evaluation includes cycles 30 through $T_i$ independently of policy stopping.

### 2.6 Statistical Inference Engine (`src/intellitwin/evaluation/`)
- `evaluation/inference.py`: Implements simulation-policy execution and repricing.
- `evaluation/bootstrap.py`: Executes 10,000 stratified engine-cluster bootstrap resamples with replacement, stratified by split lifetime quartiles ($Q_1$–$Q_4$) using PCG64 PRNG (`SeedSequence([2026, 6, dataset_number])`).
- `evaluation/decisions.py`: Implements Bonferroni FWER control ($\alpha = 0.0125$) and Intersection-Union Testing decision rules across all 152 pre-registered hypothesis components.
- Evaluates empirical 98.75% decision intervals and 95% descriptive intervals using linear quantile interpolation.
- Recomputes worst-group error dynamically in each replicate across eligible subgroups ($\ge 10$ engines).
- Propagates conservative missing-group bounds ($[0.0, 0.90]$ per absent group).
- Aggregates component outcomes into three-way decision classifications (`Supported`, `Unsupported`, `Inconclusive`).

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
