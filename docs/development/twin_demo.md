# IntelliTwin Validation-Replay Dashboard & Telemetry Prototype

## 1. Overview & Prototype Scope

The **IntelliTwin Validation-Replay Dashboard** is a local telemetry-replay prototype designed to provide auditable, cycle-by-cycle inspection of historical run-to-failure validation trajectories.

> [!IMPORTANT]
> **Validation Replay Prototype Scope:**
> - This dashboard operates strictly as a telemetry replay tool for inspecting frozen preprocessors, predictors, and uncertainty calibrators across C-MAPSS validation partition engines.
> - **Not Physical Bidirectional Synchronization:** This prototype replays prerecorded historical run-to-failure records. It does not establish bidirectional physical synchronization with physical aircraft turbofan machinery or real-time cyber-physical sensor streams.
> - **Not Confirmatory Performance Evidence:** Playback observations and exploratory interactions on validation engines do not constitute confirmatory statistical hypothesis evidence. Confirmatory testing runs independently on an isolated branch with held-out test engines.
> - **90% Nominal Prediction Interval:** The uncertainty bounds reflect population-level coverage across validation engines from conformal calibration. They do not constitute an individualized 90% probability guarantee for any single trajectory or cycle.

---

## 2. Architecture & Directory Layout

The implementation strictly owns and modifies only the following locations:

```text
src/intellitwin/twin/
├── __init__.py          # Package initialization
├── schemas.py           # Pydantic data schemas and contract validation
├── artifacts.py         # Isolation guards, partition catalog & model/calibrator loaders
├── replay.py            # ReplaySession state machine, anti-leakage windowing & policy
└── api.py               # FastAPI backend application & static dashboard mounting

apps/twin_dashboard/
├── index.html           # Semantic HTML5 dashboard layout
├── styles.css           # Vanilla CSS design system
└── app.js               # Reactive vanilla JavaScript application & SVG renderer

tests/twin/
├── test_replay.py       # Replay engine unit & parity tests
└── test_api.py          # API route unit & integration tests

requirements/
├── twin-demo.in         # Direct demo requirements (fastapi, uvicorn, httpx)
└── twin-demo.lock.txt   # Complete locked environment specifications

docs/development/
└── twin_demo.md         # Architecture, launch guide, API contract & verification
```

---

## 3. Environment & Setup

The dashboard backend is compatible with the frozen Python 3.14 / NumPy 2.5.3 / PyTorch 2.14.1+cpu stack, without modifying or upgrading existing model checkpoints.

### Installation

```bash
# Create an isolated environment for the twin demo
uv venv --seed .venv_twin_demo --python 3.14.0

# Install the exact locked stack
.venv_twin_demo\Scripts\pip.exe install -r requirements/twin-demo.lock.txt

# Install the package in editable mode without touching dependencies
.venv_twin_demo\Scripts\pip.exe install -e . --no-deps
```

### Tested Dependency Versions

- Python: `3.14.0`
- FastAPI: `0.161.1`
- Uvicorn: `0.54.0`
- HTTPX: `0.28.1`
- Pydantic: `2.14.1`
- NumPy: `2.5.3`
- Pandas: `3.0.6`
- Scikit-Learn: `1.9.1`
- PyTorch: `2.14.1+cpu`
- PyYAML: `6.0.3`

---

## 4. Launching the Dashboard

The dashboard frontend and API are served from the same local origin via FastAPI and Uvicorn.

```bash
# From the repository root:
python -m uvicorn intellitwin.twin.api:app --host 127.0.0.1 --port 8000
```

Open a web browser and navigate to:
```text
http://127.0.0.1:8000
```

---

## 5. Replay Rules & Anti-Leakage Contracts

1. **Anti-Leakage Boundary:**
   - Observations are consumed strictly one cycle at a time.
   - At decision cycle $t$, window inference uses only observations $\{1, \dots, t\}$.
   - No oracle fields (`failure_cycle`, `rul_true`, `rul_target`, or `lifecycle_stage`) are exposed to the predictor, calibrator, decision policy, API responses, or CSV exports.
