from agent_showdown.interfaces.game import Board, Direction, Player, PlayerStats, Position
from agent_showdown.interfaces.log import Logger


class LogGameListener:
    """Reports every game event as one INFO line through the injected logger."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    def game_started(self, board: Board, max_rounds: int) -> None:
        self._logger.info(
            f"game started on a {board.width}x{board.height} board for {max_rounds} rounds"
        )

    def player_joined(self, player: Player, position: Position) -> None:
        self._logger.info(f"player {player.get_name()} joined at {_cell(position)}")

    def round_started(self, round_number: int) -> None:
        self._logger.info(f"round {round_number} started")

    def player_turn_started(self, player: Player) -> None:
        self._logger.info(f"player {player.get_name()} started its turn")

    def player_turn_ended(self, player: Player, seconds: float) -> None:
        self._logger.info(f"player {player.get_name()} ended its turn after {seconds:.1f}s")

    def player_stats(self, player: Player, stats: PlayerStats) -> None:
        self._logger.info(
            f"player {player.get_name()} has taken {stats.turns} turns"
            f" in {stats.total_seconds:.1f}s, {stats.average_seconds:.1f}s each,"
            f" {stats.eliminations} eliminations, {stats.deaths} deaths, {stats.wins} wins"
        )

    def player_dead(self, player: Player) -> None:
        self._logger.info(f"player {player.get_name()} is out of the fight and was skipped")

    def player_moved(self, player: Player, source: Position, destination: Position) -> None:
        self._logger.info(
            f"player {player.get_name()} moved from {_cell(source)} to {_cell(destination)}"
        )

    def player_reasoned(self, player: Player, reasoning: str) -> None:
        self._logger.info(f"player {player.get_name()} reasoned: {reasoning}")

    def spell_cast(
        self,
        player: Player,
        spell: str,
        origin: Position,
        direction: Direction,
        path: tuple[Position, ...],
    ) -> None:
        squares = " ".join(_cell(square) for square in path) or "nowhere"
        self._logger.info(
            f"player {player.get_name()} cast {spell} {direction} from {_cell(origin)}"
            f" through {squares}"
        )

    def player_hit(
        self, player: Player, source: Player, spell: str, damage: int, position: Position
    ) -> None:
        self._logger.info(
            f"player {player.get_name()} was hit on {_cell(position)} by"
            f" {source.get_name()}'s {spell} for {damage}"
        )

    def player_updated(self, player: Player, health: int) -> None:
        self._logger.info(f"player {player.get_name()} is on {health} health")

    def move_blocked(self, player: Player, position: Position, direction: Direction) -> None:
        self._logger.info(
            f"player {player.get_name()} blocked moving {direction} from {_cell(position)}"
        )

    def turn_failed(self, player: Player, reason: str) -> None:
        self._logger.warning(f"player {player.get_name()} failed its turn: {reason}")

    def game_ended(self, rounds_played: int) -> None:
        self._logger.info(f"game ended after {rounds_played} rounds")


def _cell(position: Position) -> str:
    return f"({position.x},{position.y})"
