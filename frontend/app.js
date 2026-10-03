/**
 * IntelliTwin Dashboard Logic
 * Coordinates machine switching, real-time telemetry, Chart.js trends,
 * and API synchronization.
 */

// Machine Dataset with SVG icons
const MACHINES_DATA = {
  "cnc-01": {
    id: "cnc-01",
    name: "CNC Machine - 01",
    status: "healthy",
    badgeText: "Healthy",
    healthScore: 94,
    failureProb: 6,
    rulText: "320 Hours",
    ciRange: "[295 - 345 hrs]",
    nextMaint: "15 Aug 2025",
    svgFile: "assets/cnc_machine.svg",
    sparkColor: "#10b981",
    sparkPoints: "0,15 10,12 20,14 30,10 40,11 50,8 60,9",
    conditionBadgeText: "Normal Operation",
    conditionBadgeClass: "status-healthy",
    parameters: [
      { name: "Temperature", icon: "🌡️", val: "42.1 °C", status: "normal", tag: "Normal" },
      { name: "Vibration", icon: "📳", val: "1.2 mm/s", status: "normal", tag: "Normal" },
      { name: "Motor Current", icon: "⚡", val: "4.5 A", status: "normal", tag: "Normal" },
      { name: "Spindle Speed", icon: "⚙️", val: "3200 RPM", status: "normal", tag: "Normal" },
      { name: "Tool Load", icon: "🏋️", val: "52%", status: "normal", tag: "Normal" },
      { name: "Power", icon: "🔌", val: "1.4 kW", status: "normal", tag: "Normal" }
    ],
    alerts: [
      { time: "08:00 AM", title: "Daily Diagnostic Passed", desc: "All 5 axis servos reporting zero harmonic jitter." }
    ],
    aiSuggestion: {
      msg: "CNC Machine is operating well within nominal manufacturing tolerances. Predictive wear rate is minimal.",
      actions: [
        "Continue scheduled production shift.",
        "Perform routine visual spindle inspection next Friday.",
        "Maintain current coolant circulation pressure."
      ]
    },
    trends: {
      dates: ["26 Jun", "27 Jun", "28 Jun", "29 Jun", "30 Jun", "01 Jul", "02 Jul"],
      health: [96, 95, 95, 94, 94, 95, 94],
      vibration: [1.1, 1.2, 1.1, 1.3, 1.2, 1.2, 1.2],
      vibCurr: "1.2 mm/s"
    },
    history: [
      { date: "20 Jun 2025", type: "Inspection", desc: "Spindle bearing check OK", user: "John Smith" },
      { date: "10 May 2025", type: "Lubrication", desc: "Axis guideway regreased", user: "Mike Johnson" }
    ]
  },
  "robot-02": {
    id: "robot-02",
    name: "Robotic Arm - 02",
    status: "caution",
    badgeText: "Caution",
    healthScore: 72,
    failureProb: 28,
    rulText: "142 Hours",
    ciRange: "[120 - 164 hrs]",
    nextMaint: "10 Jul 2025",
    svgFile: "assets/robotic_arm.svg",
    sparkColor: "#f59e0b",
    sparkPoints: "0,8 10,9 20,11 30,13 40,16 50,18 60,20",
    conditionBadgeText: "Caution Required",
    conditionBadgeClass: "status-caution",
    parameters: [
      { name: "Temperature", icon: "🌡️", val: "58.4 °C", status: "caution", tag: "Caution" },
      { name: "Vibration", icon: "📳", val: "3.4 mm/s", status: "caution", tag: "Caution" },
      { name: "Motor Current", icon: "⚡", val: "6.8 A", status: "caution", tag: "Caution" },
      { name: "Joint Speed", icon: "⚙️", val: "180 deg/s", status: "normal", tag: "Normal" },
      { name: "Arm Load", icon: "🏋️", val: "68%", status: "caution", tag: "Caution" },
      { name: "Power", icon: "🔌", val: "1.8 kW", status: "normal", tag: "Normal" }
    ],
    alerts: [
      { time: "10:45 AM", title: "Joint 3 Temperature Warning", desc: "Temperature elevated by 8°C over operating baseline." },
      { time: "09:12 AM", title: "Harmonic Drive Jitter", desc: "Minor backlash detected on axis 4." }
    ],
    aiSuggestion: {
      msg: "Robotic Arm Joint 3 displays early thermal and harmonic backlash progression.",
      actions: [
        "Schedule joint gearbox lubrication within 7 days.",
        "Inspect harmonic drive seals for oil weeping.",
        "Calibrate position encoders at end-of-shift."
      ]
    },
    trends: {
      dates: ["26 Jun", "27 Jun", "28 Jun", "29 Jun", "30 Jun", "01 Jul", "02 Jul"],
      health: [82, 80, 78, 76, 75, 73, 72],
      vibration: [2.1, 2.4, 2.7, 3.0, 3.1, 3.3, 3.4],
      vibCurr: "3.4 mm/s"
    },
    history: [
      { date: "15 Jun 2025", type: "Calibration", desc: "End-effector TCP recalibrated", user: "Alex Brown" },
      { date: "02 May 2025", type: "Inspection", desc: "Cable harness continuity verified", user: "John Smith" }
    ]
  },
  "conveyor-03": {
    id: "conveyor-03",
    name: "Conveyor Belt - 03",
    status: "critical",
    badgeText: "Critical",
    healthScore: 38,
    failureProb: 78,
    rulText: "36 Hours",
    ciRange: "[28 - 44 hrs]",
    nextMaint: "03 Jul 2025",
    svgFile: "assets/conveyor_belt.svg",
    sparkColor: "#ef4444",
    sparkPoints: "0,5 10,7 20,9 30,12 40,15 50,19 60,22",
    conditionBadgeText: "Critical Condition",
    conditionBadgeClass: "status-critical",
    parameters: [
      { name: "Temperature", icon: "🌡️", val: "78 °C", status: "high", tag: "High" },
      { name: "Vibration", icon: "📳", val: "6.4 mm/s", status: "high", tag: "High" },
      { name: "Motor Current", icon: "⚡", val: "8.7 A", status: "caution", tag: "Caution" },
      { name: "Belt Speed", icon: "⚙️", val: "1.2 m/s", status: "normal", tag: "Normal" },
      { name: "Load", icon: "🏋️", val: "82%", status: "high", tag: "High" },
      { name: "Power", icon: "🔌", val: "2.4 kW", status: "caution", tag: "Caution" }
    ],
    alerts: [
      { time: "11:28 AM", title: "High Vibration Detected", desc: "Vibration level is 6.4 mm/s which is above the safe limit." },
      { time: "11:25 AM", title: "Motor Overheating", desc: "Motor temperature is 78 °C." },
      { time: "11:20 AM", title: "High Load", desc: "Machine is operating under high load." }
    ],
    aiSuggestion: {
      msg: "The conveyor belt is operating under critical condition. Immediate action is recommended to prevent breakdown.",
      actions: [
        "Check and replace the worn-out belt.",
        "Inspect motor and its connections.",
        "Lubricate the drive system.",
        "Reduce the load on the conveyor."
      ]
    },
    trends: {
      dates: ["26 Jun", "27 Jun", "28 Jun", "29 Jun", "30 Jun", "01 Jul", "02 Jul"],
      health: [72, 68, 62, 58, 50, 42, 38],
      vibration: [3.2, 3.8, 4.2, 4.9, 5.5, 6.0, 6.4],
      vibCurr: "6.4 mm/s"
    },
    history: [
      { date: "25 Jun 2025", type: "Inspection", desc: "Routine inspection completed", user: "John Smith" },
      { date: "18 Jun 2025", type: "Lubrication", desc: "Lubricated drive system", user: "Mike Johnson" },
      { date: "10 Jun 2025", type: "Replacement", desc: "Replaced belt roller bearings", user: "Alex Brown" }
    ]
  },
  "compressor-04": {
    id: "compressor-04",
    name: "Air Compressor - 04",
    status: "healthy",
    badgeText: "Healthy",
    healthScore: 89,
    failureProb: 11,
    rulText: "275 Hours",
    ciRange: "[250 - 300 hrs]",
    nextMaint: "28 Jul 2025",
    svgFile: "assets/air_compressor.svg",
    sparkColor: "#10b981",
    sparkPoints: "0,12 10,11 20,13 30,12 40,11 50,12 60,11",
    conditionBadgeText: "Normal Operation",
    conditionBadgeClass: "status-healthy",
    parameters: [
      { name: "Temperature", icon: "🌡️", val: "46.2 °C", status: "normal", tag: "Normal" },
      { name: "Vibration", icon: "📳", val: "1.6 mm/s", status: "normal", tag: "Normal" },
      { name: "Motor Current", icon: "⚡", val: "5.1 A", status: "normal", tag: "Normal" },
      { name: "Motor Speed", icon: "⚙️", val: "2950 RPM", status: "normal", tag: "Normal" },
      { name: "Compressor Load", icon: "🏋️", val: "60%", status: "normal", tag: "Normal" },
      { name: "Power", icon: "🔌", val: "3.2 kW", status: "normal", tag: "Normal" }
    ],
    alerts: [],
    aiSuggestion: {
      msg: "Air compressor operating smoothly with stable delivery pressure.",
      actions: [
        "Air filter replacement scheduled in 30 days.",
        "Drain condensation trap at end of week.",
        "Verify oil level in compressor sump."
      ]
    },
    trends: {
      dates: ["26 Jun", "27 Jun", "28 Jun", "29 Jun", "30 Jun", "01 Jul", "02 Jul"],
      health: [92, 91, 90, 90, 89, 89, 89],
      vibration: [1.4, 1.5, 1.5, 1.6, 1.6, 1.6, 1.6],
      vibCurr: "1.6 mm/s"
    },
    history: [
      { date: "12 Jun 2025", type: "Filter Change", desc: "Intake air filter replaced", user: "John Smith" }
    ]
  },
  "press-05": {
    id: "press-05",
    name: "Hydraulic Press - 05",
    status: "caution",
    badgeText: "Caution",
    healthScore: 65,
    failureProb: 35,
    rulText: "98 Hours",
    ciRange: "[82 - 114 hrs]",
    nextMaint: "18 Jul 2025",
    svgFile: "assets/hydraulic_press.svg",
    sparkColor: "#f59e0b",
    sparkPoints: "0,10 10,12 20,13 30,15 40,16 50,18 60,19",
    conditionBadgeText: "Caution Required",
    conditionBadgeClass: "status-caution",
    parameters: [
      { name: "Temperature", icon: "🌡️", val: "61.5 °C", status: "caution", tag: "Caution" },
      { name: "Vibration", icon: "📳", val: "3.8 mm/s", status: "caution", tag: "Caution" },
      { name: "Motor Current", icon: "⚡", val: "7.4 A", status: "caution", tag: "Caution" },
      { name: "Stroke Speed", icon: "⚙️", val: "45 cpm", status: "normal", tag: "Normal" },
      { name: "Press Load", icon: "🏋️", val: "75%", status: "caution", tag: "Caution" },
      { name: "Power", icon: "🔌", val: "4.1 kW", status: "caution", tag: "Caution" }
    ],
    alerts: [
      { time: "08:15 AM", title: "Hydraulic Fluid Temp High", desc: "Fluid reservoir temperature reached 61.5 °C." }
    ],
    aiSuggestion: {
      msg: "Hydraulic cooler heat transfer efficiency has dropped by 14%. Fluid breakdown risk.",
      actions: [
        "Check heat exchanger coolant flow rate.",
        "Inspect hydraulic cylinder seals for blow-by.",
        "Test fluid particulate level (ISO 4406)."
      ]
    },
    trends: {
      dates: ["26 Jun", "27 Jun", "28 Jun", "29 Jun", "30 Jun", "01 Jul", "02 Jul"],
      health: [75, 73, 71, 69, 68, 66, 65],
      vibration: [2.8, 3.0, 3.2, 3.4, 3.6, 3.7, 3.8],
      vibCurr: "3.8 mm/s"
    },
    history: [
      { date: "05 Jun 2025", type: "Oil Test", desc: "ISO 4406 fluid cleanliness 18/16/13", user: "Alex Brown" }
    ]
  }
};

