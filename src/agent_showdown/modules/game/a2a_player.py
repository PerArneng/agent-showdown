from agent_showdown.interfaces.agent_client import AgentClient
from agent_showdown.interfaces.game import GameView, PlayerTurn


class A2APlayer:
    """A remote agent playing as a contestant.

    A pure translator: the view goes out as JSON, the reply is parsed back into a validated
    `PlayerTurn`. All transport lives behind `AgentClient`, and every failure — a dead agent,
    a malformed reply, an unknown direction — propagates to the game, which owns the policy.
    """

    def __init__(self, name: str, context_id: str, agent_client: AgentClient) -> None:
        self._name = name
        self._context_id = context_id
        self._agent_client = agent_client

    def get_name(self) -> str:
        return self._name

    def take_turn(self, view: GameView) -> PlayerTurn:
        reply = self._agent_client.send(self._context_id, view.model_dump_json())
        return PlayerTurn.model_validate_json(reply)
