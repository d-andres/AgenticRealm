# Scenario Generation Schema

This document defines the strict JSON structure required for generating scenario instances.

## Core Objects

### 1. GeneratedScenarioInstance (Root Object)
This is the main object you must return.

```json
{
  "instance_id": "string (unique)",
  "template_id": "string (from request)",
  "scenario_name": "string (creative name)",
  "scenario_description": "string (detailed description)",
  "world_width": "integer (default: 800)",
  "world_height": "integer (default: 600)",
  "starting_position": "[x, y] (integer array)",
  "starting_gold": "integer",
  "max_turns": "integer",
  
  "stores": "[Array of GeneratedStore objects]",
  "npcs": "[Array of GeneratedNPC objects]",
  "target_item": "TargetItem object",
  
  "environmental_story": "string (flavor text)",
  "multiple_solution_paths": ["string", "string"],
  "difficulty_rating": "float (0.0 - 10.0)",
  "expected_gold_efficiency": "[min_gold, max_gold]"
}
```

### 2. GeneratedStore
Represents a shop or location in the world.

```json
{
  "store_id": "string (unique, e.g., store_01)",
  "name": "string (creative name)",
  "location": "[x, y] (integer array)",
  "proprietor_name": "string",
  "proprietor_personality": "string (traits/behavior)",
  "store_type": "string (e.g., 'general', 'black_market')",
  "pricing_multiplier": "float (e.g., 1.0 is normal, 1.5 is expensive)",
  "inventory": {
    "item_id_1": {
      "name": "string",
      "value": "integer",
      "rarity": "string (common|uncommon|rare|legendary)",
      "description": "string"
    },
    ...
  }
}
```

### 3. GeneratedNPC
Represents an interactable character.

```json
{
  "npc_id": "string (unique, e.g., npc_01)",
  "name": "string",
  "job": "string (must be from template allowed jobs)",
  "location": "[x, y] (integer array)",
  "personality": "string (description of behavior)",
  "skills": {
    "negotiation": "integer (1-10)",
    "perception": "integer (1-10)",
    "combat": "integer (1-10)"
  },
  "initial_trust": "float (0.0 to 1.0)",
  "hiring_cost": "integer (or null if not for hire)",
  "relationship_hooks": ["string", "string"]
}
```

### 4. TargetItem
The main objective of the scenario.

```json
{
  "store_id": "string (ID of the store holding it)",
  "item_id": "string (unique ID)",
  "name": "string",
  "value": "integer",
  "description": "string",
  "why_valuable": "string (plot reason)"
}
```

## Constraints
- **Coordinates**: Must be within [0, 0] and [world_width, world_height].
- **IDs**: Must be unique within the instance.
- **Game Balance**: Ensure the `target_item` price is theoretically reachable via the starting gold + possible earnings from `multiple_solution_paths`.
