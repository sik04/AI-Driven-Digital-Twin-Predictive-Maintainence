# Step 9 Confirmatory Evaluation Architecture & Verification Protocol

- **Protocol Version**: `step09-v1`
- **Schema Version**: `step09-confirmatory-v1`
- **Stage**: Phase 7 — Confirmatory Held-Out Execution Architecture
- **Date**: 2026-10-23
- **Baseline Review SHA**: `1afb9e5`
- **Status**: Executed & Independently Verified (Audit Status: PASS)

---

## 1. System Architecture & Separation of Concerns

To satisfy strict confirmatory preregistration standards (ADR-018, ADR-026), the held-out evaluation path is completely decoupled from exploratory and historical validation modules. It is implemented in a dedicated subpackage `src/intellitwin/confirmatory/`:

```
src/intellitwin/confirmatory/
├── __init__.py           # Package public exports
├── data.py               # Raw source verification, partition selection, causal windowing
├── runner.py             # 930-configuration matrix executor with dynamic manifest sizing
├── verification.py       # Independent reference verifier (bit-level & numerical reconstruction)
└── reporting.py          # Authoritative synthesis, CSV tables, and vector PDF / PNG figures

scripts/
├── run_confirmatory_evaluation.py     # Execution CLI (--partition validation|test)
└── audit_confirmatory_evaluation.py   # Independent audit CLI

tests/
└── test_confirmatory_execution.py     # Comprehensive test suite & mutation verifier
```

### Key Architectural Boundaries
1. **No Production Runner Monkeypatching**: The existing Step 8/9 validation runner (`src/intellitwin/evaluation/runner.py`) remains completely untouched and immutable.
2. **Dynamic Manifest Sizing**: Outcome and summary row counts are dynamically derived from actual partition membership. Validation evaluations evaluate 61 engines (19,590 outcome rows); test evaluations evaluate 122 engines (39,180 outcome rows).
3. **Partition Isolation Before Transformation**: Partition filtering occurs on raw data *before* preprocessor transformation and windowing.
4. **Never Accesses NASA Test Files**: Evaluations strictly use the preregistered test split partition of the run-to-failure series. NASA's truncated test files (`test_FD00x.txt`) are excluded.

---

## 2. Anti-Leakage & Governance Safeguards

### 2.1 Partition Allowlist & Gate Enforcement
- **Authorized Partitions**: Only `'validation'` and `'test'` are accepted.
- **Forbidden Partitions**: `'train'` and `'calibration'` partition requests are rejected with `PermissionError` to preserve the integrity of fitted base models and calibrators.
- **Explicit Confirmation Flag**: Access to the held-out `'test'` partition strictly requires the `--confirm-held-out` CLI flag. Any attempt to run without this flag halts execution immediately.

### 2.2 Working Tree Cleanliness & Pre-Test Readiness
Official test execution mandates:
- Clean git working tree (`git_dirty == False`).
- Passing pre-test freeze audit (`experiments/pretest_verification_v6/pretest_audit.json` must report `PASS` and `PRETEST_READY`).
- Verified raw source hashes:
  - `FD001`: `963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8`
  - `FD002`: `dac6c4dbc4e7c1bdeb5747da3d313d05c395bb99801b44a002b26a2ba13d788f`
  - `FD004`: `27ef6160b6a1dcb2613a88de9c239f763b223f02cdc41dc5cdedc5dc189b6218`

### 2.3 Resource & Thread Management
Inference runs sequentially on CPU with `torch.set_num_threads(2)` and batch size 256. Base models are loaded one at a time and released between cells to prevent memory bloat and guarantee deterministic execution.

---

## 3. Validation Equivalence Mode

Prior to opening held-out data, the confirmatory runner is verified in validation-equivalence mode against historical baseline `experiments/pretest_verification_v3/validation_smoke/`:

