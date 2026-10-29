# Authoritative Writing Handoff: Research Paper and Synopsis Synthesis

- **Document Version**: `writing-handoff-v1`
- **Date**: 2026-10-28
- **Authors**: Mayank Singh, Shiksha Pandey, Ruchi Gupta
- **Authoritative Evidence Bundle**: `experiments/phase08_exploratory_v3/`
- **Authoritative Report Bundle**: `research/results/phase08_exploratory_v3/`
- **Authoritative Execution Commit SHA**: `2e8acb156e26eb0aeec3d0ed93e4d84b0e612355`
- **Independent Audit Path**: `experiments/phase08_exploratory_v3/independent_audit.json` (`overall_status: PASS`, 0 failing reasons)
- **Final Receipt Path**: `experiments/phase08_exploratory_v3/final_receipt.json`

---

## 1. Authoritative Evidence Locations & Provenance

| Component | Path | Description & Integrity |
| :--- | :--- | :--- |
| **Execution Manifest** | `experiments/phase08_exploratory_v3/execution_manifest.json` | Hash inventory of all 265 evidence artifacts; run ID `phase08_run_20261027T201759014005+0000`, `git_dirty: false`. |
| **Input Manifest** | `experiments/phase08_exploratory_v3/input_manifest.json` | Before/after SHA-256 hashes for all 163 protected inputs (raw data, splits, base models, calibrators, caches). |
| **Independent Audit** | `experiments/phase08_exploratory_v3/independent_audit.json` | Complete independent reference reconstruction (max discrepancy 8.53e-14, atol=1e-10, 0 failing reasons). |
| **Final Receipt** | `experiments/phase08_exploratory_v3/final_receipt.json` | Non-circular checksum linking execution manifest, verifier source SHA, independent audit, and all reports. |
| **Ablation Summary** | `experiments/phase08_exploratory_v3/ablation_summary.csv` | Summary across 240 factorial ablation configurations. |
| **Stress Summary** | `experiments/phase08_exploratory_v3/stress_summary.csv` | Summary across 1,620 stress evaluations under 18 stream conditions. |
| **Paired Contrasts** | `experiments/phase08_exploratory_v3/paired_contrasts.csv` | 1,176 non-trivial paired contrasts with 10,000-draw stratified bootstrap 95% CIs. |
| **Factor Main Effects** | `experiments/phase08_exploratory_v3/factor_main_effects.csv` | 126 factor main effects across the 3 factorial dimensions ($\gamma$, $\beta$, routing). |
| **Zero Difference Checks** | `experiments/phase08_exploratory_v3/zero_difference_checks.csv` | 168 identical self-contrast sanity checks (delta_point = 0.0, CIs = [0.0, 0.0]). |
| **Subgroup Metrics** | `experiments/phase08_exploratory_v3/subgroup_metrics.csv` | Equal-engine weighted coverage and tail miss rates across regimes and lifecycle stages. |
| **Provenance Review** | `docs/development/phase08_v2_provenance_review.md` | Forensic audit documenting why v1 and v2 are preserved byte-for-byte as historical/superseded. |

---

## 2. Frozen Confirmatory Baseline (Step 9 / RQ1–RQ4)

The confirmatory findings remain strictly frozen, un-recalibrated, and preserved under `experiments/confirmatory_v1/`. Phase 8 exploratory results must **never** be cited as overturning or resolving confirmatory outcomes.

| Research Question | Confirmatory Classification | Key Evidence Path | Methodological Rationale |
| :--- | :--- | :--- | :--- |
| **RQ1** (Maintenance Utility with Reliability Safeguards) | **UNSUPPORTED** | `experiments/confirmatory_v1/step09_confirmatory_audit.json` | While cost improvement passed across 4 cells, required worst-stage coverage safeguards failed (`RQ1_GBR_worst_stage_coverage_ceiling`, `RQ1_LSTM_worst_stage_coverage_ceiling`). Under intersection-union testing (IUT), joint claim fails. |
| **RQ2** (Conditional Reliability & Interval Sharpness) | **UNSUPPORTED** | `experiments/confirmatory_v1/step09_confirmatory_audit.json` | Fails conditional regime error improvement and worst-stage coverage safeguards. |
| **RQ3** (Attribution vs. Matched-Conservatism Controls) | **UNSUPPORTED** | `experiments/confirmatory_v1/step09_confirmatory_audit.json` | Fails point-safety-margin cost improvement and worst-stage coverage safeguards. |
| **RQ4** (Cross-Dataset & Cross-Model Robustness) | **UNSUPPORTED** | `experiments/confirmatory_v1/step09_confirmatory_audit.json` | Fails worst-stage coverage ceilings across multiple sub-corpora. |

