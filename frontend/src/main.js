/**
 * AgenticRealm Frontend — App logic
 *
 * Flow:
 *   View 1 (Setup)  → register optional AI agents → generate world
 *   View 2 (Lobby)  → poll until world active → register player agent → join instance
 *   View 3 (Game)   → submit actions → poll state → render world map
 *
 * All backend communication is plain REST (fetch).  No Socket.IO required.
 */

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

// In production the frontend is served by the same FastAPI server, so relative
// paths work.  In Vite dev mode the proxy in vite.config.js forwards /api → 8000.
const API = '/api/v1';

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

let instanceId  = null;
let agentId     = null;
let gameId      = null;
let pollTimer   = null;
let gameState   = null;

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function log(selector, text, type = '') {
  const el = document.querySelector(selector);
  if (!el) return;
  const line = document.createElement('div');
  line.className = `entry ${type}`;
  line.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
  el.appendChild(line);
  el.scrollTop = el.scrollHeight;
}
const setupLog = t => log('#log',       t, arguments[1]);
const lobbyLog = t => log('#log-lobby', t, arguments[1]);

function logSetup(text, type = '')  { log('#log',       text, type); }
function logLobby(text, type = '')  { log('#log-lobby', text, type); }
function gameLog(text, type = '')   {
  const el = document.getElementById('game-log');
  if (!el) return;
  const line = document.createElement('div');
  line.className = type;
  line.textContent = text;
  el.appendChild(line);
  el.scrollTop = el.scrollHeight;
}

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
  const steps = { setup: 1, lobby: 2, game: 3 };
  const active = steps[name];
  [1, 2, 3].forEach(n => {
    const s = document.getElementById(`step-${n}`);
    s.classList.toggle('active', n === active);
    s.classList.toggle('done',   n < active);
  });
}

// ---------------------------------------------------------------------------
// API reachability check
// ---------------------------------------------------------------------------

async function checkAPI() {
  try {
    await fetch('/health');
    const dot = document.getElementById('conn-dot');
    dot.textContent = '● API connected';
    dot.className = 'ok';
  } catch {
    // stays red
  }
}

// ---------------------------------------------------------------------------
// View 1 — Setup
// ---------------------------------------------------------------------------

async function registerAIAgent() {
  const type  = document.getElementById('ai-type').value;
  const role  = document.getElementById('ai-role').value;
  const key   = document.getElementById('ai-key').value.trim();
  const model = document.getElementById('ai-model').value.trim();

  if (!key) { logSetup('API key is required to register an AI agent.', 'err'); return; }

  logSetup(`Registering ${type} ${role} agent…`, 'info');
  try {
    const data = await apiFetch('/ai-agents/register', {
      method: 'POST',
      body: JSON.stringify({
        agent_name: `${type}-${role}`,
        agent_role: role,
        agent_type: type,
        config: { api_key: key, model: model || undefined },
      }),
    });
    logSetup(`✓ ${data.message}`, 'ok');
  } catch (e) {
    logSetup(`✗ ${e.message}`, 'err');
  }
}

async function generateWorld() {
  logSetup('Generating world from scenario_001…', 'info');
  try {
    const data = await apiFetch('/scenarios/scenario_001/instances', { method: 'POST' });
    instanceId = data.instance_id;
    logSetup(`✓ World created (${instanceId.slice(0, 8)}…). Polling until active…`, 'ok');
    document.getElementById('instance-id-display').value = instanceId;
    setView('lobby');
    startPollingInstance();
  } catch (e) {
    logSetup(`✗ ${e.message}`, 'err');
  }
}

function backToSetup() {
  stopPollingInstance();
  setView('setup');
}

// ---------------------------------------------------------------------------
// View 2 — Lobby / polling
// ---------------------------------------------------------------------------

function startPollingInstance() {
  stopPollingInstance();
  pollTimer = setInterval(pollInstance, 2000);
  pollInstance();
}

function stopPollingInstance() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
}

async function pollInstance() {
  if (!instanceId) return;
  try {
    const inst = await apiFetch(`/scenarios/instances/${instanceId}`);
    const badge = document.getElementById('instance-status-badge');
    badge.textContent = inst.status;
    badge.className = `badge ${inst.status}`;

    if (inst.status === 'active') {
      stopPollingInstance();
      logLobby('✓ World is active — you can join now.', 'ok');
      const btn = document.getElementById('join-btn');
      btn.disabled = false;
      btn.textContent = 'Join Simulation';

      // Show entity count from world state
      const entityCount = Object.keys(inst.state?.entities || {}).length;
      logLobby(`World has ${entityCount} entities (stores, NPCs, items).`, 'info');
    }
  } catch (e) {
    logLobby(`Poll error: ${e.message}`, 'err');
  }
}

async function joinInstance() {
  const name    = document.getElementById('player-name').value.trim()    || 'PlayerAgent';
  const creator = document.getElementById('player-creator').value.trim() || 'player@example.com';
  const model   = document.getElementById('player-model').value.trim()   || 'gpt-4o';
  const desc    = document.getElementById('player-desc').value.trim()    || 'A strategic agent';

  try {
    logLobby('Registering player agent…', 'info');
    const reg = await apiFetch('/agents/register', {
      method: 'POST',
      body: JSON.stringify({
        name, creator, model,
        description: desc,
        system_prompt: `You are ${name}, a strategic agent navigating a market scenario.`,
        skills: { reasoning: 2, observation: 2, negotiation: 1 },
      }),
    });
    agentId = reg.agent_id;
    logLobby(`✓ Agent registered (${agentId.slice(0, 8)}…)`, 'ok');

    logLobby('Joining instance…', 'info');
    const join = await apiFetch(
      `/scenarios/instances/${instanceId}/join?agent_id=${agentId}`,
      { method: 'POST' }
    );
    gameId = join.game_id;
    logLobby(`✓ Joined! game_id=${gameId.slice(0, 8)}…`, 'ok');

    setView('game');
    gameLog(`Entered world. Turn 0. Gold: ${500}. Health: 100`, 'sys');
    startGamePolling();
    await pollState();   // immediate first state load
  } catch (e) {
    logLobby(`✗ ${e.message}`, 'err');
  }
}

