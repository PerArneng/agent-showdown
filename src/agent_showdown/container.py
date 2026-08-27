from dependency_injector import containers, providers

from agent_showdown.modules.clock import SystemClock
from agent_showdown.modules.console import StdioConsole
from agent_showdown.modules.engine import DefaultEngine
from agent_showdown.modules.file_system import LocalFileSystem
from agent_showdown.modules.log import AnsiLogFormatter, DefaultLogger


class Container(containers.DeclarativeContainer):
    """Wires every implementation together. Instantiated only by the composition root."""

    clock = providers.Singleton(SystemClock)
    console = providers.Singleton(StdioConsole)
    file_system = providers.Singleton(LocalFileSystem)
    log_formatter = providers.Singleton(AnsiLogFormatter)
    logger = providers.Singleton(
        DefaultLogger,
        clock=clock,
        formatter=log_formatter,
        console=console,
    )
    engine = providers.Singleton(DefaultEngine, logger=logger)
