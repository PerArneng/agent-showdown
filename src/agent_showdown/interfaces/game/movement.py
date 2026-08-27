from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.game.move import Move


class Movement(BaseModel):
    """A plan of moves, applied in order."""

    model_config = ConfigDict(frozen=True)

    moves: tuple[Move, ...]
