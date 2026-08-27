from pydantic import BaseModel, ConfigDict


class Board(BaseModel):
    """The game world: a grid of empty cells."""

    model_config = ConfigDict(frozen=True)

    width: int
    height: int
