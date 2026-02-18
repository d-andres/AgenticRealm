"""
Game scenario TEMPLATES - not hardcoded instances

Each template defines the rules, constraints, and success criteria for a scenario type.
When a scenario instance is created, an AI model generates unique:
- Store names, locations, proprietor personalities
- NPC characters, jobs, skills, relationships
- Item inventories and pricing strategies
- World layout and environmental details

This allows each scenario instance to be procedurally generated and unique.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

class ActionType(Enum):
    """Possible player actions (can be extended)"""
    MOVE = "move"
    TALK = "talk"
    NEGOTIATE = "negotiate"
    BUY = "buy"
    HIRE = "hire"
    STEAL = "steal"
    TRADE = "trade"
    OBSERVE = "observe"

@dataclass
class ScenarioTemplate:
    """
    Template defining a scenario type and generation constraints.
    
    When this template is used to create a scenario instance,
    an AI model generates all specific details (stores, NPCs, items) 
    based on these parameters.
    """
    scenario_id: str
    name: str
    description: str
    rules: str
    objectives: List[str]
    
    # Generation constraints
    difficulty: str  # easy, medium, hard
    world_width: int
    world_height: int
    max_turns: int
    starting_gold: int
    
    # Scenario-type specific constraints
    num_stores: tuple  # (min, max) stores to generate
    num_npcs: tuple    # (min, max) NPCs to generate
    num_items: tuple   # (min, max) unique items to generate
    
    # NPC job types that can appear
    possible_npc_jobs: List[str]  # ["shopkeeper", "guard", "thief", "merchant", "broker", ...]
    
    # Item rarity distribution
    item_rarity_distribution: Dict[str, float]  # {"common": 0.6, "uncommon": 0.25, "rare": 0.1, ...}
    
    # Action types allowed in this scenario
    allowed_actions: List[ActionType] = field(default_factory=list)
    
    # Scene/environment themes (guides AI generation)
    environment_themes: List[str] = field(default_factory=list)  # ["urban", "market", "shady", ...]
    
    # Success criteria guidance (for AI to understand when player wins)
    success_metrics: Dict[str, Any] = field(default_factory=dict)  # e.g., {"obtain_item": True, "max_cost": 1000}


# MARKET SQUARE TEMPLATE
# AI models will generate a unique market instance from this template each time
SCENARIO_MARKET_SQUARE_TEMPLATE = ScenarioTemplate(
    scenario_id="market_square",
    name="Dynamic Market Acquisition",
    description="""
    An AI-generated market scenario with unique stores, NPCs, and items each time.
    Your goal: acquire a valuable item through various means.
    
    The specific stores, prices, NPCs, and their personalities are generated uniquely
    for each scenario instance, so no two markets are the same.
    
    You can:
    - Negotiate with shopkeepers to earn trust and reduce prices
    - Hire NPCs to assist (thieves, merchants, brokers)
    - Trade items to accumulate wealth
    - Attempt theft (risky - success depends on guards and items present)
    - Gather information to make strategic decisions
    """,
    rules="""
    Core Rules:
    - Start with limited gold provided by the scenario
    - Each action consumes 1 turn
    - NPCs are System AI Agents with personalities and decision logic
    - Trust relationships affect NPC responses and pricing
    - Theft attempts have success probabilities based on guards and your items
    - Trading requires both parties to benefit
    - Prices are dynamic based on supply and NPC relationships
    
    Allowed Actions:
    - move(x, y) - navigate the world
    - observe() - assess current state, visible NPCs, nearby stores
    - talk(npc_id) - initiate conversation with an NPC
    - negotiate(npc_id, item_id, offered_price) - haggle for better deals
    - buy(store_id, item_id) - purchase an item
    - hire(npc_id) - contract an NPC (costs gold)
    - steal(store_id, item_id) - attempt theft (success depends on circumstances)
    - trade(npc_id, give_item_id, receive_item_id) - propose a trade
    """,
    objectives=[
        "Obtain the target item specified in the scenario",
        "Minimize gold spent (efficiency bonus)",
        "Discover optimal solution path",
        "Build strategic relationships with key NPCs"
    ],
    difficulty="medium",
    world_width=800,
    world_height=600,
    max_turns=150,
    starting_gold=500,
    
    # Generation constraints
    num_stores=(3, 6),  # Generate 3-6 stores
    num_npcs=(4, 8),    # Generate 4-8 NPCs
    num_items=(10, 20), # Generate 10-20 unique items across all stores
    
    possible_npc_jobs=[
        "shopkeeper",
        "guard",
        "thief",
        "merchant",
        "information_broker",
        "bouncer",
        "wealthy_collector",
        "fence"
    ],
    
    item_rarity_distribution={
        "common": 0.5,
        "uncommon": 0.3,
        "rare": 0.15,
        "legendary": 0.05
    },
    
    allowed_actions=[
        ActionType.MOVE,
        ActionType.TALK,
        ActionType.NEGOTIATE,
        ActionType.BUY,
        ActionType.HIRE,
        ActionType.STEAL,
        ActionType.TRADE,
        ActionType.OBSERVE,
    ],
    
    environment_themes=["urban_market", "merchant_district", "bustling", "diverse_goods"],
    
    success_metrics={
        "obtain_target_item": True,
        "preferred_gold_spent": "500-1500",  # Efficiency bonus if in this range
        "multiple_solution_paths": True,     # Should have multiple ways to win
    }
)


class ScenarioManager:
    """Manages available scenario templates (not instances)"""
    
    TEMPLATES = {
        'market_square': SCENARIO_MARKET_SQUARE_TEMPLATE,
        # Future templates:
        # 'heist_planning': SCENARIO_HEIST_TEMPLATE,
        # 'negotiation_chain': SCENARIO_NEGOTIATION_TEMPLATE,
    }
    
    @classmethod
    def get_template(cls, scenario_id: str) -> Optional[ScenarioTemplate]:
        """Get a scenario template by ID"""
        return cls.TEMPLATES.get(scenario_id)
    
    @classmethod
    def get_all_templates(cls) -> List[ScenarioTemplate]:
        """Get all available scenario templates"""
        return list(cls.TEMPLATES.values())
    
    @classmethod
    def template_exists(cls, scenario_id: str) -> bool:
        """Check if template exists"""
        return scenario_id in cls.TEMPLATES
