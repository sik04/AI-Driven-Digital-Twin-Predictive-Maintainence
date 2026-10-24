# Digital Twin Validation-Replay Prototype Verification Report

## 1. System Framing and Architectural Scope

The application implemented in `src/intellitwin/twin/` and `apps/twin_dashboard/` is strictly a **validation telemetry-replay digital-twin prototype**. 

- **Replay Boundary:** The system operates purely in historical playback mode over frozen C-MAPSS turbofan validation splits. It does **not** perform physical bidirectional synchronization, live hardware actuation, or real-time closed-loop sensor telemetry ingest.
- **Scientific Immutability:** All underlying ML models, calibrators, and split assignments remain frozen from Phase 7 research artifacts. No research conclusions or confirmatory findings are modified or claimed to be superior by this prototype. As established in Phase 7 held-out evaluation, all four research questions (RQ1–RQ4) remain **UNSUPPORTED**.
- **Data Integrity & Causality:** The runtime strictly enforces causal windowing ($W=30$ cycles). No predictions or uncertainty intervals are computed or displayed before cycle 30. No oracle annotations (ground-truth RUL or future observations) are exposed via API endpoints or client-side CSV downloads.

---

## 2. Test Environment & Verification Platform

- **Operating System:** Windows 10 Pro (x86_64, build 10.0.19045)
- **Processor:** Intel(R) Core(TM) i7-4790 CPU @ 3.60GHz (4 physical cores, 8 logical threads)
- **System Memory:** 8.00 GB DDR3
- **Python Version:** Python 3.14.0 (`tags/v3.14.0:eb13e22`, Oct 7 2025, 64-bit AMD64)
- **Git Commit (Head):** `feat/twin-replay-demo` tracking merged `origin/main`
- **Frozen Machine Learning Dependencies:**
  - `numpy==2.5.4`
  - `pandas==3.0.6`
  - `scikit-learn==1.9.1`
  - `torch==2.14.1+cpu`
  - `scipy==1.18.1`
  - `PyYAML==6.0.3`
- **Demo Dashboard Dependencies:**
  - `fastapi==0.135.1`
  - `uvicorn==0.44.0`
  - `httpx==0.30.0`
  - `starlette==1.0.0`
  - `pydantic==2.13.0`
- **Package Integrity:** Verified with `python -m pip check` -> `No broken requirements found.`

---

## 3. Automated Quality & Regression Execution

All verification commands were executed sequentially in the checkpoint-compatible environment.

### 3.1 Code Style & Formatting
```bash
ruff format --check src tests scripts
```
- **Outcome:** Passed. 118 files checked, 0 files modified or reformatted.

### 3.2 Static Linting
```bash
ruff check src tests scripts
```
- **Outcome:** Passed. All checks clean across 118 files with 0 errors.

### 3.3 Static Type Checking
```bash
mypy src tests
```
- **Outcome:** Passed. 94 source files inspected, 0 type issues found.

### 3.4 Unit and Subsystem Regression Suite
```bash
python -m pytest -m "not integration" tests
```
- **Outcome:** Passed.
  - **Passed Tests:** 303
  - **Deselected (Integration Tests):** 13
  - **Failed:** 0
  - **Skipped:** 0
  - **Execution Time:** 12.04 seconds

### 3.5 Integration & Twin Test Suite
```bash
python -m pytest tests/twin/test_replay.py -m integration -v
```
- **Outcome:** Passed (1 passed executing all 18 combinations in 22.26s).

```bash
python -m pytest tests/twin/ -v
```
- **Outcome:** Passed. All 15 tests in `tests/twin/` passed in 33.06s.

---

## 4. 18-Combination Parity Matrix Results

The integration test suite verified all $18$ combinations ($3\text{ datasets} \times 2\text{ base model families} \times 3\text{ conformal calibration methods}$) at seed 2026 and nominal coverage $1 - \alpha = 0.90$ using the smallest validation engine unit in each dataset:
- **FD001:** Validation Engine Unit ID `3`
- **FD002:** Validation Engine Unit ID `3`
- **FD004:** Validation Engine Unit ID `2`

