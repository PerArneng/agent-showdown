from collections.abc import Sequence

from agent_showdown.interfaces.game import GameEvent


class ScriptedEventSubscription:
    """Test fake. Replays a canned sequence, where `None` stands for a poll that timed out."""

    def __init__(self, events: Sequence[GameEvent | None]) -> None:
        self._events = list(events)
        self.closed = False
        self.timeouts: list[float] = []

    def poll(self, timeout_seconds: float) -> GameEvent | None:
        self.timeouts.append(timeout_seconds)
        return self._events.pop(0) if self._events else None

    def close(self) -> None:
        self.closed = True
