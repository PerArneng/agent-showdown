from agent_showdown.interfaces.game import Direction

# The one place direction semantics live, shared by movement and by every spell that travels.
# Row 0 is the top, so UP decreases y. This is a rule of the board, not a property of the word,
# which is why it is here and not a property on `Direction`.
DELTAS: dict[Direction, tuple[int, int]] = {
    Direction.UP: (0, -1),
    Direction.DOWN: (0, 1),
    Direction.LEFT: (-1, 0),
    Direction.RIGHT: (1, 0),
    Direction.UP_LEFT: (-1, -1),
    Direction.UP_RIGHT: (1, -1),
    Direction.DOWN_LEFT: (-1, 1),
    Direction.DOWN_RIGHT: (1, 1),
}
