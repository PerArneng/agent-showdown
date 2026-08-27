from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """The time edge: reading it and waiting on it. Both are nondeterministic, so both inject."""

    def now(self) -> datetime:
        """Return the current time."""
        ...

    def sleep(self, seconds: float) -> None:
        """Block for `seconds`."""
        ...
