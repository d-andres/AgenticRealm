/**
 * AgenticRealm Frontend — Simulation Host
 *
 * Flow:
 *   View 1 (Setup)      → external system agents connect via REST → generate world
 *   View 2 (Simulation) → host screen:
 *                          world map canvas | join key + player list + activity log
 *
 * There are no player controls here.  Players join from their own devices via
 * their own AI agents using the join key displayed on the simulation screen.
 */

const API = '/api/v1';

// ── State ──────────────────────────────────────────────────────────
let instanceId       = null;
let genPollTimer     = null;
let simTimer         = null;
let agentPollTimer   = null;   // auto-refresh agent list on setup screen
let _shownEvents = 0;   // tracks how many events we have already displayed
let _scenarios   = [];  // cached scenario list from API
let _selectedScenario = null;  // currently selected ScenarioResponse object

// ── Utilities ──────────────────────────────────────────────────────

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

function setView(name) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.getElementById(`view-${name}`).classList.add('active');
}

function logSetup(text, type = '') {
  const el = document.getElementById('setup-log');
  if (!el) return;
  const line = document.createElement('div');
  line.className = `entry ${type}`;
  line.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
  el.appendChild(line);
  el.scrollTop = el.scrollHeight;
}

// ── API status ─────────────────────────────────────────────────────

async function checkAPI() {
  try {
    const r = await fetch('/health');
    if (r.ok) {
      ['conn-dot', 'sim-conn-dot'].forEach(id => {
        const el = document.getElementById(id);
        if (el) { el.textContent = '● online'; el.className = 'ok'; }
      });
    }
  } catch { /* stays red */ }
}

function refreshBaseUrl() {
  const el = document.getElementById('setup-base-url');
  if (el) el.textContent = window.location.origin;
}

// ── VIEW 1 — Setup ─────────────────────────────────────────────────

async function loadScenarios() {
  const sel   = document.getElementById('scenario-select');
  const btn   = document.getElementById('gen-world-btn');
  try {
    const data = await apiFetch('/scenarios');
    _scenarios = Array.isArray(data) ? data : [];
    if (!_scenarios.length) {
      sel.innerHTML = '<option value="">No scenarios available</option>';
      return;
    }
    sel.innerHTML = _scenarios.map(s =>
      `<option value="${s.scenario_id}">${s.name}</option>`
    ).join('');
    sel.value = _scenarios[0].scenario_id;
    onScenarioChange();
    if (btn) btn.disabled = false;
  } catch (e) {
    sel.innerHTML = '<option value="">Failed to load scenarios</option>';
    logSetup(`Could not load scenarios: ${e.message}`, 'err');
  }
}

function onScenarioChange() {
  const sel  = document.getElementById('scenario-select');
  const desc = document.getElementById('scenario-desc');
  _selectedScenario = _scenarios.find(s => s.scenario_id === sel.value) || null;
  if (_selectedScenario) {
    desc.textContent = _selectedScenario.short_description || _selectedScenario.description.trim().split('\n')[0];
  } else {
    desc.textContent = '';
  }
}

async function refreshAgentList() {
  const el = document.getElementById('agent-list');
  if (!el) return;
  try {
    // Fetch system-role agents and all player agents in parallel
    const SYSTEM_ROLES = ['scenario_generator', 'npc_admin', 'storyteller', 'game_master'];
    const [byRoleResults, allAgents] = await Promise.all([
      Promise.all(SYSTEM_ROLES.map(r =>
        apiFetch(`/agents/by-role/${r}`).then(d => d.agents || []).catch(() => [])
      )),
      apiFetch('/agents').then(d => Array.isArray(d) ? d : (d.agents || [])).catch(() => []),
    ]);

    const systemAgents = byRoleResults.flat();
    const playerAgents = allAgents.filter(a => !a.is_system_agent);

    if (systemAgents.length === 0 && playerAgents.length === 0) {
      el.innerHTML = '<div class="muted">No agents connected.  Start an external agent and register it with one of these roles: <code>scenario_generator</code>, <code>npc_admin</code>, <code>storyteller</code>, <code>game_master</code>.</div>';
      return;
    }

    const rows = [...systemAgents, ...playerAgents].map(a => {
      const roleLabel = a.role || 'player';
      const dotClass  = a.is_system_agent ? 'ok' : '';
      return `<div class="agent-row">
        <span class="a-dot ${dotClass}">●</span>
        <span>${a.name || a.agent_id}</span>
        <span class="muted">${roleLabel}</span>
      </div>`;
    });

    if (systemAgents.length === 0) {
      rows.unshift('<div class="muted" style="margin-bottom:0.5rem;">No system agents yet — NPC behaviour will be minimal.</div>');
    }

    el.innerHTML = rows.join('');
  } catch {
    el.innerHTML = '<div class="muted">Could not load agents.</div>';
  }
}

