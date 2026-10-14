# Reproducibility Protocol and Artifact Governance

**Document Version**: `1.0`  
**Governing ADRs**: `ADR-001`, `ADR-017`, `ADR-020`, `ADR-021`, `ADR-022`, `ADR-023`  
**Tracking Reference**: `UPD-07` (Clean-Environment Replication)  
**Status**: Authoritative Protocol Specification — Pending Release Evidence Explicitly Marked

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
   Note that `lightgbm` is not a project dependency; tree boosting is executed strictly via scikit-learn's `HistGradientBoostingRegressor`.
3. **Environment Demarcation**:
   - *Declared constraints*: The version bounds specified above in `pyproject.toml`.
   - *Recorded execution environment*: Specific host platform and package builds recorded at runtime in execution provenance JSON logs.
   - *CI tested environments*: Automated GitHub Actions workflows testing Python 3.10 and 3.11 on Ubuntu and Windows. Universal verification on every Python version $\ge 3.10$ is not claimed.
4. **Strict Random Seed Policy**:
   - Base model training: five official research seeds `[2026, 2027, 2028, 2029, 2030]` (with 2026 and 2027 used for validation configuration selection).
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
│   └── step08_repair_baseline.json           # Manifest of 724 protected Step 8 artifacts
└── pretest_verification_v2/                  # Merged audit artifacts (commit bb9e345)
    ├── step08_full_audit.json                # 60 model/partition reproductions (max diff 0.0)
    ├── pretest_audit.json                    # Confirms PASS and PRETEST_READY
    ├── baseline_manifest.json                # 652 tracked protected artifacts + 72 local checkpoints
    ├── control_reconstruction.json           # RQ3 control selection parameter reconstruction
    ├── protocol_freeze.json                  # Hash freeze of confirmatory evaluation protocol
    └── supersession.json                     # Formal supersession record of historical audit reports
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
*(Note: Hardware CPU model strings, physical memory capacity, full package lockfiles, and internal PRNG state dictionaries are not captured unless explicitly logged by a specific script).*

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

## 4. Committed Verification Evidence and Pending Releases

1. **Step 8 Checkpoint Prediction Reproduction (PR #25, commit `bb9e345`)**:
   - `experiments/pretest_verification_v2/step08_full_audit.json` reports that all 6 mandatory checks ran successfully.
   - Reports 60 base-model/partition prediction reproductions across `validation` and `calibration` partitions (not training), with a maximum observed numerical difference of `0.0`.
   - `experiments/pretest_verification_v2/pretest_audit.json` reports overall status `PASS` and `PRETEST_READY`.
   - Baseline artifact accounting establishes 652 Git-tracked protected artifacts verified from the repository, while 72 historical local search checkpoints are cataloged.
   - Official held-out test execution status remains `NOT_STARTED`; confirmatory RQ outcomes remain `PENDING`.
2. **Containerized Clean-Environment Build**:
   - An independent replication in an isolated Docker container on a clean machine is scheduled under `update_register.csv` (`UPD-07`).
3. **Public Repository Archival**:
   - Final open-science deposit with a digital object identifier (DOI) is scheduled for project completion. External journal publication acceptance is not a prerequisite for repository release.
