from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.game.board import Board
from agent_showdown.interfaces.game.player_snapshot import PlayerSnapshot


class GameSnapshot(BaseModel):
    """The current game, as a value.

    `GET /api/events` is a live stream with no replay, so a client that connects mid-game never
    learns the board it is meant to draw on. This is that missing state and nothing else: what the
    stream would have told a client that had been listening from the start.
    """

    model_config = ConfigDict(frozen=True)

    board: Board | None = None
    max_rounds: int = 0
    round_number: int = 0
    playing: bool = False
    # No contestants registered, so nothing is being played and nothing will be until
    # somebody joins. A client that connects while the arena is idle needs to say so.
    paused: bool = False
    players: tuple[PlayerSnapshot, ...] = ()
    # Who is in the arena, which is not the same as who is on the board: the roster changes
    # between matches. Filled from the registry when the snapshot is asked for, so there is one
    # source of truth and no second copy to keep in step.
    registered: tuple[str, ...] = ()
