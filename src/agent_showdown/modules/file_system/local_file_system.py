from datetime import datetime
from pathlib import Path

from agent_showdown.interfaces.file_system import FileInfo


class LocalFileSystem:
    """Edge module. Reads and writes the real filesystem."""

    def exists(self, path: Path) -> bool:
        return path.exists()

    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def append_line(self, path: Path, line: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"{line}\n")

    def stat(self, path: Path) -> FileInfo:
        result = path.stat()
        return FileInfo(
            path=path,
            size_bytes=result.st_size,
            modified_at=datetime.fromtimestamp(result.st_mtime),
            is_directory=path.is_dir(),
        )
