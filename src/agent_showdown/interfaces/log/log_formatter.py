from typing import Protocol

from agent_showdown.interfaces.log.log_record import LogRecord


class LogFormatter(Protocol):
    """Renders a log record as one line of text. Always pure."""

    def format(self, record: LogRecord) -> str:
        """Return the rendered line for the record."""
        ...
