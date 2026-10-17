# Reproducibility Protocol and Artifact Governance

**Document Version**: `2.0 (v4 Audit Alignment)`  
**Reviewed Repository Baseline**: `c163bb279e7427b8f1b6e75955af4969ff9370fd`  
**Committed Readiness Evidence**: `experiments/pretest_verification_v4/` (Audit Execution Commit: `550a7994d5746d3bcbfa28c26e7ed4f1a26a6153`, `git_dirty: false`, readiness: `PRETEST_READY`, held-out execution: `NOT_STARTED`, RQ outcomes: `PENDING`)  
**Governing ADRs**: `ADR-001`, `ADR-017`, `ADR-020`, `ADR-021`, `ADR-022`, `ADR-023`  
**Tracking Reference**: `UPD-01`, `UPD-07`, `DEV-01` to `DEV-04`  
**Status**: Authoritative Protocol Specification — Pending Release Evidence Explicitly Marked

> **Status Statement**: Base predictors and conformal calibrators are implemented and frozen. The committed v4 pre-test audit reports PASS and PRETEST_READY. Held-out execution has not started, and RQ1–RQ4 outcomes remain pending. Development validation and audit results do not establish confirmatory maintenance benefit, subgroup reliability, or robustness.

---

## 1. Reproducibility Charter and Determinism Principles

The IntelliTwin initiative was established under a research-first charter prioritizing computational reproducibility, cryptographic provenance, and complete auditability:

1. **Independent Verification Standards**: Following ACM and IEEE computational reproducibility guidelines, no empirical claim is accepted into formal research deliverables without reproducible code, frozen configuration artifacts, cryptographic hash manifests, and deterministic seed sequences.
2. **Declared Dependencies**:
   The formal research dependencies declared in `pyproject.toml` (under the `research` extra) are:
   - `numpy>=1.24.0`
   - `pandas>=2.0.0`
   - `scikit-learn>=1.2.0`
   - `torch>=2.2`
   - `PyYAML>=6,<7`
   Tree boosting is executed strictly via scikit-learn's `HistGradientBoostingRegressor`.
3. **Environment Demarcation**:
   - *Declared constraints*: The version bounds specified above in `pyproject.toml`.
   - *Recorded execution environment*: Specific host platform and package builds recorded at runtime in execution provenance JSON logs.
   - *CI tested environments*: Automated GitHub Actions workflows testing Python 3.10–3.13 on Ubuntu, alongside a targeted Windows Python 3.11 portability job. Passing local development tests does not establish clean-environment checkpoint reproduction across all environments.
4. **Strict Random Seed Policy**:
   - Base model training: five prespecified research seeds `[2026, 2027, 2028, 2029, 2030]` (with 2026 and 2027 used for validation configuration selection).
   - Cluster bootstrap PRNG: `numpy.random.Generator(PCG64(SeedSequence([2026, 6, dataset_number])))`.
   - CPU-based PyTorch inference with deterministic algorithms enabled.

---

## 2. Configuration and Artifact Tracking Infrastructure

All research phases generate immutable JSON registries and cryptographic audit reports:

```text
experiments/
├── base_models/
│   ├── model_registry.json                   # 30 base model checkpoints with SHA-256 hashes
│   └── reproducibility_audit_seed_2026.json  # Seed-2026 independent reproduction audit
├── calibration/
│   ├── calibration_registry.json             # 90 calibrator bundles and 270 coverage configurations
│   └── selection/
│       └── selection_freeze.json             # Frozen candidate selection (gamma2_betam1 across 6 cells)
├── audits/
│   ├── step07_prediction_reproduction.json   # Base model prediction verification
│   └── step08_repair_baseline.json           # Historical Step 8 manifest
└── pretest_verification_v4/                  # Committed v4 pretest audit artifacts
    ├── pretest_audit.json                    # Reports overall PASS and PRETEST_READY
    ├── content_verification.json             # Structural content check logs
    ├── input_manifest.json                   # 652 tracked protected artifacts + 72 historical entries
    ├── reused_evidence.json                  # Reused historical evidence: 60 records, max diff 0.0
    ├── protocol_freeze.json                  # Hash freeze of confirmatory evaluation protocol
    ├── supersession.json                     # Formal supersession record of historical audit reports
    └── regression_test_report.json           # Fixed mutation-summary record
```

