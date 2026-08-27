import sys
from typing import TextIO


class StdioConsole:
    """Edge module. The only writer to standard output and standard error."""

    def __init__(self, stdout: TextIO | None = None, stderr: TextIO | None = None) -> None:
        self._stdout = stdout if stdout is not None else sys.stdout
        self._stderr = stderr if stderr is not None else sys.stderr

    def write_line(self, text: str) -> None:
        self._stdout.write(f"{text}\n")
        self._stdout.flush()

    def write_error_line(self, text: str) -> None:
        self._stderr.write(f"{text}\n")
        self._stderr.flush()
