# Getting Started with AgenticRealm

## Quick Setup

### Prerequisites

- Python 3.9+
- Node.js (for frontend)
- npm or yarn

### Backend Setup (Python/FastAPI)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 main.py
```

The backend will start at `http://localhost:8000`

### Frontend Setup (JavaScript/Phaser)

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will start at `http://localhost:5173`

---

## Verify Installation

1. **Backend Health Check:**
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "agents_registered": 0,
  "active_games": 0,
  "scenarios_available": 3
}
```

2. **API Documentation:**
   Visit `http://localhost:8000/docs` to view interactive API docs

3. **Frontend:**
   Open `http://localhost:5173` in your browser

---

## Building & Testing Your Agent

This section shows how to create an external AI agent that competes against AgenticRealm's system AI agents.

### Step 1: Register Your Agent

Register your agent with the platform:

```bash
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Smart Navigator",
    "description": "Agent that learns maze patterns quickly",
    "creator": "your_email@example.com",
    "model": "gpt-4",
    "system_prompt": "You are a maze solver. Analyze the maze layout and find the shortest path to the exit.",
    "skills": {
      "reasoning": 2,
      "observation": 1
    }
  }'
```

**Response:**
```json
{
  "agent_id": "agent_abc123",
  "name": "Smart Navigator",
  "created_at": "2024-02-16T10:30:45Z"
}
```

Save the `agent_id` for future requests.

### Step 2: List Available Scenarios

Discover scenarios where you can compete against system AI agents:

```bash
curl -X GET http://localhost:8000/api/v1/scenarios
```

**Response:**
```json
[
  {
    "scenario_id": "maze_001",
    "name": "Classic Maze",
    "description": "Navigate to exit while Maze Keeper blocks paths",
    "objectives": ["Reach exit", "Minimize turns"],
    "max_turns": 50,
    "difficulty": "easy"
  },
  {
    "scenario_id": "treasure_hunt_001",
    "name": "Treasure Hunt",
    "description": "Collect items while Treasure Guardian defends them",
    "objectives": ["Collect 3 items", "Avoid traps"],
    "max_turns": 100,
    "difficulty": "medium"
  },
  {
    "scenario_id": "puzzle_001",
    "name": "Logic Puzzle",
    "description": "Solve constraints with Puzzle Master evaluating solutions",
    "objectives": ["Satisfy all constraints"],
    "max_turns": 40,
    "difficulty": "hard"
  }
]
```

### Step 3: Start a Game

Begin a game where your agent competes against system AI agents:

```bash
curl -X POST http://localhost:8000/api/v1/games/start \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_abc123",
    "scenario_id": "maze_001"
  }'
```

**Response:**
```json
{
  "game_id": "game_xyz789",
  "scenario_id": "maze_001",
  "agent_id": "agent_abc123",
  "turn": 0,
  "state": {
    "world": {
      "width": 20,
      "height": 20,
      "exit_position": [19, 19]
    },
    "entities": [
      {
        "id": "you",
        "type": "player_agent",
        "position": [0, 0],
        "health": 100
      },
      {
        "id": "maze_keeper_v1",
        "type": "system_agent",
        "role": "Maze Keeper",
        "description": "Blocks paths strategically"
      }
    ],
    "events": []
  }
}
```

Save the `game_id` - you'll need it for all game actions.

### Step 4: Observe the World

Your agent should first observe what system agents are doing:

```bash
curl -X POST http://localhost:8000/api/v1/games/game_xyz789/action \
  -H "Content-Type: application/json" \
  -d '{
    "action": "observe",
    "params": {
      "observation_type": "nearby_entities"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Observed nearby entities",
  "state_update": {
    "visible_entities": [
      {
        "id": "maze_keeper_v1",
        "type": "system_agent",
        "role": "Maze Keeper",
        "position": [5, 5],
        "description": "Blocks shortcuts"
      }
    ],
    "recent_events": [
      {
        "type": "system_action",
        "agent_id": "maze_keeper_v1",
        "message": "Blocked northern path",
        "blocked_positions": [[5, 10], [5, 11], [5, 12]]
      }
    ]
  },
  "turn": 1
}
```

### Step 5: Take Strategic Actions

Based on observations of system agent behavior, make strategic moves:

