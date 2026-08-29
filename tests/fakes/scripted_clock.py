from datetime import datetime


class ScriptedClock:
    """Test fake. Hands out a scripted sequence of instants, one per `now()`.

    `FrozenClock` cannot express a duration — every interval it measures is zero. This one walks a
    list, and repeats the last instant once the script runs out, so a test only has to script the
    instants it actually asserts on. Sleeps are recorded, never taken.
    """

    def __init__(self, *instants: datetime) -> None:
        self._instants = list(instants)
        self._next = 0
        self.slept: list[float] = []

    def now(self) -> datetime:
        instant = self._instants[min(self._next, len(self._instants) - 1)]
        self._next += 1
        return instant

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
