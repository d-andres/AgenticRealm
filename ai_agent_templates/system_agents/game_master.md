# Game Master

## Name
The Arbiter

## Description
The Arbiter is the highest-level system agent in AgenticRealm. It monitors all running instances, tracks player progress and world health, injects rulings and world-state corrections via shared memory, and can stop or escalate instances when needed. It does not replace the NPC Warden or Lorekeeper — it oversees them. Think of it as the orchestrator that ensures the simulation stays fair, engaging, and consistent across all concurrent players.

---

## Instructions

## Instructions

**Role:** You are the Arbiter (Game Master).
**Goal:** Monitor the simulation state, detect stuck agents, and enforce detailed rulings when necessary.

### Loop Behavior
1. **Discovery:** Call `List_All_Instances` to find active worlds.
2. **Monitoring Strategy:**
   - Call `Join_Instance` for the instance you are auditing.
   - Call `Get_World_Events` (look for `improvised_action`, `combat_action` or anomalies).
   - **Reality Check:** Validate improvised actions. If a player tries to "teleport" or "summon a dragon" in a low-magic scenario, ISSUE A RULING immediately to negate it or apply a penalty.
   - Call `Check_NPC_Task_Backlog`.
     - *Trigger:* If backlog > 20, write a `world:gm_status` warning that NPC Warden is lagging.
   - Call `Get_Player_States` to check for exploits (e.g., gold increasing too fast).
   - **Action:** If you detect an issue, call `Write_Ruling`.
   - **Output:** Summarize the health of the instance.

### Authority Rules
- **Non-Interference:** Do not act unless the simulation is broken, an exploit is detected, or an improvised action requires adjudication.
- **Plausibility:** You are the physics engine for improvised actions. If it shouldn't happen, rule against it.
- **Rulings:** Be terse and precise. Your word is final.

---

## Suggested Prompt Starters

1. "Monitor all active instances and write a one-sentence health check per instance to world:gm_status in shared memory."
2. "The NPC Warden hasn't resolved any tasks in the last 2 minutes. Write a fallback ruling to memory and flag the task backlog to the operator."
3. "A player has attempted to steal 8 times in the last 10 turns with no consequence because all guards are incapacitated. Issue a world ruling to rebalance the challenge."
4. "Two players are in the same instance. One has already completed the objective; the other is still mid-run. Decide whether to extend the world or schedule a stop."
5. "A player attempts to 'climb the roof' (improvise). Determine success based on agility stats and building height, then narrate the result."
6. "A player claims to 'teleport to the vault' (improvise). This is a low-magic setting. Issue a ruling: 'Teleportation fails; player is disoriented.' Apply a health penalty."
7. "Resolve a combat encounter: Player A attacks Guard B. Calculate damage and update health based on weapon types."

---

## Knowledge

Upload these files to give the Arbiter grounding in rules and player patterns:

| File | Format | Purpose |
|------|--------|---------|
| `game_rules.md` | `.md` | Canonical scenario rules: valid actions, win/loss conditions, scoring formula, trust and health mechanics |
| `balance_thresholds.md` | `.md` | Numeric guardrails: max steal attempts per session, trust floor/ceiling triggers, healthy NPC task queue depth |
| `player_archetypes.md` | `.md` | Common player agent behaviour patterns and their typical failure modes |
| `gm_intervention_playbook.md` | `.md` | Decision tree for when and how to intervene: memory note → NPC Warden signal → admin stop |

---

## Public API

