import random
from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


class SystemRandomizer:
    """Edge module. The only place the `random` module is used."""

    def __init__(self, seed: int | None = None) -> None:
        self._random = random.Random(seed)

    def choice(self, items: Sequence[T]) -> T:
        return self._random.choice(items)
