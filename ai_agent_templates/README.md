# AI Agent Templates

This directory contains configuration templates and prompts for **external AI agents** that connect to AgenticRealm over its REST API.

AgenticRealm is a pure game runtime — it has no embedded LLM. All intelligence is **external**. These templates describe how to prompt and structure an agent so it can register with the server, claim a role, and interact through the REST polling loop.

## Supported Platforms

These templates can be adapted for any system that makes HTTP requests:

- **Python scripts** using `requests` / `httpx`
- **LangChain / CrewAI / AutoGen** agents with tool-use
- **LLM APIs** (OpenAI, Anthropic, Gemini) inside a custom polling loop
- **Workflow tools** (n8n, Zapier, Make) with HTTP action steps
- **Any process** that can register, poll, and POST JSON

Refer to `backend/clients/` for working Python reference clients.

## How It Works

Every external agent follows the same lifecycle:

1. **Register** — `POST /agents/register` with a `name` and `role`
2. **Join an instance** — `POST /instances/{id}/join` with your `agent_id`
3. **Act** — call role-specific endpoints in a loop (see individual templates)

System agents (non-player roles) additionally:

4. **Poll for tasks** — `GET /instances/{id}/npc-tasks` every few seconds
5. **Resolve tasks** — `POST /instances/{id}/npc-tasks/{task_id}/resolve` with a decision JSON

Tasks expire after **12 seconds** if unresolved; the engine applies a rule-based fallback automatically.

## Roles

| Role string | Template | Responsibility |
|-------------|----------|----------------|
| `player` | — | Submits game actions (`buy`, `talk`, `move`, etc.) as a player character. |
| `npc_admin` | [`system_agents/npc_manager.md`](system_agents/npc_manager.md) | Polls pending NPC tasks and resolves NPC decisions (dialogue, mood, movement). |
| `scenario_generator` | [`system_agents/scenario_generator.md`](system_agents/scenario_generator.md) | Generates procedural scenario instances from templates via the API. |
| `game_master` | [`system_agents/game_master.md`](system_agents/game_master.md) | Monitors world events and injects narrative rulings or world-state notes via shared memory. |
| `storyteller` | [`system_agents/storyteller.md`](system_agents/storyteller.md) | Narrates world events by writing flavour text to the shared memory board. |

## Recommended Startup Order

For a fully-staffed world, connect agents in this order before generating a world on the host screen:

1. **Realm Architect** (`scenario_generator`) — must be connected *before* world generation so it can build the world instead of the fallback rule-based generator.
2. **NPC Warden** (`npc_admin`) — connect before or immediately after generation; NPC tasks start queuing as soon as players join.
3. **The Lorekeeper** (`storyteller`) — can join at any time; reads the event log catch-up on startup.
4. **The Arbiter** (`game_master`) — optional; useful for multi-player or long-running sessions.

Any subset works — agents not connected fall back to the backend's built-in rule-based defaults.

## Shared Memory Key Conventions

Agents communicate through the instance memory board at `GET/POST /instances/{id}/memory`. Use these key namespaces to stay organised:

| Prefix | Written by | Read by | Content |
|--------|-----------|---------|---------|
| `world:layout` | Realm Architect | NPC Warden, Lorekeeper | Generated stores, NPCs, target item |
| `world:facts` | Lorekeeper | All agents | Established in-world facts |
| `world:narrative` | Lorekeeper | Host screen, GM | Live narrative passages |
| `world:atmosphere` | Lorekeeper | All agents | Current world mood/tone |
| `world:rulings` | Arbiter | NPC Warden, Lorekeeper | GM overrides and balance corrections |
| `world:gm_status` | Arbiter | Operator | World health check notes |
| `npc:{id}:context` | NPC Warden | Lorekeeper, Arbiter | NPC current mood, trust, last resolution |
| `npc:{id}:dialogue_history` | NPC Warden | Lorekeeper | Recent NPC lines for consistency |
| `player:{id}:interactions` | NPC Warden | Lorekeeper, Arbiter | Player interaction history per NPC |

## Task TTL Reminder

NPC tasks expire after **12 seconds** if not resolved. The engine applies a rule-based fallback automatically. Design your polling loop to resolve tasks within 8–10 seconds to leave margin.

## Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/agents/register` | Register and receive an `agent_id` |
| GET  | `/agents` | List all connected agents |
| GET  | `/agents/by-role/{role}` | Filter agents by role |
| POST | `/instances/{id}/join` | Join a running scenario instance |
| POST | `/instances/{id}/action` | Submit a player action |
| GET  | `/instances/{id}/npc-tasks` | Poll pending NPC tasks (`npc_admin`) |
| POST | `/instances/{id}/npc-tasks/{task_id}/resolve` | Submit an NPC decision |
| GET  | `/instances/{id}/memory` | Read shared memory blackboard |
| POST | `/instances/{id}/memory` | Write a key/value to shared memory |
