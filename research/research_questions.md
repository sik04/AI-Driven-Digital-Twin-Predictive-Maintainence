# Provisional Research Questions and Direction

> **Important Notice on Scientific Status**:
> The questions and directions documented below represent **provisional research hypotheses**. They reflect initial inquiries formulated by the research team (Mayank Singh, Shiksha Pandey, and Ruchi Gupta) prior to conducting the formal systematic literature review.
>
> **No claim of novelty is asserted at this stage.** These questions are subject to formal refinement, sharpening, or revision following the completion of Phase 1 (Systematic Literature Review) and Phase 2 (Research Gap and Hypotheses Formulation).

---

## Provisional Candidate Research Questions

### Research Question 1 (RQ1: Benchmark Comparison under Strict Protocol)
- **Question**: *How do selected Remaining Useful Life (RUL) prediction methods compare under a consistent, leak-free engine-level evaluation protocol?*
- **Motivation**: Existing literature frequently reports disparate RUL metrics without consistent windowing strategies, engine-isolation criteria, or standardized scaling regimes, hindering fair head-to-head comparison.
- **Provisional Hypothesis**: When evaluated under strictly identical engine-level splits and preprocessing pipelines, temporal deep learning architectures will exhibit lower late-prediction penalties (asymmetric scoring) than standard non-recurrent baselines, but the magnitude of advantage may vary across single- vs. multi-operating condition datasets.
- **Status**: Provisional; to be refined post-literature review.

---

### Research Question 2 (RQ2: Uncertainty Quantification Reliability)
- **Question**: *How reliably can uncertainty estimates quantify RUL prediction error across varying operating conditions and asset wear stages?*
- **Motivation**: Point predictions of RUL lack risk boundaries, which are critical in aviation and industrial maintenance where under-estimating failure cycles can lead to catastrophic damage.
- **Provisional Hypothesis**: Calibrated prediction intervals (e.g., via inductive conformal prediction or ensemble variance) achieve empirical coverage probabilities matching nominal confidence levels ($1 - \alpha$), with interval widths narrowing meaningfully as assets approach end-of-life.
- **Status**: Provisional; to be refined post-literature review.

---

### Research Question 3 (RQ3: Uncertainty-Aware Maintenance Decision Quality)
- **Question**: *Can uncertainty-aware maintenance decisions improve warning quality and reduce operational risk relative to appropriate simple baseline heuristics?*
- **Motivation**: Traditional predictive maintenance decisions rely on arbitrary static RUL thresholds (e.g., schedule overhaul when $\hat{\text{RUL}} < 30$), which ignore prediction variance.
- **Provisional Hypothesis**: Factoring lower prediction bounds and uncertainty percentiles into maintenance scheduling policies reduces catastrophic late warnings without incurring prohibitive false-alarm maintenance overhead.
- **Status**: Provisional; to be refined post-literature review.

---

### Research Question 4 (RQ4: Component Utility and Boundary Conditions)
- **Question**: *Which framework components provide measurable empirical benefits, and under what operational conditions do these benefits persist?*
- **Motivation**: Complex machine learning pipelines frequently incorporate multiple modules without verifying whether each sub-component contributes statistically significant value.
- **Provisional Hypothesis**: Systematic component ablations and stress testing under injected sensor noise will identify the specific operational regimes where recurrent temporal modelling, conformal calibration, and adaptive thresholding each provide statistically significant improvements.
- **Status**: Provisional; to be refined post-literature review.

---

## Revision Protocol

Following Phase 1 (Systematic Literature Review), this document will be updated to:
1. Re-evaluate each candidate question against published methodologies.
2. Formalize explicit null ($H_0$) and alternative ($H_1$) hypotheses.
3. Define the precise statistical tests and validation metrics corresponding to each hypothesis.
