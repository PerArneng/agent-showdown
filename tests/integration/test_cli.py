import threading
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import pytest
from fastapi import FastAPI
from typer.testing import CliRunner, Result

from agent_showdown.cli import main as cli_main
from agent_showdown.container import Container
from agent_showdown.interfaces.config import AppConfig
from agent_showdown.interfaces.game import Action, ActionKind, Direction, PlayerTurn
from tests.fakes import FixedRandomizer, FrozenClock, InMemoryConsole, ScriptedAgentRoster

runner = CliRunner()


def _wait_until(condition: Callable[[], bool], seconds: float = 5.0) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline and not condition():
        time.sleep(0.01)


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


@pytest.fixture
def client_dir(tmp_path: Path) -> Path:
    """A built client, as far as the CLI is concerned."""
    (tmp_path / "index.html").write_text("<!doctype html>")
    return tmp_path


def _start(client_dir: Path, *args: str) -> Result:
    return runner.invoke(cli_main.app, ["start", "--client-dir", str(client_dir), *args])


def test_start_serves_on_the_default_port(
    server: RecordingServer, client_dir: Path
) -> None:
    result = _start(client_dir)

    assert result.exit_code == 0
    assert [port for _, port in server.calls] == [8066]


def test_start_honours_the_port_flag(server: RecordingServer, client_dir: Path) -> None:
    result = _start(client_dir, "--port", "9000")

    assert result.exit_code == 0
    assert [port for _, port in server.calls] == [9000]


def test_start_logs_the_url(server: RecordingServer, client_dir: Path) -> None:
    result = _start(client_dir, "--port", "9000")

    assert "http://127.0.0.1:9000" in result.stdout
    assert "INFO" in result.stdout


def test_start_builds_a_real_app(server: RecordingServer, client_dir: Path) -> None:
    _start(client_dir)

    app, _ = server.calls[0]
    routes = {getattr(route, "path", None) for route in app.routes}
    assert {"/", "/api/new-game", "/api/players", "/api/events"} <= routes


def test_the_container_still_plays_a_game() -> None:
    console = InMemoryConsole()
    container = Container()
    container.clock.override(FrozenClock(datetime(2025, 9, 10)))
    container.console.override(console)
    container.randomizer.override(FixedRandomizer([3, 1]))
    container.config.override(AppConfig(max_rounds=2))
    # Stands in for the model, so the suite never opens a socket.
    container.agent_roster.override(
        ScriptedAgentRoster(
            turns=[
                PlayerTurn(
                    reasoning="",
                    actions=(Action(kind=ActionKind.MOVE, direction=Direction.UP),),
                )
            ]
        )
    )
    engine = container.engine()
    for player in container.agent_roster().create_players():
        engine.register_player(player)

    # The arena never returns on its own, so it is driven the way the server drives it.
    thread = threading.Thread(target=engine.run_arena, daemon=True)
    thread.start()
    _wait_until(lambda: any("game ended" in line for line in console.lines))
    engine.stop_arena()
    thread.join(timeout=5.0)

    assert "2025-09-10 \x1b[32mINFO\x1b[0m match 1 started" in console.lines
    assert any("game ended after" in line for line in console.lines)


def test_start_refuses_when_the_client_is_not_built(
    server: RecordingServer, tmp_path: Path
) -> None:
    result = _start(tmp_path / "never-built")

    assert result.exit_code == 1
    assert "not built" in result.stdout
    assert "npm --prefix web_client run build" in result.stdout
    assert server.calls == []


def test_start_refuses_a_config_path_that_does_not_exist(
    server: RecordingServer, client_dir: Path, tmp_path: Path
) -> None:
    result = _start(client_dir, "--config", str(tmp_path / "absent.yaml"))

    assert result.exit_code == 1
    assert "no config file at" in result.stdout
    assert server.calls == []


def test_start_refuses_a_config_it_cannot_parse(
    server: RecordingServer, client_dir: Path, tmp_path: Path
) -> None:
    broken = tmp_path / "broken.yaml"
    broken.write_text("agents:\n  - name: a\n    tokens: 3\n")

    result = _start(client_dir, "--config", str(broken))

    assert result.exit_code == 1
    assert "not a valid config" in result.stdout
    assert server.calls == []


def test_start_accepts_a_config_naming_its_own_agents(
    server: RecordingServer, client_dir: Path, tmp_path: Path
) -> None:
    config = tmp_path / "showdown.yaml"
    config.write_text(
        "agents:\n  - name: local\n    base_url: http://localhost:1234/v1\n"
        "    model_id: qwen/qwen3.8-27b\n"
    )

    result = _start(client_dir, "--config", str(config))

    assert result.exit_code == 0
    assert len(server.calls) == 1


def test_help_documents_the_config_flag() -> None:
    result = runner.invoke(cli_main.app, ["start", "--help"])
    assert "--config" in result.stdout


def test_help_documents_the_client_dir_flag() -> None:
    result = runner.invoke(cli_main.app, ["start", "--help"])
    assert "--client-dir" in result.stdout


def test_no_args_shows_help() -> None:
    result = runner.invoke(cli_main.app, [])
    assert "start" in result.stdout


def test_help_documents_the_port_flag() -> None:
    result = runner.invoke(cli_main.app, ["start", "--help"])
    assert "--port" in result.stdout

