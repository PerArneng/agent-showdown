from pydantic import BaseModel, ConfigDict


class PlayerStats(BaseModel):
    """A contestant's running totals, across every match of a series.

    `turns` counts every turn that *started* while the robot was alive, so a turn that raised or
    was refused is in here too: it still cost wall time, which for an agent that is timing out is
    the whole story. A turn skipped because the robot is dead is not, or a corpse's average would
    fall towards zero. `eliminations`, `deaths` and `wins` outlive a single match, which is why
    they are kept by the `Scoreboard` rather than by a `Game`.
    """

    model_config = ConfigDict(frozen=True)

    turns: int
    total_seconds: float
    average_seconds: float
    eliminations: int = 0
    deaths: int = 0
    wins: int = 0
