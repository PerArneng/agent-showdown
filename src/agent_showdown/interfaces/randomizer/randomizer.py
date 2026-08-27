from collections.abc import Sequence
from typing import Protocol, TypeVar

T = TypeVar("T")


class Randomizer(Protocol):
    """Source of randomness. Implementations that draw real entropy are edge modules."""

    def choice(self, items: Sequence[T]) -> T:
        """Return one item picked at random. `items` must not be empty."""
        ...
