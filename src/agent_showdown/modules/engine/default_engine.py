import threading
from collections.abc import Sequence

from agent_showdown.interfaces.builtin_agents import AgentRoster
from agent_showdown.interfaces.game import (
    Board,
    GameFactory,
    GameListener,
    GameSnapshot,
    PlayerFactory,
    Position,
    SnapshotSource,
)
from agent_showdown.interfaces.log import Logger

_BOARD = Board(width=10, height=10)
_MAX_ROUNDS = 10
# Where the built-in agents sit down, in configuration order. Cycled, so more agents than
# seats still starts a game.
_AGENT_SEATS = (Position(x=9, y=9), Position(x=0, y=9), Position(x=9, y=0))


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
    ) -> None:
        self._logger = logger
        self._game_factory = game_factory
        self._player_factory = player_factory
        self._agent_roster = agent_roster
        self._game_listeners = game_listeners
        self._snapshot_source = snapshot_source
        # One game at a time: two would interleave their events into one stream of listeners.
        self._running = threading.Lock()

    def game_snapshot(self) -> GameSnapshot:
        return self._snapshot_source.snapshot()

    def start_game(self) -> None:
        if not self._running.acquire(blocking=False):
            self._logger.warning("a game is already running")
            return
        try:
            self._play()
        finally:
            self._running.release()

    def _play(self) -> None:
        self._logger.info("started")
        game = self._game_factory.create(_BOARD)
        for listener in self._game_listeners:  # first, so player_joined is observed
            game.add_listener(listener)
        game.register_player(self._player_factory.create("dummy-1"), Position(x=0, y=0))
        for index, player in enumerate(self._agent_roster.create_players()):
            game.register_player(player, _AGENT_SEATS[index % len(_AGENT_SEATS)])
        game.start(max_rounds=_MAX_ROUNDS)
