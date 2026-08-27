from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from agent_showdown.interfaces.file_system import FileInfo
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
