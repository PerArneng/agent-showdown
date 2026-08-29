from agent_showdown.interfaces.config import AgentConfig
from agent_showdown.interfaces.game import Player
from agent_showdown.modules.builtin_agents.simple_strands.simple_strands_player import (
    SimpleStrandsPlayer,
)
from agent_showdown.modules.builtin_agents.simple_strands.strands_turn_planner import (
    StrandsTurnPlanner,
)


class SimpleStrandsAgentFactory:
    """One contestant per config, each with its own planner and therefore its own endpoint."""

    def create(self, config: AgentConfig) -> Player:
        return SimpleStrandsPlayer(
            config.name, StrandsTurnPlanner(config), config.max_actions
        )
