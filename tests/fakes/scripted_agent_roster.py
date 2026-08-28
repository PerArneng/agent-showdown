from collections.abc import Sequence

from agent_showdown.interfaces.game import Player, PlayerTurn
from agent_showdown.modules.builtin_agents import SimpleStrandsPlayer
from tests.fakes.scripted_turn_planner import ScriptedTurnPlanner


class ScriptedAgentRoster:
    """Test fake. The built-in contestants, with the model replaced by a script."""

    def __init__(
        self,
        names: Sequence[str] = ("simple-strands-1",),
        turns: Sequence[PlayerTurn] = (),
        max_moves: int = 4,
    ) -> None:
        self._names = list(names)
        self._max_moves = max_moves
        self.planner = ScriptedTurnPlanner(turns)

    def create_players(self) -> Sequence[Player]:
        return [
            SimpleStrandsPlayer(name, self.planner, self._max_moves) for name in self._names
        ]