async function generateWorld() {
  if (!_selectedScenario) {
    logSetup('Select a scenario first.', 'err');
    return;
  }
  const scenarioId = _selectedScenario.scenario_id;


  const tickRateInput = document.getElementById('tick-rate-input');
  const tickRate = parseFloat(tickRateInput?.value) || 2.0;
  const clampedTick = Math.min(30, Math.max(0.5, tickRate));

  logSetup(`Generating world from "${_selectedScenario.name}"… (tick: ${clampedTick}s)`, 'info');
  try {
    const d = await apiFetch(`/scenarios/${scenarioId}/instances?tick_rate=${clampedTick}`, { method: 'POST' });
    instanceId = d.instance_id;
    logSetup(`✓ Instance ${instanceId.slice(0, 8)}… created. Waiting for world to become active…`, 'ok');
    startGenPoll();
  } catch (e) {
    logSetup(`✗ ${e.message}`, 'err');
  }
}

function startGenPoll() {
  if (genPollTimer) clearInterval(genPollTimer);
  genPollTimer = setInterval(async () => {
    try {
      const inst = await apiFetch(`/scenarios/instances/${instanceId}`);
      logSetup(`World status: ${inst.status}`, 'info');
      if (inst.status === 'active') {
        clearInterval(genPollTimer);
        genPollTimer = null;
        logSetup('✓ World is active — launching simulation screen.', 'ok');
        enterSimulation();
      }
    } catch (e) {
      logSetup(`Poll error: ${e.message}`, 'err');
    }
  }, 2000);
}

// ── VIEW 2 — Simulation ────────────────────────────────────────────

function enterSimulation() {
  // Stop the setup-screen agent poller — no longer needed
  if (agentPollTimer) { clearInterval(agentPollTimer); agentPollTimer = null; }

  // Update sim header tag with the selected scenario name
  const tag = document.getElementById('sim-scenario-tag');
  if (tag && _selectedScenario) tag.textContent = _selectedScenario.name;
  updateJoinInfo();
  setView('simulation');
  startSimPolling();
  pollSim();  // immediate first render
}

function updateJoinInfo() {
  const code = instanceId.slice(0, 8).toUpperCase();
  document.getElementById('join-code').textContent = code;
  const base = window.location.origin;
  document.getElementById('join-instance-url').textContent =
    `POST ${base}/api/v1/scenarios/instances/${instanceId}/join?agent_id=YOUR_AGENT_ID`;
}

function copyJoinKey() {
  if (!instanceId) return;
  navigator.clipboard.writeText(instanceId).then(() => {
    const btn = document.querySelector('#sim-right .btn');
    if (btn) {
      btn.textContent = '✓ Copied!';
      setTimeout(() => { btn.textContent = 'Copy Full ID'; }, 1600);
    }
  });
}

function startSimPolling() {
  if (simTimer) clearInterval(simTimer);
  simTimer = setInterval(pollSim, 3000);
}

async function pollSim() {
  if (!instanceId) return;
  try {
    const [instData, eventsData, playersData] = await Promise.all([
      apiFetch(`/scenarios/instances/${instanceId}`),
      apiFetch(`/scenarios/instances/${instanceId}/events?limit=120`),
      apiFetch(`/scenarios/instances/${instanceId}/players`),
    ]);

    // Header badges
    const badge = document.getElementById('sim-status-badge');
    badge.textContent = instData.status;
    badge.className = `badge ${instData.status}`;

    const entities = Object.values(instData.state?.entities || {});
    const npcs   = entities.filter(e => e.type === 'npc').length;
    const stores = entities.filter(e => e.type === 'store').length;
    document.getElementById('sim-entity-count').textContent =
      `${npcs} NPCs · ${stores} stores · ${entities.length} entities`;

    // World tick counter from engine turn (exposed via state properties)
    const worldTurn = instData.state?.turn ?? instData.state?.properties?.turn ?? '—';
    document.getElementById('sim-tick').textContent = `world tick ${worldTurn}`;

    renderMap(instData.state);
    appendNewEvents(eventsData.events || []);
    renderPlayers(playersData.players || []);
  } catch (e) {
    console.warn('[pollSim]', e.message);
  }
}

