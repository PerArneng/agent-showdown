import queue
from collections.abc import Callable

from agent_showdown.interfaces.game import GameEvent


class QueueEventSubscription:
    """Edge module. One reader's queue, and the blocking wait on it.

    Its public surface is exactly `EventSubscription`: the channel fills the queue, and nothing
    reaches in here to do it.
    """

    def __init__(self, events: queue.Queue[GameEvent], on_close: Callable[[], None]) -> None:
        self._events = events
        self._on_close = on_close
        self._closed = False

    def poll(self, timeout_seconds: float) -> GameEvent | None:
        try:
            return self._events.get(timeout=timeout_seconds)
        except queue.Empty:
            return None

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._on_close()
