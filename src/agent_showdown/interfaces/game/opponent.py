from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.game.position import Position


class Opponent(BaseModel):
    """Another robot, as the one being asked for a turn sees it. Health of 0 means eliminated."""

    model_config = ConfigDict(frozen=True)

    name: str
    position: Position
    health: int
