from typing import Literal

from pydantic import BaseModel, ConfigDict


class PlayerUpdatedEvent(BaseModel):
    """A player's health changed. Zero means eliminated."""

    model_config = ConfigDict(frozen=True)

    type: Literal["player_updated"] = "player_updated"
    player: str
    health: int
