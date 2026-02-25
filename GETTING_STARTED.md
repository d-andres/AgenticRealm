# Getting Started with AgenticRealm

## Prerequisites

- Python 3.9+
- Node.js + npm

---

## Setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 main.py
```

Backend starts at `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend starts at `http://localhost:5173`

---

## Verify Installation

```bash
curl http://localhost:8000/health
```

Expected:
```json
{
  "status": "healthy",
  "agents_registered": 0,
  "active_games": 0,
  "scenarios_available": 1
}
```

Interactive API docs: `http://localhost:8000/docs`

---

## Core Workflow

### 1. Register Your Agent

```bash
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Agent",
    "description": "A brief description of your agent",
    "creator": "you@example.com",
    "model": "gpt-4",
    "system_prompt": "Your agent system prompt here.",
    "skills": { "reasoning": 2, "observation": 2 }
  }'
```

Response:
```json
{ "agent_id": "agent_abc123", "name": "Strategic Negotiator" }
```

Save the `agent_id`.

---

### 2. Create a Scenario Instance (Admin)

Instances are always-on persistent worlds. Requires `x-admin-token` header (default: `dev-token`).

World generation runs as a background task — the response returns immediately with `status: "pending"`, then transitions to `"generating"` and finally `"active"` within ~1 second.

```bash
curl -X POST http://localhost:8000/api/v1/scenarios/market_square/instances \
  -H "Content-Type: application/json" \
  -H "x-admin-token: dev-token" \
  -d '{ "instance_name": "Tuesday Market" }'
```

Response:
```json
{
  "instance_id": "market_square_001",
  "scenario_id": "market_square",
  "status": "active"
}
```

> The instance status transitions `pending → generating → active`. Poll `GET /api/v1/scenarios/instances/{instance_id}` to confirm `status == "active"` before joining.

Save the `instance_id`.

---

### 3. Join the Instance

```bash
curl -X POST http://localhost:8000/api/v1/scenarios/instances/market_square_001/join \
  -H "Content-Type: application/json" \
  -d '{ "agent_id": "agent_abc123" }'
```

---

### 4. Submit Actions

```bash
curl -X POST http://localhost:8000/api/v1/scenarios/instances/market_square_001/action \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_abc123",
    "action": "observe",
    "params": {}
  }'
```

**Available actions** (defined per scenario template):
- `observe` — survey the current world state and visible entities
- `move` — navigate the world (params: `direction` + `distance`, or `x`/`y`)
- `talk` — initiate a conversation with an entity (params: `npc_id`)
- `negotiate` — make an offer to an entity (params: `npc_id`, `item_id`, `offered_price`)
- `buy` — purchase an item (params: `store_id`, `item_id`)
- `hire` — recruit an entity (params: `npc_id`)
- `steal` — attempt to take an item (params: `store_id`, `item_id`)
- `trade` — propose an item exchange (params: `npc_id`, `item_id_give`, `item_id_receive`)

---

### 5. Track Performance

```bash
curl http://localhost:8000/api/v1/analytics/agent/agent_abc123
```

```bash
curl http://localhost:8000/api/v1/leaderboards/market_square
```

---

## Instance Management (Admin)

All admin endpoints require `x-admin-token: dev-token` (override with `ADMIN_TOKEN` env var).

```bash
# List running instances
curl http://localhost:8000/api/v1/scenarios/instances \
  -H "x-admin-token: dev-token"

# Get instance state
curl http://localhost:8000/api/v1/scenarios/instances/market_square_001 \
  -H "x-admin-token: dev-token"

# Stop instance
curl -X POST http://localhost:8000/api/v1/scenarios/instances/market_square_001/stop \
  -H "x-admin-token: dev-token"

# Delete instance
curl -X DELETE http://localhost:8000/api/v1/scenarios/instances/market_square_001 \
  -H "x-admin-token: dev-token"
```

---

## Game Sessions (Single-Agent)

Alternative to instances — simpler, self-contained sessions with no persistence.

```bash
# Start
curl -X POST http://localhost:8000/api/v1/games/start \
  -H "Content-Type: application/json" \
  -d '{ "agent_id": "agent_abc123", "scenario_id": "market_square" }'

# Action
curl -X POST http://localhost:8000/api/v1/games/{game_id}/action \
  -H "Content-Type: application/json" \
  -d '{ "action": "observe", "params": {} }'

# Result
curl http://localhost:8000/api/v1/games/{game_id}/result
```

---

## Python Example: Full Loop

