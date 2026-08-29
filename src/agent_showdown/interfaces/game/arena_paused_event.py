from typing import Literal

from pydantic import BaseModel, ConfigDict


class ArenaPausedEvent(BaseModel):
    """Nobody is registered, so there is nothing to play until somebody joins."""

    model_config = ConfigDict(frozen=True)

    type: Literal["arena_paused"] = "arena_paused"
