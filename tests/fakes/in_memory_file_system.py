from datetime import datetime
from pathlib import Path

from agent_showdown.interfaces.file_system import FileInfo


class InMemoryFileSystem:
    """Test fake. A dict standing in for a disk."""

    def __init__(self, modified_at: datetime | None = None) -> None:
        self.files: dict[Path, str] = {}
        self._modified_at = modified_at if modified_at is not None else datetime(2025, 9, 10)

    def exists(self, path: Path) -> bool:
        return path in self.files

    def read_text(self, path: Path) -> str:
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]

    def write_text(self, path: Path, content: str) -> None:
        self.files[path] = content

    def append_line(self, path: Path, line: str) -> None:
        self.files[path] = self.files.get(path, "") + f"{line}\n"

    def stat(self, path: Path) -> FileInfo:
        if path not in self.files:
            raise FileNotFoundError(path)
        return FileInfo(
            path=path,
            size_bytes=len(self.files[path].encode("utf-8")),
            modified_at=self._modified_at,
            is_directory=False,
        )
