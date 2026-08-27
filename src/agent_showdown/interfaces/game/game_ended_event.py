from typing import Literal

from pydantic import BaseModel, ConfigDict


class GameEndedEvent(BaseModel):
    """The game is over."""

    model_config = ConfigDict(frozen=True)

    type: Literal["game_ended"] = "game_ended"
    rounds_played: int
