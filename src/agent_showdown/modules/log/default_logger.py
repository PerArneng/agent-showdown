from agent_showdown.interfaces.clock import Clock
from agent_showdown.interfaces.console import Console
from agent_showdown.interfaces.log import LogFormatter, LogLevel, LogRecord


class DefaultLogger:
    """Builds a record, has it formatted, and hands the line to the console.

    The only class permitted to depend on `Console`.
    """

    def __init__(self, clock: Clock, formatter: LogFormatter, console: Console) -> None:
        self._clock = clock
        self._formatter = formatter
        self._console = console

    def debug(self, message: str) -> None:
        self._log(LogLevel.DEBUG, message)

    def info(self, message: str) -> None:
        self._log(LogLevel.INFO, message)

    def warning(self, message: str) -> None:
        self._log(LogLevel.WARNING, message)

    def error(self, message: str) -> None:
        self._log(LogLevel.ERROR, message)

    def critical(self, message: str) -> None:
        self._log(LogLevel.CRITICAL, message)

    def _log(self, level: LogLevel, message: str) -> None:
        record = LogRecord(level=level, message=message, timestamp=self._clock.now())
        self._console.write_line(self._formatter.format(record))