### Execution Provenance Tracking (`src/intellitwin/provenance.py`)
Automated scripts record runtime provenance via `capture_environment_metadata` and `get_git_info`. The emitted fields are precisely:
- `timestamp_utc`: ISO-8601 UTC execution timestamp.
- `python_version`: `sys.version` string.
- `platform`: `platform.platform()` operating system and kernel release string.
- `device`: Device type (`"cpu"` or `"cuda"`).
- `packages`: Dictionary of installed runtime versions for `numpy`, `pandas`, `scikit_learn`, `torch`, and `pyyaml`.
- `command_args`: `sys.argv` command arguments.
- `git_commit_sha`: Git HEAD commit hash.
- `git_dirty`: Boolean flag indicating whether uncommitted modifications exist.
- `file_hashes`: SHA-256 cryptographic hashes of input and output files.

---

## 3. Documented Execution Commands

All reproduction workflows are automated through dedicated Python scripts in `scripts/`:

### 3.1 Auditing Base Predictors (Step 7)
```powershell
python scripts/audit_step07_base_models.py
```

### 3.2 Auditing Conformal Calibration Registry (Step 8)
```powershell
python scripts/audit_step08_calibration.py
```

### 3.3 Auditing Pre-Test Freeze (Step 9)
```powershell
python scripts/audit_step09_freeze.py --verification-dir experiments/pretest_verification_v4 --verify-only
```

### 3.4 Executing Development Validation Smoke Test
```powershell
python scripts/run_step09_validation_smoke.py
```

---

## 4. Committed Verification Evidence and Pending Releases

1. **Committed Pretest Verification v4 (`experiments/pretest_verification_v4/`)**:
   - Audit Execution Commit: `550a7994d5746d3bcbfa28c26e7ed4f1a26a6153` (`git_dirty: false`).
   - `pretest_audit.json` reports overall status `PASS` and `PRETEST_READY`.
   - Baseline artifact accounting verifies 652 Git-tracked protected artifacts from the repository, while 72 historical/unavailable entries are cataloged.
   - Reused historical evidence: 60 base-model/partition prediction reproduction records across `validation` and `calibration` partitions (not training), reporting maximum numerical difference `0.0`. Preserved with original provenance; raw inference was not rerun during documentation repair.
   - Validation-smoke evidence: 930 configurations (810 primary + 120 controls), 19,590 engine-seed outcome rows, 186 cell-summary rows, 152 hypothesis-component rows, 10,000 bootstrap replicates (validation-smoke counts, not observed held-out results).
   - Official held-out test execution status remains strictly `NOT_STARTED`; confirmatory RQ outcomes remain `PENDING`.
2. **Developer-Owned Audit Limitations and Handoff Items**:
   - `DEV-01`: `scripts/audit_step09_freeze.py::build_regression_test_report` constructs a fixed mutation-summary record; documentation distinguishes stored regression metadata from actual pytest execution evidence.
   - `DEV-02`: `tests/test_pretest_reference_verification.py::test_mutation_bootstrap_stat_with_consistent_contrast_fails_closed` uses 5th/95th percentiles; developer correction is to construct consistent summaries using frozen 0.00625/0.99375 decision quantiles.
   - `DEV-03`: `experiments/pretest_verification_v4/supersession.json` contains a local staging path; documentation links use canonical repository paths while preserving the historical artifact.
   - `DEV-04`: Scikit-learn 1.9.1 checkpoints loaded with 1.8.0 emitted compatibility warnings in review environment; dependency-compatible reproduction is recorded as a developer-owned release task.
3. **Containerized Clean-Environment Build**:
   - Independent replication in an isolated container on a clean machine is scheduled under `update_register.csv` (`UPD-07`).
4. **Public Repository Archival**:
   - Final open-science deposit with a digital object identifier (DOI) is scheduled for project completion. External journal publication acceptance is not a prerequisite for repository release.