// ---------------------------------------------------------------------------
// View 3 — Game
// ---------------------------------------------------------------------------

let gamePolling = null;

function startGamePolling() {
  if (gamePolling) clearInterval(gamePolling);
  gamePolling = setInterval(pollState, 3000);
}

async function pollState() {
  if (!gameId) return;
  try {
    const data = await apiFetch(`/games/${gameId}`);
    gameState = data;
    refreshGameUI(data);
  } catch (e) {
    gameLog(`Refresh error: ${e.message}`, 'err');
  }
}

function refreshGameUI(data) {
  const agent = data.entities?.[agentId];
  if (agent) {
    document.getElementById('g-turn').textContent   = data.turn ?? 0;
    document.getElementById('g-health').textContent = agent.properties?.health ?? '—';
    document.getElementById('g-gold').textContent   = agent.properties?.gold   ?? '—';
    document.getElementById('g-score').textContent  = Math.round(agent.properties?.score ?? 0);
  }

  // Render nearby entities (from last observe result or full state)
  const entities = Object.values(data.entities || {})
    .filter(e => e.id !== agentId)
    .slice(0, 20);

  const list = document.getElementById('entity-list');
  if (entities.length === 0) {
    list.innerHTML = '<div style="color:var(--muted)">No entities visible — use Observe.</div>';
  } else {
    list.innerHTML = entities.map(e => {
      const name = e.properties?.name || e.id.replace(/_/g, ' ');
      const job  = e.properties?.job  ? ` · ${e.properties.job}` : '';
      return `<div class="entity-row">
        <span class="etype">${e.type}</span>
        <span class="ename">${name}${job}</span>
        <span class="edist">${e.id}</span>
      </div>`;
    }).join('');
  }

  renderMap(data);
}

function renderMap(data) {
  const canvas = document.getElementById('world-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.offsetWidth  || 600;
  const H = canvas.offsetHeight || 380;
  canvas.width  = W;
  canvas.height = H;

  const worldW = data.world_properties?.world_width  || 800;
  const worldH = data.world_properties?.world_height || 600;
  const scaleX = W / worldW;
  const scaleY = H / worldH;

  ctx.fillStyle = '#020208';
  ctx.fillRect(0, 0, W, H);

  const colorMap = {
    agent:   '#00ff00',
    npc:     '#ffcc00',
    store:   '#4499ff',
    item:    '#ff88ff',
    hazard:  '#ff4444',
    exit:    '#ffffff',
  };

  Object.values(data.entities || {}).forEach(e => {
    const x = e.x * scaleX;
    const y = e.y * scaleY;
    const r = e.id === agentId ? 6 : 4;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fillStyle = colorMap[e.type] || '#888';
    ctx.fill();
    if (e.id === agentId) {
      ctx.strokeStyle = '#00ff00';
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }
  });
}

async function quickAction(action, params = {}) {
  await submitAction(action, params);
}

async function submitCustomAction() {
  const action = document.getElementById('custom-action').value;
  const target = document.getElementById('custom-target').value.trim();
  let extra = {};
  try {
    const raw = document.getElementById('custom-params').value.trim();
    if (raw) extra = JSON.parse(raw);
  } catch { gameLog('Invalid JSON in extra params.', 'err'); return; }

  const params = { ...extra };
  if (target) {
    // auto-assign target to the right param key based on action
    if (['buy', 'steal', 'negotiate'].includes(action)) params.store_id = target;
    else params.npc_id = target;
  }
  await submitAction(action, params);
  hideCustomAction();
}

async function submitAction(action, params) {
  if (!gameId) return;
  try {
    const res = await apiFetch(`/games/${gameId}/action`, {
      method: 'POST',
      body: JSON.stringify({ action, params }),
    });
    const icon = res.success ? '✓' : '✗';
    gameLog(`${icon} [${action}] ${res.message}`, res.success ? 'ok' : 'err');
    await pollState();
  } catch (e) {
    gameLog(`✗ ${e.message}`, 'err');
  }
}

function showCustomAction() {
  document.getElementById('action-params').style.display = 'block';
}

function hideCustomAction() {
  document.getElementById('action-params').style.display = 'none';
}

async function endGame() {
  if (!gameId) return;
  try {
    await apiFetch(`/games/${gameId}/end`, { method: 'POST' });
    const result = await apiFetch(`/games/${gameId}/result`);
    gameLog(`── Game Over ── success=${result.success}  score=${Math.round(result.score)}  turns=${result.turns_taken}`, 'sys');
    gameLog(result.feedback, 'sys');
  } catch (e) {
    gameLog(`Error ending game: ${e.message}`, 'err');
  }
  if (gamePolling) { clearInterval(gamePolling); gamePolling = null; }
}

// ---------------------------------------------------------------------------
// Expose to HTML onclick handlers
// ---------------------------------------------------------------------------

window.App = {
  registerAIAgent,
  generateWorld,
  backToSetup,
  joinInstance,
  pollState,
  quickAction,
  showCustomAction,
  hideCustomAction,
  submitCustomAction,
  endGame,
};

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

checkAPI();
