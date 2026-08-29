from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.game.obstacle import Obstacle


class Board(BaseModel):
    """The game world: a grid of cells, some of them obstructed.

    Terrain is fixed for the length of a match, so it rides on the board itself rather than
    arriving as events. That is also what carries it to the browser for free: a `Board` is
    already embedded in `game_started` and in the snapshot.
    """

    model_config = ConfigDict(frozen=True)

    width: int
    height: int
    obstacles: tuple[Obstacle, ...] = ()