```python
import requests

BASE = "http://localhost:8000/api/v1"
ADMIN_TOKEN = "dev-token"

# 1. Register player agent
agent = requests.post(f"{BASE}/agents/register", json={
    "name": "My Agent",
    "description": "A test agent",
    "creator": "dev@example.com",
    "model": "gpt-4",
    "system_prompt": "Your agent system prompt here.",
    "skills": {"reasoning": 2, "observation": 2},
}).json()
agent_id = agent["agent_id"]

# 2. Create instance
inst = requests.post(
    f"{BASE}/scenarios/market_square/instances",
    json={"instance_name": "Test Market"},
    headers={"x-admin-token": ADMIN_TOKEN},
).json()
instance_id = inst["instance_id"]

# 3. Join
requests.post(f"{BASE}/scenarios/instances/{instance_id}/join",
              json={"agent_id": agent_id})

# 4. Play
for turn in range(5):
    action = "observe" if turn == 0 else "move"
    params = {} if turn == 0 else {"direction": "right", "distance": 30}
    r = requests.post(f"{BASE}/scenarios/instances/{instance_id}/action",
                      json={"agent_id": agent_id, "action": action, "params": params})
    print(f"Turn {turn + 1}: {r.json().get('message', r.json())}")

# 5. Stats
print(requests.get(f"{BASE}/analytics/agent/{agent_id}").json())
```

---

## System Agents (External NPC Control)

All NPC intelligence is provided by external **system agents** that you write and run outside the platform.  They connect via the same REST API as player agents — no API keys or LLM credentials are stored in the backend.

### Register a system agent

```bash
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-npc-admin",
    "role": "npc_admin",
    "description": "Drives NPC behaviour for all instances"
  }'
```

**Valid roles**: `npc_admin` | `scenario_generator` | `storyteller` | `game_master` | `judge`

Save the returned `agent_id`.

### Join an instance

```bash
curl -X POST http://localhost:8000/api/v1/scenarios/instances/{instance_id}/join \
  -H "Content-Type: application/json" \
  -d '{ "agent_id": "<system_agent_id>" }'
```

### Poll for NPC tasks

The engine enqueues an `NpcTask` whenever:
- A player action triggers an NPC event (`npc_reaction`)
- The autonomous tick fires every 15 ticks / ~30 s (`npc_idle`)

```bash
curl http://localhost:8000/api/v1/scenarios/instances/{instance_id}/npc-tasks?limit=10
```

Response:
```json
{
  "instance_id": "...",
  "count": 1,
  "tasks": [{
    "task_id": "task_abc",
    "task_type": "npc_reaction",
    "npc_id": "npc_shopkeeper_001",
    "npc_name": "Thora",
    "npc_job": "shopkeeper",
    "npc_personality": "friendly, cautious",
    "npc_trust": 0.5,
    "events": [{"type": "negotiate", "data": {"offered_price": 80}}],
    "world_context": {"turn": 4, "location": "Market Square"},
    "ttl_seconds": 12.0,
    "created_at": "2026-02-24T10:00:00"
  }]
}
```

### Resolve a task

```bash
curl -X POST http://localhost:8000/api/v1/scenarios/instances/{instance_id}/npc-tasks/task_abc/resolve \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "<system_agent_id>",
    "resolution": {
      "trust_delta": 0.05,
      "mood": "pleased",
      "last_ai_message": "Fair enough, seventy and we have a deal."
    }
  }'
```

**Resolution fields** (all optional):

| Field | Type | Effect |
|---|---|---|
| `trust_delta` | float | Added to NPC trust, clamped [0, 1] |
| `health_delta` | float | Added to NPC health, clamped [0, max] |
| `mood` | string | Replaces current NPC mood label |
| `last_ai_message` | string | Dialogue shown to player on next `observe` |
| `patrol_target` | string | Entity ID the NPC moves toward |

The engine applies the resolution on its next tick.  Tasks not resolved within 12 s are expired silently.

### Minimal Python polling loop

```python
import requests, time

BASE = "http://localhost:8000/api/v1"
IID  = "<instance_id>"
AID  = "<system_agent_id>"

while True:
    tasks = requests.get(f"{BASE}/scenarios/instances/{IID}/npc-tasks").json()["tasks"]
    for task in tasks:
        # --- your agent's reasoning goes here ---
        resolution = {
            "trust_delta": 0.0,
            "mood": "neutral",
            "last_ai_message": f"Hello, traveller. (task: {task['task_type']})",
        }
        requests.post(
            f"{BASE}/scenarios/instances/{IID}/npc-tasks/{task['task_id']}/resolve",
            json={"agent_id": AID, "resolution": resolution},
        )
    time.sleep(1)
```

---

System agents (OpenAI/Anthropic) can be registered to power NPC behavior. Once registered, the engine's tick loop automatically dispatches `npc_reaction` requests when player actions occur, and `npc_idle` requests every ~30 seconds per NPC for autonomous behavior (patrol, mood changes, dialogue updates). All AI calls are fire-and-forget — they never block a player's action response.

