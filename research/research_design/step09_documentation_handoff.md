# Step 9 Confirmatory Evaluation — Pre-Test Documentation Handoff

- **Protocol Version**: `step09-v1`
- **Schema Version**: `step09-handoff-v3`
- **Date**: 2026-10-14
- **Branch**: `fix/pretest-evidence-integrity`
- **Baseline Git SHA**: `bb9e34579343881a831e3f052608ee15e183df76`
- **Active Pre-Test Verification Directory**: `experiments/pretest_verification_v3/`
- **Pre-Test Audit Status**: **PRETEST_READY** (`experiments/pretest_verification_v3/pretest_audit.json`)
- **Held-Out Execution**: **NOT_STARTED**
- **Hypothesis Outcomes (RQ1–RQ4)**: **PENDING**

---

## 1. Executive Summary

This handoff document certifies the completion, rigorous verification, and cryptographic freeze of the confirmatory evaluation machinery under **ADR-025**.

All seven pre-test verification defects (A–G) identified in prior versions have been systematically remedied. A complete validation smoke evaluation across all 930 configurations and 10,000 bootstrap draws per dataset was executed and independently audited with 100% fail-closed verification passes.

Prior verification records in `experiments/pretest_verification_v2/` remain preserved byte-for-byte as historical audit evidence and are formally superseded in `experiments/pretest_verification_v3/supersession.json`.

---

## 2. Directory Layout of Pre-Test Verification v3

```text
experiments/pretest_verification_v3/
├── protocol_freeze.json                 # Comprehensive cryptographic freeze manifest (schema v3)
├── pretest_audit.json                  # Authoritative pre-test readiness audit (PRETEST_READY)
├── content_verification.json           # 18-point fail-closed independent verification report
├── input_manifest.json                 # Exact input artifact hashes (30 models, 3 preprocessors, 90 calibrators)
├── reused_evidence.json                # Reused Step 8 audit and Step 9 control references
├── supersession.json                   # Formal supersession of v2 artifacts
├── prior_v2_content_audit.json         # Fail-closed audit report documenting v2 omissions
├── step08_full_audit.json              # Re-verified Step 8 raw inference reproduction (60/60 passing)
├── control_reconstruction.json         # Control reconstruction manifest
├── controls/                           # Selected FD002 benchmark controls (GBR and LSTM)
│   └── FD002/
│       ├── GBR/ (selection.json, candidate_metrics.csv, engine_seed_outcomes.csv)
│       └── LSTM/ (selection.json, candidate_metrics.csv, engine_seed_outcomes.csv)
└── validation_smoke/                   # Complete validation smoke evaluation evidence (DEVELOPMENT_SMOKE_ONLY)
    ├── point_predictions.csv           # Multi-seed point predictions (5 seeds: 2026-2030)
    ├── interval_predictions.csv        # Interval predictions across methods and coverages
    ├── decision_traces.csv             # Step-by-step sequential maintenance decisions
    ├── engine_seed_outcomes.csv        # 19,590 engine seed outcome rows
    ├── engine_metrics.csv              # Engine-level aggregated performance metrics
    ├── subgroup_metrics.csv            # Operating regime and lifecycle stage subgroup metrics
    ├── cell_summary.csv                # 186 cell summaries
    ├── contrast_intervals.csv          # 74 bootstrap contrast confidence intervals
    ├── component_evidence.csv          # 152 hypothesis component evidence rows
    ├── bootstrap_draws_FD001.npz       # 10,000 stratified draws for FD001 (shape: 10000 x 10)
    ├── bootstrap_draws_FD002.npz       # 10,000 stratified draws for FD002 (shape: 10000 x 26)
    ├── bootstrap_draws_FD004.npz       # 10,000 stratified draws for FD004 (shape: 10000 x 25)
    ├── bootstrap_statistics_FD001.npz  # Bootstrap replicate arrays for FD001
    ├── bootstrap_statistics_FD002.npz  # Bootstrap replicate arrays for FD002
    ├── bootstrap_statistics_FD004.npz  # Bootstrap replicate arrays for FD004
    ├── bootstrap_statistics_RQ4.npz    # Bootstrap replicate arrays for RQ4 cross-cell aggregates
    └── execution_manifest.json         # Smoke execution environment and timing metadata
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
# 1. Run deterministically seeded integrity test suite (20 tests)
uv run pytest tests/test_pretest_evidence_integrity.py -v

# 2. Run static analysis quality gates
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src

# 3. Verify validation smoke evidence matrix
uv run python -c "from pathlib import Path; from intellitwin.evaluation.verification import verify_validation_smoke_matrix; res = verify_validation_smoke_matrix(Path('experiments/pretest_verification_v3/validation_smoke')); assert res['status'] == 'PASS', res['failing_reasons']; print('Validation smoke evidence independently verified: PASS')"

# 4. Verify protocol freeze and pre-test readiness audit
uv run python scripts/audit_step09_freeze.py --verification-dir experiments/pretest_verification_v3 --allow-dirty
```

---

## 6. Pre-Test Scientific Boundaries and Handoff Sign-off

- **Strict Anti-Leakage Boundary**: Strictly zero held-out test windows have been evaluated, preprocessed, or prepared.
- **Hypothesis Outcomes**: Confirmatory scientific conclusions for RQ1 through RQ4 remain strictly **PENDING**.
- **Historical Evidence**: `experiments/pretest_verification_v2/` is preserved untouched as historical evidence.
- **Handoff Conclusion**: The confirmatory evaluation machinery is fully verified, mathematically sound, and ready for official held-out test evaluation upon authorization.
