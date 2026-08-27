from agent_showdown.interfaces.game import Player
from agent_showdown.interfaces.randomizer import Randomizer
from agent_showdown.modules.game.dummy_player import DummyPlayer


class DummyPlayerFactory:
    """Builds `DummyPlayer`s that share one source of randomness."""

    def __init__(self, randomizer: Randomizer) -> None:
        self._randomizer = randomizer

    def create(self, name: str) -> Player:
        return DummyPlayer(name, self._randomizer)
