from typing import Protocol


class AgentClient(Protocol):
    """Talks to a remote agent. Implementations that reach the network are edge modules."""

    def send(self, context_id: str, payload: str) -> str:
        """Send `payload` to the remote agent and block until it replies.

        `context_id` threads a multi-turn conversation, so the agent can remember what it
        was told earlier. Raises `AgentClientError` if the exchange fails.
        """
        ...
