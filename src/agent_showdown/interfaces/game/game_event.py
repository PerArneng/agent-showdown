from typing import Annotated

from pydantic import Field

from agent_showdown.interfaces.game.arena_paused_event import ArenaPausedEvent
from agent_showdown.interfaces.game.arena_resumed_event import ArenaResumedEvent
from agent_showdown.interfaces.game.game_ended_event import GameEndedEvent
from agent_showdown.interfaces.game.game_started_event import GameStartedEvent
from agent_showdown.interfaces.game.move_blocked_event import MoveBlockedEvent
from agent_showdown.interfaces.game.player_dead_event import PlayerDeadEvent
from agent_showdown.interfaces.game.player_hit_event import PlayerHitEvent
from agent_showdown.interfaces.game.player_joined_event import PlayerJoinedEvent
from agent_showdown.interfaces.game.player_moved_event import PlayerMovedEvent
from agent_showdown.interfaces.game.player_reasoned_event import PlayerReasonedEvent
from agent_showdown.interfaces.game.player_registered_event import PlayerRegisteredEvent
from agent_showdown.interfaces.game.player_stats_event import PlayerStatsEvent
from agent_showdown.interfaces.game.player_turn_ended_event import PlayerTurnEndedEvent
from agent_showdown.interfaces.game.player_turn_started_event import PlayerTurnStartedEvent
from agent_showdown.interfaces.game.player_unregistered_event import PlayerUnregisteredEvent
from agent_showdown.interfaces.game.player_updated_event import PlayerUpdatedEvent
from agent_showdown.interfaces.game.round_started_event import RoundStartedEvent
from agent_showdown.interfaces.game.spell_cast_event import SpellCastEvent
from agent_showdown.interfaces.game.turn_failed_event import TurnFailedEvent

# One event per GameListener method, told apart by `type`. This is what crosses a wire, so the
# player is named rather than referenced.
GameEvent = Annotated[
    ArenaPausedEvent
    | ArenaResumedEvent
    | PlayerRegisteredEvent
    | PlayerUnregisteredEvent
    | GameStartedEvent
    | PlayerJoinedEvent
    | RoundStartedEvent
    | PlayerTurnStartedEvent
    | PlayerTurnEndedEvent
    | PlayerStatsEvent
    | PlayerMovedEvent
    | PlayerReasonedEvent
    | PlayerDeadEvent
    | SpellCastEvent
    | PlayerHitEvent
    | PlayerUpdatedEvent
    | MoveBlockedEvent
    | TurnFailedEvent
    | GameEndedEvent,
    Field(discriminator="type"),
]
