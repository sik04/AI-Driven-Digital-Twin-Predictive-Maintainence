# Step 9 Confirmatory Evaluation Pre-Test Freeze Checklist

- **Protocol Version**: `step09-v1`
- **Schema Version**: `step09-checklist-v1`
- **Status**: Complete — Pre-Test Readiness Gates Verified (Held-out evaluation pending)

---

## Pre-Test Freeze Verification Gates

| # | Verification Item | Status | Evidence Path |
| :-: | :--- | :-: | :--- |
| 1 | Baseline Preservation Manifest created with actual SHA-256 hashes of all 724 protected artifacts | **PASS** | `experiments/audits/step08_repair_baseline.json` |
| 2 | Calibration Registry migrated to POSIX paths; bit-for-bit non-path equality verified | **PASS** | `experiments/calibration/calibration_registry.json` |
| 3 | Strengthened calibrator loader verified across all 90 committed calibrators on Windows & Linux | **PASS** | `tests/test_step08_repair_and_step09_confirmatory.py` |
| 4 | Step 8 Repair Audit verifies cache completeness, LOEO candidate reconstruction, and rational quantiles | **PASS** | `experiments/audits/step08_repair_verification.json` |
| 5 | Clean execution provenance recorded; dirty execution refused by default | **PASS** | `src/intellitwin/provenance.py` |
| 6 | Documentation corrected and verified via automated rendering check | **PASS** | `scripts/render_step08_completion.py --check` |
| 7 | ADR-022 and ADR-023 recorded in project decision log | **PASS** | `research/decision_log.md` |
| 8 | Confirmatory protocol and configuration frozen (810 primary configs, 120 control configs) | **PASS** | `research/research_design/step09_confirmatory_config.json` |
| 9 | RQ3 Control parameter selection executed on FD002 validation engines only | **PASS** | `experiments/confirmatory_development/controls/` |
| 10 | Production statistical inference engine implemented with 10,000-draw stratified bootstrap and IUT | **PASS** | `src/intellitwin/evaluation/` |
| 11 | Validation smoke evaluation executed across all cells (DEVELOPMENT_SMOKE_ONLY) | **PASS** | `experiments/confirmatory_development/validation_smoke/` |
| 12 | Pre-test audit and protocol freeze bindings generated and verified | **PASS** | `experiments/confirmatory_development/protocol_freeze.json` |
| 13 | Pre-test anti-leakage barrier confirmed: Zero held-out test data windows prepared or evaluated | **PASS** | Pre-test gate verification (held-out evaluation NOT STARTED) |
