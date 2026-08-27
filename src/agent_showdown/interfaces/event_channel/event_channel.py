from typing import Protocol

from agent_showdown.interfaces.event_channel.event_subscription import EventSubscription
from agent_showdown.interfaces.game import GameEvent


class EventChannel(Protocol):
    """Carries game events from whoever plays the game to whoever is watching."""

    def publish(self, event: GameEvent) -> None:
        """Hand `event` to every open subscription. Never blocks the publisher."""
        ...

    def subscribe(self) -> EventSubscription:
        """Open a new subscription. It only sees events published from now on."""
        ...
