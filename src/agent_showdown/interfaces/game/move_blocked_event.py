from typing import Literal

from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.game.direction import Direction
from agent_showdown.interfaces.game.position import Position


class MoveBlockedEvent(BaseModel):
    """A move would have left the board, so the player stayed on `position`."""

    model_config = ConfigDict(frozen=True)

    type: Literal["move_blocked"] = "move_blocked"
    player: str
    position: Position
    direction: Direction
