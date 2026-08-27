from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.game.movement import Movement


class PlayerTurn(BaseModel):
    """What a player hands back when the game asks it to act."""

    model_config = ConfigDict(frozen=True)

    movement: Movement
