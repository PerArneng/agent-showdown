from agent_showdown.interfaces.builtin_agents import TurnPlanner
from agent_showdown.interfaces.game import Player
from agent_showdown.modules.builtin_agents.simple_strands.simple_strands_player import (
    SimpleStrandsPlayer,
)


class SimpleStrandsPlayerFactory:
    """Builds `SimpleStrandsPlayer`s that share one planner and one move budget."""

    def __init__(self, planner: TurnPlanner, max_moves: int) -> None:
        self._planner = planner
        self._max_moves = max_moves

    def create(self, name: str) -> Player:
        return SimpleStrandsPlayer(name, self._planner, self._max_moves)
