import queue
import threading

from agent_showdown.interfaces.game import GameEvent
from agent_showdown.modules.event_channel.queue_event_subscription import QueueEventSubscription


class QueueEventChannel:
    """Edge module. Where the thread playing the game meets the threads serving requests.

    Owns a queue per subscriber and fans every event out to all of them, so a slow reader cannot
    stall the game and a browser that goes away takes its queue with it.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._queues: list[queue.Queue[GameEvent]] = []

    def publish(self, event: GameEvent) -> None:
        with self._lock:
            queues = list(self._queues)
        for events in queues:
            events.put(event)

    def subscribe(self) -> QueueEventSubscription:
        events: queue.Queue[GameEvent] = queue.Queue()
        with self._lock:
            self._queues.append(events)
        return QueueEventSubscription(events, on_close=lambda: self._drop(events))

    def _drop(self, events: queue.Queue[GameEvent]) -> None:
        with self._lock:
            if events in self._queues:
                self._queues.remove(events)
