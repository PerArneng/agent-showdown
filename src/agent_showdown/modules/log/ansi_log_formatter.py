from typing import Final

from agent_showdown.interfaces.log import LogLevel, LogRecord

TIMESTAMP_FORMAT: Final = "%Y-%m-%d"

RESET: Final = "\x1b[0m"

LEVEL_COLORS: Final[dict[LogLevel, str]] = {
    LogLevel.DEBUG: "\x1b[36m",
    LogLevel.INFO: "\x1b[32m",
    LogLevel.WARNING: "\x1b[33m",
    LogLevel.ERROR: "\x1b[31m",
    LogLevel.CRITICAL: "\x1b[1;31m",
}


class AnsiLogFormatter:
    """Pure. Renders a record as `<timestamp> <colored level> <message>`.

    Only the level token is colored; the timestamp and message are left untouched.
    """

    def format(self, record: LogRecord) -> str:
        timestamp = record.timestamp.strftime(TIMESTAMP_FORMAT)
        color = LEVEL_COLORS[record.level]
        return f"{timestamp} {color}{record.level.value}{RESET} {record.message}"