// ── Map rendering ──────────────────────────────────────────────────

function renderMap(state) {
  const canvas = document.getElementById('world-canvas');
  if (!canvas) return;
  const ctx  = canvas.getContext('2d');
  const W    = canvas.clientWidth  || 800;
  const H    = canvas.clientHeight || 500;
  canvas.width  = W;
  canvas.height = H;

  const worldW = state?.properties?.world_width  || 800;
  const worldH = state?.properties?.world_height || 600;
  const sx = W / worldW;
  const sy = H / worldH;

  // Background + subtle grid
  ctx.fillStyle = '#020208';
  ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = '#08080f';
  ctx.lineWidth = 1;
  for (let gx = 0; gx <= W; gx += W / 10) {
    ctx.beginPath(); ctx.moveTo(gx, 0); ctx.lineTo(gx, H); ctx.stroke();
  }
  for (let gy = 0; gy <= H; gy += H / 8) {
    ctx.beginPath(); ctx.moveTo(0, gy); ctx.lineTo(W, gy); ctx.stroke();
  }

  const COLOR = {
    agent:  '#00ff00',
    npc:    '#ffcc00',
    store:  '#4499ff',
    item:   '#ff88ff',
    hazard: '#ff4444',
    exit:   '#eeeeee',
  };

  const entities = Object.values(state?.entities || {});

  // Draw stores as areas (behind everything else)
  entities.filter(e => e.type === 'store').forEach(e => {
    const x = e.x * sx, y = e.y * sy;
    const areaW = 36 * sx, areaH = 28 * sy;
    // Semi-transparent fill
    ctx.fillStyle = 'rgba(68, 153, 255, 0.12)';
    ctx.fillRect(x - areaW / 2, y - areaH / 2, areaW, areaH);
    // Border
    ctx.strokeStyle = '#4499ff';
    ctx.lineWidth = 1.5;
    ctx.strokeRect(x - areaW / 2, y - areaH / 2, areaW, areaH);
    // Name label centered
    const name = e.properties?.name || '';
    if (name) {
      ctx.fillStyle = '#7ab8ff';
      ctx.font = '9px monospace';
      ctx.textAlign = 'center';
      ctx.fillText(name, x, y + 4);
      ctx.textAlign = 'left';
    }
  });

  // Draw items (small, behind NPCs)
  entities.filter(e => e.type === 'item').forEach(e => {
    const x = e.x * sx, y = e.y * sy;
    ctx.fillStyle = COLOR.item;
    ctx.beginPath(); ctx.arc(x, y, 2, 0, Math.PI * 2); ctx.fill();
  });

  // Draw NPCs
  entities.filter(e => e.type === 'npc').forEach(e => {
    const x = e.x * sx, y = e.y * sy;
    const status = e.properties?.status;
    ctx.fillStyle = status === 'incapacitated' ? '#555' : COLOR.npc;
    ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2); ctx.fill();
    const name = e.properties?.name?.split(' ')[0] || '';
    if (name) {
      ctx.fillStyle = status === 'incapacitated' ? '#444' : '#887700';
      ctx.font = '8px monospace';
      ctx.fillText(name, x + 6, y + 3);
    }
  });

  // Draw player agents on top (largest, glowing)
  entities.filter(e => e.type === 'agent').forEach(e => {
    const x = e.x * sx, y = e.y * sy;
    // Glow
    ctx.shadowColor = '#00ff00';
    ctx.shadowBlur  = 8;
    ctx.fillStyle = COLOR.agent;
    ctx.beginPath(); ctx.arc(x, y, 6, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = '#00aa00';
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.shadowBlur = 0;
    ctx.fillStyle = '#00cc00';
    ctx.font = 'bold 9px monospace';
    ctx.fillText('Player', x + 9, y + 4);
  });
}

// ── Activity log ───────────────────────────────────────────────────

const EV_ICON = {
  talk:           '💬',
  buy:            '💰',
  steal_attempt:  '🃏',
  hire:           '🤝',
  negotiate:      '📊',
  trade_proposal: '⇄',
  hazard_hit:     '⚡',
  exit_reached:   '🚪',
  entity_added:   '＋',
  entity_updated: '~',
};

