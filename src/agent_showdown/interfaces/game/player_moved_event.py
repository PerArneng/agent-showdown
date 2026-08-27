from typing import Literal

from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.game.position import Position


class PlayerMovedEvent(BaseModel):
    """A player left `source` and now stands on `destination`."""

    model_config = ConfigDict(frozen=True)

    type: Literal["player_moved"] = "player_moved"
    player: str
    source: Position
    destination: Position
