from strands import Agent
from strands.models.openai import OpenAIModel

from agent_showdown.interfaces.agent_client import AgentClientError
from agent_showdown.interfaces.game import PlayerTurn

_SYSTEM_PROMPT = (
    "You are a contestant in a grid game. You are told the board, where you stand and which "
    "directions exist. Answer with the moves you want to make and a one-sentence reason. "
    "Never plan a move that would leave the board."
)


class StrandsTurnPlanner:
    """Edge module. The only place a model is called over the network.

    A fresh `Agent` per turn: the contestant is stateless by design, and a system prompt that never
    varies is exactly what the server's prefix cache keys on.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model_id: str,
        max_tokens: int,
        timeout: float,
    ) -> None:
        self._model = OpenAIModel(
            client_args={"base_url": base_url, "api_key": api_key, "timeout": timeout},
            model_id=model_id,
            # A reasoning model spends this budget on thinking first. Too small and the answer
            # never arrives.
            params={"max_tokens": max_tokens},
        )

    def plan(self, prompt: str) -> PlayerTurn:
        try:
            agent = Agent(
                model=self._model,
                system_prompt=_SYSTEM_PROMPT,
                # Strands prints the model's thinking to stdout by default, which would
                # trample the terminal log. The console is the logger's, not the SDK's.
                callback_handler=None,
            )
            result = agent(prompt, structured_output_model=PlayerTurn)
        except Exception as error:  # A model behind a network fails in ways we cannot enumerate.
            raise AgentClientError(f"{type(error).__name__}: {error}") from error
        turn = result.structured_output
        if not isinstance(turn, PlayerTurn):
            raise AgentClientError("the model answered without a turn")
        return turn