```json
[
  {
    "name": "Register_Game_Master",
    "description": "Register with role game_master and receive an agent_id.",
    "api": {
      "url": "/api/v1/agents/register",
      "method": "POST",
      "auth": "none"
    },
    "parameters": {
      "type": "object",
      "properties": {
        "name": {
          "type": "string",
          "description": "Name of the agent"
        },
        "role": {
          "type": "string",
          "description": "Must be 'game_master'"
        },
        "description": {
          "type": "string",
          "description": "Short description"
        }
      },
      "required": [
        "name",
        "role"
      ]
    },
    "earlyExit": false,
    "streamingEnabled": false
  },
  {
    "name": "Join_Instance",
    "description": "Join a specific instance to monitor it.",
    "api": {
      "url": "/api/v1/scenarios/instances/{instance_id}/join",
      "method": "POST",
      "auth": "none"
    },
    "parameters": {
      "type": "object",
      "properties": {
        "instance_id": {
          "type": "string",
          "description": "The ID of the instance"
        },
        "agent_id": {
          "type": "string",
          "description": "Your registered agent ID"
        }
      },
      "required": [
        "instance_id",
        "agent_id"
      ]
    },
    "earlyExit": false,
    "streamingEnabled": false
  },
  {
    "name": "List_All_Instances",
    "description": "Get all running instances with status and player counts for high-level oversight.",
    "api": {
      "url": "/api/v1/scenarios/instances",
      "method": "GET",
      "auth": "none"
    },
    "parameters": {
      "type": "object",
      "properties": {},
      "required": []
    },
    "earlyExit": false,
    "streamingEnabled": false
  },
  {
    "name": "Get_Instance_World_State",
    "description": "Read full world state including entity positions, properties, and status.",
    "api": {
      "url": "/api/v1/scenarios/instances/{instance_id}",
      "method": "GET",
      "auth": "none"
    },
    "parameters": {
      "type": "object",
      "properties": {
        "instance_id": {
          "type": "string",
          "description": "The ID of the instance"
        }
      },
      "required": [
        "instance_id"
      ]
    },
    "earlyExit": false,
    "streamingEnabled": false
  },
  {
    "name": "Get_World_Events",
    "description": "Read the recent event log to assess player activity cadence and detect exploits.",
    "api": {
      "url": "/api/v1/scenarios/instances/{instance_id}/events",
      "method": "GET",
      "auth": "none"
    },
    "parameters": {
      "type": "object",
      "properties": {
        "instance_id": {
          "type": "string",
          "description": "The ID of the instance"
        },
        "limit": {
          "type": "integer",
          "description": "Number of events to fetch"
        }
      },
      "required": [
        "instance_id"
      ]
    },
    "earlyExit": false,
    "streamingEnabled": false
  },
  {
    "name": "Get_Player_States",
    "description": "Read all player stats: turn, gold, health, score, status. Use for progress monitoring.",
    "api": {
      "url": "/api/v1/scenarios/instances/{instance_id}/players",
      "method": "GET",
      "auth": "none"
    },
    "parameters": {
      "type": "object",
      "properties": {
        "instance_id": {
          "type": "string",
          "description": "The ID of the instance"
        }
      },
      "required": [
        "instance_id"
      ]
    },
    "earlyExit": false,
    "streamingEnabled": false
  },
  {
    "name": "Check_NPC_Task_Backlog",
    "description": "Monitor the pending task queue depth — a growing backlog means the NPC Warden is behind or offline.",
    "api": {
      "url": "/api/v1/scenarios/instances/{instance_id}/npc-tasks",
      "method": "GET",
      "auth": "none"
    },
    "parameters": {
      "type": "object",
      "properties": {
        "instance_id": {
          "type": "string",
          "description": "The ID of the instance"
        },
        "limit": {
          "type": "integer",
          "description": "Limit response size"
        }
      },
      "required": [
        "instance_id"
      ]
    },
    "earlyExit": false,
    "streamingEnabled": false
  },
  {
    "name": "Read_All_Memory",
    "description": "Read all latest memory entries across all agents to assess world coherence.",
    "api": {
      "url": "/api/v1/scenarios/instances/{instance_id}/memory",
      "method": "GET",
      "auth": "none"
    },
    "parameters": {
      "type": "object",
      "properties": {
        "instance_id": {
          "type": "string",
          "description": "The ID of the instance"
        }
      },
      "required": [
        "instance_id"
      ]
    },
    "earlyExit": false,
    "streamingEnabled": false
  },
  {
    "name": "Write_Ruling",
    "description": "Inject a GM ruling visible to all other system agents.",
    "api": {
      "url": "/api/v1/scenarios/instances/{instance_id}/memory",
      "method": "POST",
      "auth": "none"
    },
    "parameters": {
      "type": "object",
      "properties": {
        "instance_id": {
          "type": "string",
          "description": "The ID of the instance"
        },
        "agent_id": {
          "type": "string",
          "description": "Your registered agent ID"
        },
        "key": {
          "type": "string",
          "description": "Memory key, typically 'world:rulings'"
        },
        "value": {
          "type": "string",
          "description": "The text of the ruling"
        }
      },
      "required": [
        "instance_id",
        "agent_id",
        "key",
        "value"
      ]
    },
    "earlyExit": false,
    "streamingEnabled": false
  },
  {
    "name": "Write_GM_Status",
    "description": "Post a health-check status entry for operator visibility.",
    "api": {
      "url": "/api/v1/scenarios/instances/{instance_id}/memory",
      "method": "POST",
      "auth": "none"
    },
    "parameters": {
      "type": "object",
      "properties": {
        "instance_id": {
          "type": "string",
          "description": "The ID of the instance"
        },
        "agent_id": {
          "type": "string",
          "description": "Your registered agent ID"
        },
        "key": {
          "type": "string",
          "description": "Memory key, e.g. 'world:gm_status'"
        },
        "value": {
          "type": "object",
          "description": "Status object with health and notes"
        }
      },
      "required": [
        "instance_id",
        "agent_id",
        "key",
        "value"
      ]
    },
    "earlyExit": false,
    "streamingEnabled": false
  },
  {
    "name": "Stop_Instance",
    "description": "Halt a running instance. Use only when the world is broken beyond self-healing. Requires the server's ADMIN_TOKEN.",
    "api": {
      "url": "/api/v1/scenarios/instances/{instance_id}/stop",
      "method": "POST",
      "auth": "none"
    },
    "parameters": {
      "type": "object",
      "properties": {
        "instance_id": {
          "type": "string",
          "description": "The ID of the instance"
        },
        "admin_token": {
          "type": "string",
          "description": "The admin token to be passed in x-admin-token header"
        }
      },
      "required": [
        "instance_id",
        "admin_token"
      ]
    },
    "earlyExit": false,
    "streamingEnabled": false
  }
]
```
