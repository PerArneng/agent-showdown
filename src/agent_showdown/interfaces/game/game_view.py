from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.game.board import Board
from agent_showdown.interfaces.game.position import Position


class GameView(BaseModel):
    """What a player is shown when asked for its turn."""

    model_config = ConfigDict(frozen=True)

    board: Board
    position: Position
    round_number: int
