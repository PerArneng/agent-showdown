from datetime import datetime


class SystemClock:
    """Edge module. Reads the real wall clock."""

    def now(self) -> datetime:
        return datetime.now()
