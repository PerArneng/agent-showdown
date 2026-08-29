from agent_showdown.interfaces.event_channel import EventChannel
from agent_showdown.interfaces.game import (
    ArenaPausedEvent,
    ArenaResumedEvent,
    Board,
    BoardChangedEvent,
    Direction,
    GameEndedEvent,
    GameStartedEvent,
    MoveBlockedEvent,
    Player,
    PlayerDeadEvent,
    PlayerHitEvent,
    PlayerJoinedEvent,
    PlayerMovedEvent,
    PlayerReasonedEvent,
    PlayerRegisteredEvent,
    PlayerStats,
    PlayerStatsEvent,
    PlayerTurnEndedEvent,
    PlayerTurnStartedEvent,
    PlayerUnregisteredEvent,
    PlayerUpdatedEvent,
    Position,
    RoundStartedEvent,
    SpellCastEvent,
    TurnFailedEvent,
)


class ChannelGameListener:
    """Turns game events into published messages. Pure: it knows nothing about SSE or HTTP."""

    def __init__(self, channel: EventChannel) -> None:
        self._channel = channel

    def arena_paused(self) -> None:
        self._channel.publish(ArenaPausedEvent())

    def arena_resumed(self) -> None:
        self._channel.publish(ArenaResumedEvent())

    def player_registered(self, player: Player) -> None:
        self._channel.publish(PlayerRegisteredEvent(player=player.get_name()))

    def player_unregistered(self, name: str) -> None:
        self._channel.publish(PlayerUnregisteredEvent(player=name))

    def game_started(self, board: Board, max_rounds: int) -> None:
        self._channel.publish(GameStartedEvent(board=board, max_rounds=max_rounds))

    def player_joined(self, player: Player, position: Position) -> None:
        self._channel.publish(
            PlayerJoinedEvent(player=player.get_name(), position=position)
        )

    def board_changed(self, board: Board) -> None:
        self._channel.publish(BoardChangedEvent(board=board))

    def round_started(self, round_number: int) -> None:
        self._channel.publish(RoundStartedEvent(round_number=round_number))

    def player_turn_started(self, player: Player) -> None:
        self._channel.publish(PlayerTurnStartedEvent(player=player.get_name()))

    def player_turn_ended(self, player: Player, seconds: float) -> None:
        self._channel.publish(PlayerTurnEndedEvent(player=player.get_name(), seconds=seconds))

    def player_stats(self, player: Player, stats: PlayerStats) -> None:
        self._channel.publish(PlayerStatsEvent(player=player.get_name(), stats=stats))

    def player_dead(self, player: Player) -> None:
        self._channel.publish(PlayerDeadEvent(player=player.get_name()))

    def player_moved(self, player: Player, source: Position, destination: Position) -> None:
        self._channel.publish(
            PlayerMovedEvent(player=player.get_name(), source=source, destination=destination)
        )

    def player_reasoned(self, player: Player, reasoning: str) -> None:
        self._channel.publish(PlayerReasonedEvent(player=player.get_name(), reasoning=reasoning))

    def spell_cast(
        self,
        player: Player,
        spell: str,
        origin: Position,
        direction: Direction,
        path: tuple[Position, ...],
    ) -> None:
        self._channel.publish(
            SpellCastEvent(
                player=player.get_name(),
                spell=spell,
                direction=direction,
                origin=origin,
                path=path,
            )
        )

    def player_hit(
        self, player: Player, source: Player, spell: str, damage: int, position: Position
    ) -> None:
        self._channel.publish(
            PlayerHitEvent(
                player=player.get_name(),
                source=source.get_name(),
                spell=spell,
                damage=damage,
                position=position,
            )
        )

    def player_updated(self, player: Player, health: int) -> None:
        self._channel.publish(PlayerUpdatedEvent(player=player.get_name(), health=health))

    def move_blocked(self, player: Player, position: Position, direction: Direction) -> None:
        self._channel.publish(
            MoveBlockedEvent(player=player.get_name(), position=position, direction=direction)
        )

    def turn_failed(self, player: Player, reason: str) -> None:
        self._channel.publish(TurnFailedEvent(player=player.get_name(), reason=reason))

    def game_ended(self, rounds_played: int) -> None:
        self._channel.publish(GameEndedEvent(rounds_played=rounds_played))
