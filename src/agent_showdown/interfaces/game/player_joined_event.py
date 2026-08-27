from typing import Literal

from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.game.position import Position


class PlayerJoinedEvent(BaseModel):
    """A player was registered at its starting position."""

    model_config = ConfigDict(frozen=True)

    type: Literal["player_joined"] = "player_joined"
    player: str
    position: Position
