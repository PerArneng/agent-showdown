from agent_showdown.interfaces.clock import Clock
from agent_showdown.interfaces.game import Player
from agent_showdown.interfaces.randomizer import Randomizer
from agent_showdown.modules.game.dummy_player import DummyPlayer


class DummyPlayerFactory:
    """Builds `DummyPlayer`s that share one source of randomness and one think time."""

    def __init__(self, randomizer: Randomizer, clock: Clock, think_time: float) -> None:
        self._randomizer = randomizer
        self._clock = clock
        self._think_time = think_time

    def create(self, name: str) -> Player:
        return DummyPlayer(name, self._randomizer, self._clock, self._think_time)
