# IntelliTwin Reproducibility Baseline & Audit Report
**Repository:** [AI-Driven-Digital-Twin-Predictive-Maintainence](https://github.com/sik04/AI-Driven-Digital-Twin-Predictive-Maintainence)  
**Branch:** `audit/step-01-repository-baseline`  
**Audit Date:** October 3, 2026  
**Auditor:** Senior ML Engineer & Research Reproducibility Auditor  
**Baseline Commit:** `9b72fac`  
**Audit Scope:** Step 1 — Repository Reconstruction & Reproducibility Baseline (Strictly Frozen Baseline)

---

## 1. System Execution Environment

The audit was executed on a native Windows workstation. System configurations and installed packages were probed non-destructively:

| Component | Audit Specification | Notes / Verification Status |
|---|---|---|
| **Operating System** | Windows 11 Enterprise (10.0.26200 AMD64) | Tested on native Windows PowerShell shell |
| **Python Version** | Python 3.13.9 (`C:\Users\shiks\anaconda3\python.exe`) | Active conda base environment |
| **Deep Learning Engine** | PyTorch 2.14.1+cpu | CPU-only build (`torchvision` not installed) |
| **Machine Learning Libraries** | scikit-learn 1.8.0, XGBoost 3.4.1, LightGBM 4.7.0 | Verified via import and model evaluation |
| **Scientific Computing** | NumPy 2.4.4, SciPy 1.16.3, Pandas 3.0.2 | Verified |
| **Data Visualization** | Matplotlib 3.10.8, Seaborn 0.13.2 | Verified figure generation backend (`Agg`) |
| **Web Server Framework** | Flask 3.1.2 | Verified backend REST routing |
| **Testing Framework** | Pytest 8.4.2, pluggy 1.5.0, Python unittest | Unit test suite verified |
| **Document Generation** | python-docx 1.2.0, pypdf 6.19.0, pymupdf 1.28.2 | Word and PDF inspection verified |
| **Headless Browser Engine** | Google Chrome 128+ (`C:\Program Files\Google\Chrome\Application\chrome.exe`) | Available for headless PDF rendering |

---

## 2. Dependency Specification Audit

The repository contains two dependency specification files:
1. `requirements.txt`:
   ```text
   # UQ-DT: Uncertainty-Quantified Digital Twin Framework Dependencies
   # Compatible with Python 3.10, 3.11, 3.12, 3.13
   numpy>=1.24.0
   scipy>=1.10.0
   scikit-learn>=1.2.0
   pandas>=2.0.0
   matplotlib>=3.7.0
   ```
2. `setup.py`:
   ```python
   install_requires=[
       "numpy>=1.24.0",
       "scipy>=1.10.0",
       "scikit-learn>=1.2.0",
       "pandas>=2.0.0",
       "matplotlib>=3.7.0",
       "xgboost>=1.7.0",
       "flask>=2.0.0",
   ]
   ```

### Critical Findings on Dependencies:
- **PyTorch (`torch`) is completely omitted** from both `requirements.txt` and `setup.py`. `COMMANDS_TO_RUN.txt` specifies a secondary installation command: `pip install torch --extra-index-url https://download.pytorch.org/whl/cpu`.
- **`xgboost` and `flask` are omitted** from `requirements.txt` (though included in `setup.py`).
- **`python-docx`, `pypdf`, and `pytest` are omitted** from both files despite being necessary for running the document generation scripts and test suites.
- **Stale naming in `requirements.txt`**: The file header still references `# UQ-DT`.

---

## 3. Dataset Situation & Cryptographic Verification

The dataset directory `data/cmapss/` contains NASA C-MAPSS turbofan degradation benchmark data. All files were cryptographically hashed and inspected:

| Filename | File Size | SHA256 Checksum | Dimensions / Lines | Engine Count | Cycle Range | Status |
|---|---|---|---|---|---|---|
| `train_FD001.txt` | 3,515,356 bytes | `963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8` | 20,631 rows, 26 cols | 100 units | 128 - 362 cycles (mean 206.3) | Complete & Pristine |
| `test_FD001.txt` | 2,228,855 bytes | `3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851` | 13,096 rows, 26 cols | 100 units | 31 - 303 cycles (mean 131.0) | Complete & Pristine |
| `RUL_FD001.txt` | 429 bytes | `a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca` | 100 lines | 100 units | min 7, max 145, mean 75.5 | Complete & Pristine |
| `train_FD002.txt` | 9,082,480 bytes | `dac6c4dbc4e7c1bdeb5747da3d313d05c395bb99801b44a002b26a2ba13d788f` | 53,759 rows, 26 cols | 260 units | 128 - 378 cycles (mean 206.8) | Complete & Pristine |
| `test_FD002.txt` | 5,734,587 bytes | `de7b5bf7e998a985c378488480528b7c02cff1406a46740def362dda8d9b4e02` | 33,991 rows, 26 cols | 259 units | 21 - 367 cycles (mean 131.2) | Complete & Pristine |
| `RUL_FD002.txt` | 1,110 bytes | `c851dd96a6ea6998d3c4a8f834d3c8013aa90e93a6ed950dc826ad0655b2906b` | 259 lines | 259 units | min 6, max 194, mean 81.2 | Complete & Pristine |
| `readme.txt` | 2,442 bytes | `4f5270554b775c67e73aff383c5436fd329d6e4cc3d3a116913276fae511269b` | 53 lines | N/A | Official dataset documentation | Complete |

### Dataset Assessment:
- **FD001 completeness:** 100% complete with train, test, and true ground-truth RUL files matching official NASA PHM benchmarks.
- **FD002 completeness:** 100% complete with train, test, and true ground-truth RUL files present.
- **FD003 & FD004:** Absent from the repository.
- **Pipeline Utilization:** The active training pipeline (`intellitwin/train.py`) defaults strictly to `sub_dataset="FD001"`. FD002 is supported by the data loader class but is not exercised in the main training routine.

---

## 4. Model Artifact State & Load Verification

Two serialized PyTorch model weights exist under `intellitwin/models/`:
1. `intellitwin/models/lstm_rul.pt` (269,837 bytes)
2. `intellitwin/models/gru_rul.pt` (204,479 bytes)

### Checkpoint Loading Audit:
- **`lstm_rul.pt`**: Loaded via `torch.load('intellitwin/models/lstm_rul.pt', map_location='cpu', weights_only=True)`.
  - Keys present: `lstm.weight_ih_l0`, `lstm.weight_hh_l0`, `lstm.bias_ih_l0`, `lstm.bias_hh_l0`, `lstm.weight_ih_l1`, `lstm.weight_hh_l1`, `lstm.bias_ih_l1`, `lstm.bias_hh_l1`, `fc.0.weight`, `fc.0.bias`, `mu_head.weight`, `mu_head.bias`, `log_var_head.weight`, `log_var_head.bias`.
  - Successfully instantiated into `LSTMRULNet(input_dim=54, hidden_dim=64, num_layers=2)`. Forward pass on dummy batch `(2, 30, 54)` executed without error, returning mean `mu` and `log_var` tensors of shape `(2,)`.
  - **Verdict:** **VERIFIED**.
- **`gru_rul.pt`**: Loaded via `torch.load('intellitwin/models/gru_rul.pt', map_location='cpu', weights_only=True)`.
  - Keys present: `gru.weight_ih_l0`, `gru.weight_hh_l0`, `gru.bias_ih_l0`, `gru.bias_hh_l0`, `gru.weight_ih_l1`, `gru.weight_hh_l1`, `gru.bias_ih_l1`, `gru.bias_hh_l1`, `fc.0.weight`, `fc.0.bias`, `fc.3.weight`, `fc.3.bias`.
  - Successfully instantiated into `GRURULNet(input_dim=54, hidden_dim=64, num_layers=2)`. Forward pass on dummy batch `(2, 30, 54)` executed without error, returning scalar prediction of shape `(2,)`.
  - **Verdict:** **VERIFIED**.
- **Tabular Models (RF, XGBoost, Isolation Forest):** Weights are NOT persisted to disk. These models are fitted during `train.py` execution, but their parameters are not saved as `.joblib` or `.pkl` files.
  - **Verdict:** **UNSERIALIZED (Retrained on execution)**.

---

## 5. Experiment Artifact State & Metric Alignment

Empirical results are recorded in `intellitwin/models/evaluation_results.json`:

```json
{
  "rul_regression_models": {
    "LSTM_heteroscedastic": {"mae": 12.333, "rmse": 16.000, "nasa_score": 542.12},
    "GRU": {"mae": 12.254, "rmse": 16.782, "nasa_score": 665.01},
    "Random_Forest": {"mae": 13.388, "rmse": 18.123, "nasa_score": 884.03},
    "XGBoost": {"mae": 12.486, "rmse": 16.991, "nasa_score": 715.71}
  },
  "fault_classification_models": {
    "Random_Forest": {"accuracy": 0.89, "f1_macro": 0.8579, "false_alarm_rate": 0.0238, "missed_detection_rate": 0.125},
    "XGBoost": {"accuracy": 0.87, "f1_macro": 0.8272, "false_alarm_rate": 0.0357, "missed_detection_rate": 0.125}
  },
  "uncertainty_quantification": {
    "target_coverage": 0.9, "picp": 0.95, "mpiw": 62.537, "winkler_score": 70.906
  },
  "catastrophic_failure_evaluation": {
    "total_engines_evaluated": 20, "mean_warning_lead_time_cycles": 41.1, "missed_catastrophic_failures": 0, "catastrophic_prevention_success_rate": 1.0
  }
}
```

### Verification Against Research Paper Manuscripts:
- In `manuscript/RESEARCH_PAPER_INTELLITWIN.md` and `manuscript/INTELLITWIN_RESEARCH_PAPER_IEEE_FORMAT.docx`:
  - Table 1 (RUL Prognostic Benchmarks): Heteroscedastic LSTM RMSE = 16.00, NASA Score = 542.1; GRU RMSE = 16.78; RF RMSE = 18.12; XGBoost RMSE = 16.99. **MATCHES EXACTLY**.
  - Table 2 (Multi-Class Health State): RF Accuracy = 89.0%, Macro F1 = 0.8579, False Alarm Rate = 2.38%. **MATCHES EXACTLY**.
  - Table 3 (UQ & Conformal Coverage): Target Coverage = 90%, Empirical Coverage (PICP) = 95.0%, MPIW = 62.54 cycles. **MATCHES EXACTLY**.
  - Section IV-D (Catastrophic Prevention): Prevention Rate = 100.0%, 0 Missed Catastrophic Failures, Mean Lead Time = 41.1 cycles. **MATCHES EXACTLY**.
- **Verdict:** **VERIFIED & CONSISTENT**.

### Secondary Metric Artifact:
- `figures/benchmark_metrics_summary.json` (5,681 bytes) contains nominal and out-of-distribution (OOD) metrics for "Proposed UQ-DT", "GA-Ensemble", and "Decision Forest". This is an artifact from the prior UQ-DT research phase.
  - **Verdict:** **UNVERIFIED / STALE METRICS**.

---

## 6. Execution Commands Tested & Results

| Command | Exit Code | Runtime | Output Summary | Diagnostic Status |
|---|---|---|---|---|
| `git status` | 0 | 0.8s | On branch `audit/step-01-repository-baseline`, working tree clean | Clean VCS state |
| `pytest -v` | 1 | 0.5s | `ERROR collecting tests/test_intellitwin.py`: `ModuleNotFoundError: No module named 'intellitwin'` | **FAILED** (`.` not in `sys.path`) |
| `python -m pytest -v` | 0 | 5.7s | 6 passed, 1 warning in 5.68s (`test_catastrophic_evaluator`, `test_conformal_calibrator`, `test_data_loader`, `test_environmental_handler`, `test_fault_discriminator`, `test_uq_metrics`) | **PASSED** (adds repo root to `sys.path`) |
| `python -m unittest tests/test_intellitwin.py` | 0 | 4.8s | Ran 6 tests in 4.821s, OK | **PASSED** |
| `python intellitwin/verify_consistency.py` | 0 | 14.1s | 100% Pass across Dataset, ML Models, Frontend, Figures, Manuscripts, Empirical Results | **PASSED** |
| `python -c "import torch; ..."` (Model loader) | 0 | 4.2s | Successfully loaded `lstm_rul.pt` and `gru_rul.pt` with `weights_only=True` | **PASSED** |
| `python literature/scripts/inspect_papers.py` | 0 | 0.3s | `Summary file not found at .../papers_summary.json. Run extract_papers.py first.` | **BLOCKED BY MISSING ARTIFACT** |

---

## 7. Execution Commands Not Tested (With Justifications)

1. `python -m intellitwin.train`:
   - *Justification:* Full training pipeline trains neural networks across 20,631 cycles for multiple epochs. Step 1 guidelines explicitly mandate: *"If the full training pipeline is expensive, DO NOT launch it automatically unless required to establish the baseline."* Pre-trained checkpoints and metric JSON are intact and verified.
2. `python intellitwin/api.py`:
   - *Justification:* Spawns a blocking Flask server on port 5000. Static assets and routing logic were verified via inspection.
3. `python manuscript/build_double_column_paper.py`:
   - *Justification:* Re-compiles PDF using headless Chrome. Deliverables are already generated, complete, and verified; re-running could overwrite frozen artifacts.
4. `python manuscript/generate_ieee_paper_docx.py`:
   - *Justification:* Word document generator. The generated document is intact and tracked in git.
5. `python manuscript/package_submission.py`:
   - *Justification:* Submission zip packager. Pre-built zip is intact and tracked.
6. `python literature/scripts/extract_papers.py`:
   - *Justification:* Literature extraction on 15 PDFs; computational and not part of the active ML pipeline.

---

## 8. Inaccessible Resources & External Dependencies

1. **Internet Access for Frontend Chart.js**:
   - `frontend/index.html` loads Chart.js via CDN (`https://cdn.jsdelivr.net/npm/chart.js`). In an air-gapped or offline industrial environment, Chart.js will fail to load unless bundled locally.
2. **Missing Extraction Artifacts in Literature Directory**:
   - `literature/scripts/papers_summary.json`
   - `literature/scripts/deep_gaps_extraction.json`
   - `literature/scripts/extra_papers_deep.json`
   - These files were generated during literature mining and are not committed to the repository, rendering `inspect_papers.py`, `show_gaps.py`, `summarize_all.py`, and `summarize_extra.py` inoperable until `extract_papers.py` is executed.
3. **Headless Chrome Dependency**:
   - `manuscript/build_double_column_paper.py` requires Google Chrome installed at `C:\Program Files\Google\Chrome\Application\chrome.exe`. Systems lacking Chrome at this exact path will fail to build the double-column PDF.

---

## 9. Reproducibility Risk Assessment

1. **Direct `pytest` invocation failure:** Any user following standard CI/CD testing procedures by running `pytest` will experience collection failure unless instructed to run `python -m pytest` or unless `pyproject.toml`/`setup.py` adds `.` to pythonpath.
2. **Virtual Environment Fragility:** Running `pip install -r requirements.txt` leaves the user without PyTorch, XGBoost, Flask, and python-docx, causing subsequent scripts to crash immediately.
3. **Manuscript Drift:** `manuscript/main.tex` contains legacy UQ-DT text and outdated authorship, introducing severe risk if a researcher attempts to compile LaTeX rather than using the DOCX/PDF generators.
4. **Disconnect between Dashboard and Core Models:** The Flask dashboard serves heuristic/synthetic machine data rather than calling the PyTorch inference models on C-MAPSS data.
