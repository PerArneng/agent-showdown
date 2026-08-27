from datetime import datetime

from agent_showdown.container import Container
from tests.fakes import FrozenClock, InMemoryConsole


def test_container_wires_a_working_engine() -> None:
    console = InMemoryConsole()
    container = Container()
    container.clock.override(FrozenClock(datetime(2025, 9, 10)))
    container.console.override(console)

    container.engine().start()

    assert console.lines == ["2025-09-10 \x1b[32mINFO\x1b[0m started"]


def test_providers_are_singletons() -> None:
    container = Container()
    assert container.engine() is container.engine()
    assert container.logger() is container.logger()
