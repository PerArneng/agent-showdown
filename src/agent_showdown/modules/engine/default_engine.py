import threading
from collections.abc import Sequence

from agent_showdown.interfaces.builtin_agents import AgentRoster
from agent_showdown.interfaces.game import (
    Board,
    Game,
    GameFactory,
    GameListener,
    GameSnapshot,
    Player,
    PlayerFactory,
    Position,
    SnapshotSource,
)
from agent_showdown.interfaces.log import Logger

_BOARD = Board(width=10, height=10)
# Where the built-in agents sit down, in configuration order. Cycled, so more agents than
# seats still starts a game.
_AGENT_SEATS = (Position(x=9, y=9), Position(x=0, y=9), Position(x=9, y=0))
_DUMMY_SEAT = Position(x=0, y=0)


class DefaultEngine:
    """The application facade. Gains one constructor parameter per module it needs."""

    def __init__(
        self,
        logger: Logger,
        game_factory: GameFactory,
        player_factory: PlayerFactory,
        agent_roster: AgentRoster,
        game_listeners: Sequence[GameListener],
        snapshot_source: SnapshotSource,
        max_games: int,
        max_rounds: int,
    ) -> None:
        self._logger = logger
        self._game_factory = game_factory
        self._player_factory = player_factory
        self._agent_roster = agent_roster
        self._game_listeners = game_listeners
        self._snapshot_source = snapshot_source
        self._max_games = max_games
        self._max_rounds = max_rounds
        # One series at a time: two would interleave their events into one stream of listeners.
        self._running = threading.Lock()
        self._stopping = threading.Event()
        # Written by the thread playing the series, read by whoever calls `stop_game`.
        self._game: Game | None = None

    def game_snapshot(self) -> GameSnapshot:
        return self._snapshot_source.snapshot()

    def start_game(self) -> None:
        if not self._running.acquire(blocking=False):
            self._logger.warning("a game is already running")
            return
        try:
            self._stopping.clear()
            self._play_series()
        finally:
            self._game = None
            self._running.release()

    def stop_game(self) -> None:
        self._stopping.set()
        game = self._game
        if game is not None:
            game.stop()

    def _play_series(self) -> None:
        # Built once and reused for every match, so the scoreboard's per-player totals accumulate
        # across the series and no model client is rebuilt between matches.
        players = self._contestants()
        for match in range(1, self._max_games + 1):
            if self._stopping.is_set():
                break
            self._logger.info(f"match {match} of {self._max_games} started")
            self._play(players)
        self._logger.info("series ended")

    def _contestants(self) -> list[tuple[Player, Position]]:
        seated: list[tuple[Player, Position]] = [
            (self._player_factory.create("dummy-1"), _DUMMY_SEAT)
        ]
        for index, player in enumerate(self._agent_roster.create_players()):
            seated.append((player, _AGENT_SEATS[index % len(_AGENT_SEATS)]))
        return seated

    def _play(self, players: Sequence[tuple[Player, Position]]) -> None:
        # A fresh game per match, so health and seats reset while the scoreboard does not.
        game = self._game_factory.create(_BOARD)
        self._game = game
        for listener in self._game_listeners:  # first, so player_joined is observed
            game.add_listener(listener)
        for player, seat in players:
            game.register_player(player, seat)
        if self._stopping.is_set():
            game.stop()
        game.start(max_rounds=self._max_rounds)
