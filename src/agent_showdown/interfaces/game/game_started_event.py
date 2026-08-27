from typing import Literal

from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.game.board import Board


class GameStartedEvent(BaseModel):
    """The game is about to run for `max_rounds` rounds."""

    model_config = ConfigDict(frozen=True)

    type: Literal["game_started"] = "game_started"
    board: Board
    max_rounds: int
