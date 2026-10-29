# Phase 8 (v2) Provenance and Evidence Review

## 1. Executive Summary

This document provides a forensic provenance audit and scientific validity review of the Phase 8 exploratory ablation and robustness evidence bundle (`experiments/phase08_exploratory_v2/` and `research/results/phase08_exploratory_v2/`).

The v2 bundle succeeded in defining the 2×2×2 factorial component ablation matrix (240 cells) and the frozen-method engineering stress probes (1,620 evaluations), establishing initial quantitative metrics for research questions RQ1–RQ4 in an exploratory capacity (`EXPLORATORY_POST_CONFIRMATORY`). However, forensic inspection revealed provenance defects, git dirty state execution, inconsistent timestamps, reuse of unverified prior evidence, and reporting literals that preclude the v2 bundle from serving as the trustworthy, immutable foundation for manuscript claims.

In accordance with scientific integrity and reproducibility standards, the v2 artifacts are preserved byte-for-byte in the repository as immutable historical records, marked explicitly as superseded by the clean authoritative successor bundle (`phase08_exploratory_v3`).

---

## 2. Forensic Audit Findings for Phase 8 v2

### A. Working Tree Dirty State (`--allow-dirty`)
- **Recorded Metadata**:
  - `git_commit`: `95b9ea40121b0a5e31a0d3919f0a4e5a0f587dde`
  - `git_dirty`: `true`
  - Command: `python scripts/complete_phase08_v2_bundle.py --allow-dirty`
- **Scientific Implication**:
  Because `--allow-dirty` was active and `git_dirty: true` was recorded, the exact working tree state during execution did not strictly correspond to the committed tree at SHA `95b9ea4`. Source files could have contained uncommitted modifications that cannot be cryptographically proven from the commit alone.

### B. Execution Timestamps and Duration Anomaly
- **Recorded Metadata**:
  - `start_time_utc`: `2026-10-24T18:42:07.755490+00:00`
  - `end_time_utc`: `2026-10-26T21:48:47.387713+00:00`
  - `duration_seconds`: `2942.14` (~49.0 minutes)
- **Scientific Implication**:
  The recorded execution dates span more than 48 hours (from Oct 24 to Oct 26), while the reported runtime duration is only ~49 minutes. This anomaly confirms that execution was non-atomic and multi-segmented: initial runs were stopped or interrupted, intermediate caches were retained across multiple days, and the final bundle was assembled after substantial wall-clock delay.

### C. Reuse of Pre-Existing Intermediate Ablation Artifacts
- **Recorded Evidence in `execution.log`**:
  The execution log records that pre-existing ablation prediction files and intermediate calibrators from a prior attempt (`phase08_exploratory_v1` or an uncommitted staging attempt) were read in rather than computed in a unified, end-to-end execution.
- **Scientific Implication**:
  Because intermediate ablation evidence was reused across distinct runtime sessions without end-to-end verification under a single clean execution environment, intermediate data transformations cannot be certified as free from transient side effects.

### D. Hard-Coded Reporting Literals and Flawed Interpretations
- **Observed Literals in `reporting.py`**:
  The previous reporting module contained hard-coded static strings with cost effects of `-1.42`, `+0.18`, and `-0.09` SCU, an arbitrary "85% lower acceptance boundary", and speculative assertions that higher coverage is always better or that noise causes monotonic degradation.
- **Diagnostic Observation vs Reality**:
  The actual equal-weight six-cell descriptive means computed from the v2 `factor_main_effects.csv` were:
  - `gamma_scale`: `-10.482297` SCU
  - `beta_asymmetry`: `-1.214172` SCU
  - `regime_routing`: `+0.559421` SCU
  These figures were diagnostic observations of the v2 data, but were masked by hardcoded narrative text in the synthesis reports.

---

## 3. What the v2 Evidence Proves vs What Cannot Be Reconstructed

| Dimension | What v2 Evidence Proves | What Conflicts or Cannot Be Reconstructed |
| :--- | :--- | :--- |
| **Ablation Structure** | 240 cells ($3 \times 2 \times 5 \times 8$) were defined and evaluated against the 122 held-out test engines. | Exact uncommitted source code generating intermediate ablation records is lost due to `git_dirty: true`. |
| **Stress Probes** | 1,620 stress evaluations ($3 \times 2 \times 5 \times 18 \times 3 \text{ methods}$) were run and point prediction streams were generated. | Execution timeline was non-atomic (48-hour timestamp span vs 49-minute runtime). |
| **Calibrators** | Quantile thresholds were fit using hierarchical conformal prediction on calibration caches. | Regime threshold records lacked strict fail-closed presence verification during automated audit. |
| **Bootstrap Contrasts** | 10,000 paired draws were sampled and contrast statistics were computed. | Verification only audited a single sample key rather than all 1,176 contrasts and 126 factor effects. |
| **Synthesis Reports** | Synthesis markdown and matplotlib figures were generated. | Reports emitted hardcoded literal values and unsupported monotonic degradation claims. |

---

## 4. Preservation Policy for v1 and v2

1. **Byte-for-Byte Preservation**:
   - `experiments/phase08_exploratory_v1/` and `research/results/phase08_exploratory_v1/` remain untouched.
   - `experiments/phase08_exploratory_v2/` and `research/results/phase08_exploratory_v2/` remain untouched.
   - None of their files, manifests, logs, or tables will be deleted or silently overwritten.
2. **Historical Classification**:
   - Both v1 and v2 are classified as historical, superseded exploratory bundles.
   - They must not be cited or transcribed as primary evidence for the research paper or synopsis.

---

## 5. Transition to Authoritative Successor (`phase08_exploratory_v3`)

The authoritative successor bundle (`phase08_exploratory_v3`) addresses every identified deficiency:
1. **Clean Commit Enforcement**: Executed strictly from a committed tree with `git_dirty: false` and `--allow-dirty` disallowed.
2. **Streaming Direct-to-Disk Architecture**: Per-cycle interval streams (`ablation_interval_predictions.csv.gz` and `stress_interval_predictions.csv.gz`) are streamed directly to gzip without intermediate memory accumulation, preventing RAM blowup.
3. **Preloaded Checkpoint Inference**: Base model checkpoints are loaded into memory once and reused across all 540 stress cells.
4. **Independent Reference Verifier**: Full independent audit verifying:
   - 100% of all 1,176 paired contrasts and 126 factor effects against independent PCG64 bootstrap draws;
   - All 240 exploratory calibrators with fail-closed regime threshold checks;
   - Pre- and post-execution protected input hash invariance (163 protected files);
   - Checkpoint prediction parity at `atol=1e-4` and deterministic reconstruction at `atol=1e-10`.
5. **Dynamic, Literal-Free Reporting**: All report values, factor main effects, and contrast tables are computed dynamically from independently audited evidence, with no hardcoded scientific constants.
