from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.game.action import Action


class PlayerTurn(BaseModel):
    """What a player hands back when the game asks it to act.

    One ordered plan: moves and casts interleaved, applied in the order given.
    """

    model_config = ConfigDict(frozen=True)

    reasoning: str
    actions: tuple[Action, ...]
