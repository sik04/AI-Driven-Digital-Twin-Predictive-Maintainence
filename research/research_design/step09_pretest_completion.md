# Step 9 Confirmatory Evaluation Preparation — Pre-Test Completion and Verification Report

- **Protocol Version**: `step09-v1`
- **Schema Version**: `step09-pretest-completion-v2`
- **Date**: 2026-10-14
- **Branch**: `fix/complete-pretest-verification`
- **Baseline Git SHA**: `f1edce7fdf48b45513ff90a680da49701451d9cb`
- **Pre-Test Audit Status**: **PRETEST_READY** (`experiments/pretest_verification_v2/pretest_audit.json`)
- **Held-Out Confirmatory Execution**: **NOT_STARTED**
- **Hypothesis Outcomes (RQ1–RQ4)**: **PENDING**

---

## 1. Executive Summary and Defect Remediation

This document certifies the complete, rigorous, and truthful pre-test readiness verification for Step 9 (Roadmap Phase 7) of the IntelliTwin predictive maintenance research project.

An exhaustive code and evidence review revealed critical defects in prior Step 8 repair and Step 9 completion records:
1. **Prior Step 8 Full-Audit Claim Exceeded Executed Checks**: The Step 8 repair report recorded `checkpoint_prediction_reproduction = NOT RUN` while claiming `overall_status = PASS`. Step 9 completion documentation nevertheless claimed raw prediction reproduction had succeeded.
2. **Prior Smoke Run Omitted Controls and Statistical Calculations**: The Step 9 smoke runner evaluated only 810 primary configurations, completely omitting all 120 control configurations. It generated raw bootstrap draw arrays but never applied them to compute replicate statistics, contrasts, or confidence intervals, and omitted point predictions, interval predictions, and decision traces.
3. **Dirty Working Tree Provenance**: Historical smoke runs were executed with `--allow-dirty`, recording `git_dirty = true`, and official audit scripts bypassed selected audit files when testing for dirty working trees.
4. **Historical Baseline SHA Typo**: The baseline commit was erroneously recorded as `f1edce7858c9748b6ee92e7c4f4a3b7849e7b235` instead of actual commit `f1edce7fdf48b45513ff90a680da49701451d9cb`.
5. **Preservation Inventory Conflation**: The preservation inventory claimed 724 verified artifacts, but 72 model-selection checkpoints were exploratory local-only files never committed to Git and absent from a fresh checkout.
6. **Non-Standard Control Tie-Breaking**: Control selection used rounded tolerance buckets rather than the locked rule of retaining candidates within $10^{-8}$ of the actual minimum.
7. **FD004 Validation Count Typo**: Script documentation stated FD004 had 27 validation engines instead of the true split count of 25.

Under **ADR-024**, every defect has been systematically repaired with genuine execution evidence written to `experiments/pretest_verification_v2/`. Prior incomplete records are preserved unchanged and formally superseded in `experiments/pretest_verification_v2/supersession.json`.

---

## 2. Git Baseline Preservation and Artifact Categorization

The preservation manifest `experiments/pretest_verification_v2/baseline_manifest.json` was rebuilt directly from Git blob objects at baseline `f1edce7fdf48b45513ff90a680da49701451d9cb` using batch cryptographic hashing (`git cat-file --batch`):

| Category | Artifact Description | Expected | Matched | Missing | Changed | Verification Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Category A** | Repository-tracked protected scientific artifacts (base models, preprocessing, splits, calibration selection, point predictions, fitted calibrators, summary tables) | 652 | 652 | 0 | 0 | **PASS** |
| **Category B** | Historical local-only exploratory model-selection checkpoints (untracked in Git) | 72 | 0 verified from Git | 72 | 0 | **NOT_AVAILABLE_LOCAL_ONLY** |

### Registry Portability Migration
- Original registry at baseline had Windows backslashes (`\\`).
- Migrated registry uses canonical POSIX slashes (`/`).
- Verified that all 90 entries and all non-path fields agree 100% between baseline and current registry.

---

## 3. Full Step 8 Reverification and Raw Checkpoint Reproduction

The official full Step 8 audit was executed (`scripts/audit_step08_calibration.py`) from a clean working tree (`git_dirty = false`, `device = cpu`), writing to `experiments/pretest_verification_v2/step08_full_audit.json`:

