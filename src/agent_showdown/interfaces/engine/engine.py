from typing import Protocol


class Engine(Protocol):
    """The facade every frontend calls. All behaviour of the application hangs off this."""

    def start(self) -> None:
        """Run the `start` use case."""
        ...