Manuscript Rule: The paper must state clearly that the primary confirmatory hypotheses regarding decision-aware conformal prediction utility and reliability were **not supported** under the preregistered Bonferroni/IUT criteria.

---

## 3. Verified Phase 8 Exploratory Findings

All findings reported below are exploratory post-confirmatory observations derived from independently verified tables.

### 3.1 Factorial Component Main Effects on Maintenance Cost (SCU)

Estimated via paired differences ($On - Off$) with 10,000 stratified engine bootstrap draws:

| Dataset | Model Family | Factor | Effect ($On - Off$) | 95% Bootstrap CI | Stated Direction |
| :--- | :--- | :--- | :---: | :---: | :--- |
| FD001 | GBR | `gamma_scale` | -10.1800 SCU | [-11.8600, -8.4550] | Cost reduction |
| FD001 | GBR | `beta_asymmetry` | -1.4000 SCU | [-2.1050, -0.8700] | Cost reduction |
| FD001 | GBR | `regime_routing` | +0.0000 SCU | [+0.0000, +0.0000] | Null (Identical by definition) |
| FD001 | LSTM | `gamma_scale` | -11.1600 SCU | [-12.9481, -9.2660] | Cost reduction |
| FD001 | LSTM | `beta_asymmetry` | -1.2960 SCU | [-1.6710, -0.9710] | Cost reduction |
| FD001 | LSTM | `regime_routing` | +0.0000 SCU | [+0.0000, +0.0000] | Null (Identical by definition) |
| FD002 | GBR | `gamma_scale` | -6.5365 SCU | [-7.0798, -6.0038] | Cost reduction |
| FD002 | GBR | `beta_asymmetry` | -1.1558 SCU | [-1.4038, -0.9250] | Cost reduction |
| FD002 | GBR | `regime_routing` | +0.0615 SCU | [-0.0683, +0.1740] | Inconclusive / Near-zero |
| FD002 | LSTM | `gamma_scale` | -9.8438 SCU | [-10.8002, -8.9510] | Cost reduction |
| FD002 | LSTM | `beta_asymmetry` | -1.4435 SCU | [-1.6548, -1.2479] | Cost reduction |
| FD002 | LSTM | `regime_routing` | +0.2704 SCU | [+0.1796, +0.3683] | Modest cost increase |
| FD004 | GBR | `gamma_scale` | -17.1560 SCU | [-19.0670, -15.2970] | Cost reduction |
| FD004 | GBR | `beta_asymmetry` | -0.8700 SCU | [-1.1040, -0.6590] | Cost reduction |
| FD004 | GBR | `regime_routing` | +0.7200 SCU | [+0.3360, +1.1420] | Modest cost increase |
| FD004 | LSTM | `gamma_scale` | -8.0174 SCU | [-9.4986, -6.6020] | Cost reduction |
| FD004 | LSTM | `beta_asymmetry` | -1.1198 SCU | [-1.3170, -0.9292] | Cost reduction |
| FD004 | LSTM | `regime_routing` | +2.3046 SCU | [+2.0252, +2.5806] | Modest cost increase |

**Unweighted Six-Cell Descriptive Means** (Diagnostic only; not pooled inferential parameters):
- `gamma_scale`: **-10.4823 SCU**
- `beta_asymmetry`: **-1.2142 SCU**
- `regime_routing`: **+0.5594 SCU**

*Note on Reporting*: The manuscript must report all six individual cell estimates and bootstrap intervals. Do not average CI endpoints across cells or imply an overall inferential p-value for the combined population.

---

## 4. Separation of Confirmatory and Exploratory Conclusions

1. **Confirmatory Verdict**: The preregistered confirmatory study demonstrated that `decision_aware_hcp` **failed to meet joint confirmatory standards** because required worst-stage coverage bounds were breached, despite achieving cost reductions in specific operational regimes.
2. **Exploratory Attribution**: Post-confirmatory factor ablation reveals that maintenance cost reductions are predominantly driven by **scale dilation ($\gamma$)**, which systematically expands late-life intervals to avoid catastrophic premature interventions, with a secondary contribution from **safety buffer asymmetry ($\beta$)**.
3. **Condition-Adaptive Routing Limitation**: Operating-regime routing provides **zero benefit on single-condition fleets (FD001)** and exhibits small, heterogeneous cost increases on complex multi-condition fleets (FD002, FD004), contradicting the prior intuition that regime-partitioned calibration is universally superior.

