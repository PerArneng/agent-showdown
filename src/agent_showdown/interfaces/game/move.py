from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.game.direction import Direction


class Move(BaseModel):
    """A single step of a movement plan."""

    model_config = ConfigDict(frozen=True)

    direction: Direction
