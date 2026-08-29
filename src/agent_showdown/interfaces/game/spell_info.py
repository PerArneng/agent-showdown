from pydantic import BaseModel, ConfigDict


class SpellInfo(BaseModel):
    """A spell as it is described to whoever carries it. `name` is what an `Action` must name."""

    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    damage: int
    range: int
