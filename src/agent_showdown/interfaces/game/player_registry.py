from typing import Protocol

from agent_showdown.interfaces.game.player import Player


class PlayerRegistry(Protocol):
    """Who is currently in the arena. Contestants come and go while it keeps playing.

    The arena consults this before every match, so a robot that joins mid-match sits down for the
    next one. An empty registry is what pauses the arena, and a registration is what wakes it.
    """

    def register(self, player: Player) -> None:
        """Add a contestant. Wakes a paused arena."""
        ...

    def unregister(self, name: str) -> bool:
        """Remove the contestant known by `name`. False if nobody was."""
        ...

    def players(self) -> tuple[Player, ...]:
        """Everyone currently registered, in the order they joined."""
        ...

    def await_players(self, timeout: float) -> bool:
        """Block until somebody is registered, or `timeout` passes. True if anybody is.

        Bounded rather than endless so a waiting arena can still notice it is being shut down.
        """
        ...
