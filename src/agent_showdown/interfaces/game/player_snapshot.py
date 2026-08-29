from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.game.position import Position


class PlayerSnapshot(BaseModel):
    """One contestant as a late-joining client needs it: where it stands, and why."""

    model_config = ConfigDict(frozen=True)

    name: str
    position: Position
    health: int = 100
    reasoning: str = ""
    think_seconds: float = 0.0
