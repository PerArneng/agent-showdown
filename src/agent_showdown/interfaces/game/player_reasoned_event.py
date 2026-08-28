from typing import Literal

from pydantic import BaseModel, ConfigDict


class PlayerReasonedEvent(BaseModel):
    """A player explained the turn it just planned."""

    model_config = ConfigDict(frozen=True)

    type: Literal["player_reasoned"] = "player_reasoned"
    player: str
    reasoning: str
