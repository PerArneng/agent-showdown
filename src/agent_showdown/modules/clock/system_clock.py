import time
from datetime import datetime


class SystemClock:
    """Edge module. Reads the real wall clock and waits on it."""

    def now(self) -> datetime:
        return datetime.now()

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)
