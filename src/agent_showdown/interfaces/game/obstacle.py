from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.game.position import Position
from agent_showdown.interfaces.game.terrain_kind import TerrainKind


class Obstacle(BaseModel):
    """One blocked square. Nothing walks onto it and no bolt flies through it."""

    model_config = ConfigDict(frozen=True)

    position: Position
    kind: TerrainKind
