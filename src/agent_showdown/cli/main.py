import typer

from agent_showdown.container import Container
from agent_showdown.web import INDEX_PATH, WebServer, create_app

app = typer.Typer(help="agent-showdown", no_args_is_help=True)

_DEFAULT_PORT = 8066


@app.callback()
def cli() -> None:
    """Keep the app a command group even while `start` is the only subcommand."""


@app.command()
def start(port: int = typer.Option(_DEFAULT_PORT, help="Port to serve the web client on.")) -> None:
    """Serve the web client. Games are started from the browser."""
    container = Container()  # Composition root. The only place the container is instantiated.
    server = WebServer()
    web_app = create_app(
        engine=container.engine(),
        event_channel=container.event_channel(),
        file_system=container.file_system(),
        index_path=INDEX_PATH,
        stopping=server.stopping,
    )
    container.logger().info(f"serving on http://127.0.0.1:{port}")
    server.run(web_app, port)


def main() -> None:
    app()
