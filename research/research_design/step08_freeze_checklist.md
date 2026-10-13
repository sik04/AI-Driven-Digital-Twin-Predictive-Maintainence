# Step 8 Selection Freeze & Verification Checklist

- **Protocol Version**: `step08-v1`
- **Schema Version**: `step08-freeze-v1`
- **Status**: Completed & Verified (Corrected Audit)

---

## Pre-Selection Verification
- [x] Base predictor registry `experiments/base_models/model_registry.json` verified and intact (30 models). Evidence: `experiments/audits/step08_repair_baseline.json`
- [x] Step 7 prediction reproduction audit passed (`experiments/audits/step07_prediction_reproduction.json`). Evidence: `experiments/audits/step08_repair_verification.json`
- [x] No held-out test data accessed or leaked. Evidence: `experiments/audits/step08_repair_verification.json`
- [x] Preprocessor and split manifest hashes verified against committed constants. Evidence: `experiments/audits/step08_repair_verification.json`

---

## Validation-Only Development Execution
- [x] Leave-one-engine-out validation executed across all 6 dataset/model-family cells and all 5 seeds. Evidence: `experiments/calibration/selection/`
- [x] All 9 candidates evaluated per cell under `primary_reference` cost scenario. Evidence: `candidate_summary.csv`
- [x] Global and regime baselines evaluated under identical protocol. Evidence: `candidate_summary.csv`
- [x] Feasibility constraints applied objectively. Evidence: `selection.json`
- [x] Deterministic tie-breaking documented. Evidence: `selection.json`
- [x] Per-cell selection records created:
  - [x] `experiments/calibration/selection/FD001/GBR/selection.json`
  - [x] `experiments/calibration/selection/FD001/LSTM/selection.json`
  - [x] `experiments/calibration/selection/FD002/GBR/selection.json`
  - [x] `experiments/calibration/selection/FD002/LSTM/selection.json`
  - [x] `experiments/calibration/selection/FD004/GBR/selection.json`
  - [x] `experiments/calibration/selection/FD004/LSTM/selection.json`
- [x] Consolidated selection freeze manifest created:
  - [x] `experiments/calibration/selection/selection_freeze.json`

---

## Selection Freeze Gate (Mandatory Commit)
- [x] Selection freeze manifest verified. Evidence: `experiments/audits/step08_repair_verification.json`
- [x] All 6 selection records and selection freeze manifest committed to Git on `feat/step08-decision-aware-calibration`. Evidence: Commit `940c793`
- [x] Working tree clean of uncommitted selection files. Evidence: Commit `940c793`

---

## Final Calibration Execution & Verification
- [x] Final calibration runner verifies selection freeze commit status and artifact hashes. Evidence: `scripts/run_step08_final_calibration.py`
- [x] Final hierarchical thresholds fitted on calibration engines only (90 bundles; 270 coverage configs). Evidence: `experiments/calibration/fitted/`
- [x] Post-selection validation diagnostics computed. Evidence: `experiments/calibration/diagnostics/`
- [x] `calibration_registry.json` created with exactly 90 unique entries and verified hashes. Evidence: `experiments/calibration/calibration_registry.json`
- [x] Independent audit executed via `scripts/audit_step08_calibration.py`. Evidence: `experiments/audits/step08_repair_verification.json`
- [x] Immutability of base predictors and split manifests re-verified. Evidence: `experiments/audits/step08_repair_baseline.json`
- [x] Absolute absence of held-out test predictions or metrics confirmed. Evidence: `experiments/audits/step08_repair_verification.json`
