# Step 9 Confirmatory Evaluation — Pre-Test Documentation Handoff

- **Protocol Version**: `step09-v1`
- **Schema Version**: `step09-handoff-v4`
- **Date**: 2026-10-15
- **Branch**: `fix/pretest-verifier-fail-closed`
- **Active Pre-Test Verification Directory**: `experiments/pretest_verification_v4/`
- **Pre-Test Audit Status**: **PRETEST_READY** (`experiments/pretest_verification_v4/pretest_audit.json`)
- **Held-Out Execution**: **NOT_STARTED**
- **Hypothesis Outcomes (RQ1–RQ4)**: **PENDING**

---

## 1. Executive Summary

This handoff document certifies the completion, rigorous independent reference reconstruction, and cryptographic freeze of the confirmatory evaluation machinery under **ADR-026**.

All five confirmed false-PASS mutations identified during adversarial verification have been decisively rejected with explicit failure logging. Pure independent mathematical, decision, and bootstrap reference reconstruction has been integrated into the verifier, achieving 100% agreement with frozen numerical evidence within $10^{-10}$ tolerance.

Prior verification records in `experiments/pretest_verification_v2/` and `experiments/pretest_verification_v3/` remain preserved byte-for-byte as historical audit evidence. The v4 audit bundle (`experiments/pretest_verification_v4/`) reuses v3 numerical evidence via explicit relative paths and cryptographic hashes with clean git status (`git_dirty = false`).

---

## 2. Directory Layout of Pre-Test Verification v4

```text
experiments/pretest_verification_v4/
├── protocol_freeze.json                 # Comprehensive cryptographic freeze manifest (schema v4)
├── pretest_audit.json                  # Authoritative pre-test readiness audit (PRETEST_READY)
├── content_verification.json           # Fail-closed pure independent reference verification report
├── input_manifest.json                 # Exact input artifact hashes (30 models, 3 preprocessors, 90 calibrators)
├── reused_evidence.json                # Reused v3 evidence references with relative paths and SHA-256 hashes
├── supersession.json                   # Formal supersession of v2 and v3 artifacts
└── regression_test_report.json         # Complete test suite results confirming zero regressions
```

---

## 3. Systematic Resolution of Pre-Test Defects (ADR-025)

| Defect ID | Description | Remediation Implemented | Verification Gate |
| :---: | :--- | :--- | :---: |
| **Defect A** | Permissive skips in verifier | Removed all `continue` statements; verifier fails closed if any expected file, row, configuration, metric, or bootstrap statistic is absent. | **PASS** |
| **Defect B** | Independent draw reconstruction | Implemented `independently_generate_bootstrap_draws` with PCG64 PRNG seeded strictly with `SeedSequence([2026, 6, dataset_number])`; verified exact array match against generated NPZs. | **PASS** |
| **Defect C** | Cartesian configuration & outcome checks | Exact bi-directional set equality asserted for 930 configurations, 19,590 outcome keys, 186 cell summary keys, and canonical coverage integers {80, 90, 95}. | **PASS** |
| **Defect D** | Conservative error bounds & explicit bounded replicate arrays | Subgroup error contrasts propagate conservative interval arithmetic ($\Delta_{\text{lower}} = \text{base}_L - \text{prop}_U$ and $\Delta_{\text{upper}} = \text{base}_U - \text{prop}_L$). Bounded statistics store explicit `_lower` and `_upper` replicate distributions; absent subgroups preserve $[0.0, 0.90]$. | **PASS** |
| **Defect E** | Complete 152 hypothesis component evidence | Implemented `component_evidence.csv` with exactly 152 rows and 19 canonical columns; verified via `validate_component_manifest_completeness` and failure safeguard reconciliation. | **PASS** |
| **Defect F** | Multi-seed point predictions export | Exported all 5 seeds (2026–2030) to `point_predictions.csv` with unique keys and verified against frozen validation caches. | **PASS** |
| **Defect G** | Strengthened protocol freeze & audit gate | Audited all 60 Step-8 raw checkpoint reproduction records independently, verified transitive dependency hashes (30 base checkpoints, 3 preprocessors, 90 calibrators), and derived validation-only partition status. | **PASS** |

---

## 4. Verification and Audit Results

Independent verification (`src/intellitwin/evaluation/verification.py`) and pre-test audit (`scripts/audit_step09_freeze.py`) executed with zero failures:

1. **Independent Verification Matrix (`verify_validation_smoke_matrix`)**:
   - `required_files_present`: **PASS** (17 of 17 required smoke files verified)
   - `validation_engine_counts`: **PASS** (FD001: 10, FD002: 26, FD004: 25)
   - `canonical_coverage_valid`: **PASS** (all coverages map strictly to {80, 90, 95})
   - `configurations_exact_match`: **PASS** (exact Cartesian set equality: 930/930)
   - `outcome_keys_exact_match`: **PASS** (exact Cartesian set equality: 19,590/19,590)
   - `engine_metric_keys_exact_match`: **PASS** (19,590 engine metric rows)
   - `validation_partition_only`: **PASS** (zero calibration or test engine leakage)
   - `cell_summary_keys_exact_match`: **PASS** (186/186 cell summary keys)
   - `cell_summary_cost_reconstruction`: **PASS** (maximum numerical error: $0.0$)
   - `point_predictions_all_seeds`: **PASS** (all 5 seeds 2026..2030 present)
   - `point_predictions_unique_keys`: **PASS** (zero duplicate rows)
   - `point_predictions_cache_match`: **PASS** (exact value match against frozen caches)
   - `bootstrap_draws_exact_reconstruction`: **PASS** (100% exact bit-for-bit array equality across all 3 datasets)
   - `ci_verification`: **PASS** (all 74 contrast confidence intervals match independently reconstructed quantiles with maximum discrepancy $0.0 < 10^{-10}$)
   - `component_evidence_completeness`: **PASS** (all 152 hypothesis components present without duplication)
   - `component_manifest_validation`: **PASS** (validated against `get_rq_component_manifest`)
   - `failure_safeguards_exact_match`: **PASS** (empirical failure counts match outcome tables)
   - `development_smoke_status_only`: **PASS** (all rows strictly labeled `DEVELOPMENT_SMOKE_ONLY`)

2. **Pre-Test Readiness Status**:
   - `overall_status`: **PASS**
   - `pretest_readiness_status`: **PRETEST_READY**
   - `held_out_execution_status`: **NOT_STARTED**
   - `rq_outcomes_status`: **PENDING**

---

## 5. Verification Commands

To independently reproduce the complete verification and pre-test audit from a clean checkout:

```powershell
# 1. Run deterministically seeded reference verification and integrity test suites
uv run pytest tests/test_pretest_reference_verification.py -v
uv run pytest tests/test_pretest_evidence_integrity.py -v

# 2. Run static analysis quality gates
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run mypy src tests

# 3. Verify protocol freeze and pre-test readiness audit (v4 verify-only)
uv run python scripts/audit_step09_freeze.py --verification-dir experiments/pretest_verification_v4 --verify-only
```

---

## 6. Pre-Test Scientific Boundaries and Handoff Sign-off

- **Strict Anti-Leakage Boundary**: Strictly zero held-out test windows have been evaluated, preprocessed, or prepared.
- **Hypothesis Outcomes**: Confirmatory scientific conclusions for RQ1 through RQ4 remain strictly **PENDING**.
- **Historical Evidence**: `experiments/pretest_verification_v2/` is preserved untouched as historical evidence.
- **Handoff Conclusion**: The confirmatory evaluation machinery is fully verified, mathematically sound, and ready for official held-out test evaluation upon authorization.
