from typing import Any

from agent_showdown.interfaces.game import Board, Direction, Player, PlayerStats, Position


class RecordingGameListener:
    """Test fake. Records every event as an (name, args) tuple instead of reporting it."""

    def __init__(self) -> None:
        self.events: list[tuple[str, tuple[Any, ...]]] = []

    def arena_paused(self) -> None:
        self.events.append(("arena_paused", ()))

    def arena_resumed(self) -> None:
        self.events.append(("arena_resumed", ()))

    def player_registered(self, player: Player) -> None:
        self.events.append(("player_registered", (player.get_name(),)))

    def player_unregistered(self, name: str) -> None:
        self.events.append(("player_unregistered", (name,)))

    def game_started(self, board: Board, max_rounds: int) -> None:
        self.events.append(("game_started", (board, max_rounds)))

    def player_joined(self, player: Player, position: Position) -> None:
        self.events.append(("player_joined", (player.get_name(), position)))

    def board_changed(self, board: Board) -> None:
        self.events.append(("board_changed", (board,)))

    def round_started(self, round_number: int) -> None:
        self.events.append(("round_started", (round_number,)))

    def player_turn_started(self, player: Player) -> None:
        self.events.append(("player_turn_started", (player.get_name(),)))

    def player_turn_ended(self, player: Player, seconds: float) -> None:
        self.events.append(("player_turn_ended", (player.get_name(), seconds)))

    def player_stats(self, player: Player, stats: PlayerStats) -> None:
        self.events.append(("player_stats", (player.get_name(), stats)))

    def player_dead(self, player: Player) -> None:
        self.events.append(("player_dead", (player.get_name(),)))

    def player_moved(self, player: Player, source: Position, destination: Position) -> None:
        self.events.append(("player_moved", (player.get_name(), source, destination)))

    def player_reasoned(self, player: Player, reasoning: str) -> None:
        self.events.append(("player_reasoned", (player.get_name(), reasoning)))

    def spell_cast(
        self,
        player: Player,
        spell: str,
        origin: Position,
        direction: Direction,
        path: tuple[Position, ...],
    ) -> None:
        self.events.append(("spell_cast", (player.get_name(), spell, origin, direction, path)))

    def player_hit(
        self, player: Player, source: Player, spell: str, damage: int, position: Position
    ) -> None:
        self.events.append(
            ("player_hit", (player.get_name(), source.get_name(), spell, damage, position))
        )

    def player_updated(self, player: Player, health: int) -> None:
        self.events.append(("player_updated", (player.get_name(), health)))

    def move_blocked(self, player: Player, position: Position, direction: Direction) -> None:
        self.events.append(("move_blocked", (player.get_name(), position, direction)))

    def turn_failed(self, player: Player, reason: str) -> None:
        self.events.append(("turn_failed", (player.get_name(), reason)))

    def game_ended(self, rounds_played: int) -> None:
        self.events.append(("game_ended", (rounds_played,)))

    def names(self) -> list[str]:
        """The event names in order, for asserting on shape rather than payload."""
        return [name for name, _ in self.events]