| Check Name | Status | Details |
| :--- | :---: | :--- |
| `registry_completeness` | **PASS** | All 90 calibrator bundles load, conform to schema, and match registered SHA-256 hashes. |
| `prediction_cache_integrity` | **PASS** | Trajectories run strictly cycles 30..T with non-negative finite predictions and correct true RUL labels. |
| `selection_freeze_reconstruction` | **PASS** | Full candidate evidence tables, metrics, and deterministic tie-breaking for all 6 cells reconstruct exactly from cached validation predictions. |
| `threshold_and_interval_reconstruction`| **PASS** | Re-fitted hierarchical quantiles match saved artifacts within numerical tolerance $\Delta \le 1.0 \times 10^{-10}$. |
| `scoped_isolation` | **PASS** | Strictly zero held-out test engines or official test files accessed. |
| `checkpoint_prediction_reproduction` | **PASS** | Re-executed CPU inference for all 30 frozen models on raw validation and calibration partitions (60 model/partition checks). Maximum absolute prediction error is $0.0 \le 1.0 \times 10^{-4}$ cycles. |
| **Overall Status** | **PASS** | Every mandatory check executed and passed. |

---

## 4. Benchmark Control Selection and Complete Grid Validation

Control selection on FD002 validation engines was repaired in `src/intellitwin/decision/controls.py`:
- Replaced rounded tolerance buckets with exact minimum-relative filtering:
  - `matched_width_interval`: Retain candidates with width error $\le \text{minimum} + 10^{-8}$, then cost $\le \text{minimum} + 10^{-8}$, then smaller $\lambda$, then `global_hcp` before `regime_hcp`.
  - Other controls: Retain candidates with cost $\le \text{minimum} + 10^{-8}$, then smaller parameter, then `global_hcp` before `regime_hcp`.
- Evaluated complete candidate grids: 810 matched-width, 612 widened, 251 safety-margin, 502 earlier-intervention = 2,175 candidates per model family (4,350 total across GBR and LSTM).
- Recomputed on FD002 validation partition only (26 engines, 5 seeds, 130 trajectories) under `primary_reference` scenario:

### Verified Selected Controls (FD002 Validation Only)

| Model Family | Benchmark Control ID | Parameter Name | Selected Parameter | Source Method | Mean Cost (SCU) | Matched Width Diff (cycles) | Readiness Gate ($\le 1.0$ cycle) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **GBR** | `matched_width_interval` | $\lambda$ | 0.92 | `global_hcp` | 13.9923 | 0.2547 | **PASS** |
| **GBR** | `widened_interval` | $\lambda$ | 1.00 | `regime_hcp` | 14.9000 | — | **PASS** |
| **GBR** | `point_safety_margin` | $m$ | 5 | `regime_hcp` | 2.7462 | — | **PASS** |
| **GBR** | `earlier_intervention` | $h$ | 1 | `regime_hcp` | 14.9000 | — | **PASS** |
| **LSTM** | `matched_width_interval` | $\lambda$ | 0.90 | `regime_hcp` | 16.3985 | 0.0582 | **PASS** |
| **LSTM** | `widened_interval` | $\lambda$ | 1.00 | `global_hcp` | 18.0523 | — | **PASS** |
| **LSTM** | `point_safety_margin` | $m$ | 4 | `regime_hcp` | 2.3846 | — | **PASS** |
| **LSTM** | `earlier_intervention` | $h$ | 1 | `global_hcp` | 18.0523 | — | **PASS** |

Target proposed validation MPIW: GBR = 111.4749 cycles; LSTM = 110.0624 cycles. Both matched-width controls achieved width differences well within the 1.0-cycle readiness threshold ($0.2547 \le 1.0$ and $0.0582 \le 1.0$).

---

## 5. Complete Validation Smoke Execution

The production evaluation runner (`src/intellitwin/evaluation/runner.py`) executed the complete validation matrix from a clean checkout, writing all artifacts to `experiments/pretest_verification_v2/validation_smoke/`:

### Matrix Structure and Row Counts

| Partition / Evaluation Scope | Datasets | Models | Seeds | Methods / Controls | Coverages | Scenarios | Total Configurations | Outcome Rows | Summary Rows |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Primary Methods** | 3 | 2 | 5 | 3 | 3 | 3 | 810 | 16,470 | 162 |
| **FD002 Benchmark Controls** | 1 | 2 | 5 | 4 | 1 | 3 | 120 | 3,120 | 24 |
| **Total Validation Matrix** | — | — | — | — | — | — | **930** | **19,590** | **186** |

Validation engine counts: FD001 = 10 engines; FD002 = 26 engines; FD004 = 25 engines (total = 61 validation engines).
Outcome rows: Primary = $61 \text{ engines} \times 2 \times 5 \times 3 \times 3 \times 3 = 16,470$; Controls = $26 \text{ engines} \times 2 \times 5 \times 4 \times 1 \times 3 = 3,120$; Total = 19,590 rows.

