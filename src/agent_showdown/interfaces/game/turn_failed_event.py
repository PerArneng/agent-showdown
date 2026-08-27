from typing import Literal

from pydantic import BaseModel, ConfigDict


class TurnFailedEvent(BaseModel):
    """A player could not be asked for a turn, or answered with something unusable."""

    model_config = ConfigDict(frozen=True)

    type: Literal["turn_failed"] = "turn_failed"
    player: str
    reason: str
