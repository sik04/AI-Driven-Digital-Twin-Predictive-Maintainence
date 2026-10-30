# Phase 8: Exploratory Component Ablation and Robustness Analysis

- **Protocol**: `phase08-v1`
- **Authoritative Evidence Location**: `experiments/phase08_exploratory_v3/`
- **Submission Audit Location**: `experiments/phase08_submission_verification_v1/independent_audit.json`
- **Authoritative Report Location**: `research/results/phase08_submission_v2/`
- **Writing Handoff Document**: [`research/results/phase08_submission_v2/writing_handoff.md`](../../research/results/phase08_submission_v2/writing_handoff.md)
- **Execution Commit SHA**: `2e8acb156e26eb0aeec3d0ed93e4d84b0e612355` (`git_dirty: false`)

---

## 1. Overview & Objectives

Phase 8 provides an exploratory post-confirmatory investigation into the mechanisms and sensitivity limits of the conformal prediction systems evaluated in Step 9:
1. **Experiment A (Component Ablation)**: Disentangles the individual and interactive contributions of the three components in `decision_aware_hcp`: scale dilation ($\gamma \in \{0, 2\}$), asymmetry ($\beta \in \{0, -\ln(2)\}$), and condition-adaptive routing (`global` vs. `regime`).
2. **Experiment B (Stress Testing)**: Probes empirical degradation boundaries of frozen calibrators under sensor Gaussian noise, causal forward-fill sensor dropout, and operational setting measurement bias across 1,620 method evaluations.

---

## 2. Versioning History and Historical Bundle Supersession

To protect scientific integrity and traceability, earlier exploratory bundles are preserved byte-for-byte and superseded:

- **v1 Bundle (`experiments/phase08_exploratory_v1/`)**: Initial exploratory prototype. Preserved byte-for-byte as historical; superseded due to incomplete stress matrix coverage and initial uncompressed streaming formats.
- **v2 Bundle (`experiments/phase08_exploratory_v2/`)**: Intermediate evaluation bundle. Preserved byte-for-byte as historical material. As documented in [`docs/development/phase08_v2_provenance_review.md`](phase08_v2_provenance_review.md), v2 was executed with `--allow-dirty` (`git_dirty: true`), had execution timestamps spanning over 48 hours while recording ~49 minutes duration, and reused prior log entries. It is unsuitable as the final authoritative manuscript evidence source.
- **v3 Authoritative Bundle (`experiments/phase08_exploratory_v3/`)**: The clean, authoritative successor executed from clean commit `2e8acb156e26eb0aeec3d0ed93e4d84b0e612355` without dirty flags. Outputs were staged externally to avoid dirtying the source tree.
- **Submission Verification Bundle (`experiments/phase08_submission_verification_v1/`)**: Fully audited with independent reference verifier under schema `phase08-independent-audit-v3`, passing all 10 mandatory checks with 0 failing reasons and maximum absolute error $\le 4.55 \times 10^{-13}$.
- **Submission Reports Bundle (`research/results/phase08_submission_v1/`)**: Historical initial submission reporting bundle, preserved unchanged for provenance.
- **Submission Reports Bundle v2 (`research/results/phase08_submission_v2/`)**: Active authoritative reports, publication figures (PDF/PNG), `results_summary.md`, `writing_handoff.md`, and non-circular `final_receipt.json`. `phase08_submission_v2` corrects documentation-path portability using the same audited evidence. It does not represent a new experiment or changed result.

---

## 3. Architecture & File Structure

The implementation is located under `src/intellitwin/robustness/`:
- `__init__.py`: Public package exports.
- `ablation.py`: Factorial configuration definitions, candidate mapping, exploratory calibrator fitting, and ablation evaluation.
- `perturbations.py`: Deterministic feature-stream perturbation generators (Gaussian noise, causal forward-fill dropout, setting bias) with exact PCG64 SeedSequence reproducibility.
- `runner.py`: Orchestrates Experiment A and Experiment B execution with CPU batching, direct-to-gzip streaming, base model preloading, and immutable artifact generation.
- `statistics.py`: Engine-level metric aggregation, paired stratified cluster-bootstrap (10,000 draws, PCG64 `[2026, 8, ds_num]`), factor main-effects computation, and unadjusted 95% confidence intervals.
- `verification.py`: Independent reference verifier performing closed-form threshold reconstruction, bootstrap draw validation, perturbation hash checks, and parity audits without importing production runner, perturbation, windowing, or scoring routines.
- `reporting.py`: Markdown synthesizer, dynamic CSV summarizer, and high-resolution publication figure generator with cell-level variation display, bound to passing audit.

---

## 4. CLI Interfaces

### Historical Invocations (Published Artifacts)
The following commands record the historical invocations that generated the published evidence, audit, and successor report bundles (do not rerun into published directories):

- **Historical Run**:
  ```bash
  python scripts/run_phase08_robustness.py \
      --output-dir experiments/phase08_exploratory_v3 \
      --report-dir research/results/phase08_exploratory_v3
  ```
- **Historical Audit**:
  ```bash
  python scripts/audit_phase08_robustness.py \
      --evidence-dir experiments/phase08_exploratory_v3 \
      --output-audit experiments/phase08_submission_verification_v1/independent_audit.json
  ```
- **Historical Reporting Finalization (v2)**:
  ```bash
  python scripts/finalize_phase08_reporting.py \
      --base-dir . \
      --evidence-dir experiments/phase08_exploratory_v3 \
      --audit-path experiments/phase08_submission_verification_v1/independent_audit.json \
      --report-dir research/results/phase08_submission_v2
  ```

### Local Reproduction Workflow
To reproduce Phase 8 execution, independent auditing, and reporting locally without overwriting published evidence, use new, unoccupied reproduction directories:

1. **Execute Exploratory Matrix Locally**:
   ```bash
   python scripts/run_phase08_robustness.py \
       --output-dir experiments/local_reproduction \
       --report-dir research/results/local_reproduction_exploratory
   ```

2. **Run Independent Reference Audit**:
   ```bash
   python scripts/audit_phase08_robustness.py \
       --evidence-dir experiments/local_reproduction \
       --output-audit experiments/local_reproduction/independent_audit.json
   ```

3. **Finalize Reporting Bundle**:
   ```bash
   python scripts/finalize_phase08_reporting.py \
       --base-dir . \
       --evidence-dir experiments/local_reproduction \
       --audit-path experiments/local_reproduction/independent_audit.json \
       --report-dir research/results/local_reproduction
   ```

---

## 5. Scientific Guardrails & Interpretive Boundaries

- All findings in Phase 8 are strictly `EXPLORATORY_POST_CONFIRMATORY`.
- They do not alter or overturn the frozen `UNSUPPORTED` outcomes for RQ1–RQ4.
- Negative, null, and non-monotonic responses under synthetic stress probes are reported without claims of physical real-world invariance.
- RUL interval lower-tail misses ($y < L$) must not be conflated with physical turbine failure events ($T$).
- Aggregate means across the six cells are descriptive summaries and must not be reported as pooled inferential parameters.
