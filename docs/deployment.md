# Deployment Guide: IntelliTwin Validation Replay

This document describes how to deploy the IntelliTwin validation replay demonstration using a decoupled architecture:
- **Backend API**: Hosted on [Render](https://render.com) (FastAPI + Uvicorn)
- **Frontend Dashboard**: Hosted on [Vercel](https://vercel.com) (Static Web Application)

---

## Architecture Overview

```
                                +-----------------------------+
                                |      Vercel Dashboard       |
                                | (apps/twin_dashboard/...)   |
                                +-----------------------------+
                                               |
                                     Fetch / REST API (CORS)
                                               |
                                               v
                                +-----------------------------+
                                |       Render Backend        |
                                |    (FastAPI / Uvicorn)      |
                                +-----------------------------+
                                               |
                          +--------------------+--------------------+
                          |                                         |
                          v                                         v
              +-----------------------+                 +-----------------------+
              |   Frozen Model &      |                 |   Bundled Validation  |
              | Calibrator Artifacts  |                 |       Telemetry       |
              | (models/, calibrators)|                 | (data/validation_... )|
              +-----------------------+                 +-----------------------+
```

### Self-Contained Deployment (Zero Raw Data Dependency)
- The production demo does **not require raw C-MAPSS files** (`data/raw/cmapss/*.txt`).
- All 61 validation partition engines across datasets (`FD001`, `FD002`, `FD004`) are pre-extracted and bundled in `data/validation_telemetry/`.
- **Zero test data exposure**: Only validation trajectories are bundled. Held-out test trajectories, training partition data, and oracle labels (`rul_true`, `failure_cycle`, `lifecycle_stage`) are strictly excluded.

---

## 1. Backend Deployment on Render

### Option A: Render Blueprint (Recommended)
1. Fork or push this repository to GitHub.
2. In the Render Dashboard, click **New +** and select **Blueprint**.
3. Select your repository. Render will automatically detect [`render.yaml`](../render.yaml).
4. Review the service configuration:
   - **Service Name**: `intellitwin-backend`
   - **Runtime**: `Python`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements/twin-demo.lock.txt && pip install -e . --no-deps`
   - **Start Command**: `uvicorn intellitwin.twin.api:app --host 0.0.0.0 --port $PORT`
5. Click **Apply**.
6. Once deployed, Render provides a service URL, e.g., `https://intellitwin-backend.onrender.com`.

### Option B: Manual Web Service Setup
1. In Render Dashboard, click **New +** > **Web Service**.
2. Connect your repository.
3. Configure the following fields:
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements/twin-demo.lock.txt && pip install -e . --no-deps`
   - **Start Command**: `uvicorn intellitwin.twin.api:app --host 0.0.0.0 --port $PORT`
4. In **Environment Variables**, add:
   - `PYTHON_VERSION`: `3.11.9`
   - `CORS_ORIGINS`: `*` (or your specific Vercel app domain, e.g., `https://intellitwin.vercel.app`)
5. Click **Deploy Web Service**.

### Verifying Backend Health
Once deployed, verify the health endpoint:
```bash
curl https://<your-render-service>.onrender.com/api/health
```
Expected response:
```json
{
  "status": "ok",
  "dependencies_ready": true,
  "artifacts_ready": true,
  "active_session_id": null
}
```

---

## 2. Dashboard Deployment on Vercel

The front-end is a static single-page application located in `apps/twin_dashboard/`.

### Deployment Steps
1. Log in to [Vercel](https://vercel.com) and click **Add New...** > **Project**.
2. Import the `AI-Driven-Digital-Twin-Predictive-Maintainence` repository.
3. In **Project Settings**:
   - **Framework Preset**: `Other`
   - **Root Directory**: You can either leave it as `./` (the root [`vercel.json`](../vercel.json) routes requests to `apps/twin_dashboard/`) or set it to `apps/twin_dashboard` (which uses [`apps/twin_dashboard/vercel.json`](../apps/twin_dashboard/vercel.json)).
   - **Build & Output Settings**: No build step required (static HTML/CSS/JS).
4. Click **Deploy**.

---

## 3. Connecting Dashboard to Backend

The dashboard supports three seamless methods to link to the deployed Render backend:

### Method 1: URL Query Parameter (Instant Link)
Append `?api=<backend-url>` to the Vercel dashboard URL:
```
https://<your-vercel-dashboard>.vercel.app/?api=https://<your-render-backend>.onrender.com
```
The application automatically saves this URL in browser `localStorage` for future visits.

### Method 2: In-App Connection Dialog
1. Click the status indicator or the gear icon (⚙) in the top-right header of the dashboard.
2. Enter your Render backend URL (e.g. `https://intellitwin-backend.onrender.com`).
3. Click **Save & Connect**. The dashboard immediately validates the connection and loads the replay catalog.

### Method 3: Environment / HTML Meta Tag
You can configure a default backend URL by setting a `<meta>` tag in `apps/twin_dashboard/index.html`:
```html
<meta name="intellitwin-api-url" content="https://intellitwin-backend.onrender.com">
```

---

## 4. Local Smoke Test (Offline & Cross-Origin Emulation)

To verify the setup locally before deploying:

1. **Start the FastAPI backend**:
   ```bash
   uv run uvicorn intellitwin.twin.api:app --host 127.0.0.1 --port 8000
   ```

2. **Start a separate static server for the dashboard** (emulating Vercel):
   ```bash
   # From apps/twin_dashboard
   python -m http.server 3000
   ```

3. **Open the browser**:
   Navigate to `http://localhost:3000/?api=http://127.0.0.1:8000`.
   - Verify the connection status shows **Connected** (green dot).
   - Select dataset `FD002`, engine `9`, model `GBR`, method `decision_aware_hcp`.
   - Click **Apply & Load Session**.
   - Click **Start Playback** or step through cycles.
   - Verify that predictions, uncertainty bounds, and operational statuses update each cycle.
   - Click **Download Trace (CSV)** to verify export functionality.
