from agent_showdown.interfaces.game import Direction, GameView, Move, Movement, PlayerTurn
from agent_showdown.interfaces.randomizer import Randomizer


class DummyPlayer:
    """Wanders. Picks one random direction per round and ignores what it can see."""

    def __init__(self, name: str, randomizer: Randomizer) -> None:
        self._name = name
        self._randomizer = randomizer

    def get_name(self) -> str:
        return self._name

    def take_turn(self, view: GameView) -> PlayerTurn:
        direction = self._randomizer.choice(list(Direction))
        return PlayerTurn(movement=Movement(moves=(Move(direction=direction),)))