let currentMachineId = "conveyor-03";
let healthChartInstance = null;
let vibrationChartInstance = null;

// Initialize Dashboard
document.addEventListener("DOMContentLoaded", () => {
  renderMachineCards();
  loadMachineDetail(currentMachineId);
  setupEventListeners();
  fetchBackendData();
});

function renderMachineCards() {
  const container = document.getElementById("machine-cards-container");
  if (!container) return;

  let html = "";
  Object.values(MACHINES_DATA).forEach(m => {
    const isSelected = m.id === currentMachineId ? "selected" : "";
    html += `
      <div class="machine-card ${isSelected}" data-id="${m.id}" onclick="selectMachine('${m.id}')">
        <div class="card-top">
          <span class="card-machine-name">${m.name}</span>
          <span class="status-badge ${m.status}">${m.badgeText}</span>
        </div>
        <div class="card-image-box">
          <img src="${m.svgFile}" alt="${m.name}" style="max-height: 100%; max-width: 100%;">
        </div>
        <div class="card-bottom">
          <div>
            <div class="card-health-label">Health Score</div>
            <div class="card-health-num">${m.healthScore}%</div>
          </div>
          <svg class="sparkline-svg" viewBox="0 0 60 25">
            <polyline fill="none" stroke="${m.sparkColor}" stroke-width="2" points="${m.sparkPoints}" />
          </svg>
        </div>
      </div>
    `;
  });

  // Add Machine Card
  html += `
    <div class="add-machine-card" onclick="alert('Connect new digital twin telemetry stream via MQTT/OPC-UA')">
      <span class="add-icon">+</span>
      <span style="font-size: 12px; font-weight: 500;">Add Machine</span>
    </div>
  `;

  container.innerHTML = html;
}

