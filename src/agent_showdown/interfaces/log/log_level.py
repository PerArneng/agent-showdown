from enum import StrEnum


class LogLevel(StrEnum):
    """Severity of a log record."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
