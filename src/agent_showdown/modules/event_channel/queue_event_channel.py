import threading

from agent_showdown.interfaces.game import GameEvent
from agent_showdown.modules.event_channel.queue_event_subscription import QueueEventSubscription


class QueueEventChannel:
    """Edge module. Where the thread playing the game meets the threads serving requests.

    Fans every event out to a queue per subscriber, so a slow reader cannot stall the game and a
    browser that goes away takes its queue with it.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscriptions: list[QueueEventSubscription] = []

    def publish(self, event: GameEvent) -> None:
        with self._lock:
            subscriptions = list(self._subscriptions)
        for subscription in subscriptions:
            subscription.offer(event)

    def subscribe(self) -> QueueEventSubscription:
        subscription = QueueEventSubscription(on_close=self._remove)
        with self._lock:
            self._subscriptions.append(subscription)
        return subscription

    def _remove(self, subscription: QueueEventSubscription) -> None:
        with self._lock:
            if subscription in self._subscriptions:
                self._subscriptions.remove(subscription)
