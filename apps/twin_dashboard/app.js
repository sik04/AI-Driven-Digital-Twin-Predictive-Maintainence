/**
 * IntelliTwin Validation Replay Dashboard Front-End Application
 * 
 * Implements:
 * - Direct REST interaction with /api/catalog, /api/sessions, /api/sessions/{id}/advance, etc.
 * - Single-step and playback loops (1, 2, or 5 cycles/second)
 * - Anti-skipping: one in-flight request at a time with expected_cycle tracking
 * - Inline SVG rendering for RUL trajectory, uncertainty band, and selectable sensor curves
 * - Accessible controls and visible error handling
 */

// Application State
const state = {
  catalog: null,
  activeSession: null,
  history: [], // [{ cycle, prediction, lower_rul, upper_rul, regime, sensors, state, action }]
  isPlaying: false,
  playbackTimer: null,
  inFlight: false,
  selectedSensors: ['s2', 's3', 's4'],
};

const SENSOR_COLUMNS = [
  's2', 's3', 's4', 's7', 's8', 's9',
  's11', 's12', 's13', 's14', 's15', 's17', 's20', 's21'
];

// DOM Elements
const dom = {
  datasetSelect: document.getElementById('dataset-select'),
  engineSelect: document.getElementById('engine-select'),
  modelSelect: document.getElementById('model-select'),
  methodSelect: document.getElementById('method-select'),
  btnCreateSession: document.getElementById('btn-create-session'),
  btnReleaseSession: document.getElementById('btn-release-session'),
  playbackSpeed: document.getElementById('playback-speed'),
  btnPlayPause: document.getElementById('btn-play-pause'),
  btnStep: document.getElementById('btn-step'),
  btnReset: document.getElementById('btn-reset'),
  btnDownloadTrace: document.getElementById('btn-download-trace'),
  statusAlert: document.getElementById('status-alert'),
  valCycle: document.getElementById('val-cycle'),
  valWarmup: document.getElementById('val-warmup'),
  valRegime: document.getElementById('val-regime'),
  valPrediction: document.getElementById('val-prediction'),
  valInterval: document.getElementById('val-interval'),
  valLowerBound: document.getElementById('val-lower-bound'),
  decisionBanner: document.getElementById('decision-banner'),
  decisionActionBadge: document.getElementById('decision-action-badge'),
  decisionExplanation: document.getElementById('decision-explanation'),
  rulChartSvg: document.getElementById('rul-chart-svg'),
  sensorChartSvg: document.getElementById('sensor-chart-svg'),
  sensorSelect1: document.getElementById('sensor-select-1'),
  sensorSelect2: document.getElementById('sensor-select-2'),
  sensorSelect3: document.getElementById('sensor-select-3'),
  provenanceContent: document.getElementById('provenance-content'),
};

// Initial Setup
document.addEventListener('DOMContentLoaded', async () => {
  setupSensorSelectors();
  bindEventListeners();
  await loadCatalog();
  await checkHealthAndActiveSession();
});

function setupSensorSelectors() {
  const selects = [dom.sensorSelect1, dom.sensorSelect2, dom.sensorSelect3];
  selects.forEach((sel, idx) => {
    sel.innerHTML = '';
    SENSOR_COLUMNS.forEach(col => {
      const opt = document.createElement('option');
      opt.value = col;
      opt.textContent = col.toUpperCase();
      if (col === state.selectedSensors[idx]) {
        opt.selected = true;
      }
      sel.appendChild(opt);
    });
    sel.addEventListener('change', () => {
      state.selectedSensors[idx] = sel.value;
      renderSensorChart();
    });
  });
}

function bindEventListeners() {
  dom.datasetSelect.addEventListener('change', onDatasetChange);
  dom.btnCreateSession.addEventListener('click', onCreateSession);
  dom.btnReleaseSession.addEventListener('click', onReleaseSession);
  dom.btnPlayPause.addEventListener('click', togglePlayback);
  dom.btnStep.addEventListener('click', advanceSingleCycle);
  dom.btnReset.addEventListener('click', onReset);
  dom.btnDownloadTrace.addEventListener('click', onDownloadTrace);
}

