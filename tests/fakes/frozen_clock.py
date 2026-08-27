from datetime import datetime


class FrozenClock:
    """Test fake. Always returns the same instant."""

    def __init__(self, fixed: datetime) -> None:
        self._fixed = fixed

    def now(self) -> datetime:
        return self._fixed
