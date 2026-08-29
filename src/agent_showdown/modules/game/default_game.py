from collections.abc import Callable

from agent_showdown.interfaces.clock import Clock
from agent_showdown.interfaces.game import (
    Board,
    Direction,
    GameListener,
    GameView,
    Player,
    PlayerStats,
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
    """One match on one board. Pure: no IO, no randomness; time only through the injected clock."""

    def __init__(self, board: Board, clock: Clock) -> None:
        self._board = board
        self._clock = clock
        self._listeners: list[GameListener] = []
        self._players: list[Player] = []
        self._positions: dict[Player, Position] = {}
        # Keyed by object like `_positions`, because two contestants may share a name. A fresh
        # game is built per match, so these cannot leak from one game into the next.
        self._turns: dict[Player, int] = {}
        self._seconds: dict[Player, float] = {}

    def add_listener(self, listener: GameListener) -> None:
        self._listeners.append(listener)

    def register_player(self, player: Player, position: Position) -> None:
        self._players.append(player)
        self._positions[player] = position
        self._turns[player] = 0
        self._seconds[player] = 0.0
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
        self._emit(lambda listener: listener.player_turn_started(player))
        started_at = self._clock.now()
        try:
            self._plan_and_apply(player, round_number)
        finally:
            # In `finally`, so a refused or exploding turn still reports what it cost.
            seconds = (self._clock.now() - started_at).total_seconds()
            self._emit(lambda listener: listener.player_turn_ended(player, seconds))
            stats = self._record(player, seconds)
            self._emit(lambda listener: listener.player_stats(player, stats))

    def _plan_and_apply(self, player: Player, round_number: int) -> None:
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

    def _record(self, player: Player, seconds: float) -> PlayerStats:
        """Add one finished turn to a player's totals and return them.

        The average is computed here, beside the rest of the rules, because `PlayerStats` is data
        and holds no behaviour. A turn has just ended, so `turns` is never zero.
        """
        turns = self._turns[player] = self._turns[player] + 1
        total = self._seconds[player] = self._seconds[player] + seconds
        return PlayerStats(turns=turns, total_seconds=total, average_seconds=total / turns)

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