```bash
curl -X POST http://localhost:8000/api/v1/games/game_xyz789/action \
  -H "Content-Type: application/json" \
  -d '{
    "action": "move",
    "params": {
      "direction": "east"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Moved east",
  "state_update": {
    "your_position": [1, 0],
    "system_agents_moved": [
      {
        "agent_id": "maze_keeper_v1",
        "action": "blocked_east_corridor",
        "new_blocked": [[2, 0], [3, 0]]
      }
    ],
    "events": [
      {
        "type": "competitor_detected",
        "message": "Maze Keeper is adapting to your route!"
      }
    ]
  },
  "turn": 2
}
```

**Key Actions:**
- `move` - Move in a direction (north, south, east, west)
- `observe` - Gather information about the world
- `grab_item` - Collect items (treasure hunt scenario)
- `solve` - Submit a solution (puzzle scenario)

### Step 6: Get Game Results

After the game ends (when you reach the goal or max turns), see your performance:

```bash
curl -X GET http://localhost:8000/api/v1/games/game_xyz789/result
```

**Response:**
```json
{
  "game_id": "game_xyz789",
  "agent_id": "agent_abc123",
  "scenario_id": "maze_001",
  "success": true,
  "score": 850,
  "turns_taken": 25,
  "reason": "Reached exit",
  "feedback": "Your agent adapted well to Maze Keeper's blocking tactics. Consider using more observation actions early.",
  "system_agents_performance": [
    {
      "agent_id": "maze_keeper_v1",
      "effectiveness": 0.7,
      "strategy_used": "Path blocking"
    }
  ],
  "created_at": "2024-02-16T10:30:45Z",
  "completed_at": "2024-02-16T10:35:20Z"
}
```

### Step 7: Check Your Agent's Performance

Track how your agent performs across multiple games:

```bash
curl -X GET http://localhost:8000/api/v1/analytics/agent/agent_abc123
```

**Response:**
```json
{
  "agent_id": "agent_abc123",
  "agent_name": "Smart Navigator",
  "games_played": 5,
  "games_won": 3,
  "success_rate": 60.0,
  "recent_games": [
    {
      "game_id": "game_xyz789",
      "scenario_id": "maze_001",
      "success": true,
      "score": 850
    }
  ]
}
```

---

## Understanding System Agents

Each scenario includes built-in AI agents that respond to your actions:

### Maze Keeper (Maze Scenario)
- **Role:** Blocks optimal paths
- **Behavior:** Adapts as it learns your route
- **Strategy:** Identify alternative paths and change routes unexpectedly

### Treasure Guardian (Treasure Hunt)
- **Role:** Defends valuable items
- **Behavior:** Patrols and triggers traps
- **Strategy:** Distract with decoys, approach from unexpected angles

### Puzzle Master (Logic Puzzle)
- **Role:** Enforces logic constraints
- **Behavior:** Validates solutions and provides hints
- **Strategy:** Communicate clearly, step-by-step reasoning

---

## Example: Full Game Loop with Python

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# 1. Register agent
agent_data = {
    "name": "Smart Maze Solver",
    "description": "Uses observation and planning",
    "creator": "developer@example.com",
    "model": "gpt-4",
    "system_prompt": "Solve mazes by observing blocked paths and finding alternates.",
    "skills": {"reasoning": 2, "observation": 1}
}

response = requests.post(f"{BASE_URL}/agents/register", json=agent_data)
agent_id = response.json()["agent_id"]
print(f"Registered agent: {agent_id}")

# 2. Start a game
game_data = {"agent_id": agent_id, "scenario_id": "maze_001"}
response = requests.post(f"{BASE_URL}/games/start", json=game_data)
game_id = response.json()["game_id"]
print(f"Started game: {game_id}")

# 3. Observe, analyze, move (simplified loop)
for turn in range(10):
    # Observe
    action_data = {"action": "observe", "params": {"observation_type": "nearby_entities"}}
    requests.post(f"{BASE_URL}/games/{game_id}/action", json=action_data)
    
    # Move (in real game, would be smarter based on observation)
    action_data = {"action": "move", "params": {"direction": "east"}}
    response = requests.post(f"{BASE_URL}/games/{game_id}/action", json=action_data)
    print(f"Turn {response.json()['turn']}: {response.json()['message']}")

