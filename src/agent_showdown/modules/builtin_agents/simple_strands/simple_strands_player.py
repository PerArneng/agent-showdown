from agent_showdown.interfaces.builtin_agents import TurnPlanner
from agent_showdown.interfaces.game import Direction, GameView, Opponent, PlayerTurn, SpellInfo


class SimpleStrandsPlayer:
    """A contestant that renders its view into a prompt and asks a planner what to do.

    Pure: it builds a string and returns what it is handed. Everything that touches a model lives
    behind `TurnPlanner`, which is what keeps this testable in memory.
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
            f"({view.position.x},{view.position.y}) with {view.health} health.\n"
            f"{self._robots(view)}\n"
            f"{self._spells(view)}\n"
            f"Legal directions: {directions}.\n"
            f"Plan at most {self._max_actions} actions, applied in order. A move action steps one "
            f"square in a direction; a move off the arena is refused and you stay where you are. "
            f"A cast action needs the name of a spell you carry and the direction to aim it.\n"
            f"Say briefly why you chose this plan."
        )

    def _robots(self, view: GameView) -> str:
        if not view.opponents:
            return "There are no other robots in the arena."
        return "Other robots:\n" + "\n".join(
            f"- {_robot(opponent)}" for opponent in view.opponents
        )

    def _spells(self, view: GameView) -> str:
        if not view.spells:
            return "You carry no spells."
        return "Spells you carry:\n" + "\n".join(f"- {_spell(spell)}" for spell in view.spells)


def _robot(opponent: Opponent) -> str:
    where = f"({opponent.position.x},{opponent.position.y})"
    if opponent.health <= 0:
        return f"{opponent.name} at {where}, scrapped — it cannot fight, but it still blocks spells"
    return f"{opponent.name} at {where}, {opponent.health} health"


def _spell(spell: SpellInfo) -> str:
    return (
        f'"{spell.name}", {spell.damage} damage, range {spell.range} squares: {spell.description}'
    )
