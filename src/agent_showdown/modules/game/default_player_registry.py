import threading

from agent_showdown.interfaces.game import Player


class DefaultPlayerRegistry:
    """The arena's roster, shared between the thread playing and the threads serving HTTP.

    Concurrency lives here for the same reason it lives in `event_channel`: this is where an HTTP
    request meets the game. A `Condition` guards the list and is what a paused arena waits on, so
    a registration wakes it rather than leaving it to poll.
    """

    def __init__(self) -> None:
        self._players: list[Player] = []
        self._changed = threading.Condition()

    def register(self, player: Player) -> None:
        with self._changed:
            self._players.append(player)
            self._changed.notify_all()

    def unregister(self, name: str) -> bool:
        with self._changed:
            remaining = [player for player in self._players if player.get_name() != name]
            if len(remaining) == len(self._players):
                return False
            self._players = remaining
            return True

    def players(self) -> tuple[Player, ...]:
        with self._changed:
            return tuple(self._players)

    def await_players(self, timeout: float) -> bool:
        with self._changed:
            if self._players:
                return True
            self._changed.wait(timeout)
            return bool(self._players)
