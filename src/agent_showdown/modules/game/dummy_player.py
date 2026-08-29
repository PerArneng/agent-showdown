from agent_showdown.interfaces.clock import Clock
from agent_showdown.interfaces.game import Action, ActionKind, Direction, GameView, PlayerTurn
from agent_showdown.interfaces.randomizer import Randomizer


class DummyPlayer:
    """Wanders. Picks one random direction per round and ignores what it can see.

    It pauses before answering, which buys nothing except that a human watching the board can see
    it move. Real thinking would take time too.
    """

    def __init__(self, name: str, randomizer: Randomizer, clock: Clock, think_time: float) -> None:
        self._name = name
        self._randomizer = randomizer
        self._clock = clock
        self._think_time = think_time

    def get_name(self) -> str:
        return self._name

    def take_turn(self, view: GameView) -> PlayerTurn:
        self._clock.sleep(self._think_time)
        direction = self._randomizer.choice(list(Direction))
        return PlayerTurn(
            reasoning=f"no plan, wandering {direction}",
            actions=(Action(kind=ActionKind.MOVE, direction=direction),),
        )
