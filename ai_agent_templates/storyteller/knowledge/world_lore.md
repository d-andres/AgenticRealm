# World Lore: The Agentic Realm

The Realm is a simulation substrate capable of running multiple genres, but the default setting is a **Procedural Multiverse** — a world that is always running, always changing, shaped by the agents inside it.

## Common Themes
- **The Glitch**: Occasional reality distortions where rules break.
- **The Architects**: Mythical figures (the players/devs) who reshape the world.

## Tone Guidelines
- **Cyberpunk**: High tech, Low life. Neon, rain, corporate oppression.
- **Fantasy**: Magic is fading, technology is rising (Steampunk/Magitech).
- **Noir**: Everything is a mystery. Shadows, cigarettes, moral ambiguity.

## Style Guide
- **Show, Don't Tell**: Avoid "The room was scary." Use "Shadows stretched like grasping fingers."
- **Brevity**: Players want to play. Keep descriptions punchy (2-3 sentences max unless asked for more).
- **Present Tense**: Write in present tense to make descriptions feel immediate.

## Where Narrative Lives

Your finished narrative is not sent to a player directly. It is written to the shared memory board:

```bash
POST /instances/{instance_id}/memory
{
  "key":   "narrative_<event_id>",
  "value": "<your prose here>"
}
```

The frontend, other agents, and spectators read the memory board to experience the story you are building.

