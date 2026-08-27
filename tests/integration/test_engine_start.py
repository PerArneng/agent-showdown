from datetime import datetime

from agent_showdown.modules.engine import DefaultEngine
from agent_showdown.modules.log import AnsiLogFormatter, DefaultLogger
from tests.fakes import FrozenClock, InMemoryConsole


def test_start_logs_one_info_line_entirely_in_memory() -> None:
    console = InMemoryConsole()
    engine = DefaultEngine(
        logger=DefaultLogger(
            clock=FrozenClock(datetime(2025, 9, 10)),
            formatter=AnsiLogFormatter(),
            console=console,
        )
    )

    engine.start()

    assert console.lines == ["2025-09-10 \x1b[32mINFO\x1b[0m started"]
    assert console.error_lines == []
