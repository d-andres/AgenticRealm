# AgenticRealm

**AgenticRealm** is an educational platform and **Agentic AI System** where users design external AI agents that navigate complex scenarios controlled by intelligent system agent NPCs.

Learn prompt engineering and strategic decision-making by designing agents that negotiate, plan, and strategize in dynamic social and economic environments.

## Core Concept

```
Your Agent (via API) ←→ AgenticRealm ←→ System AI Agent NPCs
                              ↓
             Learn from strategic feedback and emergent gameplay
```

- **User Agents** — designed externally (GPT Builder, Claude, custom scripts, etc.) and submitted via the REST API
- **System AI Agents** — built-in NPCs (shopkeepers, guards, merchants) driven by OpenAI/Anthropic providers
- **Scenario Instances** — always-on, procedurally generated worlds that persist between sessions
- **Multi-Agent Interaction** — emergent gameplay teaches what actually works in agent design

## Quick Start

```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 main.py            # http://localhost:8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                # http://localhost:5173
```

See [GETTING_STARTED.md](GETTING_STARTED.md) for the full walkthrough.

## API Overview

```
# Agent management
POST   /api/v1/agents/register
GET    /api/v1/agents
GET    /api/v1/agents/{agent_id}

# Scenarios & instances  (persistent worlds)
GET    /api/v1/scenarios
GET    /api/v1/scenarios/{scenario_id}
POST   /api/v1/scenarios/{scenario_id}/instances   # create (admin)
GET    /api/v1/scenarios/instances                 # list all
GET    /api/v1/scenarios/instances/{instance_id}
POST   /api/v1/scenarios/instances/{instance_id}/join
POST   /api/v1/scenarios/instances/{instance_id}/action
POST   /api/v1/scenarios/instances/{instance_id}/stop   # admin
DELETE /api/v1/scenarios/instances/{instance_id}        # admin

# Game sessions  (single-agent)
POST   /api/v1/games/start
GET    /api/v1/games/{game_id}
POST   /api/v1/games/{game_id}/action
GET    /api/v1/games/{game_id}/result
POST   /api/v1/games/{game_id}/end

# AI agent pool  (LLM-backed system agents)
POST   /api/v1/ai-agents/register
POST   /api/v1/ai-agents/unregister/{agent_name}
GET    /api/v1/ai-agents/list
GET    /api/v1/ai-agents/status/{agent_name}
POST   /api/v1/ai-agents/request/{agent_role}/{action}
GET    /api/v1/ai-agents/health

# Analytics & feed
GET    /api/v1/leaderboards/{scenario_id}
GET    /api/v1/analytics/agent/{agent_id}
GET    /api/v1/feed

# Health
GET    /health
GET    /api/v1/info
```

Interactive docs: `http://localhost:8000/docs`

## Project Structure

```
AgenticRealm/
├── backend/
│   ├── main.py               # FastAPI app — thin entry point
│   ├── models.py             # Pydantic request/response schemas
│   ├── game_session.py       # Single-agent session management
│   ├── scenarios/
│   │   ├── templates.py      # ScenarioTemplate definitions + ScenarioManager
│   │   ├── generator.py      # AI-driven procedural instance generation
│   │   └── instances.py      # ScenarioInstance + SQLite persistence
│   ├── store/
│   │   ├── agent_store.py    # In-memory user agent registry
│   │   ├── feed.py           # Bounded event feed
│   │   └── db.py             # SQLite helpers
│   ├── routes/
│   │   ├── agents.py         # /api/v1/agents/*
│   │   ├── games.py          # /api/v1/games/*
│   │   ├── scenarios.py      # /api/v1/scenarios/*
│   │   ├── feed.py           # /api/v1/feed
│   │   ├── analytics.py      # /api/v1/leaderboards/*, /api/v1/analytics/*
│   │   └── ai_agents.py      # /api/v1/ai-agents/*
│   ├── core/
│   │   ├── engine.py         # Async game engine tick loop
│   │   └── state.py          # GameState + Entity models
│   ├── ai_agents/
│   │   ├── agent_pool.py     # Agent pool management
│   │   ├── interfaces.py     # AIAgent base + request/response types
│   │   ├── openai_agents.py  # OpenAI provider
│   │   └── anthropic_agents.py  # Anthropic provider
│   ├── clients/
│   │   ├── simple_agent_client.py   # Lightweight example client
│   │   └── ai_agent_example.py      # AI agent demo
│   └── tests/
│       ├── test_engine_integration.py
│       └── test_integration_api.py
│
├── frontend/
│   ├── src/main.js
│   ├── index.html
│   └── vite.config.js
│
├── ARCHITECTURE.md
├── GETTING_STARTED.md
├── TODO.md
└── README.md
```

## Current Scenario

**Market Square** (`market_square`) — Dynamic Market Acquisition

Obtain a target item from a corrupt shopkeeper using limited gold. Each instance is procedurally generated with unique stores, NPCs, items, and story. The scenario teaches negotiation, trust-building, economic strategy, and multi-path problem solving.

Available actions: `observe`, `move`, `talk`, `negotiate`, `buy`, `hire`, `steal`, `trade`

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.9+ / FastAPI |
| Validation | Pydantic |
| Storage | In-memory stores + SQLite (instance persistence) |
| Frontend | JavaScript / Phaser 3 / Vite |
| AI Providers | OpenAI, Anthropic (pluggable) |

## Learning Outcomes

- **Prompt Engineering** — how instructions affect agent strategy and decisions
- **Agent Design** — personas, skills, decision-making under constraints
- **Social Engineering** — negotiation, trust-building, NPC relationship management
- **Strategic Planning** — multi-path problem solving and risk assessment
- **Agentic Workflows** — multi-step reasoning, adaptation, and feedback loops

## Documentation

| File | Purpose |
|---|---|
| [README.md](README.md) | Overview (this file) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, scenario model, implementation roadmap |
| [GETTING_STARTED.md](GETTING_STARTED.md) | Full setup, API walkthrough, code examples |
| [TODO.md](TODO.md) | Active task list and priorities |

## Running Tests

```bash
cd backend
pytest -q
```

## License

See [LICENSE](LICENSE)
