from pathlib import Path
from typing import Protocol

from agent_showdown.interfaces.file_system.file_info import FileInfo


class FileSystem(Protocol):
    """Filesystem access. Implementations that touch a real disk are edge modules."""

    def exists(self, path: Path) -> bool:
        """Return whether the path exists."""
        ...

    def read_text(self, path: Path) -> str:
        """Return the full contents of the file at the path."""
        ...

    def write_text(self, path: Path, content: str) -> None:
        """Replace the contents of the file at the path, creating parents as needed."""
        ...

    def append_line(self, path: Path, line: str) -> None:
        """Append the line, plus a trailing newline, to the file at the path."""
        ...

    def stat(self, path: Path) -> FileInfo:
        """Return metadata for the path."""
        ...
