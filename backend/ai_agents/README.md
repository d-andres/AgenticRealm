# AI Agent Framework for AgenticRealm

## Overview

AgenticRealm now includes a **live AI agent framework** where external AI agents (GPT, Claude, Copilot, etc.) can stay connected and actively manage system components in real-time.

Instead of hardcoded NPC behavior or rule-based scenario generation, AI agents continuously:
- **Generate scenarios**: Create unique stores, NPCs, items based on context
- **Manage NPCs**: Generate authentic NPC responses, maintain conversation history, evolve trust/relationships
- **Judge actions**: Decide outcomes of player actions
- **Tell stories**: Generate narrative descriptions and events

## Architecture

### Core Components

```
System Request → API Route → AgentPool → Load-Balanced Agent → AI Provider → Response
                                                ↓
                                        Stays Connected
                                        Listens for Events
                                        Responds in Real-time
```

### Modules

- **`ai_agents/interfaces.py`**: Abstract base classes and request/response models
  - `AIAgent`: Base class all agents inherit
  - `AIAgentRequest`: What system sends to agent (role, action, context)
  - `AIAgentResponse`: What agent returns (result, reasoning, metadata)
  - Role-specific interfaces: `ScenarioGeneratorAgentInterface`, `NPCAdminAgentInterface`, etc.

- **`ai_agents/agent_pool.py`**: Central agent lifecycle manager
  - Register agents (they connect and stay listening)
  - Route requests (round-robin if multiple agents same role)
  - Broadcast to all agents of role (parallel execution)
  - Unregister/shutdown gracefully

- **`ai_agents/gpt_agents.py`**: Example implementations using OpenAI GPT-4
  - `GPTScenarioGeneratorAgent`: Generates unique scenarios
  - `GPTNPCAdminAgent`: Manages NPC behavior and interactions

- **`routes/ai_agent_routes.py`**: REST API for agent management
  - Register/unregister agents
  - List connected agents
  - Send requests to agents
  - Health checks

## Quick Start

### 1. Set Up Environment

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="sk-your-key-here"

# or on Windows:
set OPENAI_API_KEY=sk-your-key-here
```

### 2. Start AgenticRealm Backend

```bash
cd backend
python main.py
```

The API will be running at `http://localhost:8000`

### 3. Run Example Client

The example client shows how to use the agent framework:

```bash
python backend/clients/ai_agent_example.py
```

This demonstrates:
- Registering agents via API
- Requesting scenario generation
- Requesting NPC decisions
- Requesting NPC interactions
- Checking agent pool health

## Usage Examples

### Register a Scenario Generator Agent

```python
import httpx
import asyncio

async def register_agent():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/ai-agents/register",
            json={
                "agent_name": "gpt4-scenario-gen",
                "agent_role": "scenario_generator",
                "agent_type": "gpt",
                "config": {
                    "api_key": "sk-...",
                    "model": "gpt-4"
                }
            }
        )
    print(response.json())

asyncio.run(register_agent())
```

### Request Scenario Generation

```python
async def generate_scenario():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/ai-agents/request/scenario_generator/generate_stores",
            json={
                "context": {
                    "num_stores": 5,
                    "themes": ["urban_market", "bustling", "merchant_quarter"],
                    "npc_count": 3
                }
            }
        )
    
    result = response.json()
    if result["success"]:
        stores = result["result"]["stores"]
        for store in stores:
            print(f"{store['name']} - owned by {store['proprietor']}")

asyncio.run(generate_scenario())
```

### Request NPC Response

```python
async def get_npc_response():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/ai-agents/request/npc_admin/npc_interaction",
            json={
                "context": {
                    "npc_id": "merchant_001",
                    "npc_data": {
                        "name": "Thora the Merchant",
                        "job": "shopkeeper",
                        "personality": "friendly, haggler",
                        "skills": {"negotiation": 2}
                    },
                    "player_message": "Can you give me a discount?"
                }
            }
        )
    
    result = response.json()
    if result["success"]:
        npc_response = result["result"]
        print(f"NPC: {npc_response['response']}")
        print(f"Accepts: {npc_response['accepts']}")
        print(f"Trust change: {npc_response['trust_change']}")

asyncio.run(get_npc_response())
```

