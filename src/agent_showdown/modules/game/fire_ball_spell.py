from agent_showdown.interfaces.game import (
    Board,
    Direction,
    Position,
    SpellEffect,
    SpellInfo,
)
from agent_showdown.modules.game.deltas import DELTAS

_NAME = "fireball"
_DAMAGE = 10
_RANGE = 3


class FireBallSpell:
    """A bolt down one direction. Travels up to three squares and stops on the first robot."""

    def describe(self) -> SpellInfo:
        return SpellInfo(
            name=_NAME,
            description=(
                f"A bolt of fire down one direction. It travels up to {_RANGE} squares and burns"
                f" the first robot in its way for {_DAMAGE} damage. It stops there, so a robot"
                " standing behind another is safe. It only travels along the eight directions, so"
                " it reaches a robot only when that robot is on your row, your column or an exact"
                " diagonal from you. Fired at anything else it hits nothing and the action is"
                " wasted."
            ),
            damage=_DAMAGE,
            range=_RANGE,
        )

    def cast(
        self,
        origin: Position,
        direction: Direction,
        board: Board,
        occupied: frozenset[Position],
    ) -> SpellEffect:
        dx, dy = DELTAS[direction]
        path: list[Position] = []
        square = origin
        for _ in range(_RANGE):
            square = Position(x=square.x + dx, y=square.y + dy)
            if not (0 <= square.x < board.width and 0 <= square.y < board.height):
                break  # It fizzles at the wall rather than flying off the board.
            path.append(square)
            if square in occupied:
                return SpellEffect(path=tuple(path), impact=square, damage=_DAMAGE)
        return SpellEffect(path=tuple(path), impact=None, damage=_DAMAGE)
