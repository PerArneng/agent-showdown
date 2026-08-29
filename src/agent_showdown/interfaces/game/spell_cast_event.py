from typing import Literal

from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.game.direction import Direction
from agent_showdown.interfaces.game.position import Position


class SpellCastEvent(BaseModel):
    """A player cast a spell down a direction. `path` is every square it travelled through."""

    model_config = ConfigDict(frozen=True)

    type: Literal["spell_cast"] = "spell_cast"
    player: str
    spell: str
    direction: Direction
    origin: Position
    path: tuple[Position, ...]
