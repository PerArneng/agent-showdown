from typing import Protocol

from agent_showdown.interfaces.game import GameSnapshot


class Engine(Protocol):
    """The facade every frontend calls. All behaviour of the application hangs off this."""

    def start_game(self) -> None:
        """Play one game to the end. Does nothing if a game is already running."""
        ...

    def game_snapshot(self) -> GameSnapshot:
        """Return the current game as a value, for a client that connected mid-game."""
        ...