## API Endpoints

### Agent Management

- **POST** `/api/v1/ai-agents/register`
  - Register a new AI agent
  - Body: `{agent_name, agent_role, agent_type, config}`

- **POST** `/api/v1/ai-agents/unregister/{agent_name}`
  - Unregister and disconnect an agent

- **GET** `/api/v1/ai-agents/list`
  - List all registered agents and their status

- **GET** `/api/v1/ai-agents/status/{agent_name}`
  - Get status of specific agent

- **GET** `/api/v1/ai-agents/health`
  - Check agent pool health

### Request Routing

- **POST** `/api/v1/ai-agents/request/{agent_role}/{action}`
  - Send request to agent pool
  - Body: `{context: dict}`
  - Response: `{success, result, reasoning, metadata}`
  - AgentPool automatically selects agent (round-robin if multiple same role)

## Creating Custom Agents

To add a new AI provider (Claude, Copilot, custom logic), create a new agent class:

```python
from ai_agents.interfaces import AIAgent, AIAgentRequest, AIAgentResponse, AgentRole

class CustomAgent(AIAgent):
    def __init__(self, agent_name: str, config: dict):
        super().__init__(agent_name, AgentRole.CUSTOM, config)
    
    async def connect(self) -> bool:
        """Initialize connection to your AI provider"""
        # TODO: Connect to Claude API, Copilot API, or custom logic
        self.is_connected = True
        return True
    
    async def disconnect(self) -> bool:
        """Gracefully disconnect"""
        self.is_connected = False
        return True
    
    async def handle_request(self, request: AIAgentRequest) -> AIAgentResponse:
        """Process request from system"""
        try:
            # TODO: Call your AI provider with request.context
            result = await self.my_ai_call(request.context)
            
            return AIAgentResponse(
                request_id=request.request_id,
                agent_role=self.role,
                success=True,
                result=result,
                reasoning="Your reasoning here"
            )
        except Exception as e:
            return AIAgentResponse(
                request_id=request.request_id,
                agent_role=self.role,
                success=False,
                result={"error": str(e)}
            )
    
    async def listen(self):
        """Keep agent alive and listening"""
        while self.is_connected:
            await asyncio.sleep(1)
            # TODO: Check for events from your AI provider
```

Then register it:

```python
async def register_custom_agent():
    agent = CustomAgent(
        agent_name="my-custom-agent",
        config={"provider": "claude", "api_key": "sk-..."}
    )
    
    pool = get_agent_pool()
    await pool.register_agent(agent)
```

## Agent Roles

Current supported agent roles (extensible):

- **`SCENARIO_GENERATOR`**: Creates unique scenarios (stores, items, NPCs)
- **`NPC_ADMIN`**: Manages NPC behavior and interactions
- **`GAME_MASTER`**: Adjudicates game rules and outcomes
- **`JUDGE`**: Validates player actions
- **`STORYTELLER`**: Generates narrative descriptions
- **`CUSTOM`**: Any custom role you define

## Integration Points (TODO)

The framework is ready. Now integrate it into your existing system:

### 1. Wire into main.py
```python
from ai_agents.agent_pool import get_agent_pool, shutdown_agent_pool

app = FastAPI()

@app.on_event("startup")
async def startup():
    # Agent pool initializes on server start
    # (Agents registered via API can now connect)
    print("Agent pool ready")

@app.on_event("shutdown")
async def shutdown():
    await shutdown_agent_pool()
    print("Agent pool shutdown")
```

### 2. Wire into Scenario Generation
Replace rule-based logic with agent requests:

```python
# Instead of:
# scenario = generate_hardcoded_scenario()

# Do this:
from ai_agents.agent_pool import get_agent_pool
from ai_agents.interfaces import AgentRole

pool = get_agent_pool()
response = await pool.request(
    role=AgentRole.SCENARIO_GENERATOR,
    action="generate_stores",
    context={
        "num_stores": 5,
        "themes": scenario_template.get("themes", [])
    }
)

if response.success:
    stores = response.result["stores"]
```

