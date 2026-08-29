from typing import Literal

from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.game.position import Position


class PlayerHitEvent(BaseModel):
    """A spell landed. `player` is who was hit, `source` is who cast it."""

    model_config = ConfigDict(frozen=True)

    type: Literal["player_hit"] = "player_hit"
    player: str
    source: str
    spell: str
    damage: int
    position: Position
