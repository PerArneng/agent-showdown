from collections.abc import Callable

from agent_showdown.interfaces.game import (
    Board,
    Direction,
    GameListener,
    GameView,
    Player,
    Position,
)

# The one place direction semantics live. Row 0 is the top, so UP decreases y.
_DELTAS: dict[Direction, tuple[int, int]] = {
    Direction.UP: (0, -1),
    Direction.DOWN: (0, 1),
    Direction.LEFT: (-1, 0),
    Direction.RIGHT: (1, 0),
    Direction.UP_LEFT: (-1, -1),
    Direction.UP_RIGHT: (1, -1),
    Direction.DOWN_LEFT: (-1, 1),
    Direction.DOWN_RIGHT: (1, 1),
}

# A turn is one plan. This stops a single greedy agent from hogging a round.
_MAX_MOVES_PER_TURN = 8


class DefaultGame:
    """One match on one board. Pure: no IO, no randomness, no clock."""

    def __init__(self, board: Board) -> None:
        self._board = board
        self._listeners: list[GameListener] = []
        self._players: list[Player] = []
        self._positions: dict[Player, Position] = {}

    def add_listener(self, listener: GameListener) -> None:
        self._listeners.append(listener)

    def register_player(self, player: Player, position: Position) -> None:
        self._players.append(player)
        self._positions[player] = position
        self._emit(lambda listener: listener.player_joined(player, position))

    def start(self, max_rounds: int) -> None:
        self._emit(lambda listener: listener.game_started(self._board, max_rounds))
        for round_number in range(1, max_rounds + 1):
            self._play_round(round_number)
        self._emit(lambda listener: listener.game_ended(max_rounds))

    def _play_round(self, round_number: int) -> None:
        self._emit(lambda listener: listener.round_started(round_number))
        for player in self._players:
            self._play_turn(player, round_number)

    def _play_turn(self, player: Player, round_number: int) -> None:
        view = GameView(
            board=self._board,
            position=self._positions[player],
            round_number=round_number,
        )
        try:
            turn = player.take_turn(view)
        except Exception as error:  # A remote player fails in ways we cannot enumerate.
            self._fail_turn(player, f"{type(error).__name__}: {error}")
            return
        # Before the plan is judged, so an over-long plan still says what it was for.
        if turn.reasoning:
            self._emit(lambda listener: listener.player_reasoned(player, turn.reasoning))
        moves = turn.movement.moves
        if len(moves) > _MAX_MOVES_PER_TURN:
            self._fail_turn(
                player, f"planned {len(moves)} moves, the limit is {_MAX_MOVES_PER_TURN}"
            )
            return
        for move in moves:
            self._apply(player, move.direction)

    def _fail_turn(self, player: Player, reason: str) -> None:
        self._emit(lambda listener: listener.turn_failed(player, reason))

    def _apply(self, player: Player, direction: Direction) -> None:
        source = self._positions[player]
        dx, dy = _DELTAS[direction]
        destination = Position(x=source.x + dx, y=source.y + dy)
        if not self._is_on_board(destination):
            self._emit(lambda listener: listener.move_blocked(player, source, direction))
            return
        self._positions[player] = destination
        self._emit(lambda listener: listener.player_moved(player, source, destination))

    def _is_on_board(self, position: Position) -> bool:
        return 0 <= position.x < self._board.width and 0 <= position.y < self._board.height

    def _emit(self, notify: Callable[[GameListener], None]) -> None:
        for listener in self._listeners:
            notify(listener)
