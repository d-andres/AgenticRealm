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

| Role string | Directory | Responsibility |
|-------------|-----------|----------------|
| `player` | — | Submits game actions (`buy`, `talk`, `move`, etc.) as a player character. |
| `npc_admin` | `/npc_manager` | Polls pending NPC tasks and resolves NPC decisions (dialogue, mood, movement). |
| `scenario_generator` | `/realm_architect` | Generates procedural scenario instances from templates via the API. |
| `game_master` | `/game_master` | Monitors world events and injects narrative rulings or world-state notes via shared memory. |
| `storyteller` | `/storyteller` | Narrates world events by writing flavor text to the shared memory board. |

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