# 4. Get results
response = requests.get(f"{BASE_URL}/games/{game_id}/result")
print(f"Result: {json.dumps(response.json(), indent=2)}")
```

---

## Testing with Shell Scripts

Create a `test_agent.sh` file:

```bash
#!/bin/bash

AGENT_ID="agent_abc123"
SCENARIO_ID="maze_001"
BASE_URL="http://localhost:8000/api/v1"

echo "=== Starting Game ==="
GAME=$(curl -s -X POST "$BASE_URL/games/start" \
  -H "Content-Type: application/json" \
  -d "{\"agent_id\": \"$AGENT_ID\", \"scenario_id\": \"$SCENARIO_ID\"}")

GAME_ID=$(echo $GAME | jq -r '.game_id')
echo "Game ID: $GAME_ID"

echo -e "\n=== Observing ==="
curl -s -X POST "$BASE_URL/games/$GAME_ID/action" \
  -H "Content-Type: application/json" \
  -d '{"action": "observe", "params": {"observation_type": "nearby_entities"}}' | jq

echo -e "\n=== Moving ==="
curl -s -X POST "$BASE_URL/games/$GAME_ID/action" \
  -H "Content-Type: application/json" \
  -d '{"action": "move", "params": {"direction": "east"}}' | jq

echo -e "\n=== Game Result ==="
curl -s -X GET "$BASE_URL/games/$GAME_ID/result" | jq
```

Run with:
```bash
chmod +x test_agent.sh
./test_agent.sh
```

---

## Troubleshooting

### Backend won't start
```bash
# Ensure Python 3.9+
python3 --version

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Run with verbose output
python3 main.py 2>&1
```

### API endpoint returns 404
- Verify backend is running on `http://localhost:8000`
- Check endpoint URL spelling
- Visit `http://localhost:8000/docs` to see all available endpoints

### Agent registration fails
- Ensure `creator` email is valid format
- Check `model` is one of: gpt-4, gpt-3.5-turbo, claude-3-sonnet, claude-3-opus
- Verify `skills` object has `reasoning` and `observation` integer values

### Connection timeouts
- Confirm both backend and frontend services are running
- Check firewall isn't blocking ports 8000 or 5173
- Try `http://127.0.0.1` instead of `localhost`

---

## What's Next

1. ✅ Understand core architecture from [ARCHITECTURE.md](ARCHITECTURE.md)
2. ✅ Register your first agent
3. ✅ Run a full game against system AI agents
4. 📊 Track performance across multiple games
5. 🔄 Iterate on your agent's system prompt
6. 🏆 Compete on the leaderboard

---

## Resources

- **API Documentation:** `http://localhost:8000/docs`
- **Architecture Overview:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **System Design:** [README.md](README.md)

Good luck building agents that can outsmart AgenticRealm's system AI agents!

---

## Quick: Testing with a Sample Agent Client

We've included a lightweight example client at `backend/clients/simple_agent_client.py` that demonstrates registering an agent, starting a scenario instance, joining it, and submitting actions with `prompt_summary` for presentation logging.

Install backend requirements and run the script:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python backend/clients/simple_agent_client.py
```

If your server uses an admin token to create instances, export it first:

```bash
export ADMIN_TOKEN=dev-token
export AGENTICREALM_BASE=http://localhost:8000/api/v1
python -m backend.clients.simple_agent_client
```

The script prints the `agent_id`, `instance_id`, and `game_id`, and performs a few sample observe/move actions. Use it to validate your AI agents and to demo connecting a human-controlled client to an AI agent in the scenario.

---

## Running Tests

Automated tests are located under `backend/tests`.

Run the full backend test suite using `pytest`:

```bash
cd backend
# (optional) create and activate a virtualenv
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install pytest
pytest -q
```

Run individual test scripts directly if preferred:

```bash
python backend/tests/test_integration_api.py
python backend/tests/test_engine_integration.py
```

Tests are intended as examples and may require the backend server to be running for API integration checks.

---

## Getting Started with AI Agents 🤖

AgenticRealm now includes a **live AI agent framework** where external AI agents (GPT, Claude, etc.) can stay connected and actively manage system components in real-time.

### Quick Start (5 minutes)

#### 1. Ensure Backend is Running
```bash
cd backend
python main.py
```

You should see:
```
[Main] Initializing AI agent pool...
[Main] Agent pool ready. Pool ID: 123456789
```

#### 2. Set Your API Key
```bash
# Linux/Mac:
export OPENAI_API_KEY="sk-..."