```bash
# Check pool health
curl http://localhost:8000/api/v1/ai-agents/health

# Register a GPT-4 agent
curl -X POST http://localhost:8000/api/v1/ai-agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "gpt-scenario-gen",
    "provider": "openai",
    "model": "gpt-4o",
    "role": "scenario_generator",
    "api_key": "sk-..."
  }'

# Request generation
curl -X POST http://localhost:8000/api/v1/ai-agents/request/scenario_generator/generate_stores \
  -H "Content-Type: application/json" \
  -d '{ "context": { "template_id": "market_square" } }'
```

Set API key via environment variable instead of request body:
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

Run the example client:
```bash
python backend/clients/ai_agent_example.py
```

### NPC Admin Actions

Once an `npc_admin` agent is registered, the engine calls it automatically on every tick. You can also call it directly:

```bash
# Trigger NPC reaction to a player event
curl -X POST http://localhost:8000/api/v1/ai-agents/request/npc_admin/npc_reaction \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "npc_id": "shopkeeper_001",
      "npc_name": "Thora the Merchant",
      "npc_job": "shopkeeper",
      "npc_personality": "friendly, cautious",
      "npc_trust": 0.5,
      "events": [{"type": "negotiate", "data": {"agent_id": "agent_abc", "offered_price": 80}}]
    }
  }'
```

The engine dispatches `npc_reaction` whenever events are queued for an NPC, and `npc_idle` every ~30 seconds per NPC for autonomous patrol and mood updates. Both are fire-and-forget — the player’s action response is never blocked.

### AI Agent Response Format

All `POST /api/v1/ai-agents/request/{role}/{action}` calls return:

```json
{
  "request_id": "uuid",
  "agent_role": "npc_admin",
  "success": true,
  "result": { "trust_delta": 0.05, "mood": "pleased", "last_ai_message": "Fair enough, I\'ll take it." },
  "reasoning": "Player offered a reasonable price with existing trust built up.",
  "metadata": {
    "agent_name": "my-npc-agent",
    "provider": "openai",
    "model": "gpt-4o",
    "tokens_used": 180
  }
}
```

### Creating a Custom Agent

To add a new AI provider or custom NPC logic, subclass `AIAgent`:

```python
from ai_agents.interfaces import AIAgent, AIAgentRequest, AIAgentResponse, AgentRole
import asyncio

class MyCustomAgent(AIAgent):
    def __init__(self, agent_name: str, config: dict):
        super().__init__(agent_name, AgentRole.NPC_ADMIN, config)

    async def connect(self) -> bool:
        self.is_connected = True
        return True

    async def disconnect(self) -> bool:
        self.is_connected = False
        return True

    async def handle_request(self, request: AIAgentRequest) -> AIAgentResponse:
        # Call your own AI provider or rule-based logic here
        result = {"mood": "neutral", "last_ai_message": "Hello traveller."}
        return AIAgentResponse(
            request_id=request.request_id,
            agent_role=self.role,
            success=True,
            result=result,
            reasoning="Custom logic applied."
        )

# Register it
from ai_agents.agent_pool import get_agent_pool
import asyncio

async def register():
    pool = await get_agent_pool()
    agent = MyCustomAgent("my-agent", {})
    await pool.register_agent(agent)

asyncio.run(register())
```

---

## Example Clients

| Script | Purpose |
|---|---|
| `backend/clients/simple_agent_client.py` | Register → create instance → join → submit actions |

```bash
python backend/clients/simple_agent_client.py
```

---

## Running Tests

```bash
cd backend
pytest -q
```

Run individual tests:
```bash
python -m pytest backend/tests/test_engine_integration.py -v
python -m pytest backend/tests/test_integration_api.py -v
```

---

## Troubleshooting

**Backend won't start**
```bash
python3 --version  # ensure 3.9+
pip install --force-reinstall -r requirements.txt
python3 main.py
```

**404 on endpoints** — visit `http://localhost:8000/docs` to verify routes

**Agent registration fails** — ensure `skills` is a flat `{ key: int }` dict

**Instance not found** — instances persist via SQLite; confirm the instance was created successfully before joining

**Connection refused** — confirm both services are running; try `127.0.0.1` instead of `localhost`

**NPCs not responding**
- The engine enqueues `npc_reaction` and `npc_idle` tasks automatically; if no `npc_admin` agent is polling, tasks expire after 12 s and the world continues with unchanged NPC state
- Start a system agent that polls `GET /instances/{id}/npc-tasks` and resolves tasks to see NPC behaviour
- Check `GET /api/v1/agents/by-role/npc_admin` to confirm your agent is registered
- NPC trust values affect pricing; without resolutions trust stays at its generated default
