from agent_showdown.interfaces.event_channel import EventSubscription
from agent_showdown.interfaces.game import GameEvent


class InMemoryEventChannel:
    """Test fake. Keeps every published event instead of handing it to a reader."""

    def __init__(self) -> None:
        self.published: list[GameEvent] = []

    def publish(self, event: GameEvent) -> None:
        self.published.append(event)

    def subscribe(self) -> EventSubscription:
        raise NotImplementedError("Tests read `published` directly.")
