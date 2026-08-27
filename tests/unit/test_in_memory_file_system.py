from pathlib import Path

import pytest

from tests.fakes import InMemoryFileSystem


def test_write_then_read_round_trips() -> None:
    fs = InMemoryFileSystem()
    fs.write_text(Path("a.txt"), "hello")

    assert fs.exists(Path("a.txt"))
    assert fs.read_text(Path("a.txt")) == "hello"


def test_append_line_adds_a_newline() -> None:
    fs = InMemoryFileSystem()
    fs.append_line(Path("a.txt"), "one")
    fs.append_line(Path("a.txt"), "two")

    assert fs.read_text(Path("a.txt")) == "one\ntwo\n"


def test_stat_reports_byte_size() -> None:
    fs = InMemoryFileSystem()
    fs.write_text(Path("a.txt"), "hallå")

    info = fs.stat(Path("a.txt"))
    assert info.path == Path("a.txt")
    assert info.size_bytes == len("hallå".encode())
    assert info.is_directory is False


def test_reading_a_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        InMemoryFileSystem().read_text(Path("missing.txt"))
