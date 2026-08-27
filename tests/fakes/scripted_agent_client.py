from collections.abc import Sequence

from agent_showdown.interfaces.agent_client import AgentClientError


class ScriptedAgentClient:
    """Test fake. Replays canned replies instead of reaching a remote agent."""

    def __init__(self, replies: Sequence[str] = (), fails_with: str | None = None) -> None:
        self._replies = list(replies)
        self._fails_with = fails_with
        self._next = 0
        self.sent: list[tuple[str, str]] = []

    def send(self, context_id: str, payload: str) -> str:
        self.sent.append((context_id, payload))
        if self._fails_with is not None:
            raise AgentClientError(self._fails_with)
        reply = self._replies[self._next % len(self._replies)]
        self._next += 1
        return reply

    def payloads(self) -> list[str]:
        """Just the payloads, for asserting on what the game told the agent."""
        return [payload for _, payload in self.sent]
