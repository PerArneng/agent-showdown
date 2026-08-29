import threading
import time
from collections.abc import Callable
from datetime import datetime

from agent_showdown.container import Container
from agent_showdown.interfaces.config import AppConfig
from agent_showdown.interfaces.game import Action, ActionKind, Board, Direction, PlayerTurn
from tests.fakes import FixedRandomizer, FrozenClock, InMemoryConsole, ScriptedAgentRoster

_PLANNED = PlayerTurn(
    reasoning="walking the diagonal",
    actions=(Action(kind=ActionKind.MOVE, direction=Direction.UP_LEFT),),
)


def _roster() -> ScriptedAgentRoster:
    """Stands in for the model, so the suite never opens a socket."""
    return ScriptedAgentRoster(("simple-strands-1",), [_PLANNED])


def _container(console: InMemoryConsole) -> Container:
    container = Container()
    container.clock.override(FrozenClock(datetime(2025, 9, 10)))
    container.console.override(console)
    container.randomizer.override(FixedRandomizer([3, 1]))
    # Short matches: the point is the wiring, not a long game.
    container.config.override(AppConfig(max_rounds=2))
    container.agent_roster.override(_roster())
    return container


def _wait_until(condition: Callable[[], bool], seconds: float = 5.0) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline and not condition():
        time.sleep(0.01)


def test_container_wires_a_working_arena() -> None:
    console = InMemoryConsole()
    container = _container(console)
    engine = container.engine()
    for player in container.agent_roster().create_players():
        engine.register_player(player)

    thread = threading.Thread(target=engine.run_arena, daemon=True)
    thread.start()
    _wait_until(lambda: any("game ended" in line for line in console.lines))
    engine.stop_arena()
    thread.join(timeout=5.0)

    joined = "2025-09-10 \x1b[32mINFO\x1b[0m player simple-strands-1 joined at (0,0)"
    assert joined in console.lines
    assert any("game ended after" in line for line in console.lines)


def test_an_arena_nobody_joined_pauses_rather_than_playing() -> None:
    console = InMemoryConsole()
    engine = _container(console).engine()

    thread = threading.Thread(target=engine.run_arena, daemon=True)
    thread.start()
    _wait_until(lambda: any("arena paused" in line for line in console.lines))
    engine.stop_arena()
    thread.join(timeout=5.0)

    assert any("arena paused" in line for line in console.lines)
    assert not any("game started" in line for line in console.lines)


def test_providers_are_singletons() -> None:
    container = Container()
    container.config.override(AppConfig())
    container.agent_roster.override(_roster())
    assert container.engine() is container.engine()
    assert container.logger() is container.logger()
    assert container.randomizer() is container.randomizer()
    # One roster shared by the arena and by everyone joining over HTTP.
    assert container.player_registry() is container.player_registry()


def test_the_game_factory_hands_out_a_fresh_game_each_time() -> None:
    factory = Container().game_factory()
    assert factory.create(Board(width=2, height=2)) is not factory.create(Board(width=2, height=2))
