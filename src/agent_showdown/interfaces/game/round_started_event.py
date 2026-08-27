from typing import Literal

from pydantic import BaseModel, ConfigDict


class RoundStartedEvent(BaseModel):
    """A new round begins. Rounds are numbered from 1."""

    model_config = ConfigDict(frozen=True)

    type: Literal["round_started"] = "round_started"
    round_number: int
