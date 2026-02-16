"""
Game scenarios - predefined puzzle/challenge templates

Each scenario is a self-contained game variant that agents can play
"""

from typing import Dict, List
from dataclasses import dataclass

@dataclass
class Scenario:
    """A game scenario definition"""
    scenario_id: str
    name: str
    description: str
    rules: str
    objectives: List[str]
    max_turns: int
    difficulty: str  # easy, medium, hard
    world_width: int
    world_height: int
    starting_position: tuple
    exit_position: tuple
    traps: List[Dict]  # {'id': 'trap_1', 'x': 100, 'y': 100, 'radius': 30, 'damage': 10}

# Example scenarios
SCENARIO_MAZE = Scenario(
    scenario_id="maze_01",
    name="Simple Maze",
    description="Navigate through a simple maze to reach the exit without hitting traps",
    rules="""
    - Move in 4 directions (up, down, left, right)
    - Each move costs 1 turn
    - Hitting a trap ends the game
    - Goal: Reach the exit position
    """,
    objectives=[
        "Reach the exit without hitting any traps",
        "Complete in minimum turns",
        "Demonstrate efficient pathfinding"
    ],
    max_turns=50,
    difficulty="easy",
    world_width=400,
    world_height=300,
    starting_position=(50, 50),
    exit_position=(350, 250),
    traps=[
        {'id': 'trap_1', 'x': 100, 'y': 100, 'radius': 30, 'damage': 10},
        {'id': 'trap_2', 'x': 200, 'y': 150, 'radius': 30, 'damage': 10},
        {'id': 'trap_3', 'x': 150, 'y': 250, 'radius': 30, 'damage': 10},
    ]
)

SCENARIO_TREASURE = Scenario(
    scenario_id="treasure_01",
    name="Treasure Hunt",
    description="Collect items strategically while avoiding traps",
    rules="""
    - Observe your surroundings
    - Items grant points (gold: 10pts, gems: 20pts, keys: 5pts)
    - Traps deal damage
    - Goal: Collect maximum points and escape
    """,
    objectives=[
        "Maximize points collected",
        "Avoid traps",
        "Escape the arena within turn limit"
    ],
    max_turns=100,
    difficulty="medium",
    world_width=500,
    world_height=400,
    starting_position=(50, 50),
    exit_position=(450, 350),
    traps=[
        {'id': 'trap_1', 'x': 150, 'y': 150, 'radius': 40, 'damage': 15},
        {'id': 'trap_2', 'x': 300, 'y': 200, 'radius': 40, 'damage': 15},
        {'id': 'trap_3', 'x': 250, 'y': 300, 'radius': 40, 'damage': 15},
    ]
)

SCENARIO_PUZZLE = Scenario(
    scenario_id="puzzle_01",
    name="Logic Puzzle",
    description="Solve puzzles through careful observation and logical reasoning",
    rules="""
    - Observe patterns in environment
    - Some tiles are safe, others are dangerous
    - Pattern: Lines of 3 similar symbols are safe
    - Goal: Cross to the other side
    """,
    objectives=[
        "Identify safe path using logic",
        "Cross the puzzle area",
        "Demonstrate reasoning ability"
    ],
    max_turns=40,
    difficulty="hard",
    world_width=400,
    world_height=300,
    starting_position=(50, 150),
    exit_position=(350, 150),
    traps=[
        {'id': 'trap_1', 'x': 120, 'y': 150, 'radius': 20, 'damage': 20},
        {'id': 'trap_2', 'x': 180, 'y': 150, 'radius': 20, 'damage': 20},
        {'id': 'trap_3', 'x': 240, 'y': 150, 'radius': 20, 'damage': 20},
        {'id': 'trap_4', 'x': 300, 'y': 150, 'radius': 20, 'damage': 20},
    ]
)

class ScenarioManager:
    """Manages available scenarios"""
    
    SCENARIOS = {
        'maze_01': SCENARIO_MAZE,
        'treasure_01': SCENARIO_TREASURE,
        'puzzle_01': SCENARIO_PUZZLE,
    }
    
    @classmethod
    def get_scenario(cls, scenario_id: str) -> Scenario:
        """Get a scenario by ID"""
        return cls.SCENARIOS.get(scenario_id)
    
    @classmethod
    def get_all_scenarios(cls) -> List[Scenario]:
        """Get all available scenarios"""
        return list(cls.SCENARIOS.values())
    
    @classmethod
    def scenario_exists(cls, scenario_id: str) -> bool:
        """Check if scenario exists"""
        return scenario_id in cls.SCENARIOS
