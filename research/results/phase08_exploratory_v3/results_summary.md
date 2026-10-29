# Phase 8 Exploratory Ablation & Robustness Analysis: Scientific Synthesis

- **Protocol Version**: `phase08-v1`
- **Status**: Verified Exploratory Analysis
- **Scope**: 240 Ablation Cells, 1,620 Stress Evaluations across 122 Held-Out Engines
- **Scientific Status**: EXPLORATORY_POST_CONFIRMATORY (Original RQ1–RQ4 confirmatory classifications remain frozen as UNSUPPORTED)

---

## 1. Executive Summary & Observed Findings

Phase 8 conducts an exploratory post-confirmatory investigation into the sensitivity and component contributions of the conformal predictive maintenance systems evaluated in Step 9. All findings are derived directly from independently verified evidence tables.

1. **Scale Dilation (gamma: 2 vs 0)**: Associated with an unweighted descriptive mean cost reduction of -10.4823 SCU across the six evaluated cells. Cell-level estimates range from -17.1560 to -6.5365 SCU.
2. **Directional Asymmetry (beta: -ln(2) vs 0)**: Yields an unweighted descriptive mean cost reduction of -1.2142 SCU across the six evaluated cells (cell-level range: -1.4435 to -0.8700 SCU).
3. **Operating Regime Routing (regime vs global)**: Shows an unweighted descriptive mean cost increase of +0.5594 SCU across all six cells. On FD001 (single operating condition), routing has exactly zero effect across all metrics by mathematical equivalence (global == regime); on multi-regime datasets (FD002, FD004), routing exhibits localized cell-dependent differences.
4. **Engineering Stress Probes**: Under Gaussian sensor noise probes, the mean paired cost difference relative to clean streams was +0.0000 SCU across all evaluated noise conditions and methods. Under causal sensor dropout probes, the mean paired coverage change relative to clean was +0.0000. Observed responses vary by cell and condition; no universal physical degradation law is claimed.

---

## 2. Factorial Component Main Effects on Maintenance Cost

| Dataset | Model | Factor | Effect (On - Off) | 95% Bootstrap CI |
| :--- | :--- | :--- | :---: | :---: |
| FD001 | GBR | gamma_scale | -10.1800 SCU | [-11.8600, -8.4550] |
| FD001 | GBR | beta_asymmetry | -1.4000 SCU | [-2.1050, -0.8700] |
| FD001 | GBR | regime_routing | +0.0000 SCU | [+0.0000, +0.0000] |
| FD001 | LSTM | gamma_scale | -11.1600 SCU | [-12.9481, -9.2660] |
| FD001 | LSTM | beta_asymmetry | -1.2960 SCU | [-1.6710, -0.9710] |
| FD001 | LSTM | regime_routing | +0.0000 SCU | [+0.0000, +0.0000] |
| FD002 | GBR | gamma_scale | -6.5365 SCU | [-7.0798, -6.0038] |
| FD002 | GBR | beta_asymmetry | -1.1558 SCU | [-1.4038, -0.9250] |
| FD002 | GBR | regime_routing | +0.0615 SCU | [-0.0683, +0.1740] |
| FD002 | LSTM | gamma_scale | -9.8438 SCU | [-10.8002, -8.9510] |
| FD002 | LSTM | beta_asymmetry | -1.4435 SCU | [-1.6548, -1.2479] |
| FD002 | LSTM | regime_routing | +0.2704 SCU | [+0.1796, +0.3683] |
| FD004 | GBR | gamma_scale | -17.1560 SCU | [-19.0670, -15.2970] |
| FD004 | GBR | beta_asymmetry | -0.8700 SCU | [-1.1040, -0.6590] |
| FD004 | GBR | regime_routing | +0.7200 SCU | [+0.3360, +1.1420] |
| FD004 | LSTM | gamma_scale | -8.0174 SCU | [-9.4986, -6.6020] |
| FD004 | LSTM | beta_asymmetry | -1.1198 SCU | [-1.3170, -0.9292] |
| FD004 | LSTM | regime_routing | +2.3046 SCU | [+2.0252, +2.5806] |

> [!IMPORTANT]
> **Descriptive Aggregate Means**:
> - `gamma_scale`: -10.4823 SCU
> - `beta_asymmetry`: -1.2142 SCU
> - `regime_routing`: +0.5594 SCU
> *Note: These unweighted averages across the six dataset/model combinations are descriptive summaries. Because bootstrap confidence intervals reflect cell-specific engine sampling variability, interval endpoints cannot be pooled or averaged across heterogeneous populations.*

---

## 3. Methodological Guardrails & Interpretive Boundaries

1. **Exploratory Post-Confirmatory Standing**: Phase 8 was designed after inspection of held-out confirmatory results. Findings are hypothesis-generating and exploratory; they do not overturn the frozen Step 9 RQ1–RQ4 `UNSUPPORTED` classifications.
2. **Coverage and Width Trade-offs**: Calibration is evaluated against the 90% nominal target and proper interval scores. Higher coverage is not inherently superior when achieved through excessive width; narrower intervals are not superior when undercovering.
3. **Terminal Precedence**: RUL lower-tail misses ($y < L$) indicate predictive bound misses and must not be conflated with simulated physical turbine failure events ($T$).
4. **Independent Audit**: The evidence supporting these reports was independently verified by the reference audit protocol with zero failing reasons.