function selectMachine(machineId) {
  currentMachineId = machineId;
  renderMachineCards();
  loadMachineDetail(machineId);
}

function loadMachineDetail(machineId) {
  const m = MACHINES_DATA[machineId];
  if (!m) return;

  // Header & Title
  document.getElementById("detail-machine-name").textContent = m.name;
  const badge = document.getElementById("detail-condition-badge");
  badge.className = `critical-header-badge ${m.status}`;
  document.getElementById("detail-condition-text").textContent = m.conditionBadgeText;

  // Health Score Donut
  const healthNum = document.getElementById("detail-health-num");
  const healthStatus = document.getElementById("detail-health-status");
  const healthFill = document.getElementById("detail-health-fill");

  healthNum.textContent = `${m.healthScore}%`;
  healthStatus.textContent = m.badgeText;

  let strokeColor = "#10b981";
  if (m.status === "caution") strokeColor = "#f59e0b";
  if (m.status === "critical") strokeColor = "#ef4444";

  healthFill.style.stroke = strokeColor;
  const circumference = 251.2;
  const offset = circumference - (circumference * (m.healthScore / 100));
  healthFill.style.strokeDashoffset = offset;

  // SVG render
  document.getElementById("detail-machine-svg-box").innerHTML = `
    <img src="${m.svgFile}" alt="${m.name}" style="max-height: 100%; max-width: 100%;">
  `;

  // KPIs
  const failProbEl = document.getElementById("detail-fail-prob");
  failProbEl.textContent = `${m.failureProb}% ↗`;
  if (m.failureProb > 50) failProbEl.className = "health-kpi-val highlight-crit";
  else failProbEl.className = "health-kpi-val";

  document.getElementById("detail-rul").textContent = m.rulText;
  document.getElementById("detail-ci-range").textContent = m.ciRange;
  document.getElementById("detail-next-maint").textContent = m.nextMaint;

  // Real-time Parameters
  const paramList = document.getElementById("detail-param-list");
  let paramHtml = "";
  m.parameters.forEach(p => {
    paramHtml += `
      <div class="param-item">
        <div class="param-name">
          <span>${p.icon}</span>
          <span>${p.name}</span>
        </div>
        <div class="param-val-box">
          <span class="param-num">${p.val}</span>
          <span class="param-tag ${p.status}">${p.tag}</span>
        </div>
      </div>
    `;
  });
  paramList.innerHTML = paramHtml;

  // Alerts & Warnings
  const alertList = document.getElementById("detail-alert-list");
  if (m.alerts.length === 0) {
    alertList.innerHTML = `<div style="color: var(--text-muted); font-size: 12px; padding: 12px 0;">No active alerts. System healthy.</div>`;
  } else {
    let alertHtml = "";
    m.alerts.forEach(a => {
      alertHtml += `
        <div class="alert-entry ${m.status === 'critical' ? 'critical' : ''}">
          <div class="alert-entry-header">
            <span class="alert-entry-title">⚠️ ${a.title}</span>
            <span class="alert-entry-time">${a.time}</span>
          </div>
          <div class="alert-entry-desc">${a.desc}</div>
        </div>
      `;
    });
    alertList.innerHTML = alertHtml;
  }

  // AI Suggestion
  document.getElementById("detail-ai-msg").textContent = m.aiSuggestion.msg;
  const actionsList = document.getElementById("detail-ai-actions");
  let actionHtml = "";
  m.aiSuggestion.actions.forEach(act => {
    actionHtml += `<li>${act}</li>`;
  });
  actionsList.innerHTML = actionHtml;

  // Bottom Current Vibration Tag
  document.getElementById("curr-vib-tag").textContent = m.trends.vibCurr;

  // Maintenance History Table
  const tbody = document.getElementById("detail-history-tbody");
  let histHtml = "";
  m.history.forEach(h => {
    histHtml += `
      <tr>
        <td>${h.date}</td>
        <td><strong style="color: #fff;">${h.type}</strong></td>
        <td>${h.desc}</td>
        <td>${h.user}</td>
      </tr>
    `;
  });
  tbody.innerHTML = histHtml;

  // Update Charts
  renderCharts(m.trends, m.status);
}

