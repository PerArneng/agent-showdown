from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.game.board import Board
from agent_showdown.interfaces.game.opponent import Opponent
from agent_showdown.interfaces.game.position import Position
from agent_showdown.interfaces.game.spell_info import SpellInfo


class GameView(BaseModel):
    """What a player is shown when asked for its turn. It never sees the board itself."""

    model_config = ConfigDict(frozen=True)

    board: Board
    position: Position
    round_number: int
    health: int
    opponents: tuple[Opponent, ...] = ()
    spells: tuple[SpellInfo, ...] = ()
