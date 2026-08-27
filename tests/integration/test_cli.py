from datetime import datetime

from typer.testing import CliRunner

from agent_showdown.cli import main as cli_main
from agent_showdown.container import Container
from tests.fakes import FrozenClock, InMemoryConsole

runner = CliRunner()


def test_start_command_exits_cleanly_and_prints_the_line() -> None:
    result = runner.invoke(cli_main.app, ["start"])

    assert result.exit_code == 0
    assert result.stdout.strip().endswith("started")
    assert "INFO" in result.stdout


def test_start_command_goes_through_the_engine() -> None:
    console = InMemoryConsole()
    container = Container()
    container.clock.override(FrozenClock(datetime(2025, 9, 10)))
    container.console.override(console)

    container.engine().start()

    assert console.lines == ["2025-09-10 \x1b[32mINFO\x1b[0m started"]


def test_no_args_shows_help() -> None:
    result = runner.invoke(cli_main.app, [])
    assert "start" in result.stdout