2. **Warm-Up Phase (Cycles 1–29):**
   - Observations are accumulated into the active buffer.
   - `state` is reported as `warming_up`.
   - `prediction`, `lower_rul`, `upper_rul`, and `action` remain `null`.
3. **Active Inference & Decision (Cycles 30–T):**
   - At each cycle $t \ge 30$, a float32 causal lookback window of shape $(30, 17)$ is extracted from the most recent 30 observations.
   - GBR models receive a row-major flattened 510-element vector.
   - LSTM models receive the $(1, 30, 17)$ tensor sequence.
   - Nonconformity scores and conformal intervals are inverted using the active frozen calibrator for nominal coverage 0.90.
   - Policy `lower_bound_one_cycle_policy` evaluates:
     $$\text{Action} = \begin{cases} \text{MAINTAIN\_NOW} & \text{if } \text{lower\_rul} \le 1.0 \\ \text{CONTINUE} & \text{otherwise} \end{cases}$$
4. **Maintenance Precedence vs. Terminal Failure:**
   - If `lower_rul <= 1.0` is triggered at cycle $t < T$, the episode enters state `maintained` and halts further progression.
   - If the engine reaches terminal failure cycle $T$ without prior maintenance, failure takes precedence: no maintenance is issued at cycle $T$, and the episode enters state `failed`.
5. **Concurrency & Anti-Skipping:**
   - Single in-memory active session per server. Attempts to create a second session return HTTP 409 until the active session is deleted.
   - Each advance request must provide `expected_cycle`. Stale or out-of-order cycle advances return HTTP 409 to prevent client races or skipped cycles.

---

## 6. API Reference

| Method | Endpoint | Description | Status Codes |
|---|---|---|---|
| `GET` | `/api/health` | Check service readiness and artifact availability | 200 |
| `GET` | `/api/catalog` | List supported datasets, models, methods, seed, and validation engines | 200 |
| `POST` | `/api/sessions` | Create a new active replay session | 201, 409, 422, 503 |
| `GET` | `/api/sessions/{id}` | Read current session state without advancing | 200, 404 |
| `POST` | `/api/sessions/{id}/advance` | Advance replay by exactly one cycle with `expected_cycle` lock check | 200, 404, 409, 500 |
| `POST` | `/api/sessions/{id}/reset` | Reset active replay session to cycle 0 and clear history | 200, 404 |
| `DELETE` | `/api/sessions/{id}` | Delete session and release in-memory artifacts | 204, 404 |
| `GET` | `/api/sessions/{id}/trace.csv` | Download history of consumed cycles and observations | 200, 404 |

---

## 7. Resource & Hardware Performance

- **Memory Footprint:** In-memory footprint is constrained to the single active model and calibrator (~15 MB for GBR, ~25 MB for LSTM). Releasing or switching sessions releases existing models via garbage collection.
- **CPU Inference Latency:** Single-cycle inference runs in < 2 ms on modern x86_64 CPUs, supporting real-time playback rates of 1, 2, or 5 cycles/second smoothly without CPU throttling.

---

## 8. Verification & Test Execution

The implementation is verified by:
1. `tests/twin/test_replay.py`:
   - Rejection of train, calibration, and test partition IDs.
   - Cycles 1–29 warm-up behavior with null predictions.
   - Cycle 30 causal lookback using exactly 30 observations.
   - Anti-leakage invariance when altering future rows.
   - Strict `expected_cycle` matching and conflict rejection.
   - State clearing on reset.
   - Maintenance termination at lower bound threshold $\le 1.0$.
   - Terminal failure precedence at trajectory termination.
   - Real numerical parity matching cached validation predictions within $\text{atol} = 10^{-4}, \text{rtol} = 0$ across all 18 benchmark cells.
2. `tests/twin/test_api.py`:
   - Endpoint schema validation and health checks.
   - Catalog querying and validation engine listings.
   - Session lifecycle (create, duplicate conflict, advance, reset, download, delete).
   - Rejection of disallowed datasets/models/methods and non-validation engines.
3. **Browser Smoke Testing:**
   - Full automated browser interaction verifying UI rendering, SVG charts, play/pause controls, trace download, and cryptographic provenance display.
