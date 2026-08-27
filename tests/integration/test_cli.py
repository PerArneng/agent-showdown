from datetime import datetime

import pytest
from fastapi import FastAPI
from typer.testing import CliRunner

from agent_showdown.cli import main as cli_main
from agent_showdown.container import Container
from tests.fakes import FixedRandomizer, FrozenClock, InMemoryConsole

runner = CliRunner()


class RecordingServer:
    """Stands in for uvicorn so no test ever binds a socket."""

    def __init__(self) -> None:
        self.calls: list[tuple[FastAPI, int]] = []

    def stopping(self) -> bool:
        return False

    def run(self, app: FastAPI, port: int) -> None:
        self.calls.append((app, port))


@pytest.fixture
def server(monkeypatch: pytest.MonkeyPatch) -> RecordingServer:
    recording = RecordingServer()
    monkeypatch.setattr(cli_main, "WebServer", lambda: recording)
    return recording


def test_start_serves_on_the_default_port(server: RecordingServer) -> None:
    result = runner.invoke(cli_main.app, ["start"])

    assert result.exit_code == 0
    assert [port for _, port in server.calls] == [8066]


def test_start_honours_the_port_flag(server: RecordingServer) -> None:
    result = runner.invoke(cli_main.app, ["start", "--port", "9000"])

    assert result.exit_code == 0
    assert [port for _, port in server.calls] == [9000]


def test_start_logs_the_url(server: RecordingServer) -> None:
    result = runner.invoke(cli_main.app, ["start", "--port", "9000"])

    assert "http://127.0.0.1:9000" in result.stdout
    assert "INFO" in result.stdout


def test_start_builds_a_real_app(server: RecordingServer) -> None:
    runner.invoke(cli_main.app, ["start"])

    app, _ = server.calls[0]
    routes = {getattr(route, "path", None) for route in app.routes}
    assert {"/", "/api/start", "/api/events"} <= routes


def test_the_container_still_plays_a_game() -> None:
    console = InMemoryConsole()
    container = Container()
    container.clock.override(FrozenClock(datetime(2025, 9, 10)))
    container.console.override(console)
    container.randomizer.override(FixedRandomizer([3, 1]))

    container.engine().start_game()

    assert console.lines[0] == "2025-09-10 \x1b[32mINFO\x1b[0m started"


def test_no_args_shows_help() -> None:
    result = runner.invoke(cli_main.app, [])
    assert "start" in result.stdout


def test_help_documents_the_port_flag() -> None:
    result = runner.invoke(cli_main.app, ["start", "--help"])
    assert "--port" in result.stdout