// API Communication
async function loadCatalog() {
  try {
    const res = await fetch('/api/catalog');
    if (!res.ok) throw new Error(`Catalog load failed: ${res.statusText}`);
    const data = await res.json();
    state.catalog = data;

    // Populate dataset dropdown
    dom.datasetSelect.innerHTML = '';
    data.datasets.forEach(ds => {
      const opt = document.createElement('option');
      opt.value = ds;
      opt.textContent = ds;
      if (ds === data.default_dataset) opt.selected = true;
      dom.datasetSelect.appendChild(opt);
    });

    // Populate engine dropdown for default dataset
    populateEngineDropdown(dom.datasetSelect.value);

    // Set defaults
    dom.modelSelect.value = data.default_model;
    dom.methodSelect.value = data.default_method;
  } catch (err) {
    showError(`Failed to load catalog: ${err.message}`);
  }
}

function onDatasetChange() {
  populateEngineDropdown(dom.datasetSelect.value);
}

function populateEngineDropdown(dataset) {
  if (!state.catalog) return;
  const engines = state.catalog.validation_engines[dataset] || [];
  dom.engineSelect.innerHTML = '';
  engines.forEach(eid => {
    const opt = document.createElement('option');
    opt.value = eid;
    opt.textContent = `Unit ${eid}`;
    dom.engineSelect.appendChild(opt);
  });
  if (dataset === state.catalog.default_dataset && engines.includes(state.catalog.default_engine)) {
    dom.engineSelect.value = state.catalog.default_engine;
  }
}

async function checkHealthAndActiveSession() {
  try {
    const res = await fetch('/api/health');
    if (!res.ok) {
      showError(`Backend health check failed (HTTP ${res.status}).`);
      return;
    }
    const data = await res.json();
    if (data.status !== 'ok') {
      showError(`Backend status degraded: dependencies_ready=${data.dependencies_ready}, artifacts_ready=${data.artifacts_ready}`);
    }
    if (data.active_session_id) {
      // Resume or fetch active session
      const sRes = await fetch(`/api/sessions/${data.active_session_id}`);
      if (sRes.ok) {
        const sData = await sRes.json();
        setActiveSession(sData);
      }
    }
  } catch (err) {
    console.warn('Initial health check notice:', err);
    showError(`Cannot connect to backend server: ${err.message}. Ensure backend is running at http://127.0.0.1:8000.`);
  }
}

async function onCreateSession() {
  clearError();
  pausePlayback();

  const engineId = parseInt(dom.engineSelect.value, 10);
  if (!state.catalog || !dom.datasetSelect.value || isNaN(engineId)) {
    showError('Please select a valid dataset and validation engine ID.');
    return;
  }

  // If there is an existing active session, release it first so the new session succeeds
  if (state.activeSession) {
    try {
      await fetch(`/api/sessions/${state.activeSession.session_id}`, { method: 'DELETE' });
    } catch (e) {
      console.warn('Could not cleanly release previous session before creation', e);
    }
  } else {
    // Check if an orphaned session exists on the backend
    try {
      const hRes = await fetch('/api/health');
      if (hRes.ok) {
        const hData = await hRes.json();
        if (hData.active_session_id) {
          await fetch(`/api/sessions/${hData.active_session_id}`, { method: 'DELETE' });
        }
      }
    } catch (_) {}
  }

  const payload = {
    dataset: dom.datasetSelect.value,
    engine_id: engineId,
    model_family: dom.modelSelect.value,
    method_id: dom.methodSelect.value,
  };

  try {
    dom.btnCreateSession.disabled = true;
    const res = await fetch('/api/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (res.status === 409) {
      throw new Error('An active replay session is already open. Release it first.');
    }
    if (!res.ok) {
      const errJson = await res.json().catch(() => ({}));
      throw new Error(errJson.message || `Session creation failed (HTTP ${res.status})`);
    }

    const data = await res.json();
    state.history = [];
    setActiveSession(data);
  } catch (err) {
    showError(err.message);
  } finally {
    dom.btnCreateSession.disabled = false;
  }
}

async function onReleaseSession() {
  if (!state.activeSession) return;
  pausePlayback();
  clearError();

  try {
    const res = await fetch(`/api/sessions/${state.activeSession.session_id}`, {
      method: 'DELETE',
    });
    if (!res.ok && res.status !== 404) {
      const errJson = await res.json().catch(() => ({}));
      throw new Error(errJson.message || `Failed to release session`);
    }
    clearActiveSession();
  } catch (err) {
    showError(err.message);
  }
}

