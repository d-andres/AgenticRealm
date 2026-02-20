"""
OpenAI AI Agents - Concrete implementations using the OpenAI API.

These are provider-specific implementations of the AIAgent interfaces.
To use a different LLM provider, see anthropic_agents.py or implement
your own using the base classes in interfaces.py.
"""

import json
from typing import Dict, Any
import httpx

from .interfaces import (
    AIAgentRequest,
    AIAgentResponse,
    AgentRole,
    ScenarioGeneratorAgentInterface,
    NPCAdminAgentInterface,
)

OPENAI_CHAT_ENDPOINT = "https://api.openai.com/v1/chat/completions"
OPENAI_MODELS_ENDPOINT = "https://api.openai.com/v1/models"


class OpenAIScenarioGeneratorAgent(ScenarioGeneratorAgentInterface):
    """
    Scenario generator backed by the OpenAI chat completions API.

    Supported models: gpt-4o, gpt-4-turbo, gpt-4, gpt-3.5-turbo, etc.
    """

    def __init__(
        self,
        agent_name: str,
        api_key: str,
        model: str = "gpt-4o",
    ):
        super().__init__(agent_name)
        self.api_key = api_key
        self.model = model

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> bool:
        """Validate API key against OpenAI."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    OPENAI_MODELS_ENDPOINT,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                self.is_connected = response.status_code == 200
                return self.is_connected
        except Exception as e:
            print(f"[OpenAIScenarioGeneratorAgent] connect failed: {e}")
            return False

    async def disconnect(self) -> bool:
        self.is_connected = False
        return True

    # ------------------------------------------------------------------
    # Request dispatch
    # ------------------------------------------------------------------

    async def handle_request(self, request: AIAgentRequest) -> AIAgentResponse:
        try:
            dispatch = {
                "generate_stores": self._generate_stores,
                "generate_npcs": self._generate_npcs,
                "generate_items": self._generate_items,
                "generate_target_item": self._generate_target_item,
            }
            handler = dispatch.get(request.action)
            if handler is None:
                result = {"error": f"Unknown action: {request.action}"}
            else:
                result = await handler(request.context)

            return AIAgentResponse(
                request_id=request.request_id,
                agent_role=AgentRole.SCENARIO_GENERATOR,
                success=True,
                action=request.action,
                result=result,
                reasoning=f"Generated via OpenAI ({self.model})",
            )
        except Exception as e:
            return AIAgentResponse(
                request_id=request.request_id,
                agent_role=AgentRole.SCENARIO_GENERATOR,
                success=False,
                action=request.action,
                result={"error": str(e)},
            )

    # ------------------------------------------------------------------
    # Generation helpers
    # ------------------------------------------------------------------

    async def _generate_stores(self, context: Dict[str, Any]) -> Dict:
        num_stores = context.get("num_stores", 4)
        themes = context.get("themes", ["market"])

        prompt = f"""
        Generate {num_stores} unique market stores for a fantasy setting.
        Themes: {', '.join(themes)}

        For each store, provide JSON:
        {{
            "store_id": "unique_id",
            "name": "store name",
            "proprietor": "owner name",
            "proprietor_personality": "short description",
            "store_type": "general/specialty/black_market/rare",
            "pricing_multiplier": 1.0-3.0
        }}

        Make each store unique and interesting. Return a valid JSON array only.
        """
        raw = await self._call_api(prompt)
        try:
            return {"stores": json.loads(raw)}
        except json.JSONDecodeError:
            return {"error": "Failed to parse response as JSON", "raw": raw}

    async def _generate_npcs(self, context: Dict[str, Any]) -> Dict:
        num_npcs = context.get("num_npcs", 6)
        themes = context.get("themes", ["market"])

        prompt = f"""
        Generate {num_npcs} unique NPCs for a market scenario.
        Themes: {', '.join(themes)}

        For each NPC, provide JSON:
        {{
            "npc_id": "unique_id",
            "name": "npc name",
            "job": "shopkeeper/guard/thief/merchant/broker",
            "personality": "brief description of character",
            "skills": {{"skill_name": 0-3}},
            "initial_trust": 0.0-1.0
        }}

        Create diverse, interesting characters. Return a valid JSON array only.
        """
        raw = await self._call_api(prompt)
        try:
            return {"npcs": json.loads(raw)}
        except json.JSONDecodeError:
            return {"error": "Failed to parse response as JSON", "raw": raw}

    async def _generate_items(self, context: Dict[str, Any]) -> Dict:
        num_items = context.get("num_items", 15)

        prompt = f"""
        Generate {num_items} unique items for a fantasy market.
        Rarities: common, uncommon, rare, legendary

        For each item, provide JSON:
        {{
            "item_id": "unique_id",
            "name": "item name",
            "value": 10-1000,
            "rarity": "common/uncommon/rare/legendary",
            "description": "brief description",
            "tradeable": true/false
        }}

        Make items diverse (tools, gems, potions, artifacts, etc).
        Return a valid JSON array only.
        """
        raw = await self._call_api(prompt)
        try:
            return {"items": json.loads(raw)}
        except json.JSONDecodeError:
            return {"error": "Failed to parse response as JSON", "raw": raw}

    async def _generate_target_item(self, context: Dict[str, Any]) -> Dict:
        objective = context.get("objective", "acquire a precious item")

        prompt = f"""
        Create ONE valuable target item for a player to obtain.
        Objective: {objective}

        Return JSON:
        {{
            "item_id": "unique_id",
            "name": "item name",
            "base_value": 1000-5000,
            "difficulty": "easy/medium/hard",
            "why_valuable": "story reason it's valuable",
            "location": "which store has it",
            "proprietor_reaction": "how shop owner responds to interest"
        }}

        Make it interesting and desirable. Return valid JSON only.
        """
        raw = await self._call_api(prompt)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"error": "Failed to parse response as JSON", "raw": raw}

    # ------------------------------------------------------------------
    # Low-level API call
    # ------------------------------------------------------------------

    async def _call_api(self, prompt: str, system_message: str = None) -> str:
        if system_message is None:
            system_message = (
                "You are a creative game world builder. "
                "Generate detailed, JSON-formatted responses with no extra commentary."
            )
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                OPENAI_CHAT_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.9,
                    "max_tokens": 2000,
                },
            )
            data = response.json()
            if "choices" in data and data["choices"]:
                return data["choices"][0]["message"]["content"]
            raise Exception(f"Unexpected API response: {data}")


# ---------------------------------------------------------------------------


class OpenAINPCAdminAgent(NPCAdminAgentInterface):
    """
    NPC admin agent backed by the OpenAI chat completions API.

    Manages NPC behaviour, decisions, and player interactions.
    Maintains per-NPC conversation history in memory.
    """

    def __init__(
        self,
        agent_name: str,
        api_key: str,
        model: str = "gpt-4o",
    ):
        super().__init__(agent_name)
        self.api_key = api_key
        self.model = model
        self.npc_memories: Dict[str, list] = {}

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    OPENAI_MODELS_ENDPOINT,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                self.is_connected = response.status_code == 200
                return self.is_connected
        except Exception as e:
            print(f"[OpenAINPCAdminAgent] connect failed: {e}")
            return False

    async def disconnect(self) -> bool:
        self.is_connected = False
        return True

    # ------------------------------------------------------------------
    # Request dispatch
    # ------------------------------------------------------------------

    async def handle_request(self, request: AIAgentRequest) -> AIAgentResponse:
        try:
            dispatch = {
                "npc_decision":   self._npc_decision,
                "npc_perception": self._npc_perception,
                "npc_interaction": self._npc_interaction,
                "npc_reaction":   self._npc_reaction,
                "npc_idle":       self._npc_idle,
            }
            handler = dispatch.get(request.action)
            if handler is None:
                result = {"error": f"Unknown action: {request.action}"}
            else:
                result = await handler(request.context)

            return AIAgentResponse(
                request_id=request.request_id,
                agent_role=AgentRole.NPC_ADMIN,
                success=True,
                action=request.action,
                result=result,
                reasoning=f"Generated via OpenAI ({self.model})",
            )
        except Exception as e:
            return AIAgentResponse(
                request_id=request.request_id,
                agent_role=AgentRole.NPC_ADMIN,
                success=False,
                action=request.action,
                result={"error": str(e)},
            )

    # ------------------------------------------------------------------
    # NPC helpers
    # ------------------------------------------------------------------

    async def _npc_decision(self, context: Dict[str, Any]) -> Dict:
        npc_data = context.get("npc_data", {})
        situation = context.get("situation", "")

        prompt = f"""
        You are {npc_data.get('name', 'an NPC')}, a {npc_data.get('job', 'person')}.
        Personality: {npc_data.get('personality', 'neutral')}
        Skills: {npc_data.get('skills', {})}

        Current situation: {situation}

        What do you do? Respond with JSON only:
        {{
            "action": "move/speak/trade/refuse/etc",
            "message": "what you say or do",
            "reasoning": "why you chose this action",
            "emotion": "happy/suspicious/greedy/tired/etc"
        }}
        """
        raw = await self._call_api(prompt, system_message="You are an NPC in a fantasy market. Respond in JSON format only. Be creative, consistent, and stay in character.")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"error": "Failed to parse response", "raw": raw}

    async def _npc_perception(self, context: Dict[str, Any]) -> Dict:
        npc_data = context.get("npc_data", {})
        world_state = context.get("world_state", {})

        prompt = f"""
        You are {npc_data.get('name', 'an NPC')}, a {npc_data.get('job', 'person')}.

        What do you perceive in the current situation?
        World state: {json.dumps(world_state, indent=2)}

        Respond with JSON only:
        {{
            "observations": ["thing1", "thing2"],
            "threats": ["threat1"],
            "opportunities": ["opportunity1"],
            "interests": ["interest1"]
        }}
        """
        raw = await self._call_api(prompt, system_message="You are an NPC in a fantasy market. Respond in JSON format only.")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"error": "Failed to parse response", "raw": raw}

    async def _npc_interaction(self, context: Dict[str, Any]) -> Dict:
        npc_id = context.get("npc_id")
        npc_data = context.get("npc_data", {})
        player_action = context.get("player_action", "")
        player_message = context.get("player_message", "")

        if npc_id not in self.npc_memories:
            self.npc_memories[npc_id] = []

        history_text = "\n".join(
            f"Player: {m['player']}\nYou: {m['npc']}"
            for m in self.npc_memories[npc_id][-5:]  # last 5 exchanges
        )

        prompt = f"""
        You are {npc_data.get('name', 'an NPC')}, a {npc_data.get('job', 'person')}.
        Personality: {npc_data.get('personality', 'neutral')}

        Recent conversation:
        {history_text or '(none yet)'}

        A player approaches with action: {player_action}
        Player says: "{player_message}"

        How do you respond? Respond with JSON only:
        {{
            "response": "what you say back",
            "action": "what you do",
            "accepts": true/false,
            "trust_change": -1.0 to 1.0,
            "new_emotion": "emotional state",
            "next_move": "what happens next"
        }}
        """
        raw = await self._call_api(
            prompt,
            system_message="You are an NPC in a fantasy market. Respond in JSON format only. Be creative, consistent, and stay in character.",
        )
        try:
            interaction = json.loads(raw)
            self.npc_memories[npc_id].append(
                {"player": player_message, "npc": interaction.get("response", "")}
            )
            return interaction
        except json.JSONDecodeError:
            return {"error": "Failed to parse response", "raw": raw}

    async def _npc_reaction(self, context: Dict[str, Any]) -> Dict:
        """React to one or more player events near this NPC (Reaction Phase)."""
        npc_name  = context.get("npc_name", "NPC")
        npc_job   = context.get("npc_job", "unknown")
        npc_pers  = context.get("npc_personality", "neutral")
        npc_trust = context.get("npc_trust", 0.5)
        npc_hp    = context.get("npc_health", 100)
        npc_maxhp = context.get("npc_max_health", 100)
        npc_status = context.get("npc_status", "alive")
        events    = context.get("events", [])
        events_desc = "; ".join(
            f"{ev.get('type','event')}: {ev.get('data',{})}" for ev in events
        )
        prompt = (
            f"You are {npc_name}, a {npc_job}. Personality: {npc_pers}. "
            f"Current trust in the player: {npc_trust:.1f}/1.0. "
            f"Health: {npc_hp}/{npc_maxhp}. Status: {npc_status}.\n\n"
            f"Events that just occurred near you: {events_desc}\n\n"
            "How does this change your attitude? Return JSON ONLY:\n"
            "{\n"
            '  "trust_delta": <float -0.3 to 0.3>,\n'
            '  "mood": "<one word>",\n'
            '  "last_ai_message": "<brief in-character reaction, 1 sentence>",\n'
            '  "health_delta": <optional float, only include for violent/aggressive events>\n'
            "}"
        )
        raw = await self._call_api(
            prompt,
            system_message="You are a reactive NPC. Return only valid JSON, no commentary.",
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"trust_delta": 0.0}

    async def _npc_idle(self, context: Dict[str, Any]) -> Dict:
        """Autonomous idle/patrol behaviour (Autonomous Phase, every ~30 ticks)."""
        npc_name = context.get("npc_name", "NPC")
        npc_job  = context.get("npc_job", "unknown")
        npc_pers = context.get("npc_personality", "neutral")
        npc_mood = context.get("npc_mood", "neutral")
        turn     = context.get("world_turn", 0)
        prompt = (
            f"You are {npc_name}, a {npc_job}. Personality: {npc_pers}. "
            f"Current mood: {npc_mood}. World turn: {turn}.\n\n"
            "What are you doing right now? Return JSON ONLY:\n"
            "{\n"
            '  "mood": "<one word>",\n'
            '  "last_ai_message": "<brief in-character idle action, 1 sentence>"\n'
            "}"
        )
        raw = await self._call_api(
            prompt,
            system_message="You are an NPC going about their day. Return only valid JSON, no commentary.",
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    # ------------------------------------------------------------------
    # Low-level API call
    # ------------------------------------------------------------------

    async def _call_api(self, prompt: str, system_message: str = "You are a helpful assistant. Respond in JSON format only.") -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                OPENAI_CHAT_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.85,
                    "max_tokens": 500,
                },
            )
            data = response.json()
            if "choices" in data and data["choices"]:
                return data["choices"][0]["message"]["content"]
            raise Exception(f"Unexpected API response: {data}")
