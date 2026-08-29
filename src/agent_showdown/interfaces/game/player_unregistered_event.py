from typing import Literal

from pydantic import BaseModel, ConfigDict


class PlayerUnregisteredEvent(BaseModel):
    """A robot left the arena. It plays out the match in flight and is not seated again."""

    model_config = ConfigDict(frozen=True)

    type: Literal["player_unregistered"] = "player_unregistered"
    player: str
