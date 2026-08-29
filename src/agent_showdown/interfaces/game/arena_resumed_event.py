from typing import Literal

from pydantic import BaseModel, ConfigDict


class ArenaResumedEvent(BaseModel):
    """A contestant registered, so matches start again."""

    model_config = ConfigDict(frozen=True)

    type: Literal["arena_resumed"] = "arena_resumed"
