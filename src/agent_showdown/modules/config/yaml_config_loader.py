from pathlib import Path

import yaml
from pydantic import ValidationError

from agent_showdown.interfaces.config import AppConfig
from agent_showdown.interfaces.file_system import FileSystem

DEFAULT_CONFIG_PATH = Path("agent-showdown.yaml")


class YamlConfigLoader:
    """Reads `AppConfig` from a YAML file. Pure apart from the injected file system."""

    def __init__(self, file_system: FileSystem) -> None:
        self._file_system = file_system

    def load(self, path: Path | None) -> AppConfig:
        """Return the parsed config.

        A missing default path means "no file, use the defaults". A missing path the caller
        asked for by name is an error: a wrong `--config` must not look like success.
        """
        target = path if path is not None else DEFAULT_CONFIG_PATH
        if not self._file_system.exists(target):
            if path is not None:
                raise FileNotFoundError(f"no config file at {target}")
            return AppConfig()
        return self._parse(self._file_system.read_text(target), target)

    def _parse(self, text: str, path: Path) -> AppConfig:
        try:
            document = yaml.safe_load(text)
        except yaml.YAMLError as error:
            raise ValueError(f"{path} is not valid YAML: {error}") from error
        if document is None:  # an empty file is a file that changes nothing
            return AppConfig()
        try:
            return AppConfig.model_validate(document)
        except ValidationError as error:
            raise ValueError(f"{path} is not a valid config: {error}") from error
