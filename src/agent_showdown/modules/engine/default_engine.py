import threading
from collections.abc import Callable, Sequence

from agent_showdown.interfaces.game import (
    Board,
    BoardFactory,
    Game,
    GameFactory,
    GameListener,
    GameSnapshot,
    Player,
    PlayerRegistry,
    Position,
    SnapshotSource,
)
from agent_showdown.interfaces.log import Logger

_BOARD_WIDTH = 10
_BOARD_HEIGHT = 10
# Where contestants sit down, in registration order. A fifth robot gets a square of its own
# rather than a shared corner: two on one square is a position the rules no longer allow.
_SEATS = (
    Position(x=0, y=0),
    Position(x=9, y=9),
    Position(x=0, y=9),
    Position(x=9, y=0),
)
# How long a paused arena waits before looking again. It is woken by a registration, so this is
# only the interval at which it notices it is being shut down.
_IDLE_TIMEOUT = 0.5


class DefaultEngine:
    """The application facade. Gains one constructor parameter per module it needs.

    The arena runs for as long as the process does. It plays matches back to back, and the only
    thing that stops it is having nobody to play: an empty registry pauses it, and a registration
    wakes it up again.
    """

    def __init__(
        self,
        logger: Logger,
        board_factory: BoardFactory,
        game_factory: GameFactory,
        game_listeners: Sequence[GameListener],
        snapshot_source: SnapshotSource,
        player_registry: PlayerRegistry,
        max_rounds: int,
    ) -> None:
        self._logger = logger
        self._board_factory = board_factory
        self._game_factory = game_factory
        self._game_listeners = game_listeners
        self._snapshot_source = snapshot_source
        self._registry = player_registry
        self._max_rounds = max_rounds
        # One arena at a time: two would interleave their events into one stream of listeners.
        self._running = threading.Lock()
        self._stopping = threading.Event()
        # Written by the thread playing the arena, read by whoever asks for a new game.
        self._game: Game | None = None

    def game_snapshot(self) -> GameSnapshot:
        # The roster is the registry's, not the snapshot listener's: one source of truth, and
        # already guarded, so two robots joining at once cannot lose one.
        registered = tuple(player.get_name() for player in self._registry.players())
        return self._snapshot_source.snapshot().model_copy(update={"registered": registered})

    def register_player(self, player: Player) -> None:
        self._registry.register(player)
        self._emit(lambda listener: listener.player_registered(player))

    def unregister_player(self, name: str) -> bool:
        if not self._registry.unregister(name):
            return False
        self._emit(lambda listener: listener.player_unregistered(name))
        return True

    def run_arena(self) -> None:
        """Play matches until stopped. Blocks, so a frontend runs it on its own thread."""
        if not self._running.acquire(blocking=False):
            self._logger.warning("the arena is already running")
            return
        try:
            self._stopping.clear()
            self._arena()
        finally:
            self._game = None
            self._running.release()

    def stop_arena(self) -> None:
        self._stopping.set()
        self._end_match()

    def new_game(self) -> None:
        """Abandon the match in flight. The arena deals a fresh one immediately."""
        self._logger.info("new game requested")
        self._end_match()

    def _end_match(self) -> None:
        game = self._game
        if game is not None:
            game.stop()

    def _arena(self) -> None:
        self._logger.info("arena started")
        match = 0
        paused = False
        while not self._stopping.is_set():
            players = self._registry.players()
            if not players:
                paused = self._pause(paused)
                continue
            if paused:
                paused = False
                self._emit(lambda listener: listener.arena_resumed())
            match += 1
            self._logger.info(f"match {match} started")
            self._play(players)
        self._logger.info("arena stopped")

    def _pause(self, already_paused: bool) -> bool:
        """Wait for somebody to register, announcing the pause the first time round."""
        if not already_paused:
            self._emit(lambda listener: listener.arena_paused())
        self._registry.await_players(_IDLE_TIMEOUT)
        return True

    def _play(self, players: Sequence[Player]) -> None:
        # A fresh board per match, so every match is fought over a layout of its own, and a
        # fresh game, so health and seats reset while the scoreboard does not.
        board = self._board_factory.create(_BOARD_WIDTH, _BOARD_HEIGHT, _SEATS)
        game = self._game_factory.create(board)
        self._game = game
        for listener in self._game_listeners:  # first, so player_joined is observed
            game.add_listener(listener)
        for player, seat in zip(players, self._seats(board, len(players)), strict=True):
            game.register_player(player, seat)
        if self._stopping.is_set():
            game.stop()
        game.start(max_rounds=self._max_rounds)

    def _seats(self, board: Board, count: int) -> list[Position]:
        """One square each: the corners first, then anywhere else that is free.

        Robots may not stand on each other or on terrain, so seating two on one corner would
        start the match in a position its own rules forbid. On a board too small to seat
        everyone, the corners come round again — a cramped start beats no match at all.
        """
        blocked = {obstacle.position for obstacle in board.obstacles}
        everywhere = (
            Position(x=x, y=y) for y in range(board.height) for x in range(board.width)
        )
        seats: list[Position] = []
        for square in (*_SEATS, *everywhere):
            if len(seats) == count:
                break
            if square not in blocked and square not in seats:
                seats.append(square)
        while len(seats) < count:  # Nowhere left to put anyone. Share, as it used to.
            seats.append(_SEATS[len(seats) % len(_SEATS)])
        return seats

    def _emit(self, notify: Callable[[GameListener], None]) -> None:
        for listener in self._game_listeners:
            notify(listener)
