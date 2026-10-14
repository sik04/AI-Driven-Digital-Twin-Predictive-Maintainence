# Reproducibility Protocol and Artifact Governance

**Document Version**: `1.0`  
**Governing ADRs**: `ADR-001`, `ADR-017`, `ADR-020`, `ADR-021`, `ADR-022`, `ADR-023`  
**Tracking Reference**: `UPD-07` (Clean-Environment Replication)  
**Status**: Authoritative Protocol Specification — Pending Release Evidence Explicitly Marked

---

## 1. Reproducibility Charter and Determinism Principles

The IntelliTwin initiative was established under a research-first charter prioritizing computational reproducibility, cryptographic provenance, and complete auditability:

1. **Independent Verification Standards**: Following ACM and IEEE computational reproducibility guidelines, no empirical claim is accepted into formal research deliverables without reproducible code, frozen configuration artifacts, cryptographic hash manifests, and deterministic seed sequences.
2. **Strict Random Seed Policy**: All stochastic operations (data split stratification, neural network weight initialization, dropout masks, and bootstrap resampling) are governed by explicit PRNG specifications:
   - Base model training seeds: five official research seeds: `[2026, 2027, 2028, 2029, 2030]`.
   - Cluster bootstrap PRNG: `numpy.random.Generator(PCG64(SeedSequence([2026, 6, dataset_number])))`.
   - Python hash seed: fixed to zero where applicable to prevent dict order divergence.
3. **Hardware Determinism**: PyTorch execution enforces CPU-based deterministic inference (`torch.use_deterministic_algorithms(True)`), ensuring that checkpoints evaluated across different operating systems yield identical floating-point predictions.

---

## 2. Configuration and Artifact Tracking Infrastructure

All research phases generate immutable JSON registries and cryptographic audit reports:

```text
experiments/
├── base_models/
│   ├── model_registry.json            # 30 base model checkpoints with SHA-256 hashes
│   ├── base_predictor_validation_summary.csv # Validation performance summary across seeds
│   └── reproducibility_audit_seed_2026.json  # Seed-2026 independent reproduction audit
├── calibration/
│   ├── calibration_registry.json      # 90 calibrator bundles and 270 coverage configurations
│   ├── audit_report.json              # Historical calibration audit report
│   └── selection/
│       ├── selection_freeze.json      # Frozen candidate selection (gamma2_betam1 across 6 cells)
│       └── {FD001,FD002,FD004}/{GBR,LSTM}/selection.json # Cell-level validation selection logs
├── audits/
│   ├── step07_prediction_reproduction.json   # Base model prediction verification
│   ├── step08_repair_baseline.json           # Manifest of 724 protected Step 8 artifacts
│   └── step08_repair_verification.json       # Step 8 audit report (POSIX paths verified)
└── confirmatory_development/
    ├── protocol_freeze.json           # Cryptographic hash freeze of Step 9 protocol components
    ├── pretest_audit.json             # Pre-test audit confirming zero test data evaluated
    └── controls/FD002/{GBR,LSTM}/selection.json # Matched-control selections for RQ3
```

### Execution Provenance Tracking (`src/intellitwin/provenance.py`)
Every automated experiment script automatically records:
- UTC execution timestamp.
- Host platform details (OS name, version, CPU architecture).
- Python runtime version and complete installed dependency versions (`torch`, `scikit-learn`, `numpy`, `pandas`, `pyyaml`).
- Command-line arguments.
- Current Git commit SHA and working tree status (`git_dirty: true/false`).
- Cryptographic SHA-256 hashes of all input files (split manifests, preprocessor checkpoints, base model weights, and calibration bundles).

---

## 3. Documented Execution Commands

All reproduction workflows are automated through dedicated Python scripts in `scripts/`:

### 3.1 Auditing Base Predictors (Step 7)
```powershell
# Verify all 30 base model checkpoints and validation prediction hashes
python scripts/audit_step07_base_models.py
```

### 3.2 Auditing Conformal Calibration Registry (Step 8)
```powershell
# Verify all 90 calibrator bundles, POSIX path portability, and exact quantiles
python scripts/audit_step08_calibration.py
```

### 3.3 Auditing Pre-Test Freeze (Step 9)
```powershell
# Verify Step 9 protocol freeze and confirm zero test data leakage
python scripts/audit_step09_freeze.py
```

### 3.4 Executing Development Validation Smoke Test
```powershell
# Run validation smoke test over validation partition engines (development only)
python scripts/run_step09_validation_smoke.py
```

---

## 4. Pending Clean-Environment Release Evidence

In adherence to truth-in-reporting standards, **no clean-environment reproduction is claimed that was not actually executed**:

1. **Step 8 Checkpoint Prediction Reproduction**:
   - As documented in `discrepancy_register.md` (DISC-08), `experiments/audits/step08_repair_verification.json` recorded `checkpoint_prediction_reproduction: NOT RUN`.
   - Full clean-environment reproduction is pending the execution and merge of Mayank's corrective audit under `experiments/pretest_verification_v2/` (tracked as `UPD-01`).
2. **Containerized Clean-Environment Build**:
   - An independent replication in an isolated Docker container on a clean machine has not yet been executed. This milestone is scheduled for Phase 10 of the master roadmap and is tracked in `update_register.csv` under `UPD-07`.
3. **Public Repository Archival**:
   - Final open-science deposit on Zenodo with a digital object identifier (DOI) is scheduled for Phase 12 following manuscript acceptance.
