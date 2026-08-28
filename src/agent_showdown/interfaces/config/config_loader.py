from pathlib import Path
from typing import Protocol

from agent_showdown.interfaces.config.app_config import AppConfig


class ConfigLoader(Protocol):
    """Reads the configuration a run is started with."""

    def load(self, path: Path | None) -> AppConfig:
        """Return the config at `path`, or at the default path, or the built-in defaults."""
        ...
