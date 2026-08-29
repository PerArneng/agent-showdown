from pydantic import BaseModel, ConfigDict


class PlayerStats(BaseModel):
    """A contestant's turns so far, cumulative within one game.

    `turns` counts every turn that *started*, so a turn that raised or was refused is in here too:
    it still cost wall time, which for an agent that is timing out is the whole story.
    """

    model_config = ConfigDict(frozen=True)

    turns: int
    total_seconds: float
    average_seconds: float
