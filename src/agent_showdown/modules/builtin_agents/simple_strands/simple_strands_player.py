from agent_showdown.interfaces.builtin_agents import TurnPlanner
from agent_showdown.interfaces.game import Direction, GameView, PlayerTurn


class SimpleStrandsPlayer:
    """A built-in agent contestant. In-process, not A2A: nothing is served, nothing is dialled.

    Pure: it renders the view into a prompt and hands it to a `TurnPlanner`. Every model call, and
    so every failure, lives behind that protocol, which is what keeps this class testable in memory.
    """

    def __init__(self, name: str, planner: TurnPlanner, max_moves: int) -> None:
        self._name = name
        self._planner = planner
        self._max_moves = max_moves

    def get_name(self) -> str:
        return self._name

    def take_turn(self, view: GameView) -> PlayerTurn:
        return self._planner.plan(self._prompt(view))

    def _prompt(self, view: GameView) -> str:
        directions = ", ".join(direction.value for direction in Direction)
        return (
            f"Round {view.round_number}.\n"
            f"The board is {view.board.width} wide and {view.board.height} tall. "
            f"Cell (0,0) is the top-left corner, so UP decreases y and DOWN increases y.\n"
            f"You stand on ({view.position.x},{view.position.y}).\n"
            f"Legal directions: {directions}.\n"
            f"Plan at most {self._max_moves} moves, applied in order. A move off the board is "
            f"refused and you stay where you are.\n"
            f"Say briefly why you chose this plan."
        )
