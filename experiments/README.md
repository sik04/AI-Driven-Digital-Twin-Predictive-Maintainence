# Experiment Tracking and Logging Framework

This directory houses all experimental records, configurations, evaluation runs, and empirical benchmarks for the IntelliTwin project.

---

## 1. Principles of Experiment Tracking

1. **Every Run is Documented**: Every experiment intended to inform research decisions, whether successful or failed, must have a corresponding markdown record generated from `experiments/templates/experiment_record.md`.
2. **Negative Results are First-Class Evidence**: An architecture or optimization technique that fails to improve over baselines is valuable empirical evidence and must be documented to prevent redundant work.
3. **Immutability of Historical Records**: Once an experiment record is committed to Git, its metrics and logs must not be altered retroactively.

---

## 2. Directory Structure

```text
experiments/
├── README.md                          # This document
├── templates/
│   └── experiment_record.md           # Template for new experiment records
├── records/                           # Committed experiment record files (e.g., EXP-001.md)
└── runs/                              # (Ignored by Git) Local raw outputs, logs, and checkpoints
```

---

## 3. Workflow for Running an Experiment

1. Copy `experiments/templates/experiment_record.md` to `experiments/records/EXP-XXX.md`.
2. Record the intended hypothesis, parameters, and random seeds before execution.
3. Run the experiment and record exact commit SHA, metrics, and artifact locations.
4. Record limitations, anomalies, and formal conclusions.
5. Commit the completed markdown record as part of the relevant feature branch.
