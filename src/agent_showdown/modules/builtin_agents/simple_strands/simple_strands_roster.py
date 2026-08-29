from collections.abc import Sequence

from agent_showdown.interfaces.config import AgentConfig
from agent_showdown.interfaces.game import Player
from agent_showdown.modules.builtin_agents.simple_strands.simple_strands_player import (
    SimpleStrandsPlayer,
)
from agent_showdown.modules.builtin_agents.simple_strands.strands_turn_planner import (
    StrandsTurnPlanner,
)


class SimpleStrandsRoster:
    """Fans a list of agent configs out into one contestant per endpoint.

    Each config gets its own planner, so two contestants can run the same code against
    two different OpenAI-compatible servers.
    """

    def __init__(self, configs: Sequence[AgentConfig]) -> None:
        self._configs = list(configs)

    def create_players(self) -> Sequence[Player]:
        return [
            SimpleStrandsPlayer(config.name, StrandsTurnPlanner(config), config.max_actions)
            for config in self._configs
        ]