async function advanceSingleCycle() {
  if (!state.activeSession || state.inFlight) return;
  if (state.activeSession.state === 'maintained' || state.activeSession.state === 'failed') {
    pausePlayback();
    return;
  }

  state.inFlight = true;
  dom.btnStep.disabled = true;
  clearError();

  const expectedCycle = state.activeSession.cycle;
  try {
    const res = await fetch(`/api/sessions/${state.activeSession.session_id}/advance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ expected_cycle: expectedCycle }),
    });

    if (res.status === 409) {
      pausePlayback();
      throw new Error('Replay state conflict: out-of-order or duplicate request. Playback paused.');
    }
    if (!res.ok) {
      pausePlayback();
      const errJson = await res.json().catch(() => ({}));
      throw new Error(errJson.message || `Advance failed (HTTP ${res.status})`);
    }

    const updated = await res.json();
    updateSessionState(updated);

    if (updated.state === 'maintained' || updated.state === 'failed') {
      pausePlayback();
    }
  } catch (err) {
    pausePlayback();
    showError(err.message);
  } finally {
    state.inFlight = false;
    const isTerminal = state.activeSession && (state.activeSession.state === 'maintained' || state.activeSession.state === 'failed');
    dom.btnStep.disabled = isTerminal || !state.activeSession;
  }
}

function togglePlayback() {
  if (state.isPlaying) {
    pausePlayback();
  } else {
    startPlayback();
  }
}

function startPlayback() {
  if (!state.activeSession) return;
  if (state.activeSession.state === 'maintained' || state.activeSession.state === 'failed') return;
  if (state.isPlaying) return;

  if (state.playbackTimer) {
    clearInterval(state.playbackTimer);
    state.playbackTimer = null;
  }

  state.isPlaying = true;
  dom.btnPlayPause.textContent = 'Pause Playback';
  dom.btnPlayPause.classList.add('playing');

  const speedHz = parseFloat(dom.playbackSpeed.value) || 1.0;
  const intervalMs = Math.round(1000 / speedHz);

  state.playbackTimer = setInterval(() => {
    if (!state.inFlight && state.isPlaying) {
      advanceSingleCycle();
    }
  }, intervalMs);
}

function pausePlayback() {
  state.isPlaying = false;
  if (state.playbackTimer) {
    clearInterval(state.playbackTimer);
    state.playbackTimer = null;
  }
  dom.btnPlayPause.textContent = 'Start Playback';
  dom.btnPlayPause.classList.remove('playing');
}

async function onReset() {
  if (!state.activeSession) return;
  pausePlayback();
  clearError();

  try {
    const res = await fetch(`/api/sessions/${state.activeSession.session_id}/reset`, {
      method: 'POST',
    });
    if (!res.ok) {
      const errJson = await res.json().catch(() => ({}));
      throw new Error(errJson.message || `Reset failed`);
    }
    const resetData = await res.json();
    state.history = [];
    updateSessionState(resetData);
  } catch (err) {
    showError(err.message);
  }
}

function onDownloadTrace() {
  if (!state.activeSession) return;
  const url = `/api/sessions/${state.activeSession.session_id}/trace.csv`;
  window.location.href = url;
}

// UI State Updates
function setActiveSession(session) {
  state.activeSession = session;
  dom.btnReleaseSession.disabled = false;
  dom.btnPlayPause.disabled = false;
  dom.btnStep.disabled = false;
  dom.btnReset.disabled = false;
  dom.btnDownloadTrace.disabled = false;

  dom.datasetSelect.value = session.dataset;
  populateEngineDropdown(session.dataset);
  dom.engineSelect.value = session.engine_id;
  dom.modelSelect.value = session.model_family;
  dom.methodSelect.value = session.method_id;

  updateSessionState(session);
}

function clearActiveSession() {
  state.activeSession = null;
  state.history = [];
  dom.btnReleaseSession.disabled = true;
  dom.btnPlayPause.disabled = true;
  dom.btnStep.disabled = true;
  dom.btnReset.disabled = true;
  dom.btnDownloadTrace.disabled = true;

  dom.valCycle.textContent = '0';
  dom.valWarmup.textContent = 'Waiting for session';
  dom.valRegime.textContent = '—';
  dom.valPrediction.textContent = '—';
  dom.valInterval.textContent = '—';
  dom.valLowerBound.textContent = 'Lower bound: —';

  dom.decisionBanner.className = 'decision-banner card state-ready';
  dom.decisionActionBadge.className = 'action-badge badge-ready';
  dom.decisionActionBadge.textContent = 'READY';
  dom.decisionExplanation.textContent = 'Select a validation engine and create a session to start replay.';

  dom.provenanceContent.innerHTML = '<p class="text-muted">No active session loaded.</p>';

  renderRulChart();
  renderSensorChart();
}

function updateSessionState(session) {
  state.activeSession = session;

  if (session.cycle > 0) {
    state.history.push({
      cycle: session.cycle,
      prediction: session.prediction,
      lower_rul: session.lower_rul,
      upper_rul: session.upper_rul,
      regime: session.regime,
      sensors: session.sensors || {},
      state: session.state,
      action: session.action,
    });
  }

  // Cards
  dom.valCycle.textContent = session.cycle;
  if (session.state === 'warming_up') {
    dom.valWarmup.textContent = `Collecting observations: ${session.cycle}/30`;
  } else if (session.state === 'ready') {
    dom.valWarmup.textContent = 'Ready to advance';
  } else if (session.state === 'active') {
    dom.valWarmup.textContent = 'Sequential operation';
  } else if (session.state === 'maintained') {
    dom.valWarmup.textContent = 'Maintenance intervention';
  } else if (session.state === 'failed') {
    dom.valWarmup.textContent = 'Terminal failure';
  }

  dom.valRegime.textContent = session.regime || '—';
  dom.valPrediction.textContent = session.prediction !== null ? session.prediction.toFixed(2) : '—';

  if (session.lower_rul !== null && session.upper_rul !== null) {
    dom.valInterval.textContent = `[${session.lower_rul.toFixed(1)}, ${session.upper_rul.toFixed(1)}]`;
    dom.valLowerBound.textContent = `Lower bound: ${session.lower_rul.toFixed(2)}`;
  } else {
    dom.valInterval.textContent = '—';
    dom.valLowerBound.textContent = 'Lower bound: —';
  }

  // Decision Banner
  dom.decisionBanner.className = `decision-banner card state-${session.state}`;
  dom.decisionActionBadge.className = `action-badge badge-${session.state}`;
  dom.decisionActionBadge.textContent = (session.action || session.state).toUpperCase();
  dom.decisionExplanation.textContent = session.explanation;

  // Controls availability
  const isTerminal = session.state === 'maintained' || session.state === 'failed';
  dom.btnPlayPause.disabled = isTerminal;
  dom.btnStep.disabled = isTerminal;

  // Provenance
  renderProvenance(session.artifact_provenance);

  // Charts
  renderRulChart();
  renderSensorChart();
}

function renderProvenance(prov) {
  if (!prov) return;
  dom.provenanceContent.innerHTML = `
    <div class="prov-item">
      <span class="prov-label">Model Identifier:</span>
      <span class="prov-value">${escapeHtml(prov.model_id)} (${escapeHtml(prov.model_configuration_id)})</span>
    </div>
    <div class="prov-item">
      <span class="prov-label">Calibrator Bundle:</span>
      <span class="prov-value">${escapeHtml(prov.calibrator_bundle_id)}</span>
    </div>
    <div class="prov-item">
      <span class="prov-label">Model Checkpoint SHA-256:</span>
      <span class="prov-value">${escapeHtml(prov.model_checkpoint_sha256)}</span>
    </div>
    <div class="prov-item">
      <span class="prov-label">Calibrator Artifact SHA-256:</span>
      <span class="prov-value">${escapeHtml(prov.calibrator_artifact_sha256)}</span>
    </div>
    <div class="prov-item">
      <span class="prov-label">Fitted Preprocessor SHA-256:</span>
      <span class="prov-value">${escapeHtml(prov.preprocessor_sha256)}</span>
    </div>
    <div class="prov-item">
      <span class="prov-label">Split Manifest SHA-256:</span>
      <span class="prov-value">${escapeHtml(prov.split_manifest_sha256)}</span>
    </div>
  `;
}

// Inline SVG Chart Rendering
function renderRulChart() {
  const svg = dom.rulChartSvg;
  const pts = state.history.filter(h => h.prediction !== null && h.lower_rul !== null && h.upper_rul !== null);

  if (pts.length === 0) {
    svg.innerHTML = `
      <text x="350" y="125" text-anchor="middle" fill="#64748b" font-size="13">
        No active inference cycles yet (warm-up phase: 1–29 cycles)
      </text>
    `;
    return;
  }

  const width = 700;
  const height = 240;
  const padding = { top: 20, right: 30, bottom: 35, left: 50 };

  const minCycle = Math.min(...pts.map(p => p.cycle));
  const maxCycle = Math.max(...pts.map(p => p.cycle));
  const cycleSpan = Math.max(maxCycle - minCycle, 10);

  let maxRul = Math.max(...pts.map(p => p.upper_rul), 50);
  maxRul = Math.ceil(maxRul / 10) * 10;

  const xScale = (c) => padding.left + ((c - minCycle) / cycleSpan) * (width - padding.left - padding.right);
  const yScale = (r) => height - padding.bottom - (Math.max(0, r) / maxRul) * (height - padding.top - padding.bottom);

  // Build Uncertainty Band Path
  let bandPath = '';
  // Upper line forward
  pts.forEach((p, i) => {
    const x = xScale(p.cycle).toFixed(1);
    const y = yScale(p.upper_rul).toFixed(1);
    bandPath += (i === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`);
  });
  // Lower line backward
  for (let i = pts.length - 1; i >= 0; i--) {
    const p = pts[i];
    const x = xScale(p.cycle).toFixed(1);
    const y = yScale(p.lower_rul).toFixed(1);
    bandPath += ` L ${x} ${y}`;
  }
  bandPath += ' Z';

  // Build Prediction Line
  let predPath = '';
  pts.forEach((p, i) => {
    const x = xScale(p.cycle).toFixed(1);
    const y = yScale(p.prediction).toFixed(1);
    predPath += (i === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`);
  });

  // Threshold Line at lower_rul = 1.0
  const threshY = yScale(1.0).toFixed(1);

  svg.innerHTML = `
    <!-- Grid & Axes -->
    <line x1="${padding.left}" y1="${padding.top}" x2="${padding.left}" y2="${height - padding.bottom}" stroke="#263554" stroke-width="1"/>
    <line x1="${padding.left}" y1="${height - padding.bottom}" x2="${width - padding.right}" y2="${height - padding.bottom}" stroke="#263554" stroke-width="1"/>
    
    <!-- Y Axis Labels -->
    <text x="${padding.left - 8}" y="${padding.top + 5}" text-anchor="end" fill="#64748b" font-size="10">${maxRul}</text>
    <text x="${padding.left - 8}" y="${(padding.top + height - padding.bottom) / 2}" text-anchor="end" fill="#64748b" font-size="10">${Math.round(maxRul / 2)}</text>
    <text x="${padding.left - 8}" y="${height - padding.bottom}" text-anchor="end" fill="#64748b" font-size="10">0</text>
    <text x="15" y="${height / 2}" text-anchor="middle" fill="#64748b" font-size="10" transform="rotate(-90 15 ${height / 2})">RUL (cycles)</text>

    <!-- X Axis Labels -->
    <text x="${padding.left}" y="${height - padding.bottom + 18}" text-anchor="middle" fill="#64748b" font-size="10">${minCycle}</text>
    <text x="${width - padding.right}" y="${height - padding.bottom + 18}" text-anchor="middle" fill="#64748b" font-size="10">${maxCycle}</text>
    <text x="${(padding.left + width - padding.right) / 2}" y="${height - 8}" text-anchor="middle" fill="#64748b" font-size="10">Operating Cycles Elapsed</text>

    <!-- Policy Action Threshold (1.0 cycle) -->
    <line x1="${padding.left}" y1="${threshY}" x2="${width - padding.right}" y2="${threshY}" stroke="#f43f5e" stroke-width="1" stroke-dasharray="4 3"/>
    <text x="${width - padding.right}" y="${parseFloat(threshY) - 4}" text-anchor="end" fill="#f43f5e" font-size="9">PM Threshold (1.0 cycle)</text>

    <!-- 90% Uncertainty Band -->
    <path d="${bandPath}" fill="rgba(56, 189, 248, 0.18)"/>

    <!-- Point Prediction Path -->
    <path d="${predPath}" fill="none" stroke="#38bdf8" stroke-width="2"/>
  `;
}

function renderSensorChart() {
  const svg = dom.sensorChartSvg;
  const pts = state.history.filter(h => h.sensors && Object.keys(h.sensors).length > 0);

  if (pts.length === 0) {
    svg.innerHTML = `
      <text x="350" y="125" text-anchor="middle" fill="#64748b" font-size="13">
        No sensor observations recorded yet
      </text>
    `;
    return;
  }

  const width = 700;
  const height = 240;
  const padding = { top: 20, right: 30, bottom: 35, left: 50 };

  const minCycle = Math.min(...pts.map(p => p.cycle));
  const maxCycle = Math.max(...pts.map(p => p.cycle));
  const cycleSpan = Math.max(maxCycle - minCycle, 10);

  const colors = ['#10b981', '#f59e0b', '#a855f7'];
  const xScale = (c) => padding.left + ((c - minCycle) / cycleSpan) * (width - padding.left - padding.right);

  // Normalize each selected sensor to 0..1 range for unified multi-sensor visualization
  const linesSvg = state.selectedSensors.map((sensorKey, idx) => {
    const vals = pts.map(p => p.sensors[sensorKey]).filter(v => v !== undefined && !isNaN(v));
    if (vals.length === 0) return '';
    const minVal = Math.min(...vals);
    const maxVal = Math.max(...vals);
    const valSpan = maxVal - minVal > 1e-6 ? maxVal - minVal : 1.0;

    let pathStr = '';
    pts.forEach((p, i) => {
      const v = p.sensors[sensorKey];
      if (v === undefined || isNaN(v)) return;
      const normY = (v - minVal) / valSpan;
      const x = xScale(p.cycle).toFixed(1);
      const y = (height - padding.bottom - normY * (height - padding.top - padding.bottom)).toFixed(1);
      pathStr += (pathStr === '' ? `M ${x} ${y}` : ` L ${x} ${y}`);
    });

    return `<path d="${pathStr}" fill="none" stroke="${colors[idx]}" stroke-width="1.8"/>`;
  }).join('');

  svg.innerHTML = `
    <!-- Grid & Axes -->
    <line x1="${padding.left}" y1="${padding.top}" x2="${padding.left}" y2="${height - padding.bottom}" stroke="#263554" stroke-width="1"/>
    <line x1="${padding.left}" y1="${height - padding.bottom}" x2="${width - padding.right}" y2="${height - padding.bottom}" stroke="#263554" stroke-width="1"/>
    
    <!-- Y Axis Labels -->
    <text x="${padding.left - 8}" y="${padding.top + 5}" text-anchor="end" fill="#64748b" font-size="10">Max</text>
    <text x="${padding.left - 8}" y="${height - padding.bottom}" text-anchor="end" fill="#64748b" font-size="10">Min</text>
    <text x="15" y="${height / 2}" text-anchor="middle" fill="#64748b" font-size="10" transform="rotate(-90 15 ${height / 2})">Relative Sensor Range</text>

    <!-- X Axis Labels -->
    <text x="${padding.left}" y="${height - padding.bottom + 18}" text-anchor="middle" fill="#64748b" font-size="10">${minCycle}</text>
    <text x="${width - padding.right}" y="${height - padding.bottom + 18}" text-anchor="middle" fill="#64748b" font-size="10">${maxCycle}</text>
    <text x="${(padding.left + width - padding.right) / 2}" y="${height - 8}" text-anchor="middle" fill="#64748b" font-size="10">Operating Cycles Elapsed</text>

    <!-- Sensor Paths -->
    ${linesSvg}
  `;
}

// Helpers
function showError(msg) {
  dom.statusAlert.textContent = msg;
  dom.statusAlert.className = 'status-alert error';
  dom.statusAlert.style.display = 'block';
}

function clearError() {
  dom.statusAlert.textContent = '';
  dom.statusAlert.style.display = 'none';
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
