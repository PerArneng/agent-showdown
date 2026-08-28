from datetime import datetime

from agent_showdown.container import Container
from agent_showdown.interfaces.game import Direction, Move, Movement, PlayerTurn
from tests.fakes import FixedRandomizer, FrozenClock, InMemoryConsole, ScriptedTurnPlanner

_PLANNED = PlayerTurn(
    reasoning="walking the diagonal",
    movement=Movement(moves=(Move(direction=Direction.UP_LEFT),)),
)


def _planner() -> ScriptedTurnPlanner:
    """Stands in for the model, so the suite never opens a socket."""
    return ScriptedTurnPlanner([_PLANNED])


def _container(console: InMemoryConsole) -> Container:
    container = Container()
    container.clock.override(FrozenClock(datetime(2025, 9, 10)))
    container.console.override(console)
    container.randomizer.override(FixedRandomizer([3, 1]))
    container.turn_planner.override(_planner())
    return container


def test_container_wires_a_working_engine() -> None:
    console = InMemoryConsole()

    _container(console).engine().start_game()

    assert console.lines[0] == "2025-09-10 \x1b[32mINFO\x1b[0m started"
    assert "2025-09-10 \x1b[32mINFO\x1b[0m player dummy-1 joined at (0,0)" in console.lines
    assert console.lines[-1] == "2025-09-10 \x1b[32mINFO\x1b[0m game ended after 10 rounds"


def test_providers_are_singletons() -> None:
    container = Container()
    container.turn_planner.override(_planner())
    assert container.engine() is container.engine()
    assert container.logger() is container.logger()
    assert container.randomizer() is container.randomizer()


def test_the_game_factory_hands_out_a_fresh_game_each_time() -> None:
    from agent_showdown.interfaces.game import Board

    factory = Container().game_factory()
    assert factory.create(Board(width=2, height=2)) is not factory.create(Board(width=2, height=2))
