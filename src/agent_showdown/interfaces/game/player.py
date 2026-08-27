from typing import Protocol

from agent_showdown.interfaces.game.game_view import GameView
from agent_showdown.interfaces.game.player_turn import PlayerTurn


class Player(Protocol):
    """A contestant. The game asks it for one turn per round."""

    def get_name(self) -> str:
        """Return the name this player is known by."""
        ...

    def take_turn(self, view: GameView) -> PlayerTurn:
        """Decide what to do, given what the player can see."""
        ...
