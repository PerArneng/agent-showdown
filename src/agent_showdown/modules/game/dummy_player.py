from agent_showdown.interfaces.clock import Clock
from agent_showdown.interfaces.game import (
    Action,
    ActionKind,
    Direction,
    GameView,
    Opponent,
    PlayerTurn,
)
from agent_showdown.interfaces.randomizer import Randomizer
from agent_showdown.modules.game.deltas import DELTAS


class DummyPlayer:
    """A stand-in contestant with just enough sense to be worth playing against.

    Not an agent: it reasons about nothing and calls no model. It takes the shot in front of it,
    walks towards whoever is nearest when there is no shot, and wanders when the arena is empty —
    which is enough to pressure a real agent instead of standing around being target practice.

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
        shot = self._shot(view)
        if shot is not None:
            spell, opponent = shot
            return PlayerTurn(
                reasoning=f"{opponent.name} is lined up {opponent.direction}, so {spell}",
                actions=(
                    Action(kind=ActionKind.CAST, direction=_aim(opponent), spell=spell),
                ),
            )
        target = self._nearest(view)
        if target is not None:
            direction = _towards(view, target)
            return PlayerTurn(
                reasoning=f"closing on {target.name}, {target.distance} away",
                actions=(Action(kind=ActionKind.MOVE, direction=direction),),
            )
        direction = self._randomizer.choice(list(Direction))
        return PlayerTurn(
            reasoning=f"no plan, wandering {direction}",
            actions=(Action(kind=ActionKind.MOVE, direction=direction),),
        )

    def _shot(self, view: GameView) -> tuple[str, Opponent] | None:
        """The first cast that would land. The geometry is already in the view."""
        for spell in view.spells:
            for opponent in view.opponents:
                if (
                    opponent.health > 0
                    and opponent.direction is not None
                    and opponent.distance <= spell.range
                ):
                    return spell.name, opponent
        return None

    def _nearest(self, view: GameView) -> Opponent | None:
        living = [opponent for opponent in view.opponents if opponent.health > 0]
        if not living:
            return None
        return min(living, key=lambda opponent: opponent.distance)


def _aim(opponent: Opponent) -> Direction:
    """Only called for a lined-up opponent, so the direction is never missing."""
    assert opponent.direction is not None
    return opponent.direction


def _towards(view: GameView, target: Opponent) -> Direction:
    """One step that closes the gap, diagonally where both axes are still apart."""
    step_x = _sign(target.position.x - view.position.x)
    step_y = _sign(target.position.y - view.position.y)
    for direction, delta in DELTAS.items():
        if delta == (step_x, step_y):
            return direction
    return Direction.UP  # Only reachable if already on the target's square.


def _sign(value: int) -> int:
    return (value > 0) - (value < 0)
