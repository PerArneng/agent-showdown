from typing import Literal

from pydantic import BaseModel, ConfigDict


class PlayerDeadEvent(BaseModel):
    """A player was skipped because it has no health left."""

    model_config = ConfigDict(frozen=True)

    type: Literal["player_dead"] = "player_dead"
    player: str
