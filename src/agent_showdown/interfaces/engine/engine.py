from typing import Protocol

from agent_showdown.interfaces.game import GameSnapshot, Player


class Engine(Protocol):
    """The facade every frontend calls. All behaviour of the application hangs off this."""

    def run_arena(self) -> None:
        """Play matches back to back until stopped. Blocks; a frontend gives it a thread.

        Pauses whenever nobody is registered and resumes as soon as somebody is.
        """
        ...

    def stop_arena(self) -> None:
        """End the arena at the next turn boundary. Safe to call when nothing is running."""
        ...

    def new_game(self) -> None:
        """Abandon the match in flight. The next one starts immediately, score intact."""
        ...

    def register_player(self, player: Player) -> None:
        """Add a contestant. A paused arena starts playing again."""
        ...

    def unregister_player(self, name: str) -> bool:
        """Remove a contestant. False if nobody by that name was registered."""
        ...

    def game_snapshot(self) -> GameSnapshot:
        """Return the current game as a value, for a client that connected mid-game."""
        ...
