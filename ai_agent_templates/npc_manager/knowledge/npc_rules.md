# NPC Decision Rules

This document defines the rules governing NPC behaviour and the resolution schema you must use when answering NPC tasks from AgenticRealm.

## NPC State Properties

Every NPC task's `context` dict exposes these fields:

| Property | Type | Description |
|----------|------|-------------|
| `npc_id` | string | Unique identifier |
| `npc_name` | string | Display name |
| `npc_job` | string | Role in the world (e.g., `merchant`, `guard`, `innkeeper`) |
| `npc_mood` | string | Current mood label (e.g., `neutral`, `hostile`, `friendly`) |
| `npc_trust` | float 0–1 | Current trust level toward the player |
| `events` | string[] | Recent game events that triggered this task |
| `world_state` | object | Snapshot of nearby entities and items |

## Trust Level Guidelines

| Trust Range | Behaviour |
|-------------|-----------|
| 0.0 – 0.3 | Hostile or suspicious. Refuses most requests. May alert guards. |
| 0.3 – 0.6 | Neutral. Standard business. No special treatment. |
| 0.6 – 0.8 | Friendly. May offer discounts or share information. |
| 0.8 – 1.0 | Trusted confidant. Volunteers aid, shares secrets, offers best prices. |

## Resolution Schema

Submit to `POST /instances/{instance_id}/npc-tasks/{task_id}/resolve`:

```json
{
  "resolution": {
    "trust_delta":      "<float — change in trust, e.g. 0.05 or -0.1>",
    "mood":             "<string — new mood label, e.g. 'suspicious'>",
    "last_ai_message":  "<string — NPC dialogue for next player observe action>",
    "patrol_target":    "<string or null — entity_id NPC should move toward>"
  }
}
```

All four fields are **optional**. Only include keys that should change. An empty `{}` resolution is valid (NPC does nothing).

## Behaviour Rules by Task Type

### `npc_reaction`
A player action just occurred nearby or directly involving the NPC. React proportionally:

- Player gave gold or complimented → `trust_delta` positive, `mood: friendly`, warm dialogue.
- Player attacked or stole → `trust_delta` negative, `mood: hostile`, alarmed or threatening dialogue.
- Player just walked past → minimal reaction (brief glance or no change).

### `npc_idle`
No players have interacted recently (~30 s). Generate subtle autonomous behaviour:

- A merchant: counts coins, rearranges items, mutters about slow business.
- A guard: shifts to a new `patrol_target`, scans surroundings.
- An innkeeper: wipes down the bar, hums a tune.

Keep `trust_delta: 0` and leave `mood` unchanged unless there is a specific narrative reason.

### `npc_interaction`
The player is directly engaging: talking, trading, or initiating a specific exchange.

- Read the `events` list to understand what the player said or did.
- Respond in character via `last_ai_message`.
- Update `trust_delta` based on whether the exchange was positive, negative, or neutral.

## Dialogue Style

- Write dialogue **as the character**, not as a narrator.
- Keep lines short — 1 to 2 sentences unless the player asked an open-ended question.
- Match the world's tone: grounded, low-fantasy, market-town setting by default.
- A merchant speaks differently from a guard. An innkeeper speaks differently from both.

