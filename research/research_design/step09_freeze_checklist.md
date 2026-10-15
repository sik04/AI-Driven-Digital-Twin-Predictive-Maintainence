# Step 9 Confirmatory Evaluation Pre-Test Freeze Checklist

- **Protocol Version**: `step09-v1`
- **Schema Version**: `step09-checklist-v4`
- **Status**: Complete — Pre-Test Readiness Gates Verified under ADR-026 (Held-out evaluation pending)
- **Active Pre-Test Verification Directory**: `experiments/pretest_verification_v4/`

---

## Pre-Test Freeze Verification Gates

| # | Verification Item | Status | Evidence Path |
| :-: | :--- | :-: | :--- |
| 1 | Baseline Preservation Manifest created from Git baseline `f1edce7fdf48b45513ff90a680da49701451d9cb` separating Category A (652 tracked) and Category B (72 local-only) | **PASS** | `experiments/pretest_verification_v2/baseline_manifest.json` |
| 2 | Calibration Registry migrated to POSIX paths; bit-for-bit non-path equality verified | **PASS** | `experiments/calibration/calibration_registry.json` |
| 3 | Strengthened calibrator loader verified across all 90 committed calibrators on Windows & Linux | **PASS** | `tests/test_step08_repair_and_step09_confirmatory.py` |
| 4 | Step 8 Full Audit passed with 60/60 raw CPU inference reproduction checks ($\text{error} \le 10^{-4}$) | **PASS** | `experiments/pretest_verification_v3/step08_full_audit.json` |
| 5 | Clean execution provenance recorded (`device = cpu`, `git_dirty = false`); dirty startup refused | **PASS** | `src/intellitwin/provenance.py` |
| 6 | Documentation corrected and verified via automated checks | **PASS** | `research/research_design/step09_pretest_completion.md` |
| 7 | ADR-022 through ADR-026 recorded in project decision log | **PASS** | `research/decision_log.md` |
| 8 | Confirmatory protocol and configuration frozen (810 primary configs, 120 control configs = 930 total) | **PASS** | `research/research_design/step09_confirmatory_config.json` |
| 9 | RQ3 Control selection executed with minimum-relative tie-breaking on FD002 validation; matched-width $\le 1.0$ cycle | **PASS** | `experiments/pretest_verification_v3/controls/` |
| 10 | Production evaluation runner and statistical inference engine implemented with 10,000-draw bootstrap and IUT | **PASS** | `src/intellitwin/evaluation/runner.py`, `inference.py`, `verification.py` |
| 11 | Complete validation smoke evaluation executed across all 930 configs and 19,590 outcome rows with applied bootstrap CIs | **PASS** | `experiments/pretest_verification_v3/validation_smoke/` |
| 12 | Pure independent reference verification passes all checks with zero tolerance discrepancies ($\le 10^{-10}$) | **PASS** | `experiments/pretest_verification_v4/content_verification.json` |
| 13 | All 5 confirmed false-PASS mutations decisively rejected with explicit failure diagnostics | **PASS** | `tests/test_pretest_reference_verification.py` |
| 14 | Component evidence generated for all 152 hypothesis components and verified against preregistered manifest | **PASS** | `experiments/pretest_verification_v3/validation_smoke/component_evidence.csv` |
| 15 | Multi-seed point predictions exported for all 5 seeds (2026..2030) and verified against frozen caches | **PASS** | `experiments/pretest_verification_v3/validation_smoke/point_predictions.csv` |
| 16 | Pre-test audit and protocol freeze v4 generated and verified (`STATUS: PRETEST_READY`) | **PASS** | `experiments/pretest_verification_v4/protocol_freeze.json`, `pretest_audit.json` |
| 17 | Pre-test anti-leakage barrier confirmed: Zero held-out test data windows prepared or evaluated | **PASS** | `pretest_audit.json` (`held_out_execution_status: NOT_STARTED`, `rq_outcomes_status: PENDING`) |
| 18 | Historical record supersession documented with unchanged hashes and replacement paths | **PASS** | `experiments/pretest_verification_v4/supersession.json` |