| Artifact | Verification Criterion | Achieved Result |
| :--- | :--- | :--- |
| `bootstrap_draws_{FD001,FD002,FD004}.npz` | Bitwise array agreement | Exact Match (Bitwise) |
| `cell_summary.csv` | Numerical tolerance `atol=1e-10, rtol=0` | Max Abs Diff $\le 10^{-12}$ |
| `contrast_intervals.csv` | Numerical tolerance `atol=1e-10, rtol=0` | Max Abs Diff $\le 10^{-12}$ |
| `component_evidence.csv` | Numerical tolerance `atol=1e-10, rtol=0` | Max Abs Diff $\le 10^{-12}$ |
| `engine_seed_outcomes.csv` | Exact discrete event agreement | Exact Match |
| `subgroup_metrics.csv` | Subgroup bound agreement | Exact Match |

---

## 4. Independent Reference Verification & Audit

The independent reference verifier in `src/intellitwin/confirmatory/verification.py`:
- Reconstructs all point predictions, intervals, simulation outcomes, cell summaries, bootstrap draws, contrast distributions, and component decisions independently without importing runner internals.
- Emits `independent_audit.json` summarizing verification results.
- Mutation testing in `test_confirmatory_execution.py` confirms that the verifier fails closed when injected with altered point predictions, missing rows, tampered bootstrap draws, or modified component manifests.

---

## 5. Execution Workflows

### 5.1 Pre-Exposure Verification Run (Validation Equivalence)
```bash
python scripts/run_confirmatory_evaluation.py \
  --partition validation \
  --output-dir experiments/confirmatory_validation_smoke \
  --n-bootstrap 10000 \
  --use-validation-cache
```

### 5.2 Official Held-Out Test Evaluation
```bash
python scripts/run_confirmatory_evaluation.py \
  --partition test \
  --confirm-held-out \
  --output-dir /staging/confirmatory_v1 \
  --n-bootstrap 10000
```

### 5.3 Independent Reference Audit
```bash
python scripts/audit_confirmatory_evaluation.py \
  --evidence-dir experiments/confirmatory_v1 \
  --partition test
```

---

## 6. Official Held-Out Test Evaluation & Audit Outcomes

The official confirmatory evaluation was executed on the held-out test partition in accordance with preregistered protocol `step09-v1`:

- **Execution Commit SHA**: `67b96453bfc9b2786ce39bd5c6b510acea10c3d7`
- **Execution Timestamp**: `2026-10-23T17:20:41.476812+00:00`
- **Evaluated Engines**: 122 test engines (20 in FD001, 52 in FD002, 50 in FD004)
- **Matrix Dimensions**: 930 configurations (810 methods + 120 controls), 186 cell summaries, 39,180 engine-seed outcome rows
- **Hypothesis Components**: 152 pre-specified components evaluated across 10,000 stratified bootstrap draws
- **Independent Reference Audit**: `PASS` (0 failing reasons, all protected inputs unchanged, bitwise array reconstruction exact)

### Summary of Authoritative Research Question Decisions

| Research Question | Hypothesized Effect | Evaluated Components | Pass | Fail | Indeterminate | Authoritative Decision |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **RQ1** | Maintenance cost improvement ($\Delta_{\text{cost}} > 0.20$ SCU) & reliability | 14 | 9 | 2 | 3 | **UNSUPPORTED** |
| **RQ2** | Conditional subgroup reliability ($\Delta_{\text{error}} > 0.01$) without MPIW blowup | 20 | 10 | 4 | 6 | **UNSUPPORTED** |
| **RQ3** | Decision value vs 4 matched controls ($\Delta_{\text{cost}} > 0.20$ SCU) | 22 | 15 | 4 | 3 | **UNSUPPORTED** |
| **RQ4** | Robustness across 6 multi-dataset cells & non-harm | 96 | 71 | 9 | 16 | **UNSUPPORTED** |

Evidence artifacts are permanently archived in `experiments/confirmatory_v1/` and reporting synthesis artifacts in `research/results/confirmatory_v1/`.