### Saved Validation Artifacts
All outputs are strictly labeled `DEVELOPMENT_SMOKE_ONLY`:
- `point_predictions.csv` (1,223,781 bytes)
- `interval_predictions.csv` (8,917,451 bytes)
- `decision_traces.csv` (3,203,690 bytes)
- `engine_seed_outcomes.csv` (2,197,083 bytes)
- `engine_metrics.csv` (3,109,296 bytes)
- `subgroup_metrics.csv` (41,571 bytes)
- `cell_summary.csv` (39,287 bytes)
- `contrast_intervals.csv` (17,429 bytes)
- `execution_manifest.json` (2,927 bytes)

---

## 6. Stratified Bootstrap Calculations and Confidence Intervals

All 10,000 stratified engine-cluster bootstrap draws per dataset were applied to calculate validation replicate statistics, contrasts, and confidence intervals:
- **PRNG**: PCG64 initialized with `SeedSequence([2026, 6, dataset_number])`.
- **Multiplicity**: Duplicate engines drawn in a replicate retain multiplicity and are weighted accordingly.
- **Subgroup Worst Errors**: Recomputed across the fixed eligible group set in each replicate.
- **Missing-Group Bounds**: Absent eligible groups bound conservatively at $[0, 0.90]$ and propagate through contrasts.
- **RQ4 Aggregate Contrasts**: Computed by averaging all six dataset/model cells with equal weights ($1/6$).
- **Confidence Intervals**: 95% descriptive intervals ($[0.025, 0.975]$) and 98.75% decision intervals ($[0.00625, 0.99375]$) reconstructed with maximum difference $0.0 < 10^{-10}$ across all 60 contrast intervals.

### Saved Bootstrap Arrays (10,000 Replicates Each)
- `bootstrap_draws_FD001.npz` (shape: $10000 \times 10$)
- `bootstrap_draws_FD002.npz` (shape: $10000 \times 26$)
- `bootstrap_draws_FD004.npz` (shape: $10000 \times 25$)
- `bootstrap_statistics_FD001.npz`
- `bootstrap_statistics_FD002.npz`
- `bootstrap_statistics_FD004.npz`
- `bootstrap_statistics_RQ4.npz`

---

## 7. Pre-Test Freeze and Audit Verification

The final pre-test freeze and audit were executed (`scripts/audit_step09_freeze.py`):
1. **Phase 1: Evidence Audit**: **PASS** (baseline manifest, Step 8 full audit, controls, validation smoke matrix, zero held-out leakage all passed).
2. **Phase 2: Protocol Freeze Assembly**: Immutable cryptographic bindings saved to `experiments/pretest_verification_v2/protocol_freeze.json` (SHA-256: `82dffb2c4224d7dfbbd27012aeb7d7bdc22dc833a5e592ab7705b1ab550c2d7c`).
3. **Phase 3: Saved Freeze Verification**: Generated `experiments/pretest_verification_v2/pretest_audit.json`:
   - `overall_status`: **PASS**
   - `pretest_readiness_status`: **PRETEST_READY**
   - `held_out_execution_status`: **NOT_STARTED**
   - `rq_outcomes_status`: **PENDING**

---

## 8. Final Research Status and Readiness Gates

| Stage / Component | Status | Required Gate Condition | Evidence Path |
| :--- | :---: | :--- | :--- |
| **Step 8 Conformal Uncertainty Calibration** | **FULLY REVERIFIED (PASS)** | All 60 model/partition raw reproduction checks passed with max error $\le 10^{-4}$ | `experiments/pretest_verification_v2/step08_full_audit.json` |
| **Benchmark Matched-Control Selection** | **VERIFIED (PASS)** | Minimum-relative tie-breaking applied; matched-width diff $\le 1.0$ cycle | `experiments/pretest_verification_v2/controls/` |
| **Validation Smoke Evaluation** | **VERIFIED (PASS)** | Full 930 configurations and 19,590 rows evaluated; 10,000 bootstrap draws applied | `experiments/pretest_verification_v2/validation_smoke/` |
| **Pre-Test Protocol Freeze & Readiness Audit** | **PRETEST_READY** | Immutable freeze and pre-test audit verified from clean startup | `experiments/pretest_verification_v2/pretest_audit.json` |
| **Held-Out Test Data Execution** | **NOT_STARTED** | Zero test windows prepared or evaluated | Confirmatory protocol barrier |
| **Confirmatory Hypotheses (RQ1–RQ4)** | **PENDING** | Decision rules locked; awaiting held-out execution | `research/hypotheses/hypothesis_framework.yaml` |

*(Note: Automated verification confirms numerical reproducibility and contract adherence; it does not constitute an independent human review).*
