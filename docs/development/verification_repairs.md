# IntelliTwin Pre-Test Verification Repairs (Portion A)

## 1. Overview & Objectives

This document details the architectural and procedural repairs implemented under Portion A of the IntelliTwin pre-test readiness verification framework. These repairs address deficiencies in historical audit bundles (v3 and v4) without modifying scientific protocols, models, calibrators, preprocessing artifacts, or split manifests.

### Key Objectives Achieved

1. **Executed Regression Evidence (`regression_audit.py`)**:
   Replaced static mock records in the regression test report with actual empirical execution. The runner verifies unmodified baseline validation smoke evidence first (must PASS), creates 5 isolated temporary directory copies, executes exactly one prescribed mutation per copy, evaluates rejection against independent verifier checks, captures actual failure reasons and elapsed times, and deletes all temporary copies.
2. **Corrected Mutation 5 Fixture**:
   Corrected the construction of Mutation 5 (`FD001_GBR_global_hcp_cost_improvement` replicate shift by +100) to use `numpy.quantile(..., method="linear")` with descriptive quantiles `[0.025, 0.975]` and decision quantiles `[0.00625, 0.99375]` (avoiding 5th/95th percentiles). Recomputed mean and median, updated `contrast_intervals.csv`, asserted internal consistency within numerical tolerance ($10^{-10}$), and verified that independent reference reconstruction decisively rejects the forged bootstrap array.
3. **Repaired Portable Provenance**:
   Separated physical output generation from logical bundle paths via `--logical-output-dir` (set to `experiments/pretest_verification_v5`). Enforced normalized repository-relative POSIX paths across all artifact reference fields in `protocol_freeze.json`, `input_manifest.json`, `reused_evidence.json`, and `supersession.json`. Strictly rejects absolute paths, Windows drive prefixes, and directory traversal (`..`).
4. **Partner Evidence Integration Gate**:
   Implemented fail-closed partner checkpoint reproduction verification for `experiments/checkpoint_verification_v1/`, checking environment verification PASS, clean source execution, absence of `InconsistentVersionWarning`, full Step-8 reproduction across exactly 60 records ($\le 10^{-4}$ max absolute difference), and unchanged frozen inputs. Missing evidence fails closed with `BLOCKED` status, never silently replacing with historical reports.

---

## 2. Core Modules & Changes

### 2.1. Executed Regression Runner (`src/intellitwin/evaluation/regression_audit.py`)

- **Schema Version**: `step09-regression-report-v2`
- **Mutations Executed**:
  1. `mutation_1`: Increase one FD001/GBR/seed-2027 point prediction by 100 in `point_predictions.csv`.
     - Intended check: `point_predictions_cache_match` or reference point reconstruction discrepancy.
  2. `mutation_2`: Delete one FD001/GBR/seed-2026 point prediction row in `point_predictions.csv`.
     - Intended check: Row count mismatch, unique keys failure, or cache mismatch.
  3. `mutation_3`: Increase `ci_decision_low` by 100 for component `RQ1_GBR_global_hcp_cost_improvement` in `component_evidence.csv`.
     - Intended check: `component_evidence_reconstruction` failure with discrepancy.
  4. `mutation_4`: Set one `engine_metrics.csv` coverage value to 12345.
     - Intended check: `finite_values_and_bounds` out-of-range failure (`[0, 1]` violation).
  5. `mutation_5`: Add 100 to every replicate of `FD001_GBR_global_hcp_cost_improvement` in `bootstrap_statistics_FD001.npz` and update `contrast_intervals.csv` consistently using linear quantiles.
     - Intended check: `bootstrap_statistics_npz_reconstruction` failure with discrepancy $\ge 100.0$ while `ci_verification` passes.
- **Fail-Closed Requirements**:
  - Baseline must PASS before any mutations are evaluated.
  - Overall status requires a successful baseline and all 5 intended rejections.
  - Unrelated verifier failures, missing dependencies, or timeouts are explicitly rejected as proof of intended rejection.

### 2.2. Audit CLI Updates (`scripts/audit_step09_freeze.py`)

