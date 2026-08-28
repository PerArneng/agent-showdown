from collections.abc import Sequence
from typing import Protocol

from agent_showdown.interfaces.game import Player


class AgentRoster(Protocol):
    """The built-in contestants a run fields. Each one names itself."""

    def create_players(self) -> Sequence[Player]:
        """Return one fresh player per configured agent, in configuration order."""
        ...
