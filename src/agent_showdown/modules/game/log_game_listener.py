from agent_showdown.interfaces.game import Board, Direction, Player, Position
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

    def player_moved(self, player: Player, source: Position, destination: Position) -> None:
        self._logger.info(
            f"player {player.get_name()} moved from {_cell(source)} to {_cell(destination)}"
        )

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
