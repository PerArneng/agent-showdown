from typing import Protocol

from agent_showdown.interfaces.game.game_listener import GameListener
from agent_showdown.interfaces.game.player import Player
from agent_showdown.interfaces.game.position import Position


class Game(Protocol):
    """One match on one board. Listeners are added first so joins are observed."""

    def add_listener(self, listener: GameListener) -> None:
        """Add a listener. Every event fans out to all of them, in registration order."""
        ...

    def register_player(self, player: Player, position: Position) -> None:
        """Place a player on the board and emit `player_joined`."""
        ...

    def start(self, max_rounds: int) -> None:
        """Play up to `max_rounds` rounds, asking every player for a turn in each."""
        ...
