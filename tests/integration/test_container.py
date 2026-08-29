from datetime import datetime

from agent_showdown.container import Container
from agent_showdown.interfaces.config import AppConfig
from agent_showdown.interfaces.game import Action, ActionKind, Direction, PlayerTurn
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
    # One short match: the point is the wiring, not a ten-match series.
    container.config.override(AppConfig(max_games=1, max_rounds=10))
    container.agent_roster.override(_roster())
    return container


def test_container_wires_a_working_engine() -> None:
    console = InMemoryConsole()

    _container(console).engine().start_game()

    assert console.lines[0] == "2025-09-10 \x1b[32mINFO\x1b[0m match 1 of 1 started"
    assert "2025-09-10 \x1b[32mINFO\x1b[0m player dummy-1 joined at (0,0)" in console.lines
    assert "2025-09-10 \x1b[32mINFO\x1b[0m game ended after 10 rounds" in console.lines
    assert console.lines[-1] == "2025-09-10 \x1b[32mINFO\x1b[0m series ended"


def test_providers_are_singletons() -> None:
    container = Container()
    container.config.override(AppConfig())
    container.agent_roster.override(_roster())
    assert container.engine() is container.engine()
    assert container.logger() is container.logger()
    assert container.randomizer() is container.randomizer()


def test_the_game_factory_hands_out_a_fresh_game_each_time() -> None:
    from agent_showdown.interfaces.game import Board

    factory = Container().game_factory()
    assert factory.create(Board(width=2, height=2)) is not factory.create(Board(width=2, height=2))
