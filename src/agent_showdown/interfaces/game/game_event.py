from typing import Annotated

from pydantic import Field

from agent_showdown.interfaces.game.game_ended_event import GameEndedEvent
from agent_showdown.interfaces.game.game_started_event import GameStartedEvent
from agent_showdown.interfaces.game.move_blocked_event import MoveBlockedEvent
from agent_showdown.interfaces.game.player_joined_event import PlayerJoinedEvent
from agent_showdown.interfaces.game.player_moved_event import PlayerMovedEvent
from agent_showdown.interfaces.game.player_reasoned_event import PlayerReasonedEvent
from agent_showdown.interfaces.game.round_started_event import RoundStartedEvent
from agent_showdown.interfaces.game.turn_failed_event import TurnFailedEvent

# One event per GameListener method, told apart by `type`. This is what crosses a wire, so the
# player is named rather than referenced.
GameEvent = Annotated[
    GameStartedEvent
    | PlayerJoinedEvent
    | RoundStartedEvent
    | PlayerMovedEvent
    | PlayerReasonedEvent
    | MoveBlockedEvent
    | TurnFailedEvent
    | GameEndedEvent,
    Field(discriminator="type"),
]
