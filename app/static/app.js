/**
 * Kestrel Home · Pre-Dispatch Return Risk Intelligence Client
 * Interactive Liquidmorphism & Glassmorphic Engine Controller
 */

// DOM Elements
const form = document.getElementById('riskForm');
const submitBtn = document.getElementById('submitBtn');
const submitLabel = document.getElementById('submitLabel');
const btnResetForm = document.getElementById('btnResetForm');
const btnPresetLow = document.getElementById('btnPresetLow');
const btnPresetMedium = document.getElementById('btnPresetMedium');
const btnPresetHigh = document.getElementById('btnPresetHigh');
const btnLoadNextUnlabelled = document.getElementById('btnLoadNextUnlabelled');
const btnRefreshHistory = document.getElementById('btnRefreshHistory');

// Views & Display
const standbyView = document.getElementById('standbyView');
const activeAssessmentView = document.getElementById('activeAssessmentView');
const resOrderId = document.getElementById('resOrderId');
const riskPillBadge = document.getElementById('riskPillBadge');
const riskPillText = document.getElementById('riskPillText');
const resScoreValue = document.getElementById('resScoreValue');
const gaugeFillTrack = document.getElementById('gaugeFillTrack');
const liquidWaveFluid = document.getElementById('liquidWaveFluid');
const scaleMarkerPin = document.getElementById('scaleMarkerPin');
const actionRecBox = document.getElementById('actionRecBox');
const actionIcon = document.getElementById('actionIcon');
const resActionText = document.getElementById('resActionText');
const resActionStrategy = document.getElementById('resActionStrategy');
const reasonsContainer = document.getElementById('reasonsContainer');
const sessionChecksCount = document.getElementById('sessionChecksCount');
const auditTableBody = document.getElementById('auditTableBody');

// Numeric form fields
const NUMERIC_FIELDS = [
  'discount_pct', 'qty', 'order_value_inr', 'promised_delivery_days',
  'delivery_pincode', 'customer_prior_orders', 'customer_prior_returns'
];

// SVG circle radius is 68, circumference is ~427.26
const CIRCLE_CIRCUMFERENCE = 2 * Math.PI * 68;

let currentUnlabelledIndex = 0;
let cachedPresets = {};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  initPresets();
  loadAuditHistory();
  loadStats();
  setupMouseAura();
});

// Setup dynamic fluid aura on submit button
function setupMouseAura() {
  submitBtn.addEventListener('mousemove', (e) => {
    const rect = submitBtn.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    submitBtn.style.setProperty('--mouse-x', `${x}px`);
    submitBtn.style.setProperty('--mouse-y', `${y}px`);
  });
}

// Fetch and bind presets
async function initPresets() {
  try {
    const res = await fetch('/api/presets');
    if (!res.ok) return;
    const presets = await res.json();
    presets.forEach(p => {
      cachedPresets[p.id] = p.data;
    });

    btnPresetLow.addEventListener('click', () => applyPreset('low_risk'));
    btnPresetMedium.addEventListener('click', () => applyPreset('medium_risk'));
    btnPresetHigh.addEventListener('click', () => applyPreset('high_risk'));
  } catch (err) {
    console.warn('Presets could not be loaded:', err);
  }
}

// Apply Preset Data into Form
function applyPreset(presetId) {
  const data = cachedPresets[presetId];
  if (!data) return;
  populateForm(data);
  triggerFormFlash();
  // Auto score on preset click for smooth preview
  submitForm();
}

// Next Unlabelled Order from Test Snapshot
btnLoadNextUnlabelled.addEventListener('click', async () => {
  try {
    btnLoadNextUnlabelled.disabled = true;
    const res = await fetch(`/api/example?index=${currentUnlabelledIndex}`);
    if (!res.ok) throw new Error('Could not fetch queue order');
    const data = await res.json();
    populateForm(data);
    triggerFormFlash();
    currentUnlabelledIndex++;
    submitForm();
  } catch (err) {
    console.error(err);
  } finally {
    btnLoadNextUnlabelled.disabled = false;
  }
});

// Populate Form Inputs
function populateForm(data) {
  for (const [key, value] of Object.entries(data)) {
    const field = form.elements[key];
    if (field) {
      field.value = value ?? '';
    }
  }
}

// Subtle visual flash on load
function triggerFormFlash() {
  const panel = document.querySelector('.panel-order-entry');
  panel.style.transition = 'background-color 0.25s ease';
  panel.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
  setTimeout(() => {
    panel.style.backgroundColor = '';
  }, 300);
}

// Reset form
btnResetForm.addEventListener('click', () => {
  form.reset();
  standbyView.classList.remove('hidden');
  activeAssessmentView.classList.add('hidden');
});

// Refresh history manually
btnRefreshHistory.addEventListener('click', () => {
  loadAuditHistory();
  loadStats();
});

// Form Submission Handler
form.addEventListener('submit', (e) => {
  e.preventDefault();
  submitForm();
});

async function submitForm() {
  const payload = collectPayload();
  setBusy(true);

  try {
    const res = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || 'Prediction failed');
    }

    const data = await res.json();
    renderAssessment(data);
    loadAuditHistory();
    loadStats();
  } catch (err) {
    alert(err.message || 'Error computing risk score');
  } finally {
    setBusy(false);
  }
}

