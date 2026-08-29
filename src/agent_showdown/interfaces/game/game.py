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
        """Play up to `max_rounds` rounds, asking every living player for a turn in each.

        Ends early once at most one robot is left standing, or once `stop` has been called.
        """
        ...

    def stop(self) -> None:
        """Ask the match to end at the next turn boundary. Safe to call before it starts."""
        ...
