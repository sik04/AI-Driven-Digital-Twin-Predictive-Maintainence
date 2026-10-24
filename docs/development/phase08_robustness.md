# Phase 8: Exploratory Component Ablation and Robustness Analysis

## 1. Overview & Objectives

Phase 8 provides an exploratory post-confirmatory investigation into the mechanisms and sensitivity limits of the conformal prediction systems evaluated in Step 9:
1. **Experiment A (Component Ablation)**: Disentangles the individual and interactive contributions of the three components in `decision_aware_hcp`: scale dilation ($\gamma \in \{0, 2\}$), asymmetry ($\beta \in \{0, -\ln(2)\}$), and condition-adaptive routing (`global` vs. `regime`).
2. **Experiment B (Stress Testing)**: Probes empirical degradation boundaries of frozen calibrators under sensor Gaussian noise, causal sensor dropout, and operational setting measurement bias.

## 2. Architecture & File Structure

The implementation is located under `src/intellitwin/robustness/`:
- `__init__.py`: Public package exports.
- `ablation.py`: Factorial configuration definitions, candidate mapping, exploratory calibrator fitting, and ablation evaluation.
- `perturbations.py`: Deterministic feature-stream perturbation generators (Gaussian noise, causal forward-fill dropout, setting bias) with exact PCG64 SeedSequence reproducibility.
- `runner.py`: Orchestrates Experiment A and Experiment B execution with CPU batching and immutable artifact generation.
- `statistics.py`: Engine-level metric aggregation, paired stratified cluster-bootstrap (10,000 draws, PCG64 `[2026, 8, ds_num]`), factor main-effects computation, and unadjusted 95% confidence intervals.
- `verification.py`: Independent reference verifier performing closed-form threshold reconstruction, bootstrap draw validation, perturbation hash checks, and parity audits.
- `reporting.py`: Markdown synthesizer, CSV summarizer, and high-resolution publication figure generator.

## 3. CLI Interfaces

- **Run Script**: `scripts/run_phase08_robustness.py`
  ```bash
  python scripts/run_phase08_robustness.py --output-dir experiments/phase08_exploratory_v1 --report-dir research/results/phase08_exploratory_v1
  ```
- **Audit Script**: `scripts/audit_phase08_robustness.py`
  ```bash
  python scripts/audit_phase08_robustness.py --evidence-dir experiments/phase08_exploratory_v1 --output-audit <audit-path>
  ```

## 4. Scientific Guardrails

- All findings in Phase 8 are strictly `EXPLORATORY_POST_CONFIRMATORY`.
- They do not alter or overturn the frozen `UNSUPPORTED` outcomes for RQ1–RQ4.
- Negative, null, and non-monotonic responses under synthetic stress probes are reported without claims of physical real-world invariance.
