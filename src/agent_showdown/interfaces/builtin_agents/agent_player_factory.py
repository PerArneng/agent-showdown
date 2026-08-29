from typing import Protocol

from agent_showdown.interfaces.config import AgentConfig
from agent_showdown.interfaces.game import Player


class AgentPlayerFactory(Protocol):
    """Builds one contestant from one agent configuration.

    The same description a config file carries is what a robot joining over HTTP sends, so both
    routes into the arena go through here and neither can drift from the other.
    """

    def create(self, config: AgentConfig) -> Player:
        """Return a player that plays through the endpoint the config names."""
        ...
