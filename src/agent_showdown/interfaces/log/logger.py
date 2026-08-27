from typing import Protocol


class Logger(Protocol):
    """Emits log lines at a severity."""

    def debug(self, message: str) -> None:
        """Log the message at DEBUG."""
        ...

    def info(self, message: str) -> None:
        """Log the message at INFO."""
        ...

    def warning(self, message: str) -> None:
        """Log the message at WARNING."""
        ...

    def error(self, message: str) -> None:
        """Log the message at ERROR."""
        ...

    def critical(self, message: str) -> None:
        """Log the message at CRITICAL."""
        ...
