from typing import Any

from strands import Agent
from strands.models.openai import OpenAIModel

from agent_showdown.interfaces.agent_client import AgentClientError
from agent_showdown.interfaces.config import AgentConfig
from agent_showdown.interfaces.game import PlayerTurn

_SYSTEM_PROMPT = (
    "You are a contestant in a grid game. You are told the board, where you stand and which "
    "directions exist. Answer with the moves you want to make and a one-sentence reason. "
    "Never plan a move that would leave the board."
)


# Turning thinking off is not one field: vLLM honours the Qwen chat-template switch and
# ignores `reasoning_effort`, while LM Studio does exactly the reverse. Both ignore the
# other's field silently, so sending both is what makes one flag work on either server.
_NO_THINKING: dict[str, Any] = {
    "reasoning_effort": "none",
    "extra_body": {"chat_template_kwargs": {"enable_thinking": False}},
}


class StrandsTurnPlanner:
    """Asks a model for a turn. The only thing in the process that opens a socket."""

    def __init__(self, config: AgentConfig) -> None:
        params: dict[str, Any] = {"max_tokens": config.max_tokens}
        if not config.thinking:
            params.update(_NO_THINKING)
        self._model = OpenAIModel(
            client_args={
                "base_url": config.base_url,
                "api_key": config.api_key,
                "timeout": config.timeout,
            },
            model_id=config.model_id,
            params=params,
        )

    def plan(self, prompt: str) -> PlayerTurn:
        try:
            # A fresh agent per turn: the contestant is stateless, and an unchanging system
            # prompt is what a prefix cache keys on.
            agent = Agent(
                model=self._model,
                system_prompt=_SYSTEM_PROMPT,
                callback_handler=None,  # keeps strands from printing thinking to stdout
            )
            result = agent(prompt, structured_output_model=PlayerTurn)
        except Exception as error:
            raise AgentClientError(f"{type(error).__name__}: {error}") from error
        turn = result.structured_output
        if not isinstance(turn, PlayerTurn):
            raise AgentClientError("the model answered without a turn")
        return turn