---

## 5. Defensible Scientific Contribution Statement

The paper should articulate the contribution within strictly defensible boundaries:
> *"We formulate and rigorously evaluate a decision-aware, condition-adaptive conformal prediction framework for turbofan predictive maintenance under a preregistered confirmatory protocol. While the proposed method demonstrated maintenance cost reductions in primary settings, it failed preregistered confirmatory acceptance due to conditional coverage degradation in late-life degradation stages. Through post-confirmatory factorial ablation and independent reference auditing, we isolate the distinct mathematical drivers of decision-aware conformal bounds—demonstrating that scale dilation and directional asymmetry drive cost containment, whereas naive operating-regime partitioning introduces variance penalties on multi-condition fleets. Finally, we provide an open, fully reproducible validation telemetry replay prototype establishing traceability from raw sensor streams to decision outcomes."*

### Explicitly Disallowed Claims in Manuscript
- **DO NOT claim** that decision-aware HCP is "superior" or "outperforms" standard conformal baselines in confirmatory terms.
- **DO NOT claim** that higher coverage is unconditionally better (excessive width degrades interval scores).
- **DO NOT claim** that narrow intervals are inherently superior when undercovering.
- **DO NOT claim** that Gaussian noise or sensor dropout degrades coverage monotonically.
- **DO NOT conflate** RUL interval lower-tail misses ($y < L$) with physical turbine terminal failure events ($T$).
- **DO NOT claim** the Digital Twin prototype provides closed-loop bidirectional synchronization with live aircraft.

---

## 6. Digital Twin Scope & Software Boundary

- **Prototype Scope**: The software implementation (`src/intellitwin/twin/` and `apps/twin_dashboard/`) is strictly a **historical validation-telemetry replay prototype**.
- **Operation**: Replays NASA C-MAPSS validation engines through causal lookback sliding windows (length 30) without lookahead, streaming point predictions, conformal bounds, and maintenance recommendations to an interactive dashboard.
- **Scientific Role**: Software artifact providing interactive reproducibility, visualization, and parameter inspection. It does not generate new confirmatory evidence.

---

## 7. Approved Publication Figures and Generating Artifacts

All figures approved for publication are located in `research/results/phase08_exploratory_v3/figures/`:

| Figure File | Title / Caption | Generating Artifact |
| :--- | :--- | :--- |
| `scale_asymmetry_routing_paired_effects.pdf` | Cell-level and descriptive mean maintenance cost effects ($On - Off$) for scale dilation ($\gamma$), asymmetry ($\beta$), and routing. | `factor_main_effects.csv` |
| `ablation_cost_vs_coverage.pdf` | Empirical trade-off between total maintenance cost and empirical coverage across all 8 factorial variants (2×3 dataset/model layout). | `ablation_summary.csv` |
| `lower_upper_miss_rates_by_lifecycle_stage.pdf` | Lower ($y < L$) vs Upper ($y > U$) tail miss rates across early, mid, and late lifecycle stages (distinguishing bound misses from physical failure). | `subgroup_metrics.csv` |
| `noise_level_degradation.pdf` | Sensitivity of coverage and cost across additive Gaussian sensor noise probe levels ($\sigma \in \{0.05, 0.10, 0.20\}$). | `stress_summary.csv` |
| `dropout_degradation.pdf` | Response under causal forward-fill sensor dropout ($p \in \{0.05, 0.10\}$) across frozen conformal methods. | `stress_summary.csv` |
| `setting_bias_comparisons.pdf` | Impact of operational setting-1 measurement bias ($\pm 0.20$) on empirical coverage and maintenance cost. | `stress_summary.csv` |

---

## 8. Remaining Limitations

1. **Post-Confirmatory Nature**: All Phase 8 analyses were designed after inspecting held-out test data. P-values and confidence intervals are unadjusted for multiple post-hoc comparisons.
2. **Synthetic Stress Probes**: Gaussian noise, dropout, and setting bias are mathematical stress probes, not physically simulated turbofan hardware faults.
3. **Synthetic Cost Scenarios**: The primary maintenance cost scenario ($1:5:0.2$) is an engineering model of turbine maintenance, not an airline-audited operational accounting ledger.
4. **No Winning Model Selection**: Phase 8 does not select a "repaired winning model" to replace the evaluated candidates. Production weights and calibrators remain frozen.
