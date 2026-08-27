from typing import Protocol

from agent_showdown.interfaces.game import GameEvent


class EventSubscription(Protocol):
    """One reader's view of a channel. Closed by whoever opened it."""

    def poll(self, timeout_seconds: float) -> GameEvent | None:
        """Return the next event, or `None` if none arrived within the timeout."""
        ...

    def close(self) -> None:
        """Stop receiving. Safe to call more than once."""
        ...
