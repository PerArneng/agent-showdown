from datetime import datetime

import pytest

from agent_showdown.interfaces.log import LogLevel, LogRecord
from agent_showdown.modules.log import AnsiLogFormatter


def _record(level: LogLevel = LogLevel.INFO, message: str = "started") -> LogRecord:
    return LogRecord(level=level, message=message, timestamp=datetime(2025, 9, 10, 13, 45, 0))


def test_formats_timestamp_level_and_message() -> None:
    line = AnsiLogFormatter().format(_record())
    assert line == "2025-09-10 \x1b[32mINFO\x1b[0m started"


@pytest.mark.parametrize(
    ("level", "color"),
    [
        (LogLevel.DEBUG, "\x1b[36m"),
        (LogLevel.INFO, "\x1b[32m"),
        (LogLevel.WARNING, "\x1b[33m"),
        (LogLevel.ERROR, "\x1b[31m"),
        (LogLevel.CRITICAL, "\x1b[1;31m"),
    ],
)
def test_each_level_gets_its_color(level: LogLevel, color: str) -> None:
    line = AnsiLogFormatter().format(_record(level=level))
    assert line == f"2025-09-10 {color}{level.value}\x1b[0m started"


def test_only_the_level_is_colored() -> None:
    line = AnsiLogFormatter().format(_record(message="started"))
    timestamp, rest = line.split(" ", 1)
    colored_level, message = rest.split(" ", 1)

    assert "\x1b" not in timestamp
    assert "\x1b" not in message
    assert colored_level.startswith("\x1b[32m")
    assert colored_level.endswith("\x1b[0m")


def test_message_is_not_escaped_or_truncated() -> None:
    line = AnsiLogFormatter().format(_record(message="two words  and  spaces"))
    assert line.endswith(" two words  and  spaces")
