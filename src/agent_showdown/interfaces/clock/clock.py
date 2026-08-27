from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Source of the current time. Implementations that read the real clock are edge modules."""

    def now(self) -> datetime:
        """Return the current time."""
        ...
