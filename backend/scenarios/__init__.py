"""
Scenarios package

Sub-modules:
  templates  — ScenarioTemplate dataclass, ActionType enum, ScenarioManager
  generator  — AI-driven ScenarioGenerator and generated-world dataclasses
  instances  — Always-on ScenarioInstance worlds and their manager

Import `ScenarioManager` or `ScenarioTemplate` from this package directly.
Import `scenario_instance_manager` from `scenarios.instances` to avoid
triggering DB init as a side-effect of unrelated imports.
"""

from scenarios.templates import ScenarioTemplate, ActionType, ScenarioManager

__all__ = [
    'ScenarioTemplate',
    'ActionType',
    'ScenarioManager',
]
