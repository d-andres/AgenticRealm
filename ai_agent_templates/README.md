# AI Agent Templates

This directory contains configuration templates for external AI Agents that power the AgenticRealm system.

These templates are designed for use with:
- **OpenAI Custom GPTs**
- **Microsoft Copilot Studio**
- **LangChain / CrewAI Agents**
- **Zapier Central**
- **Any Low-Code Agent Builder**

## How to Use

1. **Choose a Role**: Decide which system component you want to configure (e.g., Realm Architect, NPC Manager).
2. **Create the Agent**: In your AI tool of choice, create a new agent.
3. **Copy Configuration**:
   - Copy the **Instructions** from the `template.md` file.
   - Set the **Name, Description, and Conversation Starters** provided.
4. **Upload Knowledge**:
   - Upload the corresponding file from the `knowledge/` folder (or copy its contents into the agent's knowledge base).
   - This gives the agent strict definitions of the JSON schemas and Rules it must follow.
5. **Connect Actions** (Advanced):
   - If your platform supports API actions (like OpenAI Actions), configure them to point to your AgenticRealm API endpoint.

## Roles

| Role | Directory | Responsibility |
|------|-----------|----------------|
| **Realm Architect** | `/realm_architect` | Generates unique scenario instances (maps, stores, NPCs) from templates. |
| **NPC Manager** | `/npc_manager` | Controls NPC behavior, dialogue, decision making, and trading logic. |
| **Game Master** | `/game_master` | Arbitrates rules, valid moves, and win/loss conditions. |
| **Storyteller** | `/storyteller` | Narrates the world events and provides environmental flavor text. |
