from collections.abc import Sequence

from agent_showdown.interfaces.config import AgentConfig
from agent_showdown.interfaces.game import Action, ActionKind, Direction, GameView, PlayerTurn


class ScriptedPlayer:
    """Test fake. A contestant that plays the same harmless plan every round."""

    def __init__(self, name: str) -> None:
        self._name = name

    def get_name(self) -> str:
        return self._name

    def take_turn(self, view: GameView) -> PlayerTurn:
        return PlayerTurn(
            reasoning="", actions=(Action(kind=ActionKind.MOVE, direction=Direction.UP),)
        )


class ScriptedAgentPlayerFactory:
    """Test fake. Builds contestants from configs without ever constructing a model client."""

    def __init__(self) -> None:
        self.configs: list[AgentConfig] = []

    def create(self, config: AgentConfig) -> ScriptedPlayer:
        self.configs.append(config)
        return ScriptedPlayer(config.name)

    def names(self) -> Sequence[str]:
        return [config.name for config in self.configs]
