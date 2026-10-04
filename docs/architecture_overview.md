# IntelliTwin Architecture Overview

## 1. Architectural Philosophy

IntelliTwin is structured around a **layered, decoupled research architecture**. The codebase strictly separates experimental and scientific algorithmic components from digital twin presentation and infrastructure services.

This design ensures:
- Statistical evaluation pipelines run independently of visualization layers.
- Model algorithms are agnostic to data delivery mechanisms (batch benchmarks vs. streaming sensors).
- Prognostic uncertainty bounds directly constrain operational maintenance logic.

---

## 2. Conceptual Layering

```text
+-------------------------------------------------------------------+
|                     Presentation & Digital Twin                   |
|          (Telemetry Dashboard, 3D Asset State, Alerts)            |
+---------------------------------+---------------------------------+
                                  |
+---------------------------------v---------------------------------+
|                    Decision Support Service                       |
|   (Uncertainty-Aware Maintenance Thresholds, Cost-Optimal DSS)   |
+---------------------------------+---------------------------------+
                                  |
+---------------------------------v---------------------------------+
|                  Uncertainty Quantification (UQ)                  |
|    (Conformal Calibration, Prediction Intervals, Bayesian/MC)    |
+---------------------------------+---------------------------------+
                                  |
+---------------------------------v---------------------------------+
|                    Prognostic RUL Estimators                      |
|         (Baseline Benchmarks, Temporal Deep Architectures)        |
+---------------------------------+---------------------------------+
                                  |
+---------------------------------v---------------------------------+
|                   Data Ingestion & Preprocessing                  |
|  (C-MAPSS Sensor Pipelines, Engine-Level Splits, Normalization)   |
+-------------------------------------------------------------------+
```

---

## 3. Package Structure

The Python codebase follows the standard modern `src/` layout under `src/intellitwin/`:

- `src/intellitwin/`: Root namespace for the core Python library.
  - Future modules (to be introduced in their respective roadmap phases):
    - `data/`: Ingestion, split isolation, and preconditioning pipelines.
    - `models/`: Prognostic predictors (baselines and proposed architectures).
    - `uncertainty/`: Calibration, coverage validation, and interval computation.
    - `decision/`: Risk-sensitive maintenance action policies.
    - `twin/`: State synchronization and telemetry simulation.

During Phase 0, only `src/intellitwin/__init__.py` is present to maintain a minimal, unencumbered foundation. Modules will be introduced alongside corresponding test suites and experiment records.
