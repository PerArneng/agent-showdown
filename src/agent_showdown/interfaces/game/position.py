from pydantic import BaseModel, ConfigDict


class Position(BaseModel):
    """A cell on the board. The single coordinate type the whole game speaks."""

    model_config = ConfigDict(frozen=True)

    x: int
    y: int
