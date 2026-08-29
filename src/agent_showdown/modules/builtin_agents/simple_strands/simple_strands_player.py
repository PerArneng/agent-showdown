from agent_showdown.interfaces.builtin_agents import TurnPlanner
from agent_showdown.interfaces.game import (
    Direction,
    GameView,
    Obstacle,
    Opponent,
    PlayerTurn,
    SpellInfo,
)


class SimpleStrandsPlayer:
    """A contestant that renders its view into a prompt and asks a planner what to do.

    Pure: it builds a string and returns what it is handed. Everything that touches a model lives
    behind `TurnPlanner`, which is what keeps this testable in memory.

    The prompt does the geometry rather than leaving it to the model. Measured over a real match,
    78% of casts were fired when no direction could have hit anything: these models are poor at
    working out whether a target is lined up, and the game already knows.
    """

    def __init__(self, name: str, planner: TurnPlanner, max_actions: int) -> None:
        self._name = name
        self._planner = planner
        self._max_actions = max_actions

    def get_name(self) -> str:
        return self._name

    def take_turn(self, view: GameView) -> PlayerTurn:
        return self._planner.plan(self._prompt(view))

    def _prompt(self, view: GameView) -> str:
        directions = ", ".join(direction.value for direction in Direction)
        return (
            f"Round {view.round_number}.\n"
            f"The arena is {view.board.width} wide and {view.board.height} tall. "
            f"Cell (0,0) is the top-left corner, so UP decreases y and DOWN increases y.\n"
            f"You are the robot {self._name}, standing on "
            f"({view.position.x},{view.position.y}) with {_health(view.health, view.max_health)}.\n"
            f"{self._obstacles(view)}\n"
            f"{self._robots(view)}\n"
            f"{self._spells(view)}\n"
            f"{self._shots(view)}\n"
            f"Legal directions: {directions}.\n"
            f"Plan at most {self._max_actions} actions, applied in order. A move action steps one "
            f"square in a direction; a move off the arena, into an obstacle, or onto another "
            f"robot, is refused and you stay where you are. "
            f"A cast action needs the name of a spell you carry and the direction to aim it.\n"
            f"Say briefly why you chose this plan."
        )

    def _obstacles(self, view: GameView) -> str:
        """The terrain, spelled out square by square: the model is given no map to look at."""
        if not view.board.obstacles:
            return "The arena is clear of obstacles."
        return "Obstacles — nothing walks onto one and no bolt flies through one:\n" + "\n".join(
            f"- {_terrain(kind)} at {squares}"
            for kind, squares in _by_kind(view.board.obstacles)
        )

    def _robots(self, view: GameView) -> str:
        if not view.opponents:
            return "There are no other robots in the arena."
        return "Other robots:\n" + "\n".join(
            f"- {_robot(opponent, view)}" for opponent in view.opponents
        )

    def _spells(self, view: GameView) -> str:
        if not view.spells:
            return "You carry no spells."
        return "Spells you carry:\n" + "\n".join(f"- {_spell(spell)}" for spell in view.spells)

    def _shots(self, view: GameView) -> str:
        """Every cast that would land right now, worked out rather than left to the model."""
        shots = [
            f"- cast {spell.name} {opponent.direction} — hits {opponent.name} "
            f"{opponent.distance} square{'' if opponent.distance == 1 else 's'} away, "
            f"leaving it on {max(0, opponent.health - spell.damage)} health"
            for spell in view.spells
            for opponent in view.opponents
            if opponent.health > 0
            and opponent.direction is not None
            and opponent.distance <= spell.range
        ]
        if shots:
            return "Shots that would land if you cast them now:\n" + "\n".join(shots)
        return (
            "No shot would land from where you stand: no living robot is on your row, your column "
            "or an exact diagonal within range, or the only one that is has an obstacle in the "
            "way. Casting now would waste the action — move to line one up first."
        )


def _by_kind(obstacles: tuple[Obstacle, ...]) -> list[tuple[str, str]]:
    """One line per kind of terrain, rather than one per square, so the prompt stays short."""
    grouped: dict[str, list[str]] = {}
    for obstacle in obstacles:
        squares = grouped.setdefault(obstacle.kind.value, [])
        squares.append(f"({obstacle.position.x},{obstacle.position.y})")
    return [(kind, ", ".join(squares)) for kind, squares in grouped.items()]


def _terrain(kind: str) -> str:
    return kind.replace("_", " ")


def _health(health: int, maximum: int) -> str:
    return f"{health}/{maximum} health"


def _robot(opponent: Opponent, view: GameView) -> str:
    where = f"({opponent.position.x},{opponent.position.y})"
    if opponent.health <= 0:
        return (
            f"{opponent.name} at {where}, scrapped — it cannot fight, but the wreck holds its "
            f"square: you cannot walk through it and a bolt stops on it"
        )
    bearing = _bearing(view, opponent)
    aim = (
        f"lined up {opponent.direction} from you"
        if opponent.direction is not None
        else "no bolt can reach it from where you stand — it is not lined up, or something "
        "is in the way"
    )
    return (
        f"{opponent.name} at {where}, {_health(opponent.health, view.max_health)}, "
        f"{opponent.distance} away ({bearing}) — {aim}"
    )


def _bearing(view: GameView, opponent: Opponent) -> str:
    """The offset in plain words, so closing the distance needs no arithmetic either."""
    dx = opponent.position.x - view.position.x
    dy = opponent.position.y - view.position.y
    parts = []
    if dx:
        parts.append(f"{abs(dx)} {'RIGHT' if dx > 0 else 'LEFT'}")
    if dy:
        parts.append(f"{abs(dy)} {'DOWN' if dy > 0 else 'UP'}")
    return " and ".join(parts) if parts else "on your square"


def _spell(spell: SpellInfo) -> str:
    return (
        f'"{spell.name}", {spell.damage} damage, range {spell.range} squares: {spell.description}'
    )
