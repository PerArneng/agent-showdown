from typing import Protocol

from agent_showdown.interfaces.game.game_snapshot import GameSnapshot


class SnapshotSource(Protocol):
    """Hands out the current game as a value. Read from threads other than the one playing."""

    def snapshot(self) -> GameSnapshot:
        """Return the game as it stands right now."""
        ...
