import threading
from collections.abc import Sequence

from agent_showdown.interfaces.game import (
    Board,
    GameFactory,
    GameListener,
    PlayerFactory,
    Position,
)
from agent_showdown.interfaces.log import Logger

_BOARD = Board(width=10, height=10)
_MAX_ROUNDS = 10


class DefaultEngine:
    """The application facade. Gains one constructor parameter per module it needs."""

    def __init__(
        self,
        logger: Logger,
        game_factory: GameFactory,
        player_factory: PlayerFactory,
        agent_player_factory: PlayerFactory,
        game_listeners: Sequence[GameListener],
    ) -> None:
        self._logger = logger
        self._game_factory = game_factory
        self._player_factory = player_factory
        self._agent_player_factory = agent_player_factory
        self._game_listeners = game_listeners
        # One game at a time: two would interleave their events into one stream of listeners.
        self._running = threading.Lock()

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
        game.register_player(
            self._agent_player_factory.create("simple-strands-1"), Position(x=9, y=9)
        )
        game.start(max_rounds=_MAX_ROUNDS)
