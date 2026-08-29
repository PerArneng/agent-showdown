from enum import StrEnum


class TerrainKind(StrEnum):
    """What stands on an obstructed square. Scenery to look at, a rule to play around."""

    TREE = "tree"
    STONE_WALL = "stone_wall"
    BOULDER = "boulder"
    # A landmark rather than a crowd: the generator lays at most one on a board.
    STONE_WELL = "stone_well"
