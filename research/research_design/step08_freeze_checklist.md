# Step 8 Selection Freeze & Verification Checklist

- **Protocol Version**: `step08-v1`
- **Schema Version**: `step08-freeze-v1`
- **Status**: Active Checklist

---

## Pre-Selection Verification
- [ ] Base predictor registry `experiments/base_models/model_registry.json` verified and intact (30 models).
- [ ] Step 7 prediction reproduction audit passed (`experiments/audits/step07_prediction_reproduction.json`).
- [ ] No held-out test data accessed or leaked.
- [ ] Preprocessor and split manifest hashes verified against committed constants.

---

## Validation-Only Development Execution
- [ ] Leave-one-engine-out validation executed across all 6 dataset/model-family cells and all 5 seeds.
- [ ] All 9 candidates evaluated per cell under `primary_reference` cost scenario.
- [ ] Global and regime baselines evaluated under identical protocol.
- [ ] Feasibility constraints applied objectively.
- [ ] Deterministic tie-breaking documented.
- [ ] Per-cell selection records created:
  - [ ] `experiments/calibration/selection/FD001/GBR/selection.json`
  - [ ] `experiments/calibration/selection/FD001/LSTM/selection.json`
  - [ ] `experiments/calibration/selection/FD002/GBR/selection.json`
  - [ ] `experiments/calibration/selection/FD002/LSTM/selection.json`
  - [ ] `experiments/calibration/selection/FD004/GBR/selection.json`
  - [ ] `experiments/calibration/selection/FD004/LSTM/selection.json`
- [ ] Consolidated selection freeze manifest created:
  - [ ] `experiments/calibration/selection/selection_freeze.json`

---

## Selection Freeze Gate (Mandatory Commit)
- [ ] Selection freeze manifest verified.
- [ ] All 6 selection records and selection freeze manifest committed to Git on `feat/step08-decision-aware-calibration`.
- [ ] Working tree clean of uncommitted selection files.

---

## Final Calibration Execution & Verification
- [ ] Final calibration runner verifies selection freeze commit status and artifact hashes.
- [ ] Final hierarchical thresholds fitted on calibration engines only (90 bundles; 270 coverage configs).
- [ ] Post-selection validation diagnostics computed.
- [ ] `calibration_registry.json` created with exactly 90 unique entries and verified hashes.
- [ ] Independent audit executed via `scripts/audit_step08_calibration.py`.
- [ ] Immutability of base predictors and split manifests re-verified.
- [ ] Absolute absence of held-out test predictions or metrics confirmed.