- **New CLI Arguments**:
  - `--logical-output-dir`: Committed repository-relative destination (default: `experiments/pretest_verification_v5`).
  - `--checkpoint-evidence-dir`: Partner checkpoint reproduction evidence path (default: `experiments/checkpoint_verification_v1`).
- **Path Validation**:
  `validate_portable_artifact_path()` enforces POSIX forward slashes, rejects Windows drive prefixes (e.g., `C:`), leading slashes (`/`), and parent directory traversal (`..`).
- **Regression Report Generation**:
  In generation mode, regression audit executes empirical tests before binding its hash into `protocol_freeze.json`.
- **v5 Verify-Only**:
  Reruns the regression audit runner in temporary storage and asserts matching logical outcomes (baseline pass, evaluated=5, rejected=5, intended check rejections confirmed) without equating timestamps or runtimes.

---

## 3. Test Coverage & Verification

The repair suite is thoroughly validated by unit and integration tests:

1. `tests/test_pretest_reference_verification.py`:
   - `test_mutation_bootstrap_stat_with_consistent_contrast_fails_closed`: Verified with shared helper `apply_mutation_5_consistent_contrast`, asserting exact linear quantile calculation and independent reference verifier rejection.
   - `test_audit_step09_freeze_cli_verify_only_v4_historical_source_mismatch`: Confirms that historical v4 fails closed on current source modifications due to legitimate source-hash invalidation.
2. `tests/test_verification_repair.py` (15 passing tests):
   - Baseline failure prevents regression-report PASS.
   - Omitted or duplicate mutation records rejected.
   - Intended-check failure detected despite unrelated verifier failures.
   - Mutation 5 linear quantiles and consistent contrast summary assertions.
   - Portable logical paths with external staging directories.
   - Rejection of absolute, drive-prefixed, and traversal artifact locators.
   - Tampered regression report rejection.
   - Missing or failed partner checkpoint evidence reporting `BLOCKED`.
   - Verify-only leaving tracked files unchanged.

---

## 4. Partner Integration & Evidence Status

- **Partner Ownership Scope**:
  - `requirements/checkpoint-verification/`
  - `scripts/verify_checkpoint_environment.py`
  - `tests/test_checkpoint_environment_verification.py`
  - `experiments/checkpoint_verification_v1/`
  - `docs/development/checkpoint_verification.md`
- **Required Partner Files**:
  - `environment_verification.json`
  - `step08_full_audit.json`
  - `input_manifest.json`
  - `execution.log`
  - `pip_freeze.txt`
  - `pip_check.txt`
- **Verification Completion Status**:
  - Partner checkpoint reproduction evidence (`experiments/checkpoint_verification_v1/`) merged via PR #32 (`14f5f57`).
  - Strict verification audit in `scripts/audit_step09_freeze.py` requires both environment status fields to be PASS, clean execution (`clean_source_execution=true`, `git_dirty=false`), exact version matches, exit code 0, 0 sklearn warnings, 60-record reproduction report PASS with max absolute diff $\le 10^{-4}$, source-execution SHA agreement, and exact category/path membership with SHA-256 hash validation across all 11 categories / 233 protected input files.
  - Successor verification bundle generated from clean source (`experiments/pretest_verification_v6/`) with `pretest_audit.json` status `PRETEST_READY` and `overall_status`: `PASS`.
  - Import-only repair in `scripts/audit_step09_freeze.py`: Resolved Ruff E402 module-level import violations by placing `sys.path` setup below `intellitwin` package imports and moving `collect_protected_input_paths` inside `verify_partner_checkpoint_evidence`.
  - Historical verification bundles (`experiments/pretest_verification_v4/` and `experiments/pretest_verification_v5/`) remain immutably preserved.
  - All empirical regression mutations decisively rejected.
  - Held-out test execution remains strictly **NOT_STARTED**; confirmatory RQ outcomes remain strictly **PENDING**.

---

## 5. Protocol and Scientific Integrity

- Scientific protocol version: `step09-v1` (unchanged).
- Base models (30 models), calibrator bundles (90 bundles), split manifests, and selected controls remain byte-for-byte unchanged.
- Historical bundles (`v2`, `v3`, `v4`, `v5`) preserved byte-for-byte.
- Held-out test execution remains strictly **NOT_STARTED**; confirmatory RQ outcomes remain strictly **PENDING**.
