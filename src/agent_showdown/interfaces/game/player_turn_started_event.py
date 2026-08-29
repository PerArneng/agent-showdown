from typing import Literal

from pydantic import BaseModel, ConfigDict


class PlayerTurnStartedEvent(BaseModel):
    """A player was handed its view and is now thinking."""

    model_config = ConfigDict(frozen=True)

    type: Literal["player_turn_started"] = "player_turn_started"
    player: str
