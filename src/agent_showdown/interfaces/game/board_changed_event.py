from typing import Literal

from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.game.board import Board


class BoardChangedEvent(BaseModel):
    """The arena has been re-dealt: this is the ground the coming round is fought over."""

    model_config = ConfigDict(frozen=True)

    type: Literal["board_changed"] = "board_changed"
    board: Board
