# Scientific and Project Risk Register

This register identifies, monitors, and tracks mitigations for scientific, technical, and methodological risks associated with the IntelliTwin research project.

---

## Risk Assessment Matrix

| Risk ID | Risk Description | Severity | Likelihood | Mitigation Strategy | Status |
| :--- | :--- | :---: | :---: | :--- | :---: |
| **RSK-01** | **Data leakage and invalid splits**<br>Cycle lookahead or sharing engine units across train and test sets. | High | Medium | Enforce strict engine-level split assertions in preprocessing scripts; verify that normalizers fit solely on training engines. | Active / Monitored |
| **RSK-02** | **Unverified or incorrectly constructed RUL labels**<br>Arbitrary piecewise linear RUL caps without empirical or literature justification. | High | Medium | Lock piecewise linear threshold at $RUL_{max} = 125$ cycles in Step 5.1 (ADR-012), preserving uncapped $RUL_{true}$ for evaluation. | Active / Monitored |
| **RSK-03** | **Inconsistent evaluation units**<br>Mixing operating cycles, operational hours, and normalized time steps across comparative tables. | Medium | Low | Standardize all reported metrics (RMSE, MAE, Score, MPIW) explicitly to discrete operational cycles. | Active / Monitored |
| **RSK-04** | **Test-set contamination during model selection**<br>Using test partitions to tune model architecture, epochs, or hyperparameters. | High | Medium | Isolate a dedicated engine-level validation partition from the training set for all model selection and early stopping. | Active / Monitored |
| **RSK-05** | **Unsupported novelty claims**<br>Claiming methodological or architectural novelty without verifying prior literature. | High | Low | Conduct systematic literature review in Phase 1; prohibit novelty assertions in manuscripts until validated against literature matrix. | Active / Monitored |
| **RSK-06** | **Unreproducible experiments**<br>Unrecorded random seeds, non-deterministic operations, or missing execution metadata. | High | Low | Enforce mandatory experiment logging via `experiments/templates/experiment_record.md` with explicit seeds, git hashes, and hardware info. | Active / Monitored |
| **RSK-07** | **Dataset licensing or provenance issues**<br>Using benchmark datasets without clear attribution, provenance, or compliance with license terms. | Medium | Low | Verify open-science NASA C-MAPSS dataset terms; document official repository links, publication origins, and citations in `docs/`. | Active / Monitored |
| **RSK-08** | **Unsupported industrial-deployment claims**<br>Asserting readiness for production aircraft without real-world testbed verification. | Medium | Low | Scope manuscript explicitly as an offline algorithmic benchmark study and simulation framework, avoiding unverified production claims. | Active / Monitored |
| **RSK-09** | **Misleading uncertainty guarantees**<br>Assuming Gaussian errors when true degradation residual distributions are heteroscedastic or heavy-tailed. | High | Medium | Adopt distribution-free uncertainty methods (e.g., conformal prediction) and empirically evaluate empirical coverage ($PICP$) against nominal level ($1-\alpha$). | Active / Monitored |
| **RSK-10** | **Incomplete dependency or environment specifications**<br>Code breaking across operating systems or package versions. | Medium | Low | Use modern `pyproject.toml`, test across Python versions (3.10–3.13) in CI, and pin environment lockfiles during Phase 10. | Mitigated / Continuous |
| **RSK-11** | **Synthetic economic cost assumptions**<br>Stylized linear cost model ($C_{\text{PM}}, C_{\text{FAIL}}, C_{\text{WASTE}}$) may be mistaken for empirical airline economics. | High | High | Scope scenarios explicitly as benchmark preferences chosen prior to test results; clearly distinguish benchmark acceptance margins from airline financial constants. | Active / Monitored |
| **RSK-12** | **Small sample subgroups and inconclusive outcomes**<br>Small engine counts in subgroups ($\ge 10$ engines) or limited test fleet size may yield wide decision intervals. | High | Medium | Pre-specify explicit "Inconclusive" decision logic under 98.75% decision intervals (ADR-018); prohibit claiming support when CI overlaps margins. | Active / Monitored |
| **RSK-13** | **Approximate cluster-bootstrap inference**<br>Percentile bootstrap intervals are asymptotic approximations and may suffer finite-sample error on non-smooth statistics. | Medium | Medium | Use 10,000 resamples, stratified quartiles, and conservative missing-group bound propagation ($[0, 0.90]$); flag degenerate intervals. | Active / Monitored |
| **RSK-14** | **Conditional inference for fixed trained runs**<br>Results may not generalize to arbitrary random model initializations outside the 5 fixed seeds. | Medium | Medium | Formulate primary estimand strictly over the 5 fixed trained runs (`[2026, 2027, 2028, 2029, 2030]`); report individual seed runs separately. | Active / Monitored |
| **RSK-15** | **No real-world safety or stopping-time guarantees**<br>Marginal exchangeable conformal prediction does not ensure pointwise conditional coverage or stopping-time coverage. | High | High | Prohibit claims of real-world operational safety; document that empirical finite-sample coverage does not establish dynamic stopping-time guarantees. | Active / Monitored |

---

## Risk Review Protocol

This register is reviewed at the conclusion of each roadmap phase. Any team member (Mayank Singh, Shiksha Pandey, or Ruchi Gupta) may propose new risks or escalate existing risk severity during pull request reviews.
