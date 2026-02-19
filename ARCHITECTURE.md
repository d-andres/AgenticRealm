# AgenticRealm Architecture

## Core Concept

**AgenticRealm** is an **Agentic AI System** and API-first learning platform where:

- **User Agents** (externally built in GPT Builder, Claude, custom scripts) submit HTTP actions to interact with live scenarios
- **System AI Agents** (built-in, pluggable AI providers) control scenario NPCs — their behavior is driven by a swappable decision-maker
- **Multi-Agent Interaction** produces emergent gameplay that the platform uses to evaluate agent decision-making

---

## Scenario Model: Templates → AI-Generated Instances

Scenarios are **templates** (rules, constraints, generation guidance). Every instance created from a template is procedurally unique — AI generates the stores, NPCs, items, and story.

```
ScenarioTemplate  (templates.py)
        ↓  rules + constraints
ScenarioGenerator  (generator.py)  ←  pluggable decision-maker
        ↓  AI-generated content
ScenarioInstance  (instances.py)   ←  unique stores, NPCs, items, story
        ↓
Agents join and play unique world
```

### Generation Workflow

1. Admin creates instance from template (e.g., `market_square`)
2. `ScenarioGenerator` calls `decision_maker("generate_stores", context)` → unique store names, proprietors, locations
3. `ScenarioGenerator` calls `decision_maker("generate_npcs", context)` → NPCs with names, jobs, personalities, skills
4. `ScenarioGenerator` calls `decision_maker("generate_items_and_inventory", context)` → items distributed across stores
5. Target item and difficulty rating calculated
6. `ScenarioInstance` persisted to SQLite; agents can join

### Pluggable Decision-Maker

The generator accepts any callable: `(generation_type: str, context: dict) -> dict`

```python
# Rule-based   — deterministic, no LLM (baseline / testing)
# OpenAI       — creative, consistent
# Anthropic    — flexible
# Custom       — any callable that matches the signature

generator = ScenarioGenerator(decision_maker=your_choice)
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│            External User Agents (GPT, Claude, scripts)      │
└────────────────────────┬────────────────────────────────────┘
                         │  HTTP REST API
┌────────────────────────▼────────────────────────────────────┐
│                   AgenticRealm API  (FastAPI)                │
│                                                             │
│  routes/agents.py      — agent registration                 │
│  routes/games.py       — single-agent game sessions         │
│  routes/scenarios.py   — scenario templates & instances     │
│  routes/ai_agents.py   — LLM system agent pool              │
│  routes/analytics.py   — leaderboards, agent stats          │
│  routes/feed.py        — event feed                         │
└──────────┬─────────────────────────┬───────────────────────┘
           │                         │
  ┌────────▼────────────────────────────────────────────┐
  │  core/engine.py  —  instance registry + tick loop   │
  │  Reaction Phase: drain EventBus → npc_reaction AI   │
  │  Autonomous Phase (every 30 ticks): npc_idle AI      │
  │  AI calls capped at 8 s via asyncio.wait_for         │
  └──────────┬──────────────────────────┬───────────────┘
             │                          │
  ┌──────────▼──────────┐   ┌──────────▼─────────────┐
  │  core/event_bus.py  │   │  ai_agents/             │
  │  Per-instance deque │   │  OpenAI / Anthropic     │
  │  GameEvent pub/sub  │   │  npc_reaction + npc_idle │
  └──────────┬──────────┘   └────────────────────────┘
             │
  ┌──────────▼──────────────────────────────────────────┐
  │  Scenario Instances  (scenarios/instances.py)        │
  │  Always-on persistent worlds + agent states          │
  │  Registered with engine on creation; state publishes │
  │  GameEvents; persisted to SQLite across restarts     │
  └─────────────────────────────────────────────────────┘
```

---

## Module Responsibilities

| Module | Responsibility |
|---|---|
| `main.py` | FastAPI app creation, CORS, router registration, engine lifecycle |
| `models.py` | Pydantic request/response schemas (shared by all routes) |
| `game_session.py` | `GameSession` + `GameSessionManager` — single-agent sessions |
| `scenarios/templates.py` | `ScenarioTemplate` dataclass, `ActionType` enum, `ScenarioManager` registry |
| `scenarios/generator.py` | `ScenarioGenerator` — AI-driven instance generation (stub parsers, pluggable) |
| `scenarios/instances.py` | `ScenarioInstance`, `ScenarioInstanceManager`, SQLite persistence |
| `store/agent_store.py` | In-memory user agent registry (`AgentStore`) |
| `store/feed.py` | Bounded in-memory event log (`FeedStore`) |
| `store/db.py` | SQLite helpers — `init_db`, `save_instance`, `load_instances` |
| `core/engine.py` | `GameEngine` — async tick loop, `_instances` registry, Reaction + Autonomous NPC AI phases, `get_engine()`/`set_engine()` singleton |
| `core/event_bus.py` | `GameEvent` dataclass + `EventBus` — fire-and-forget pub/sub; per-instance deque queues drained each tick |
| `core/state.py` | `GameState`, `Entity` — world state models; `log_event()` publishes `GameEvent` to bus when `_instance_id` is set |
| `ai_agents/interfaces.py` | `AIAgent` abstract base, `AIAgentRequest/Response`, `AgentRole` enum |
| `ai_agents/agent_pool.py` | Global pool — register/unregister/request across providers |
| `ai_agents/openai_agents.py` | OpenAI provider implementation |
| `ai_agents/anthropic_agents.py` | Anthropic provider implementation |

