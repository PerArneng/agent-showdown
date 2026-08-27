from datetime import datetime

from agent_showdown.interfaces.log import LogLevel
from agent_showdown.modules.log import AnsiLogFormatter, DefaultLogger
from tests.fakes import FrozenClock, InMemoryConsole


def _logger(console: InMemoryConsole) -> DefaultLogger:
    return DefaultLogger(
        clock=FrozenClock(datetime(2025, 9, 10)),
        formatter=AnsiLogFormatter(),
        console=console,
    )


def test_info_writes_one_line_to_the_console() -> None:
    console = InMemoryConsole()
    _logger(console).info("started")

    assert console.lines == ["2025-09-10 \x1b[32mINFO\x1b[0m started"]
    assert console.error_lines == []


def test_every_level_method_uses_its_own_level() -> None:
    console = InMemoryConsole()
    logger = _logger(console)

    logger.debug("d")
    logger.info("i")
    logger.warning("w")
    logger.error("e")
    logger.critical("c")

    levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL]
    assert len(console.lines) == len(levels)
    for line, level in zip(console.lines, levels, strict=True):
        assert level.value in line


def test_timestamp_comes_from_the_injected_clock() -> None:
    console = InMemoryConsole()
    DefaultLogger(
        clock=FrozenClock(datetime(1999, 12, 31)),
        formatter=AnsiLogFormatter(),
        console=console,
    ).info("started")

    assert console.lines[0].startswith("1999-12-31 ")
