from typing import Any

from agent_showdown.interfaces.game import Board, Direction, Player, Position


class RecordingGameListener:
    """Test fake. Records every event as an (name, args) tuple instead of reporting it."""

    def __init__(self) -> None:
        self.events: list[tuple[str, tuple[Any, ...]]] = []

    def game_started(self, board: Board, max_rounds: int) -> None:
        self.events.append(("game_started", (board, max_rounds)))

    def player_joined(self, player: Player, position: Position) -> None:
        self.events.append(("player_joined", (player.get_name(), position)))

    def round_started(self, round_number: int) -> None:
        self.events.append(("round_started", (round_number,)))

    def player_moved(self, player: Player, source: Position, destination: Position) -> None:
        self.events.append(("player_moved", (player.get_name(), source, destination)))

    def player_reasoned(self, player: Player, reasoning: str) -> None:
        self.events.append(("player_reasoned", (player.get_name(), reasoning)))

    def move_blocked(self, player: Player, position: Position, direction: Direction) -> None:
        self.events.append(("move_blocked", (player.get_name(), position, direction)))

    def turn_failed(self, player: Player, reason: str) -> None:
        self.events.append(("turn_failed", (player.get_name(), reason)))

    def game_ended(self, rounds_played: int) -> None:
        self.events.append(("game_ended", (rounds_played,)))

    def names(self) -> list[str]:
        """The event names in order, for asserting on shape rather than payload."""
        return [name for name, _ in self.events]
