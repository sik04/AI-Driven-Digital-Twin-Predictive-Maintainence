# Initial Known Issues Register
**Repository:** [AI-Driven-Digital-Twin-Predictive-Maintainence](https://github.com/sik04/AI-Driven-Digital-Twin-Predictive-Maintainence)  
**Branch:** `audit/step-01-repository-baseline`  
**Audit Date:** October 3, 2026  
**Auditor:** Senior ML Engineer & Research Reproducibility Auditor  
**Audit State:** Step 1 — Frozen Baseline (Issues Identified, NONE Fixed)

---

## Issue Classification Taxonomy

- **P0 — Research Blocking:** Critical blockers that halt fundamental execution, invalidate core research claims, or destroy baseline integrity.
- **P1 — Important:** Major reproducibility, dependency, architectural, or synchronization defects that must be resolved in subsequent steps before public release or benchmarking.
- **P2 — Improvement:** Methodological, structural, or pipeline quality improvements that enhance fidelity, coverage, and cross-platform robustness.
- **P3 — Cosmetic / Documentation:** Minor naming inconsistencies, legacy comments, warnings, or formatting items that do not compromise algorithmic correctness.

---

## 1. Summary of Identified Issues

| Issue ID | Severity | Category | Title | Target File(s) |
|---|---|---|---|---|
| `ISSUE-P0-01` | **P0** | Blocking | *None identified* (Repository executes cleanly on local baseline) | N/A |
| `ISSUE-P1-01` | **P1** | Environment / Testing | Direct `pytest` CLI invocation fails with `ModuleNotFoundError` | `tests/test_intellitwin.py`, `setup.py` |
| `ISSUE-P1-02` | **P1** | Dependency Management | Missing core ML & app packages in `requirements.txt` (`torch`, `xgboost`, `flask`, `python-docx`) | `requirements.txt`, `setup.py` |
| `ISSUE-P1-03` | **P1** | Manuscript Inconsistency | `manuscript/main.tex` contains stale UQ-DT text, old consortium authors, and old gap framing | `manuscript/main.tex` |
| `ISSUE-P1-04` | **P1** | Model Artifact Serialization | Tabular classifiers (Random Forest, XGBoost) and Isolation Forest are not saved to disk | `intellitwin/train.py`, `intellitwin/models/` |
| `ISSUE-P1-05` | **P1** | Pipeline / API Disconnect | Flask `/api/predict` endpoint uses rule-based heuristics rather than trained PyTorch LSTM weights | `intellitwin/api.py` |
| `ISSUE-P1-06` | **P1** | Data Domain Disconnect | Frontend displays synthetic factory machines while research models are trained on NASA turbofans | `frontend/app.js`, `intellitwin/api.py` |
| `ISSUE-P2-01` | **P2** | Pipeline Artifact Alignment | Mismatched figure filenames vs plot semantics (`fig2`, `fig4`, `fig5`) | `figures/`, `intellitwin/generate_figures.py` |
| `ISSUE-P2-02` | **P2** | Experimental Reproducibility | Figure generation script uses synthetic formulas and hardcoded arrays instead of empirical data | `intellitwin/generate_figures.py` |
| `ISSUE-P2-03` | **P2** | Dataset Utilization | C-MAPSS subset FD002 is present on disk but unused in the primary training pipeline | `data/cmapss/`, `intellitwin/train.py` |
| `ISSUE-P2-04` | **P2** | Platform Portability | `manuscript/build_double_column_paper.py` hardcodes Windows Chrome executable path | `manuscript/build_double_column_paper.py` |
| `ISSUE-P2-05` | **P2** | Tooling / Script Integrity | Literature review CLI tools crash due to missing uncommitted JSON extraction files | `literature/scripts/` |
| `ISSUE-P3-01` | **P3** | Documentation / Naming | Stale `# UQ-DT` header in `requirements.txt` | `requirements.txt` |
| `ISSUE-P3-02` | **P3** | Packaging Artifacts | Legacy `UQ_DT` file and zip references in `manuscript/package_submission.py` | `manuscript/package_submission.py` |
| `ISSUE-P3-03` | **P3** | Runtime Diagnostics | UserWarning regarding KMeans MKL memory leak on Windows | `intellitwin/environmental_handler.py` |
| `ISSUE-P3-04` | **P3** | Stale Artifacts | `figures/benchmark_metrics_summary.json` retains legacy UQ-DT benchmark keys | `figures/benchmark_metrics_summary.json` |

---

## 2. Detailed Issue Records

### `ISSUE-P1-01`: Direct `pytest` Invocation Fails with `ModuleNotFoundError`
- **Severity:** P1 (Important)
- **Location:** `tests/test_intellitwin.py`, repository root
- **Description:** Running `pytest` or `pytest -v` directly from the repository root fails during test collection:
  ```text
  ModuleNotFoundError: No module named 'intellitwin'
  ```
  This occurs because the current working directory is not automatically added to `sys.path` by pytest unless `pyproject.toml`, `pytest.ini`, or `python -m pytest` is used, or the package is installed in editable mode (`pip install -e .`).
- **Reproducibility Impact:** Automated CI runners or peer reviewers attempting standard pytest invocation will observe test failure.
- **Recommended Future Action:** Add a minimal `pytest.ini` or `pyproject.toml` configuration with `pythonpath = .` or instruct editable package installation.

---

### `ISSUE-P1-02`: Missing Core ML and Application Packages in `requirements.txt`
- **Severity:** P1 (Important)
- **Location:** `requirements.txt`, `setup.py`
- **Description:** `requirements.txt` lists only `numpy`, `scipy`, `scikit-learn`, `pandas`, and `matplotlib`. It completely omits:
  - `torch` (required for `intellitwin/models/lstm_rul.py` and `train.py`)
  - `xgboost` (required for `intellitwin/models/fault_classifier.py` and `train.py`)
  - `flask` (required for `intellitwin/api.py`)
  - `python-docx` (required for `manuscript/generate_ieee_paper_docx.py`)
  - `pypdf` (required for `literature/scripts/extract_papers.py`)
  - `pytest` (required for running test suites)
- **Reproducibility Impact:** Creating a pristine virtual environment and running `pip install -r requirements.txt` leaves the environment unable to execute training, tests, the API backend, or paper generation.
- **Recommended Future Action:** Align `requirements.txt` and `setup.py` with complete dependency specifications and platform-specific PyTorch wheels.

---

### `ISSUE-P1-03`: `manuscript/main.tex` Stale and Desynchronized from Current Paper
- **Severity:** P1 (Important)
- **Location:** `manuscript/main.tex`
- **Description:** `manuscript/main.tex` contains the legacy paper title:
  `UQ-DT: Uncertainty-Quantified Digital Twin Framework for Safety-Critical Infrastructure Prognostics Under Environmental Drift`
  with fictitious consortium authors:
  `Antigravity Research Consortium in Cyber-Physical Systems and Infrastructure Analytics`
  whereas the verified official research paper is:
  `IntelliTwin: An AI-Driven Digital Twin Framework for Predictive Maintenance of Engineering Assets`
  authored by `Mayank Singh, Shiksha Pandey, Ruchi Gupta`.
- **Reproducibility Impact:** Anyone compiling `main.tex` via LaTeX produces an outdated, misaligned document contradicting `RESEARCH_PAPER_INTELLITWIN.md`, `INTELLITWIN_RESEARCH_PAPER_IEEE_FORMAT.docx`, and `INTELLITWIN_RESEARCH_PAPER_DOUBLE_COLUMN.pdf`.
- **Recommended Future Action:** Synchronize `manuscript/main.tex` with the verified IntelliTwin text, authors, equations, and tables.

---

### `ISSUE-P1-04`: Tabular Classifiers and Preprocessing Artifacts Not Serialized to Disk
- **Severity:** P1 (Important)
- **Location:** `intellitwin/train.py`, `intellitwin/models/`
- **Description:** While `lstm_rul.pt` and `gru_rul.pt` are saved to disk, the Random Forest and XGBoost classifiers (`fault_classifier.py`), the Isolation Forest anomaly detector (`anomaly_detector.py`), the fitted StandardScaler (`data_loader.py`), and the fitted KMeans model (`environmental_handler.py`) are not serialized to disk.
- **Reproducibility Impact:** Downstream inference services (such as `api.py`) cannot load trained tabular models or preprocessing scalers without running full retraining.
- **Recommended Future Action:** Serialize trained scikit-learn/xgboost pipelines and scalers to `intellitwin/models/` using `joblib`.

---

### `ISSUE-P1-05`: REST API Inference Disconnected from Trained PyTorch Checkpoints
- **Severity:** P1 (Important)
- **Location:** `intellitwin/api.py` (lines 269–303)
- **Description:** In `intellitwin/api.py`, the `/api/predict` endpoint determines health state and RUL using scalar rule thresholds:
  ```python
  if vib > 5.5 or temp > 72.0:
      health_state = "Critical"
      rul = max(10, int(120 - 15 * (vib - 1.0) - 0.8 * (temp - 40)))
  ...
  ```
  It does not load `lstm_rul.pt` or execute the heteroscedastic PyTorch neural network.
- **Reproducibility Impact:** The interactive dashboard demonstrates surrogate logic rather than true model inference from the research paper.
- **Recommended Future Action:** Connect `/api/predict` to load `lstm_rul.pt` and run active tensor inference.

---

### `ISSUE-P1-06`: Domain Gap Between Factory Dashboard Assets and NASA Turbofan Telemetry
- **Severity:** P1 (Important)
- **Location:** `frontend/app.js`, `intellitwin/api.py`
- **Description:** The frontend application represents a factory floor with 5 industrial machines:
  - CNC Machine - 01
  - Robotic Arm - 02
  - Conveyor Belt - 03
  - Air Compressor - 04
  - Hydraulic Press - 05
  with variables `[Temperature, Vibration, Current, Speed, Load, Power]`. In contrast, the research paper and machine learning training pipeline operate strictly on the NASA C-MAPSS dataset (turbofan jet engine degradation with 21 sensor channels such as LPC outlet temperature, HPC pressure, etc.).
- **Reproducibility Impact:** Demonstrators might mistake the factory dashboard for a live feed of C-MAPSS engines, creating an architectural disconnect.
- **Recommended Future Action:** Clarify dashboard documentation or implement a C-MAPSS fleet viewer mode that streams actual turbofan sensor channels.

---

### `ISSUE-P2-01`: Mismatched Figure Filenames vs Generated Plot Semantics
- **Severity:** P2 (Improvement)
- **Location:** `figures/`, `intellitwin/generate_figures.py`
- **Description:** The filenames under `figures/` reflect legacy UQ-DT figure names, but the plots generated by `generate_figures.py` display updated IntelliTwin visualizations:
  - `fig2_uncertainty_decomposition.png` plots *Condition-Normalized Residual Decoupling (Masking Problem)*.
  - `fig4_pareto_coverage_width.png` plots *Prognostic Benchmark Bar Chart (RMSE vs NASA Score)*.
  - `fig5_dss_cost_comparison.png` plots *Catastrophic Warning Lead Time Distribution*.
- **Reproducibility Impact:** Filenames are counter-intuitive and misleading when reviewing the raw figure directory.
- **Recommended Future Action:** Rename figures or update document references to semantically descriptive filenames.

---

### `ISSUE-P2-02`: Figure Generation Uses Hardcoded Simulated Data Rather Than True Model Runs
- **Severity:** P2 (Improvement)
- **Location:** `intellitwin/generate_figures.py`
- **Description:** In `generate_figures.py`:
  - Fig 1 generates a synthetic degradation trajectory: `true_rul = np.maximum(0, 125 - np.maximum(0, cycles - 15))`.
  - Fig 2 uses synthetic residual equations.
  - Fig 3 uses hardcoded confusion matrix array `[[58, 3, 0], [4, 17, 2], [0, 2, 14]]`.
  - Fig 4 uses hardcoded arrays `[18.12, 16.99, 16.78, 16.00]`.
  - Fig 5 uses a hardcoded list of 20 lead times.
- **Reproducibility Impact:** If the underlying models are retrained and achieve slightly different metrics, running `generate_figures.py` will not reflect the new empirical results.
- **Recommended Future Action:** Refactor `generate_figures.py` to read directly from `evaluation_results.json` and active test predictions.

---

### `ISSUE-P2-03`: C-MAPSS FD002 Dataset Present on Disk but Excluded from Pipeline
- **Severity:** P2 (Improvement)
- **Location:** `data/cmapss/`, `intellitwin/train.py`
- **Description:** `data/cmapss/` contains complete files for `train_FD002.txt` (53,759 rows), `test_FD002.txt` (33,991 rows), and `RUL_FD002.txt`. The `data_loader.py` class supports `sub_dataset="FD002"`, but `train.py` hardcodes `sub_dataset="FD001"`. Subsets FD003 and FD004 are not present.
- **Reproducibility Impact:** Multicondition operating regimes (FD002 with 6 operating conditions) are not benchmarked despite data being stored in the repository.
- **Recommended Future Action:** Add multi-dataset evaluation flags to `train.py`.

---

### `ISSUE-P2-04`: Headless Chrome Executable Path Hardcoded to Windows Location
- **Severity:** P2 (Improvement)
- **Location:** `manuscript/build_double_column_paper.py` (line 581)
- **Description:** The PDF compilation script hardcodes:
  ```python
  chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
  ```
- **Reproducibility Impact:** Building the double-column PDF will fail on Linux, macOS, or Windows machines where Chrome is installed in local user data or absent.
- **Recommended Future Action:** Implement automated path resolution via `shutil.which('google-chrome')`, `which('chrome')`, or environment variables.

---

### `ISSUE-P2-05`: Literature Review CLI Scripts Broken by Missing Extraction Files
- **Severity:** P2 (Improvement)
- **Location:** `literature/scripts/inspect_papers.py`, `show_gaps.py`, `summarize_all.py`, `summarize_extra.py`
- **Description:** Running any of these scripts produces an error because their target JSON files (`papers_summary.json`, `deep_gaps_extraction.json`, `extra_papers_deep.json`) were not committed to the repository.
- **Reproducibility Impact:** Literature analysis tools cannot be inspected or run without executing `extract_papers.py` first.
- **Recommended Future Action:** Commit the generated summary JSON files or add pre-check commands that auto-trigger extraction.

---

### `ISSUE-P3-01`: Stale Header in `requirements.txt`
- **Severity:** P3 (Cosmetic)
- **Location:** `requirements.txt` (line 1)
- **Description:** Header reads `# UQ-DT: Uncertainty-Quantified Digital Twin Framework Dependencies` instead of `IntelliTwin`.

---

### `ISSUE-P3-02`: Legacy `UQ_DT` References in Submission Packager
- **Severity:** P3 (Cosmetic)
- **Location:** `manuscript/package_submission.py`
- **Description:** Script checks for `UQ_DT_RESEARCH_PAPER_IEEE_FORMAT.docx` and writes `uq_dt_journal_submission_package.zip` alongside the IntelliTwin package.

---

### `ISSUE-P3-03`: KMeans Windows MKL Memory Leak UserWarning
- **Severity:** P3 (Cosmetic)
- **Location:** `intellitwin/environmental_handler.py`
- **Description:** When running tests or clustering, scikit-learn emits:
  `UserWarning: KMeans is known to have a memory leak on Windows with MKL... You can avoid it by setting the environment variable OMP_NUM_THREADS=1.`

---

### `ISSUE-P3-04`: Legacy Keys in `figures/benchmark_metrics_summary.json`
- **Severity:** P3 (Cosmetic)
- **Location:** `figures/benchmark_metrics_summary.json`
- **Description:** Contains metrics labeled `"Proposed UQ-DT (CQR)"`, `"Paper 14 GA-Ensemble"`, etc., which reflect prior nomenclature.