// Collect form payload matching OrderRecord schema
function collectPayload() {
  const formData = new FormData(form);
  const data = Object.fromEntries(formData.entries());

  for (const f of NUMERIC_FIELDS) {
    data[f] = Number(data[f]) || 0;
  }

  data.delivery_note = data.delivery_note ? data.delivery_note.trim() : null;
  // Strictly enforce dispatch guardrail (exclude post-return fields)
  data.last_service_event_type = null;
  data.pickup_scheduled_at = null;

  return data;
}

function setBusy(isBusy) {
  submitBtn.disabled = isBusy;
  submitLabel.textContent = isBusy ? 'Analyzing Factors…' : 'Compute Return Risk';
}

// Render Assessment Results with Liquidmorphic Animations
function renderAssessment(data) {
  standbyView.classList.add('hidden');
  activeAssessmentView.classList.remove('hidden');

  const scorePct = data.score * 100;
  const band = (data.risk_band || 'LOW').toLowerCase();

  resOrderId.textContent = data.order_id || 'ORDER';

  // Badge pill
  riskPillBadge.className = `risk-pill-badge ${band}`;
  riskPillText.textContent = `${band.toUpperCase()} RISK`;

  // Animate Gauge Number
  animateCounter(resScoreValue, scorePct);

  // Animate SVG circular progress
  // Dashoffset: 0 = full 100%, 427 = 0%
  const offset = CIRCLE_CIRCUMFERENCE - (CIRCLE_CIRCUMFERENCE * Math.min(scorePct, 100) / 100);
  gaugeFillTrack.style.strokeDashoffset = offset;
  gaugeFillTrack.className = `gauge-fill-track ${band}`;

  // Animate Fluid Height inside Orb (min 15%, max 90%)
  const fluidHeight = Math.max(16, Math.min(scorePct * 1.5, 92));
  liquidWaveFluid.style.height = `${fluidHeight}%`;
  liquidWaveFluid.className = `liquid-wave-fluid ${band}`;

  // Move scale marker pin
  scaleMarkerPin.style.left = `${Math.min(98, Math.max(2, scorePct))}%`;

  // Recommendation Box
  actionRecBox.className = `action-recommendation-box ${band}`;
  resActionText.textContent = (data.recommended_action || '').replace(/_/g, ' ');

  if (band === 'low') {
    actionIcon.textContent = '✓';
    resActionStrategy.textContent = 'Standard dispatch. Estimated return probability is safely below the ₹45 confirmation call break-even threshold.';
  } else if (band === 'medium') {
    actionIcon.textContent = '☎';
    resActionStrategy.textContent = 'Trigger pre-dispatch confirmation call. Predicted return risk justifies the ₹45 verification call to prevent ~35% returns.';
  } else {
    actionIcon.textContent = '⚠';
    resActionStrategy.textContent = 'Manual supervisor hold & address verification required. Substantial risk factors detected across customer history or channel.';
  }

  // Render Reasons
  renderReasons(data.reasons || []);
}

// Counter animation
function animateCounter(elem, target) {
  const duration = 650;
  const startTime = performance.now();
  const startVal = parseFloat(elem.textContent) || 0;

  function update(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    // Cubic ease out
    const easeOut = 1 - Math.pow(1 - progress, 3);
    const current = startVal + (target - startVal) * easeOut;
    elem.textContent = current.toFixed(1);

    if (progress < 1) {
      requestAnimationFrame(update);
    } else {
      elem.textContent = target.toFixed(1);
    }
  }

  requestAnimationFrame(update);
}

// Render Reason Cards
function renderReasons(reasons) {
  reasonsContainer.innerHTML = '';
  reasons.forEach((reasonText, idx) => {
    const isRaised = reasonText.toLowerCase().includes('raised');
    const indicatorClass = isRaised ? 'raised' : 'reduced';
    const indicatorIcon = isRaised ? '▲' : '▼';

    const card = document.createElement('div');
    card.className = 'reason-card';
    card.style.animationDelay = `${idx * 60}ms`;

    card.innerHTML = `
      <div class="reason-indicator ${indicatorClass}">${indicatorIcon}</div>
      <div class="reason-body">${escapeHtml(reasonText)}</div>
    `;
    reasonsContainer.appendChild(card);
  });
}

// Load Audit History from SQLite
async function loadAuditHistory() {
  try {
    const res = await fetch('/api/history?limit=6');
    if (!res.ok) return;
    const history = await res.json();

    if (!history.length) {
      auditTableBody.innerHTML = '<tr><td colspan="4" class="audit-empty">No dispatches logged yet.</td></tr>';
      return;
    }

    auditTableBody.innerHTML = history.map(item => {
      const band = (item.risk_band || 'LOW').toLowerCase();
      const scorePct = (item.score * 100).toFixed(1);
      const actionName = (item.recommended_action || '').replace(/_/g, ' ');

      return `
        <tr onclick="loadHistoryItem('${escapeHtml(item.order_id)}')">
          <td><strong>${escapeHtml(item.order_id)}</strong></td>
          <td>${scorePct}%</td>
          <td><span class="audit-pill ${band}">${band.toUpperCase()}</span></td>
          <td>${escapeHtml(actionName)}</td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.warn('Could not load history:', err);
  }
}

// Load Total Stats
async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    if (!res.ok) return;
    const stats = await res.json();
    sessionChecksCount.textContent = `${stats.total_checks} Logs in SQLite`;
  } catch (err) {
    console.warn('Could not load stats:', err);
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
