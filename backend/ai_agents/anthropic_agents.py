"""
Anthropic AI Agents - Concrete implementations using the Anthropic API.

These are provider-specific implementations of the AIAgent interfaces.
To use OpenAI instead, see openai_agents.py or implement your own using
the base classes in interfaces.py.

Supported models: claude-opus-4-5, claude-sonnet-4-5, claude-haiku-4-5, etc.
"""

import json
from typing import Dict, Any, List
import httpx

from .interfaces import (
    AIAgentRequest,
    AIAgentResponse,
    AgentRole,
    ScenarioGeneratorAgentInterface,
    NPCAdminAgentInterface,
)

ANTHROPIC_MESSAGES_ENDPOINT = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


class AnthropicScenarioGeneratorAgent(ScenarioGeneratorAgentInterface):
    """
    Scenario generator backed by the Anthropic messages API (Claude).

    Supported models: claude-opus-4-5, claude-sonnet-4-5, claude-haiku-4-5
    """

    def __init__(
        self,
        agent_name: str,
        api_key: str,
        model: str = "claude-sonnet-4-5",
    ):
        super().__init__(agent_name)
        self.api_key = api_key
        self.model = model

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> bool:
        """Validate API key by sending a minimal test message."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    ANTHROPIC_MESSAGES_ENDPOINT,
                    headers=self._headers(),
                    json={
                        "model": self.model,
                        "max_tokens": 16,
                        "messages": [{"role": "user", "content": "ping"}],
                    },
                )
                # 200 = connected; 401 = bad key; other 4xx = unexpected
                self.is_connected = response.status_code == 200
                return self.is_connected
        except Exception as e:
            print(f"[AnthropicScenarioGeneratorAgent] connect failed: {e}")
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
                reasoning=f"Generated via Anthropic ({self.model})",
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

        Make each store unique and interesting. Return a valid JSON array only — no commentary.
        """
        raw = await self._call_api(
            prompt,
            system="You are a creative game world builder. Return only valid JSON arrays with no extra commentary or markdown.",
        )
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

        Create diverse, interesting characters. Return a valid JSON array only — no commentary.
        """
        raw = await self._call_api(
            prompt,
            system="You are a creative game world builder. Return only valid JSON arrays with no extra commentary or markdown.",
        )
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
        Return a valid JSON array only — no commentary.
        """
        raw = await self._call_api(
            prompt,
            system="You are a creative game world builder. Return only valid JSON arrays with no extra commentary or markdown.",
        )
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

        Make it interesting and desirable. Return valid JSON only — no commentary.
        """
        raw = await self._call_api(
            prompt,
            system="You are a creative game world builder. Return only valid JSON with no extra commentary or markdown.",
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"error": "Failed to parse response as JSON", "raw": raw}

    async def _npc_reaction(self, context: Dict[str, Any]) -> Dict:
        """React to one or more player events that just occurred near this NPC.

        Engine calls this during the Reaction Phase of each tick.
        Returns trust_delta, mood, and an optional last_ai_message.
        """
        npc_name = context.get("npc_name", "NPC")
        npc_job  = context.get("npc_job", "unknown")
        npc_pers = context.get("npc_personality", "neutral")
        npc_trust = context.get("npc_trust", 0.5)
        events   = context.get("events", [])
        events_desc = "; ".join(
            f"{ev.get('type','event')}: {ev.get('data',{})}" for ev in events
        )
        prompt = (
            f"You are {npc_name}, a {npc_job}. Personality: {npc_pers}. "
            f"Current trust in the player: {npc_trust:.1f}/1.0.\n\n"
            f"The following events just happened nearby: {events_desc}\n\n"
            "How does this change your attitude toward the player? "
            "Return JSON ONLY:\n"
            "{\n"
            '  "trust_delta": <float -0.3 to 0.3>,\n'
            '  "mood": "<one word>",\n'
            '  "last_ai_message": "<brief in-character reaction, 1 sentence>"\n'
            "}"
        )
        raw = await self._call_api(
            prompt,
            system="You are a reactive NPC. Return only valid JSON, no commentary.",
            max_tokens=150,
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"trust_delta": 0.0}

    async def _npc_idle(self, context: Dict[str, Any]) -> Dict:
        """Generate autonomous idle/patrol behaviour for an NPC.

        Engine calls this during the Autonomous Phase (every ~30 ticks).
        Returns optional mood update and/or last_ai_message.
        """
        npc_name = context.get("npc_name", "NPC")
        npc_job  = context.get("npc_job", "unknown")
        npc_pers = context.get("npc_personality", "neutral")
        npc_mood = context.get("npc_mood", "neutral")
        turn     = context.get("world_turn", 0)
        prompt = (
            f"You are {npc_name}, a {npc_job}. Personality: {npc_pers}. "
            f"Current mood: {npc_mood}. World turn: {turn}.\n\n"
            "What are you doing right now? "
            "Return JSON ONLY:\n"
            "{\n"
            '  "mood": "<one word>",\n'
            '  "last_ai_message": "<brief in-character idle action, 1 sentence>"\n'
            "}"
        )
        raw = await self._call_api(
            prompt,
            system="You are an NPC going about their day. Return only valid JSON, no commentary.",
            max_tokens=100,
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    # ------------------------------------------------------------------
    # Low-level API call
    # ------------------------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

    async def _call_api(
        self,
        prompt: str,
        system: str = "You are a helpful assistant. Return only valid JSON.",
        max_tokens: int = 2000,
    ) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                ANTHROPIC_MESSAGES_ENDPOINT,
                headers=self._headers(),
                json={
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "system": system,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            data = response.json()
            if "content" in data and data["content"]:
                return data["content"][0]["text"]
            raise Exception(f"Unexpected API response: {data}")


# ---------------------------------------------------------------------------


class AnthropicNPCAdminAgent(NPCAdminAgentInterface):
    """
    NPC admin agent backed by the Anthropic messages API (Claude).

    Manages NPC behaviour, decisions, and player interactions.
    Maintains per-NPC conversation history using Anthropic's multi-turn format.
    """

    def __init__(
        self,
        agent_name: str,
        api_key: str,
        model: str = "claude-sonnet-4-5",
    ):
        super().__init__(agent_name)
        self.api_key = api_key
        self.model = model
        # npc_memories[npc_id] = list of {"role": "user"|"assistant", "content": str}
        self.npc_memories: Dict[str, List[Dict[str, str]]] = {}

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    ANTHROPIC_MESSAGES_ENDPOINT,
                    headers=self._headers(),
                    json={
                        "model": self.model,
                        "max_tokens": 16,
                        "messages": [{"role": "user", "content": "ping"}],
                    },
                )
                self.is_connected = response.status_code == 200
                return self.is_connected
        except Exception as e:
            print(f"[AnthropicNPCAdminAgent] connect failed: {e}")
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
                reasoning=f"Generated via Anthropic ({self.model})",
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

        system = (
            f"You are {npc_data.get('name', 'an NPC')}, "
            f"a {npc_data.get('job', 'person')} in a fantasy market. "
            f"Personality: {npc_data.get('personality', 'neutral')}. "
            "Respond in JSON format only. Stay in character at all times."
        )
        prompt = f"""
        Current situation: {situation}

        What do you do? Respond with JSON only:
        {{
            "action": "move/speak/trade/refuse/etc",
            "message": "what you say or do",
            "reasoning": "why you chose this action",
            "emotion": "happy/suspicious/greedy/tired/etc"
        }}
        """
        raw = await self._call_api(prompt, system=system, max_tokens=300)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"error": "Failed to parse response", "raw": raw}

    async def _npc_perception(self, context: Dict[str, Any]) -> Dict:
        npc_data = context.get("npc_data", {})
        world_state = context.get("world_state", {})

        system = (
            f"You are {npc_data.get('name', 'an NPC')}, "
            f"a {npc_data.get('job', 'person')} in a fantasy market. "
            "Respond in JSON format only."
        )
        prompt = f"""
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
        raw = await self._call_api(prompt, system=system, max_tokens=300)
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

        # Build multi-turn messages from stored history (last 5 exchanges = 10 turns)
        history: List[Dict[str, str]] = self.npc_memories[npc_id][-10:]

        # Append the new player turn
        user_turn = (
            f"Player action: {player_action}\nPlayer says: \"{player_message}\"\n\n"
            "Respond with JSON only:\n"
            "{\n"
            '  "response": "what you say back",\n'
            '  "action": "what you do",\n'
            '  "accepts": true/false,\n'
            '  "trust_change": -1.0 to 1.0,\n'
            '  "new_emotion": "emotional state",\n'
            '  "next_move": "what happens next"\n'
            "}"
        )
        messages = history + [{"role": "user", "content": user_turn}]

        system = (
            f"You are {npc_data.get('name', 'an NPC')}, "
            f"a {npc_data.get('job', 'person')} in a fantasy market. "
            f"Personality: {npc_data.get('personality', 'neutral')}. "
            "Respond in JSON format only. Be creative, consistent, and stay in character."
        )

        raw = await self._call_api_messages(messages, system=system, max_tokens=400)
        try:
            interaction = json.loads(raw)
            # Store exchange in history using Anthropic's turn format
            self.npc_memories[npc_id].extend([
                {"role": "user", "content": user_turn},
                {"role": "assistant", "content": raw},
            ])
            return interaction
        except json.JSONDecodeError:
            return {"error": "Failed to parse response", "raw": raw}

    # ------------------------------------------------------------------
    # Low-level API calls
    # ------------------------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

    async def _call_api(
        self,
        prompt: str,
        system: str = "You are a helpful assistant. Return only valid JSON.",
        max_tokens: int = 500,
    ) -> str:
        """Single-turn API call."""
        return await self._call_api_messages(
            messages=[{"role": "user", "content": prompt}],
            system=system,
            max_tokens=max_tokens,
        )

    async def _call_api_messages(
        self,
        messages: List[Dict[str, str]],
        system: str,
        max_tokens: int = 500,
    ) -> str:
        """Multi-turn API call using the full messages list."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                ANTHROPIC_MESSAGES_ENDPOINT,
                headers=self._headers(),
                json={
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "system": system,
                    "messages": messages,
                },
            )
            data = response.json()
            if "content" in data and data["content"]:
                return data["content"][0]["text"]
            raise Exception(f"Unexpected API response: {data}")
