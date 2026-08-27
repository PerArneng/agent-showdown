from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


class FixedRandomizer:
    """Test fake. Walks a fixed cycle of indices instead of drawing entropy."""

    def __init__(self, indices: Sequence[int]) -> None:
        self._indices = list(indices)
        self._next = 0

    def choice(self, items: Sequence[T]) -> T:
        index = self._indices[self._next % len(self._indices)]
        self._next += 1
        return items[index % len(items)]
