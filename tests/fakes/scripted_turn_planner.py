from collections.abc import Sequence

from agent_showdown.interfaces.agent_client import AgentClientError
from agent_showdown.interfaces.game import PlayerTurn


class ScriptedTurnPlanner:
    """Test fake. Replays canned turns instead of calling a model."""

    def __init__(
        self, turns: Sequence[PlayerTurn] = (), fails_with: str | None = None
    ) -> None:
        self._turns = list(turns)
        self._fails_with = fails_with
        self._next = 0
        self.prompts: list[str] = []

    def plan(self, prompt: str) -> PlayerTurn:
        self.prompts.append(prompt)
        if self._fails_with is not None:
            raise AgentClientError(self._fails_with)
        turn = self._turns[self._next % len(self._turns)]
        self._next += 1
        return turn
