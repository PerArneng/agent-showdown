from collections.abc import Sequence

from agent_showdown.interfaces.builtin_agents import AgentPlayerFactory
from agent_showdown.interfaces.config import AgentConfig
from agent_showdown.interfaces.game import Player


class SimpleStrandsRoster:
    """Fans a list of agent configs out into one contestant per endpoint.

    Each config gets its own planner, so two contestants can run the same code against
    two different OpenAI-compatible servers.
    """

    def __init__(self, configs: Sequence[AgentConfig], factory: AgentPlayerFactory) -> None:
        self._configs = list(configs)
        self._factory = factory

    def create_players(self) -> Sequence[Player]:
        return [self._factory.create(config) for config in self._configs]
