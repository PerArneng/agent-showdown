from typing import Protocol

from agent_showdown.interfaces.game import GameSnapshot


class Engine(Protocol):
    """The facade every frontend calls. All behaviour of the application hangs off this."""

    def start_game(self) -> None:
        """Play a series of matches, back to back. Does nothing if a series is already running."""
        ...

    def stop_game(self) -> None:
        """End the series at the next turn boundary. Safe to call when nothing is running."""
        ...

    def game_snapshot(self) -> GameSnapshot:
        """Return the current game as a value, for a client that connected mid-game."""
        ...