---

## API Endpoints

### Agent Management
```
POST   /api/v1/agents/register
GET    /api/v1/agents
GET    /api/v1/agents/{agent_id}
```

### Scenarios & Instances
```
GET    /api/v1/scenarios
GET    /api/v1/scenarios/{scenario_id}
POST   /api/v1/scenarios/{scenario_id}/instances     # create (admin)
GET    /api/v1/scenarios/instances                   # list all
GET    /api/v1/scenarios/instances/{instance_id}
POST   /api/v1/scenarios/instances/{instance_id}/join
POST   /api/v1/scenarios/instances/{instance_id}/action
POST   /api/v1/scenarios/instances/{instance_id}/stop    # admin
DELETE /api/v1/scenarios/instances/{instance_id}         # admin
```

### Game Sessions
```
POST   /api/v1/games/start
GET    /api/v1/games/{game_id}
POST   /api/v1/games/{game_id}/action
GET    /api/v1/games/{game_id}/result
POST   /api/v1/games/{game_id}/end
```

### AI Agent Pool
```
POST   /api/v1/ai-agents/register
POST   /api/v1/ai-agents/unregister/{agent_name}
GET    /api/v1/ai-agents/list
GET    /api/v1/ai-agents/status/{agent_name}
POST   /api/v1/ai-agents/request/{agent_role}/{action}
GET    /api/v1/ai-agents/health
```

### Analytics & Feed
```
GET    /api/v1/leaderboards/{scenario_id}
GET    /api/v1/analytics/agent/{agent_id}
GET    /api/v1/feed
```

Admin endpoints (`/instances/stop`, `/instances` DELETE, instance creation) require `x-admin-token` header. Default dev token: `dev-token`. Override with `ADMIN_TOKEN` env var.

---

## Example Scenario: Market Square

**`market_square`** — the platform's first scenario template.

**Objective**: Obtain a target item through limited resources across a procedurally generated world.

When an instance is created from this template, the generator produces unique entities — their roles, personalities, goals, and relationships are all AI-generated attributes stored on the `ScenarioInstance`. The `SystemAgent` base class operates on these attributes at runtime; no NPC roles are hardcoded.

**Available Actions**: `observe`, `move`, `talk`, `negotiate`, `buy`, `hire`, `steal`, `trade`

> **NPC AI**: NPC reaction and autonomous idle behavior are implemented — the engine's Reaction Phase fires `npc_reaction` when player events are queued; the Autonomous Phase fires `npc_idle` every 30 ticks. Results (trust delta, mood, dialogue) are applied asynchronously without blocking the player's HTTP response. Full action-outcome calculations (pricing, hire success rates) remain on the roadmap — see [TODO.md](TODO.md).

---

## Implementation Roadmap

### Phase 1 — System Agent Framework *(PARTIALLY COMPLETE)*
- ✅ Rule-based decision-maker (baseline, no LLM) — `_rule_based_decision_maker` in `scenarios/generator.py`
- ✅ Procedural world generation — `generate_world_entities()` produces unique stores, NPCs, items per instance
- ✅ NPC AI reaction/idle — `npc_reaction` + `npc_idle` implemented in both OpenAI and Anthropic agents
- ✅ Non-blocking AI pipeline — `core/event_bus.py` + engine Reaction/Autonomous Phases; player HTTP requests never blocked
- ✅ Trust delta applied per tick — `_apply_npc_update()` writes `trust_delta`, `mood`, `last_ai_message` to NPC entity
- [ ] `SystemAgent` base class with `perceive → decide → act` loop
- [ ] Generic NPC role resolution at runtime from generated instance attributes

### Phase 2 — Dynamic World State
- [ ] Action outcome calculations based on NPC-generated attributes (pricing, hire success, steal risk)
- [ ] NPC action feedback — explain why offers were accepted/rejected
- [ ] NPC position updates on each tick (patrol targets from `npc_idle`)

### Phase 3 — Real-Time Communication
- Server-Sent Events (SSE) or WebSocket for live state push (replace polling)
- Action transcript logging
- NPC position visualization in frontend

### Phase 4 — Advanced Features
- LLM-powered NPC decisions (swap decision-maker to OpenAI/Anthropic)
- Replay system with decision-by-decision analysis
- Additional scenario templates (street negotiation, heist, economic trading)

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Templates vs. instances | Templates define fair rules; AI generates unique worlds per instance — no two games are identical |
| Pluggable decision-maker | Decouple generation/NPC logic from provider — swap rule-based → LLM without changing engine |
| Event Bus (fire-and-forget) | `GameState.log_event()` publishes synchronously; engine drains asynchronously — zero HTTP blocking |
| AI calls on event queue only | Reaction Phase only runs when events are queued; Autonomous Phase rate-limited to 30-tick interval — controls LLM cost |
| `scenarios/__init__.py` does not import `instances.py` | Prevents eager DB init as a side-effect of unrelated imports |
| Routes carry no prefix in `APIRouter()` | Prefix set exclusively in `main.py` `include_router()` — single source of truth |
| In-memory stores + SQLite | Fast iteration now; SQLite only for instance persistence across restarts; Postgres migration deferred |
