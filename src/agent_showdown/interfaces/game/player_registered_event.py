from typing import Literal

from pydantic import BaseModel, ConfigDict


class PlayerRegisteredEvent(BaseModel):
    """A robot entered the arena. It is seated in the next match, not the one in flight."""

    model_config = ConfigDict(frozen=True)

    type: Literal["player_registered"] = "player_registered"
    player: str
