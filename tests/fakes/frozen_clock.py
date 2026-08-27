from datetime import datetime


class FrozenClock:
    """Test fake. Always returns the same instant, and records sleeps instead of taking them."""

    def __init__(self, fixed: datetime) -> None:
        self._fixed = fixed
        self.slept: list[float] = []

    def now(self) -> datetime:
        return self._fixed

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
