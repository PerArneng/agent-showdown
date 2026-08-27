from __future__ import annotations

import queue
from collections.abc import Callable

from agent_showdown.interfaces.game import GameEvent


class QueueEventSubscription:
    """Edge module. One reader's queue, and the blocking wait that feeds it."""

    def __init__(self, on_close: Callable[[QueueEventSubscription], None]) -> None:
        self._queue: queue.Queue[GameEvent] = queue.Queue()
        self._on_close = on_close
        self._closed = False

    def offer(self, event: GameEvent) -> None:
        """Called by the channel. Dropped silently once closed."""
        if not self._closed:
            self._queue.put(event)

    def poll(self, timeout_seconds: float) -> GameEvent | None:
        try:
            return self._queue.get(timeout=timeout_seconds)
        except queue.Empty:
            return None

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._on_close(self)
