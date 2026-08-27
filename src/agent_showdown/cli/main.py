import typer

from agent_showdown.container import Container
from agent_showdown.interfaces.engine import Engine

app = typer.Typer(help="agent-showdown", no_args_is_help=True)


def _engine() -> Engine:
    """Composition root. The only place the container is instantiated."""
    return Container().engine()


@app.callback()
def cli() -> None:
    """Keep the app a command group even while `start` is the only subcommand."""


@app.command()
def start() -> None:
    """Start agent-showdown."""
    _engine().start()


def main() -> None:
    app()
