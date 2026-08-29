from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.game.position import Position


class SpellEffect(BaseModel):
    """What a cast spell did to the board, as pure geometry.

    `path` is every square it travelled through, in order, so a client can animate it. `impact` is
    the square it stopped on because something was standing there, or None if it hit nothing. Who
    was standing there, and what the damage does to them, is the game's business.
    """

    model_config = ConfigDict(frozen=True)

    path: tuple[Position, ...]
    impact: Position | None = None
    damage: int
