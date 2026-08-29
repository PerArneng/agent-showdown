from typing import Protocol

from agent_showdown.interfaces.game.spell import Spell


class SpellBook(Protocol):
    """The spells a robot starts a match with."""

    def create_spells(self) -> tuple[Spell, ...]:
        """Return a fresh set of spells, one call per robot, so nothing is shared between them."""
        ...
