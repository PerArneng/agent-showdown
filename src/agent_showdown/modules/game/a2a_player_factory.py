from agent_showdown.interfaces.agent_client import AgentClient
from agent_showdown.interfaces.game import Player
from agent_showdown.modules.game.a2a_player import A2APlayer


class A2APlayerFactory:
    """Builds `A2APlayer`s that share one transport.

    The player name doubles as the conversation id. That is unique within a game and keeps
    this deterministic; a per-game unique id needs a `uuid`, which is nondeterministic input
    and belongs in its own edge module rather than being called inline here.
    """

    def __init__(self, agent_client: AgentClient) -> None:
        self._agent_client = agent_client

    def create(self, name: str) -> Player:
        return A2APlayer(name, context_id=name, agent_client=self._agent_client)