| Dataset | Unit ID | Base Model | Calibration Method | Parity Error ($|\hat{y} - y_{\text{cached}}|$) | Interval Agreement | Policy Match | Anti-Leakage Invariance | Status |
| :--- | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **FD001** | 3 | GBR | `global_hcp` | $0.000000 \le 10^{-4}$ | Exact match | $100\%$ | Verified | **PASS** |
| **FD001** | 3 | GBR | `regime_hcp` | $0.000000 \le 10^{-4}$ | Exact match | $100\%$ | Verified | **PASS** |
| **FD001** | 3 | GBR | `decision_aware_hcp` | $0.000000 \le 10^{-4}$ | Exact match | $100\%$ | Verified | **PASS** |
| **FD001** | 3 | LSTM | `global_hcp` | $0.000000 \le 10^{-4}$ | Exact match | $100\%$ | Verified | **PASS** |
| **FD001** | 3 | LSTM | `regime_hcp` | $0.000000 \le 10^{-4}$ | Exact match | $100\%$ | Verified | **PASS** |
| **FD001** | 3 | LSTM | `decision_aware_hcp` | $0.000000 \le 10^{-4}$ | Exact match | $100\%$ | Verified | **PASS** |
| **FD002** | 3 | GBR | `global_hcp` | $0.000000 \le 10^{-4}$ | Exact match | $100\%$ | Verified | **PASS** |
| **FD002** | 3 | GBR | `regime_hcp` | $0.000000 \le 10^{-4}$ | Exact match | $100\%$ | Verified | **PASS** |
| **FD002** | 3 | GBR | `decision_aware_hcp` | $0.000000 \le 10^{-4}$ | Exact match | $100\%$ | Verified | **PASS** |
| **FD002** | 3 | LSTM | `global_hcp` | $0.000000 \le 10^{-4}$ | Exact match | $100\%$ | Verified | **PASS** |
| **FD002** | 3 | LSTM | `regime_hcp` | $0.000000 \le 10^{-4}$ | Exact match | $100\%$ | Verified | **PASS** |
| **FD002** | 3 | LSTM | `decision_aware_hcp` | $0.000000 \le 10^{-4}$ | Exact match | $100\%$ | Verified | **PASS** |
| **FD004** | 2 | GBR | `global_hcp` | $0.000000 \le 10^{-4}$ | Exact match | $100\%$ | Verified | **PASS** |
| **FD004** | 2 | GBR | `regime_hcp` | $0.000000 \le 10^{-4}$ | Exact match | $100\%$ | Verified | **PASS** |
| **FD004** | 2 | GBR | `decision_aware_hcp` | $0.000000 \le 10^{-4}$ | Exact match | $100\%$ | Verified | **PASS** |
| **FD004** | 2 | LSTM | `global_hcp` | $0.000000 \le 10^{-4}$ | Exact match | $100\%$ | Verified | **PASS** |
| **FD004** | 2 | LSTM | `regime_hcp` | $0.000000 \le 10^{-4}$ | Exact match | $100\%$ | Verified | **PASS** |
| **FD004** | 2 | LSTM | `decision_aware_hcp` | $0.000000 \le 10^{-4}$ | Exact match | $100\%$ | Verified | **PASS** |

### Verified Invariants:
1. **Point Prediction Tolerance:** Tolerance $\text{rtol}=0, \text{atol}=10^{-4}$ satisfied (exact numerical identity with cached validation predictions).
2. **Interval Bounds:** Lower and upper conformal bounds $[q_{\text{lo}}, q_{\text{hi}}]$ match the direct output of frozen calibrator objects.
3. **Decision Policy:** Lower-bound one-cycle maintenance policy ($\text{action} = \text{MAINTAIN} \iff q_{\text{lo}} \le 1.0$) was matched across all cycles.
4. **Anti-Leakage Property:** Modifying future unobserved telemetry in the validation engine dataframe caused zero change to outputs at cycle $t$.

---

## 5. End-to-End Real Browser Verification

The dashboard was validated using a headless browser subagent interacting with the live backend (`http://127.0.0.1:8000`).

### 5.1 Verification Checklist

