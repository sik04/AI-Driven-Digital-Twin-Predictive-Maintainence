# IntelliTwin: Research Scope Reconciliation & Historical Provenance

- **Document Version**: `1.0.0`
- **Reconciliation Date**: `2026-11-11T16:55:00+05:30`
- **Subject**: Architectural and Methodological Reconciliation of IntelliTwin Project Scope
- **Auditors**: Antigravity Multidisciplinary Research & Scientific Integrity Specialists

---

## 1. Historical Context and Scope Evolution

Across the historical documentation in the repository, two distinct descriptive scopes appear:

```
┌──────────────────────────────────────────────┐
│ Historical Scope A: Initial October Proposal │
│ (Found in Synopsis1.pdf)                     │
├──────────────────────────────────────────────┤
│ • Domain: CNC Machine / Factory Floor        │
│ • Data: Synthetic Random-Walk Telemetry      │
│ • Models: Logistic Regression, Random Forest │
│ • Authors: 4 students (pre-reconstitution)   │
│ • Status: SUPERSEDED                         │
└──────────────────────┬───────────────────────┘
                       │
                       ▼ Architectural Transition (ADR-001 & ADR-002)
┌──────────────────────────────────────────────┐
│ Authoritative Scope B: Final Approved PHM    │
│ (Found in src/, experiments/, synopsis/)     │
├──────────────────────────────────────────────┤
│ • Domain: Gas Turbine Turbofan Degradation   │
│ • Data: NASA C-MAPSS (FD001, FD002, FD004)   │
│ • Models: HistGradientBoosting, Deep LSTM    │
│ • Calibration: Decision-Aware Conformal Pred.│
│ • Decision: Sequential Maintenance Simulator │
│ • Authors: Shiksha Pandey & Mayank Singh     │
│ • Status: AUTHORITATIVE & FROZEN             │
└──────────────────────────────────────────────┘
```

---

## 2. Forensic Audit of Scope Artifacts

### 2.1 Scope A: The October 11, 2026 Initial Synopsis (`Synopsis1.pdf`)
- **Origin**: An early student project proposal titled *"IntelliTwin: An AI-Driven Digital Twin Framework for Predictive Maintenance of Engineering Assets (Validated through Software-Based Simulation on a CNC / Factory-Equipment Model)"*.
- **Content**: Proposed generating random-walk synthetic sensor streams (temperature, speed, torque, vibration) to train binary classifiers (Logistic Regression and Random Forest) with a Streamlit dashboard.
- **Author Roster**: Listed four students (Prateek Gangwar, Rishikesh Chaurasia, Shiksha Pandey, Surya Ranjha).
- **Scientific Limitation**: Purely synthetic random-walk telemetry lacks physical degradation dynamics, multi-regime thermodynamic shifts, and real-world failure mechanics. It represents an unvalidated classroom proposal before formal research initiation.

### 2.2 The Architectural Shift: ADR-001 & ADR-002 (October 2026)
Following departmental review and literature evaluation, the project team executed two foundational Architecture Decision Records:
1. **ADR-001 (Clean Repository Reset)**:
   - Terminated ad-hoc toy scripts and established a rigorous research-first repository foundation with modern Python packaging, automated test suites, strict typing, and reproducible protocols.
   - Reconstituted the active student team to **Shiksha Pandey** and **Mayank Singh** under the supervision of **Dr. Ruchi Gupta**.
2. **ADR-002 (Adoption of Conditional RUL Reliability as Core Direction)**:
   - Recognized that generic point classification on toy data is scientifically unpublishable.
   - Shifted focus to **conditional RUL reliability and downstream maintenance consequences** using the internationally recognized **NASA Commercial Modular Aero-Propulsion System Simulation (C-MAPSS)** turbofan benchmark.

### 2.3 Scope B: Authoritative Implemented Pipeline (`src/intellitwin/`)
The actual production implementation in `src/intellitwin/` contains:
- Multi-dataset C-MAPSS ingestion and engine-level disjoint partitioning (`src/intellitwin/data/`).
- Causal temporal windowing ($w=30$, stride 1) with zero future lookahead.
- HistGradientBoostingRegressor and two-layer LSTM prognostic models (`src/intellitwin/models/`).
- Asymmetric decision-aware nonconformity scoring parameterized by horizon dilation ($\gamma=2$) and risk asymmetry ($\beta=-\ln 2$) (`src/intellitwin/uncertainty/scores.py`).
- Finite-sample hierarchical engine-weighted calibration with rational mass $\frac{m}{m+1}$ and deterministic regime fallbacks (`src/intellitwin/uncertainty/quantiles.py`).
- Sequential discrete-time maintenance simulator with Simulated Cost Units ($\CPM=1.0, \CFAIL=5.0, \CWASTE=0.20$) (`src/intellitwin/simulator/`).
- 122 held-out test engines evaluated under 10,000 paired engine-cluster bootstrap draws (`experiments/confirmatory_v1/`).
- Approved 10-page final academic synopsis suite (`synopsis/Final_Synopsis/`, commit `989b4d6`).

---

## 3. Scope Reconciliation Decision

1. **Authoritative Status**: The **NASA C-MAPSS turbofan prognostic and conformal calibration research direction** is the sole approved, implemented, audited, and experimentally supported research direction of IntelliTwin.
2. **Treatment of Legacy Scope**: The CNC/factory-equipment toy description in `Synopsis1.pdf` is permanently marked as **SUPERSEDED** and historical. It must not be conflated with the authoritative turbofan research in the IEEE paper.
3. **Consistency Across Paper**: The corrected manuscript (`research_paper_ieee.tex`) must describe the turbofan framework exclusively, preserving full traceability to `src/intellitwin/` and `experiments/confirmatory_v1/`.