function renderCharts(trends, status) {
  const ctxHealth = document.getElementById("healthScoreChart")?.getContext("2d");
  const ctxVib = document.getElementById("vibrationChart")?.getContext("2d");
  if (!ctxHealth || !ctxVib) return;

  let lineColor = "#ef4444";
  let fillColor = "rgba(239, 68, 68, 0.15)";
  if (status === "caution") {
    lineColor = "#f59e0b";
    fillColor = "rgba(245, 158, 11, 0.15)";
  } else if (status === "healthy") {
    lineColor = "#10b981";
    fillColor = "rgba(16, 185, 129, 0.15)";
  }

  // Destroy previous instances
  if (healthChartInstance) healthChartInstance.destroy();
  if (vibrationChartInstance) vibrationChartInstance.destroy();

  // Health Score Trend Chart
  healthChartInstance = new Chart(ctxHealth, {
    type: "line",
    data: {
      labels: trends.dates,
      datasets: [{
        label: "Health Score",
        data: trends.health,
        borderColor: lineColor,
        backgroundColor: fillColor,
        fill: true,
        tension: 0.3,
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: lineColor
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          grid: { color: "rgba(255,255,255,0.05)" },
          ticks: { color: "#64748b", font: { size: 10 } }
        },
        y: {
          min: 0,
          max: 100,
          grid: { color: "rgba(255,255,255,0.05)" },
          ticks: { color: "#64748b", font: { size: 10 } }
        }
      }
    }
  });

  // Vibration Trend Chart
  vibrationChartInstance = new Chart(ctxVib, {
    type: "line",
    data: {
      labels: trends.dates,
      datasets: [{
        label: "Vibration (mm/s)",
        data: trends.vibration,
        borderColor: "#f59e0b",
        backgroundColor: "rgba(245, 158, 11, 0.1)",
        fill: true,
        tension: 0.3,
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: "#f59e0b"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          grid: { color: "rgba(255,255,255,0.05)" },
          ticks: { color: "#64748b", font: { size: 10 } }
        },
        y: {
          min: 0,
          max: 10,
          grid: { color: "rgba(255,255,255,0.05)" },
          ticks: { color: "#64748b", font: { size: 10 } }
        }
      }
    }
  });
}