### 3. Wire into Game Engine
When NPC needs to respond:

```python
# In game session when player interacts with NPC:
response = await pool.request(
    role=AgentRole.NPC_ADMIN,
    action="npc_interaction",
    context={
        "npc_id": npc.id,
        "npc_data": npc.to_dict(),
        "player_message": player_action.message
    }
)

if response.success:
    npc_response = response.result
    # Update NPC state and send response to player
```

## Performance Notes

- **Load Balancing**: Multiple agents of same role = requests distributed via round-robin
- **Concurrency**: All agents run in parallel via asyncio.gather()
- **Memory**: NPC interaction histories kept in-memory (could be moved to database for persistence)
- **Rate Limiting**: API providers (OpenAI, Anthropic) may have rate limits - consider adding queue

## Troubleshooting

**Agents not connecting?**
- Check API key is valid
- Ensure httpx is installed
- Check network connectivity to AI provider

**Scenario generation returns errors?**
- Verify API key has access to GPT-4
- Check context dict has required fields
- Review agent reasoning in response for details

**NPC responses seem generic?**
- Add more detail to npc_data (personality traits, history, relationships)
- Experiment with system prompts in agent code
- Check conversation history is being maintained

## API Quick Reference

### Register Agent
```bash
curl -X POST http://localhost:8000/api/v1/ai-agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "gpt4-scenario",
    "agent_role": "scenario_generator",
    "agent_type": "gpt",
    "config": {"api_key": "sk-...", "model": "gpt-4"}
  }'
```

### Send Request to Agent
```bash
curl -X POST http://localhost:8000/api/v1/ai-agents/request/scenario_generator/generate_stores \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "num_stores": 5,
      "themes": ["bustling", "market"]
    }
  }'
```

### Check Agent Pool Health
```bash
curl http://localhost:8000/api/v1/ai-agents/health
```

### List Registered Agents
```bash
curl http://localhost:8000/api/v1/ai-agents/list
```

### Agent Roles
- `scenario_generator` - Create unique scenarios
- `npc_admin` - Manage NPC behavior  
- `game_master` - Adjudicate game rules
- `judge` - Validate actions
- `storyteller` - Generate narrative
- `custom` - Custom implementations

### Response Format
```json
{
  "request_id": "uuid",
  "agent_role": "scenario_generator",
  "success": true,
  "result": { "stores": [...] },
  "reasoning": "Agent's explanation",
  "metadata": {
    "agent_name": "gpt4-scenario",
    "provider": "openai",
    "model": "gpt-4",
    "tokens_used": 1250
  }
}
```

## Files

```
backend/
├── ai_agents/
│   ├── __init__.py                 # Module entry point
│   ├── interfaces.py               # Abstract interfaces and base classes
│   ├── agent_pool.py              # Central agent lifecycle manager
│   ├── gpt_agents.py              # GPT implementation examples
│   └── README.md                   # This file
├── routes/
│   └── ai_agent_routes.py         # REST API endpoints
├── clients/
│   ├── ai_agent_example.py        # Complete example - run this first!
│   └── simple_agent_client.py     # Simple client example
└── main.py                         # ✅ Agent pool integrated
```

## Integration Status

✅ **Complete** - Agent pool is integrated into main.py
- Initializes on server startup
- Shutdown gracefully on server stop
- Ready for agent registration and requests

## Next Steps

1. ✅ Framework complete
2. ✅ Integrated into main.py
3. ⏳ Run example client to verify: `python backend/clients/ai_agent_example.py`
4. ⏳ Wire scenario generation to use agents
5. ⏳ Wire game engine NPC responses to use agents
6. ⏳ Add request priority queue for critical decisions
7. ⏳ Add agent performance monitoring

---

See [GETTING_STARTED.md](../../GETTING_STARTED.md) for complete setup guide and examples.
