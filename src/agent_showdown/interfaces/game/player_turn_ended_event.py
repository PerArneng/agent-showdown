from typing import Literal

from pydantic import BaseModel, ConfigDict


class PlayerTurnEndedEvent(BaseModel):
    """A player's turn is over, whether it planned, refused or failed.

    `seconds` is the wall time the whole turn cost, which for a remote agent is very nearly the
    time the model spent thinking.
    """

    model_config = ConfigDict(frozen=True)

    type: Literal["player_turn_ended"] = "player_turn_ended"
    player: str
    seconds: float
