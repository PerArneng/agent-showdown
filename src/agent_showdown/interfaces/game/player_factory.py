from typing import Protocol

from agent_showdown.interfaces.game.player import Player


class PlayerFactory(Protocol):
    """Hands out a fresh player, so callers never construct one themselves."""

    def create(self, name: str) -> Player:
        """Return a new player known by `name`."""
        ...
