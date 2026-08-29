from dependency_injector import containers, providers

from agent_showdown.interfaces.config import AppConfig
from agent_showdown.modules.builtin_agents import SimpleStrandsRoster
from agent_showdown.modules.clock import SystemClock
from agent_showdown.modules.config import YamlConfigLoader
from agent_showdown.modules.console import StdioConsole
from agent_showdown.modules.engine import DefaultEngine
from agent_showdown.modules.event_channel import QueueEventChannel
from agent_showdown.modules.file_system import LocalFileSystem
from agent_showdown.modules.game import (
    ChannelGameListener,
    DefaultGameFactory,
    DefaultScoreboard,
    DefaultSpellBook,
    DummyPlayerFactory,
    LogGameListener,
    SnapshotGameListener,
)
from agent_showdown.modules.log import AnsiLogFormatter, DefaultLogger
from agent_showdown.modules.randomizer import SystemRandomizer


class Container(containers.DeclarativeContainer):
    """Wires every implementation together. Instantiated only by the composition root."""

    # Resolved by the composition root: loading it needs `file_system`, which only exists
    # once the container is built.
    config = providers.Dependency(instance_of=AppConfig)

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
    spell_book = providers.Singleton(DefaultSpellBook)
    # A singleton, so eliminations, deaths and wins survive the match they were earned in.
    scoreboard = providers.Singleton(DefaultScoreboard)
    game_factory = providers.Singleton(
        DefaultGameFactory,
        clock=clock,
        spell_book=spell_book,
        scoreboard=scoreboard,
    )
    player_factory = providers.Singleton(
        DummyPlayerFactory,
        randomizer=randomizer,
        clock=clock,
        # Long enough that a human can watch the bots move.
        think_time=0.5,
    )
    config_loader = providers.Singleton(YamlConfigLoader, file_system=file_system)
    # One planner, and one contestant, per configured agent endpoint.
    agent_roster = providers.Singleton(SimpleStrandsRoster, configs=config.provided.agents)
    event_channel = providers.Singleton(QueueEventChannel)
    log_game_listener = providers.Singleton(LogGameListener, logger=logger)
    # Both a listener and the engine's snapshot source, so a browser that connects mid-game can
    # ask what it missed.
    snapshot_game_listener = providers.Singleton(SnapshotGameListener)
    channel_game_listener = providers.Singleton(ChannelGameListener, channel=event_channel)
    # The listener set for a run: the terminal log, and whatever the browser is watching.
    game_listeners = providers.List(
        log_game_listener, channel_game_listener, snapshot_game_listener
    )
    engine = providers.Singleton(
        DefaultEngine,
        logger=logger,
        game_factory=game_factory,
        player_factory=player_factory,
        agent_roster=agent_roster,
        game_listeners=game_listeners,
        snapshot_source=snapshot_game_listener,
        max_games=config.provided.max_games,
        max_rounds=config.provided.max_rounds,
    )
