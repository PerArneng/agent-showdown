from dependency_injector import containers, providers

from agent_showdown.modules.clock import SystemClock
from agent_showdown.modules.console import StdioConsole
from agent_showdown.modules.engine import DefaultEngine
from agent_showdown.modules.file_system import LocalFileSystem
from agent_showdown.modules.game import DefaultGameFactory, DummyPlayerFactory, LogGameListener
from agent_showdown.modules.log import AnsiLogFormatter, DefaultLogger
from agent_showdown.modules.randomizer import SystemRandomizer


class Container(containers.DeclarativeContainer):
    """Wires every implementation together. Instantiated only by the composition root."""

    clock = providers.Singleton(SystemClock)
    console = providers.Singleton(StdioConsole)
    file_system = providers.Singleton(LocalFileSystem)
    randomizer = providers.Singleton(SystemRandomizer)
    log_formatter = providers.Singleton(AnsiLogFormatter)
    logger = providers.Singleton(
        DefaultLogger,
        clock=clock,
        formatter=log_formatter,
        console=console,
    )
    game_factory = providers.Singleton(DefaultGameFactory)
    player_factory = providers.Singleton(DummyPlayerFactory, randomizer=randomizer)
    log_game_listener = providers.Singleton(LogGameListener, logger=logger)
    # The listener set for a run. A second listener is one more line here.
    game_listeners = providers.List(log_game_listener)
    engine = providers.Singleton(
        DefaultEngine,
        logger=logger,
        game_factory=game_factory,
        player_factory=player_factory,
        game_listeners=game_listeners,
    )
