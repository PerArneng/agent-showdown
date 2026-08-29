from agent_showdown.interfaces.clock import Clock
from agent_showdown.interfaces.game import (
    Action,
    ActionKind,
    Direction,
    GameView,
    Opponent,
    PlayerTurn,
    Position,
)
from agent_showdown.interfaces.randomizer import Randomizer
from agent_showdown.modules.game.deltas import DELTAS


class DummyPlayer:
    """A stand-in contestant with just enough sense to be worth playing against.

    Not an agent: it reasons about nothing and calls no model. It takes the shot in front of it,
    walks towards whoever is nearest when there is no shot, and wanders when the arena is empty —
    which is enough to pressure a real agent instead of standing around being target practice.
    It steps round whatever is in the way rather than into it, so neither a boulder nor another
    robot pins it in place for a match.

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
        step = self._towards(view, target) if target is not None else None
        if target is not None and step is not None:
            return PlayerTurn(
                reasoning=f"closing on {target.name}, {target.distance} away",
                actions=(Action(kind=ActionKind.MOVE, direction=step),),
            )
        direction = self._randomizer.choice(_open(view) or list(Direction))
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

    def _towards(self, view: GameView, target: Opponent) -> Direction | None:
        """The first step that closes the gap and is not into terrain, or None if all are."""
        for direction in _closing(view, target):
            if _is_open(view, direction):
                return direction
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


def _closing(view: GameView, target: Opponent) -> list[Direction]:
    """Steps that close the gap, best first: the diagonal, then either axis on its own.

    The axis-only steps are what gets it round an obstacle standing on the diagonal.
    """
    step_x = _sign(target.position.x - view.position.x)
    step_y = _sign(target.position.y - view.position.y)
    wanted = [(step_x, step_y), (step_x, 0), (0, step_y)]
    return [
        direction
        for delta in wanted
        if delta != (0, 0)
        for direction, offset in DELTAS.items()
        if offset == delta
    ]


def _open(view: GameView) -> list[Direction]:
    """Every direction that would not be refused: on the arena, and onto an empty square."""
    return [direction for direction in Direction if _is_open(view, direction)]


def _is_open(view: GameView, direction: Direction) -> bool:
    dx, dy = DELTAS[direction]
    square = Position(x=view.position.x + dx, y=view.position.y + dy)
    if not (0 <= square.x < view.board.width and 0 <= square.y < view.board.height):
        return False
    if any(obstacle.position == square for obstacle in view.board.obstacles):
        return False
    # A wreck counts: it holds its square whether or not it can still fight back.
    return all(opponent.position != square for opponent in view.opponents)


def _sign(value: int) -> int:
    return (value > 0) - (value < 0)
