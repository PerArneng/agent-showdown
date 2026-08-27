from datetime import datetime
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from agent_showdown.interfaces.file_system import FileInfo
from agent_showdown.interfaces.game import (
    Direction,
    GameEndedEvent,
    GameEvent,
    Move,
    MoveBlockedEvent,
    Movement,
    PlayerMovedEvent,
    PlayerTurn,
    Position,
)
from agent_showdown.interfaces.log import LogLevel, LogRecord


def test_log_record_is_frozen() -> None:
    record = LogRecord(level=LogLevel.INFO, message="started", timestamp=datetime(2025, 9, 10))
    with pytest.raises(ValidationError):
        record.message = "changed"  # type: ignore[misc]


def test_file_info_is_frozen() -> None:
    info = FileInfo(
        path=Path("a.txt"),
        size_bytes=5,
        modified_at=datetime(2025, 9, 10),
        is_directory=False,
    )
    with pytest.raises(ValidationError):
        info.size_bytes = 6  # type: ignore[misc]


def test_log_record_rejects_an_unknown_level() -> None:
    with pytest.raises(ValidationError):
        LogRecord(level="TRACE", message="x", timestamp=datetime(2025, 9, 10))


def test_position_is_frozen() -> None:
    position = Position(x=1, y=2)
    with pytest.raises(ValidationError):
        position.x = 3  # type: ignore[misc]


def test_player_turn_is_frozen() -> None:
    turn = PlayerTurn(movement=Movement(moves=(Move(direction="UP"),)))
    with pytest.raises(ValidationError):
        turn.movement = Movement(moves=())  # type: ignore[misc]


def test_move_rejects_an_unknown_direction() -> None:
    with pytest.raises(ValidationError):
        Move(direction="SIDEWAYS")


def test_game_events_are_frozen() -> None:
    event = PlayerMovedEvent(
        player="dummy-1", source=Position(x=0, y=0), destination=Position(x=1, y=0)
    )
    with pytest.raises(ValidationError):
        event.player = "dummy-2"  # type: ignore[misc]


def test_a_game_event_round_trips_through_json_as_its_own_type() -> None:
    event = MoveBlockedEvent(player="dummy-1", position=Position(x=0, y=0), direction=Direction.UP)

    parsed: GameEvent = TypeAdapter(GameEvent).validate_json(event.model_dump_json())

    assert parsed == event


def test_the_discriminator_picks_the_right_event_type() -> None:
    parsed: GameEvent = TypeAdapter(GameEvent).validate_python(
        {"type": "game_ended", "rounds_played": 10}
    )

    assert parsed == GameEndedEvent(rounds_played=10)
