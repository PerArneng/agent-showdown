from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.game.action_kind import ActionKind
from agent_showdown.interfaces.game.direction import Direction


class Action(BaseModel):
    """One entry of a turn plan: a step, or a spell aimed down a direction.

    Deliberately flat rather than a union of a move and a cast model. This is handed to a model as
    a structured-output JSON schema, and a flat object survives guided decoding where an `anyOf`
    often does not. `spell` is ignored when `kind` is MOVE.
    """

    model_config = ConfigDict(frozen=True)

    kind: ActionKind
    direction: Direction
    spell: str = ""