| Requirement | Observed Behavior | Status | Evidence Artifact |
| :--- | :--- | :---: | :--- |
| **Clean Initial Load** | Loads immediately with 0 browser console errors or network failures. | PASS | [desktop_initial_load.png](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/docs/development/screenshots/desktop_initial_load_1792847905711.png) |
| **Catalog & Engine Selectors** | Populates dataset selectors (`FD001`, `FD002`, `FD004`), validation engine IDs (`3`, `4`, `5`...), models, and calibration methods. | PASS | [desktop_initial_load.png](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/docs/development/screenshots/desktop_initial_load_1792847905711.png) |
| **Cycle 0 Initialization** | Session starts at cycle 0 with blank charts and cryptographic SHA-256 provenance hashes displayed. | PASS | [session_cycle_0.png](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/docs/development/screenshots/session_cycle_0_1792847938365.png), [session_provenance.png](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/docs/development/screenshots/session_cycle_0_provenance_1792847961620.png) |
| **Warm-up Cycles (1–29)** | Ingests telemetry into circular buffer; displays `Warm-up (cycle < 30) - buffering telemetry`; no RUL or intervals displayed. | PASS | [session_cycle_29_warmup.png](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/docs/development/screenshots/session_cycle_29_warmup_1792848011980.png) |
| **Active Inference (Cycle 30)** | RUL point prediction, 90% conformal interval, policy action, and trajectory chart with shaded uncertainty region appear. | PASS | [session_cycle_30_active.png](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/docs/development/screenshots/session_cycle_30_active_1792848031364.png) |
| **Step / Play / Pause Controls** | Step advances exactly one cycle; Play initiates smooth autoplay; Pause stops playback without skipping cycles. | PASS | [session_playback_pause.png](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/docs/development/screenshots/session_playback_pause_1792848059171.png) |
| **Anti-Duplicate Guard** | Rapid button clicks do not duplicate advance requests or desynchronize cycle sequences. | PASS | Verified in browser execution |
| **Reset Functionality** | Reset button clears trajectory charts, telemetry history, and returns engine state to cycle 0. | PASS | [session_reset_cycle_0.png](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/docs/development/screenshots/session_reset_cycle_0_1792848084513.png) |
| **Session Reconfiguration** | Switching catalog (e.g., to FD001 / Unit 3 / LSTM) cleanly releases previous session and starts a new session. | PASS | [session_fd001_lstm_cycle_30.png](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/docs/development/screenshots/session_fd001_lstm_cycle_30_1792848133982.png) |
| **Telemetry CSV Export** | Exported CSV file contains consumed observations only; zero oracle fields, no future observations leaked. | PASS | Verified via client download |
| **Mobile Responsiveness** | Responsive layout verified at 375x667 viewport; control panel wraps, charts adjust cleanly. | PASS | [mobile_responsive_view.png](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/docs/development/screenshots/mobile_responsive_view_1792848140527.png) |
| **Keyboard Accessibility** | Interactive elements have explicit `:focus-visible` styling and are navigatable via Tab and Enter keys. | PASS | Verified via styles & DOM navigation |
| **Full Session Recording** | Complete multi-step interaction recorded to WebP artifact. | PASS | [twin_browser_test.webp](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/docs/development/screenshots/twin_browser_test_1792847799416.webp) |

---

## 6. Empirical Performance Benchmark

Performance measurements were gathered directly on the local Windows workstation using high-resolution monotonic timers (`time.perf_counter()`) and Windows OS kernel memory counters via `ctypes` (`K32GetProcessMemoryInfo`).

### 6.1 Server Process Resident Memory (RSS)
- **Baseline Idle Server Process:** `328.79 MB` (Uvicorn + FastAPI + PyTorch runtime in memory)
- **Active FD002 GBR Session:** `336.26 MB` ($\Delta = +7.47\text{ MB}$)
- **Active FD002 LSTM Session:** `335.09 MB` ($\Delta = +6.30\text{ MB}$)

### 6.2 Model & Calibrator Loading Time
- **FD002 GBR (`decision_aware_hcp`):** `79.6 ms`
- **FD002 LSTM (`decision_aware_hcp`):** `18.3 ms`

### 6.3 Single-Cycle Inference Latency
*(Measured across 100 iterations following 10 warm-up cycles using causal 30-cycle window preprocessing, feature transformation, model inference, conformal calibration, and policy evaluation; excludes network I/O).*

| Configuration | Iterations | Min Latency | Median Latency | p95 Latency | Max Latency |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **FD002 GBR (`decision_aware_hcp`)** | 100 | $16.326\text{ ms}$ | **$18.658\text{ ms}$** | **$34.317\text{ ms}$** | $53.693\text{ ms}$ |
| **FD002 LSTM (`decision_aware_hcp`)** | 100 | $15.698\text{ ms}$ | **$17.359\text{ ms}$** | **$27.514\text{ ms}$** | $41.517\text{ ms}$ |

> [!NOTE]
> These latency and memory metrics are local demonstration measurements on Windows x86_64 CPU hardware. They represent interactive dashboard responsiveness, not scientific guarantees or production throughput benchmarks.

---

## 7. Known Prototype Limitations

1. **Single-Session Lock:** The backend engine supports one active telemetry session at a time per server process to maintain strict determinism and state isolation.
2. **Replay Only:** Ingestion is restricted to pre-recorded validation engine units from the C-MAPSS dataset. Live physical sensor feeds are not supported.
3. **Partition Isolation:** Training and calibration engines cannot be selected; attempting to access non-validation engines raises an explicit `PermissionError` (HTTP 422).
4. **Unsupported Research Questions:** The dashboard visualizes decision-aware conformal prediction intervals, but held-out scientific evaluation (Phase 7) confirmed that decision-aware calibration did not demonstrate statistically significant superiority over baseline methods.
