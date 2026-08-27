from typing import Protocol


class Console(Protocol):
    """Line-oriented text output. The only way anything reaches stdout or stderr."""

    def write_line(self, text: str) -> None:
        """Write one line to standard output."""
        ...

    def write_error_line(self, text: str) -> None:
        """Write one line to standard error."""
        ...