function setupEventListeners() {
  document.getElementById("btn-generate-report")?.addEventListener("click", () => {
    const m = MACHINES_DATA[currentMachineId];
    alert(`Generating Diagnostic PDF Report for ${m.name}...\nFailure Risk: ${m.failureProb}%\nRUL: ${m.rulText}\nConformal CI: ${m.ciRange}`);
  });

  // Search input filter
  document.getElementById("machine-search-input")?.addEventListener("input", (e) => {
    const query = e.target.value.toLowerCase();
    document.querySelectorAll(".machine-card").forEach(card => {
      const name = card.querySelector(".card-machine-name")?.textContent.toLowerCase() || "";
      if (name.includes(query)) card.style.display = "flex";
      else card.style.display = "none";
    });
  });

  // Tab switching
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
    });
  });
}

// Asynchronously fetch live backend status if Flask server is running
async function fetchBackendData() {
  try {
    const res = await fetch("/api/factory/overview");
    if (res.ok) {
      const data = await res.json();
      console.log("Connected to IntelliTwin Backend API:", data);
      if (data.overall_health) {
        document.getElementById("factory-health-percent").textContent = `${data.overall_health}%`;
      }
      if (data.active_machines_ratio) {
        document.getElementById("active-machines-count").textContent = data.active_machines_ratio;
      }
    }
  } catch (err) {
    console.log("IntelliTwin Backend running in standalone client mode.");
  }
}
