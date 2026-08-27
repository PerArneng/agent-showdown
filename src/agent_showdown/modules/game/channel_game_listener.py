from agent_showdown.interfaces.event_channel import EventChannel
from agent_showdown.interfaces.game import (
    Board,
    Direction,
    GameEndedEvent,
    GameStartedEvent,
    MoveBlockedEvent,
    Player,
    PlayerJoinedEvent,
    PlayerMovedEvent,
    Position,
    RoundStartedEvent,
    TurnFailedEvent,
)


class ChannelGameListener:
    """Turns game events into published messages. Pure: it knows nothing about SSE or HTTP."""

    def __init__(self, channel: EventChannel) -> None:
        self._channel = channel

    def game_started(self, board: Board, max_rounds: int) -> None:
        self._channel.publish(GameStartedEvent(board=board, max_rounds=max_rounds))

    def player_joined(self, player: Player, position: Position) -> None:
        self._channel.publish(
            PlayerJoinedEvent(player=player.get_name(), position=position)
        )

    def round_started(self, round_number: int) -> None:
        self._channel.publish(RoundStartedEvent(round_number=round_number))

    def player_moved(self, player: Player, source: Position, destination: Position) -> None:
        self._channel.publish(
            PlayerMovedEvent(player=player.get_name(), source=source, destination=destination)
        )

    def move_blocked(self, player: Player, position: Position, direction: Direction) -> None:
        self._channel.publish(
            MoveBlockedEvent(player=player.get_name(), position=position, direction=direction)
        )

    def turn_failed(self, player: Player, reason: str) -> None:
        self._channel.publish(TurnFailedEvent(player=player.get_name(), reason=reason))

    def game_ended(self, rounds_played: int) -> None:
        self._channel.publish(GameEndedEvent(rounds_played=rounds_played))
