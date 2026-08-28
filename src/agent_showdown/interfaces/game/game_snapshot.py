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
    players: tuple[PlayerSnapshot, ...] = ()
