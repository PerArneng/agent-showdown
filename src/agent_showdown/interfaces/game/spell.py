from typing import Protocol

from agent_showdown.interfaces.game.board import Board
from agent_showdown.interfaces.game.direction import Direction
from agent_showdown.interfaces.game.position import Position
from agent_showdown.interfaces.game.spell_effect import SpellEffect
from agent_showdown.interfaces.game.spell_info import SpellInfo


class Spell(Protocol):
    """Something a robot can cast. Pure geometry: it knows squares, never players.

    That is what keeps a spell testable with no game around it, and what keeps damage a rule of
    the game rather than a property of the word.
    """

    def describe(self) -> SpellInfo:
        """Return what this spell is called and what it does."""
        ...

    def cast(
        self,
        origin: Position,
        direction: Direction,
        board: Board,
        occupied: frozenset[Position],
    ) -> SpellEffect:
        """Work out where this spell travels from `origin` and what square it stops on."""
        ...
