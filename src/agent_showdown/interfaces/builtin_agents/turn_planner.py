from typing import Protocol

from agent_showdown.interfaces.game import PlayerTurn


class TurnPlanner(Protocol):
    """Turns a prompt into a validated plan. The model call lives behind this."""

    def plan(self, prompt: str) -> PlayerTurn:
        """Return the turn the model planned, or raise `AgentClientError`."""
        ...
