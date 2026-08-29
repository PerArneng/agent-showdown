from pathlib import Path
from typing import Annotated

import typer

from agent_showdown.container import Container
from agent_showdown.modules.config import DEFAULT_CONFIG_PATH
from agent_showdown.web import WebServer, create_app, find_client_dir
from agent_showdown.web.client_dir import BUILD_COMMAND

app = typer.Typer(help="agent-showdown", no_args_is_help=True)

_DEFAULT_PORT = 8066


@app.callback()
def cli() -> None:
    """Keep the app a command group even while `start` is the only subcommand."""


@app.command()
def start(
    port: Annotated[
        int, typer.Option(help="Port to serve the web client on.")
    ] = _DEFAULT_PORT,
    client_dir: Annotated[
        Path | None,
        typer.Option(help="Directory holding the built web client. Found by default."),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            help=f"Agent configuration. Defaults to ./{DEFAULT_CONFIG_PATH} when it exists."
        ),
    ] = None,
) -> None:
    """Serve the web client. The arena plays on its own; the browser watches and interrupts."""
    container = Container()  # Composition root. The only place the container is instantiated.
    logger = container.logger()
    try:
        # Two steps, because loading the config needs the container's file system.
        loaded = container.config_loader().load(config)
        container.config.override(loaded)
    except (FileNotFoundError, ValueError) as error:
        logger.error(str(error))
        raise typer.Exit(code=1) from error
    resolved = find_client_dir(container.file_system(), client_dir)
    if resolved is None:
        logger.error(f"the web client is not built. Run: {BUILD_COMMAND}")
        raise typer.Exit(code=1)

    # Whoever the config names sits down before the arena starts, so a configured run plays
    # immediately. Everyone else joins over HTTP.
    engine = container.engine()
    for player in container.agent_roster().create_players():
        engine.register_player(player)
    for number in range(1, loaded.dummies + 1):
        engine.register_player(container.player_factory().create(f"dummy-{number}"))

    server = WebServer()
    web_app = create_app(
        engine=engine,
        event_channel=container.event_channel(),
        file_system=container.file_system(),
        agent_player_factory=container.agent_player_factory(),
        client_dir=resolved,
        stopping=server.stopping,
    )
    logger.info(f"serving on http://127.0.0.1:{port}")
    server.run(web_app, port)


def main() -> None:
    app()