function _short(id) {
  return id ? id.slice(0, 8) : '?';
}

function formatEvent(ev) {
  const d    = ev.data || {};
  const icon = EV_ICON[ev.type] || '·';
  const ag   = _short(d.agent_id);

  switch (ev.type) {
    case 'talk':
      return `${icon} ${ag} → ${d.npc_id}: "${d.message || '…'}"`;
    case 'buy':
      return `${icon} ${ag} bought [${d.item_id}] for ${d.price}g from ${d.store_id}`;
    case 'steal_attempt':
      return `${icon} ${ag} stole [${d.item_id}] — ${d.success ? '✓' : '✗ caught! guards: ' + d.guards_nearby}`;
    case 'hire':
      return `${icon} ${ag} hired ${d.npc_id} for ${d.cost}g`;
    case 'negotiate':
      return `${icon} ${ag} offered ${d.offered_price}g for [${d.item_id}] at ${d.npc_id}`;
    case 'trade_proposal':
      return `${icon} ${ag} [${d.give_item_id}] ⇄ [${d.receive_item_id}] — ${d.accepted ? 'accepted' : 'refused'}`;
    case 'hazard_hit':
      return `${icon} entity hit hazard — ${d.damage} dmg`;
    case 'exit_reached':
      return `${icon} exit reached! score ${Math.round(d.score || 0)}`;
    case 'entity_added':
      return `${icon} [${d.type || 'entity'}] ${d.entity_id} entered world`;
    default:
      return `${icon} [${ev.type}]`;
  }
}

function appendNewEvents(events) {
  // API returns newest-first; reverse to get chronological order
  const ordered = [...events].reverse();
  const newOnes = ordered.slice(_shownEvents);
  if (!newOnes.length) return;
  _shownEvents = ordered.length;

  const log = document.getElementById('activity-log');
  if (!log) return;

  // Clear the initial placeholder once real events arrive
  const placeholder = log.querySelector('.log-entry.sys');
  if (placeholder) placeholder.remove();

  newOnes.forEach(ev => {
    const isActionable = ['buy', 'exit_reached', 'hire', 'steal_attempt'].includes(ev.type);
    const isWarn = ev.type === 'hazard_hit';

    const line = document.createElement('div');
    line.className = `log-entry${isActionable ? ' ok' : isWarn ? ' warn' : ''}`;
    const ts = ev.timestamp
      ? new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      : '';
    line.textContent = `${ts}  ${formatEvent(ev)}`;
    // Newest on top
    log.insertBefore(line, log.firstChild);
  });
}

// ── Player list ────────────────────────────────────────────────────

function renderPlayers(players) {
  const el    = document.getElementById('player-list');
  const count = document.getElementById('player-count');
  if (!el) return;

  count.textContent = players.length;

  if (!players.length) {
    el.innerHTML = '<div class="muted">No players yet</div>';
    return;
  }

  el.innerHTML = players.map(p => {
    const dotClass = p.status === 'completed' ? 'ok'
                   : p.status === 'failed'    ? 'err'
                   : 'active-dot';
    const gold  = p.gold  != null ? `${p.gold}g`               : '';
    const score = p.score != null ? `${Math.round(p.score)}pts` : '';
    return `<div class="player-row">
      <span class="p-dot ${dotClass}">●</span>
      <span class="p-name" title="${p.agent_id}">${p.name}</span>
      <span class="p-stat">${gold}</span>
      <span class="p-stat">${score}</span>
    </div>`;
  }).join('');
}

// ── Expose ─────────────────────────────────────────────────────────

window.App = {
  generateWorld,
  copyJoinKey,
  onScenarioChange,
  refreshAgentList,
  refreshBaseUrl,
};

// ── Boot ─────────────────────────────────────────────────────

checkAPI();
refreshAgentList();
loadScenarios();
refreshBaseUrl();

// Populate registration URL once we know the origin
const _regEl = document.getElementById('setup-register-url');
if (_regEl) _regEl.textContent = `POST ${window.location.origin}/api/v1/agents/register`;

// Periodically refresh the agent list while on the setup screen so
// operators can see external agents connect without reloading the page.
agentPollTimer = setInterval(refreshAgentList, 5000);