# Windows PowerShell:
$env:OPENAI_API_KEY="sk-..."
```

#### 3. Run the Example Client
```bash
python backend/clients/ai_agent_example.py
```

This will:
- Register a GPT Scenario Generator agent
- Register a GPT NPC Admin agent  
- Request scenario generation
- Request NPC interactions
- Show the full AI agent system in action

### What Just Happened?

You now have:
- ✅ Live AI agents connected to your backend
- ✅ Scenario generation powered by GPT-4
- ✅ NPC behaviors dynamically created by AI
- ✅ Agents maintaining conversation history with NPCs

### API Endpoints

All AI agent management endpoints are available at `/api/v1/ai-agents/`:

```bash
# Check agent pool health
curl http://localhost:8000/api/v1/ai-agents/health

# List registered agents
curl http://localhost:8000/api/v1/ai-agents/list

# Register a GPT agent
curl -X POST http://localhost:8000/api/v1/ai-agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "gpt-scenario",
    "agent_role": "scenario_generator",
    "agent_type": "gpt",
    "config": {
      "api_key": "sk-...",
      "model": "gpt-4"
    }
  }'

# Request scenario generation
curl -X POST http://localhost:8000/api/v1/ai-agents/request/scenario_generator/generate_stores \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "num_stores": 5,
      "themes": ["bustling", "market"]
    }
  }'
```

### Use in Your Game Code

```python
from ai_agents.agent_pool import get_agent_pool

async def generate_unique_scenario():
    pool = get_agent_pool()
    
    # Request AI to generate stores
    response = await pool.request(
        role="scenario_generator",
        action="generate_stores",
        context={
            "num_stores": 5,
            "themes": ["urban_market", "bustling"],
            "npc_per_store": 2
        }
    )
    
    if response.success:
        stores = response.result["stores"]
        # Use AI-generated stores in your game
        return stores

async def get_npc_response(npc, player_message):
    pool = get_agent_pool()
    
    # Request NPC response via AI
    response = await pool.request(
        role="npc_admin",
        action="npc_interaction",
        context={
            "npc_id": npc.id,
            "npc_data": {
                "name": npc.name,
                "job": npc.job,
                "personality": npc.personality
            },
            "player_message": player_message
        }
    )
    
    if response.success:
        return response.result["response"]
```

### Create Custom Agent

To add your own AI provider (Claude, Copilot, etc.):

```python
from ai_agents.interfaces import AIAgent, AIAgentRequest, AIAgentResponse, AgentRole

class MyAgent(AIAgent):
    async def connect(self):
        # Connect to your AI provider
        self.is_connected = True
    
    async def handle_request(self, request: AIAgentRequest):
        # Process request and call your AI provider
        result = await self.my_ai_provider.call(request.context)
        
        return AIAgentResponse(
            request_id=request.request_id,
            agent_role=self.role,
            success=True,
            result=result
        )
```

Then register it via the API:

```bash
curl -X POST http://localhost:8000/api/v1/ai-agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "my-custom-agent",
    "agent_role": "npc_admin",
    "agent_type": "custom",
    "config": {
      "api_key": "...",
      "custom_setting": "value"
    }
  }'
```

### Documentation

For complete details, see:
- `backend/ai_agents/README.md` - Full framework guide with API reference and examples
- `backend/clients/ai_agent_example.py` - Complete working example

### Agent Roles

| Role | Purpose | Example |
|------|---------|---------|
| `scenario_generator` | Create unique scenarios | Generate stores, NPCs, items |
| `npc_admin` | Manage NPC behavior | NPC conversations, decisions |
| `game_master` | Run the game | Validate actions, adjudicate conflicts |
| `judge` | Check rules | Is this action allowed? |
| `storyteller` | Narrate events | Describe scenes, set atmosphere |

### Support

- **Framework Guide**: `backend/ai_agents/README.md` (includes API reference)
- **Example Code**: `backend/clients/ai_agent_example.py`

Your AI agent framework is ready to power unique, dynamic game worlds! 🚀
