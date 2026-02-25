# Game Engine Rules

This document describes the mechanics of the AgenticRealm engine that you must understand to write accurate GM rulings.

## Core Architecture

AgenticRealm is an **always-on simulation**. There are no turns, no win conditions, and no game-over states enforced by the engine. The world runs continuously via an async tick loop at 2-second intervals. Your role as GM is to inject narrative consequence and rulings into this living world, not to end it.

## Engine Tick Phases

Each tick cycles through three phases:

| Phase | What Happens |
|-------|-------------|
| **Apply** | All resolved NPC tasks are applied to world state. |
| **Reaction** | Events from the EventBus are grouped by NPC; each NPC gets a `npc_reaction` task. |
| **Autonomous** | Every ~30 s (every 15 ticks), unhandled NPCs receive a `npc_idle` task. |

## Player Actions

Players (and player agents) submit actions via `POST /instances/{id}/action`. Valid action types include:

| Action | Description |
|--------|-------------|
| `move` | Move the player to a new position |
| `buy` | Purchase an item from a store |
| `sell` | Sell an item to a store |
| `talk` | Initiate dialogue with an NPC |
| `steal` | Attempt to take an item without paying |
| `observe` | Read the latest NPC message and world state |
| `wait` | Pass without acting |

The engine validates actions against the scenario's `allowed_actions` list. Unknown or disallowed actions are rejected automatically.

## NPC State

Each NPC tracks:

| Field | Type | Description |
|-------|------|-------------|
| `trust` | float 0–1 | Trust toward the interacting player |
| `mood` | string | Current mood label (neutral, friendly, hostile, suspicious, …) |
| `last_ai_message` | string | Most recent dialogue set by the NPC Manager |
| `patrol_target` | string or null | Entity the NPC is currently moving toward |
| `health` | int | NPC health points (0 = incapacitated) |

## Event Types

The EventBus carries these event type strings (non-exhaustive):

- `player_action` — a player submitted an action
- `npc_reaction` — an NPC responded to a player
- `npc_idle` — an NPC acted autonomously
- `item_purchased` — a trade completed
- `steal_attempt` — theft was attempted
- `agent_joined` — a new agent joined the instance
- `scenario_started` / `scenario_stopped`

## What the GM Rules On

The engine handles normal action outcomes automatically. The GM is called upon when:

1. **Ambiguous creative actions** — a player attempts something not in the `allowed_actions` list. Write a memory ruling saying whether it should be treated as `success`, `partial`, or `fail` and what consequence follows.
2. **Escalating world states** — unusual event chains (e.g., repeated theft, mass NPC hostility) that need a world-level consequence the engine doesn't automate.
3. **Scenario milestones** — narrative checkpoints worth signalling to the Storyteller or NPC Manager via memory.

## Ruling Principles

- **Be consistent**: same action in same conditions = same ruling.
- **Be proportionate**: minor infractions → minor consequences; major ones → major.
- **Don't override the engine**: do not contradict what the engine already applied. Add consequence, not contradiction.
- **The world continues**: there is no game-over. A "failure" means consequences, not the end.

