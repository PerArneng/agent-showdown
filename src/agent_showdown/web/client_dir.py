"""Finding the built client. The client is a separate project, so it may not be built at all."""

from pathlib import Path

from agent_showdown.interfaces.file_system import FileSystem

# The working copy, when running from a checkout: `npm run dev` writes here.
WORKING_COPY = Path(__file__).parents[3] / "web_client" / "dist"
# What ships in the wheel.
PACKAGED = Path(__file__).parent / "static"

BUILD_COMMAND = "npm --prefix web_client install && npm --prefix web_client run build"


def find_client_dir(file_system: FileSystem, override: Path | None = None) -> Path | None:
    """Return the first directory holding a built client, or `None` if none does.

    An `override` is checked like any other candidate rather than trusted, so a wrong `--client-dir`
    fails with the same message as a client that was never built.
    """
    candidates = (override,) if override is not None else (WORKING_COPY, PACKAGED)
    for candidate in candidates:
        if file_system.exists(candidate / "index.html"):
            return candidate
    return None
