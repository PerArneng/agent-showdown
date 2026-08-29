from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.game.direction import Direction
from agent_showdown.interfaces.game.position import Position


class Opponent(BaseModel):
    """Another robot, as the one being asked for a turn sees it. Health of 0 means eliminated.

    `direction` and `distance` are the geometry worked out for the contestant rather than left to
    it. A bolt only travels along the eight directions, so hitting anything requires the target to
    be on the same row, column or exact diagonal — arithmetic that a model is measurably bad at and
    that the game already knows the answer to.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    position: Position
    health: int
    # The direction a bolt would have to be fired to reach this robot, or None when it is not
    # lined up at all and no direction can reach it.
    direction: Direction | None = None
    # Steps away, counting a diagonal as one step — the same measure a move uses.
    distance: int = 0
