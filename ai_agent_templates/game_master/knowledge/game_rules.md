# Game Engine Rules

## Core Mechanics

### 1. Movement
- Use standard grid logic (or coordinate logic).
- Obstacles block movement unless a special action (skills/items) is used.

### 2. Turn Economy
- Every significant action (Move, Talk, Buy) costs **1 Turn**.
- Free actions: Inspect, Check Inventory.

### 3. Success Checks (Difficulty Checks - DC)
When resolving uncertain actions, use a standard d20-style logic:
- **Easy**: DC 10
- **Medium**: DC 15
- **Hard**: DC 20
- **Impossible**: DC 25+

**Formula**:
`Roll (1-20) + Skill Bonus >= DC` -> Success.

## Win Conditions
Defined per scenario, but general rules apply:
- **Acquisition**: Must have the target item in `inventory`.
- **Survival**: `health` > 0.
- **Freedom**: Not `status: arrested`.

## Status Effects
- **Stealth**: NPCs perceive player only if `Perception Check` > `Stealth Check`.
- **Wanted**: If player commits crime openly, all Guards become hostile.
