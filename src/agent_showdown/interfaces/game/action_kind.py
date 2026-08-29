from enum import StrEnum


class ActionKind(StrEnum):
    """What a single entry in a turn plan does."""

    MOVE = "move"
    CAST = "cast"
