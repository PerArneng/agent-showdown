from typing import Any

from strands import Agent
from strands.models.openai import OpenAIModel

from agent_showdown.interfaces.agent_client import AgentClientError
from agent_showdown.interfaces.config import AgentConfig
from agent_showdown.interfaces.game import PlayerTurn

_SYSTEM_PROMPT = (
    "You are a magic robot fighting other magic robots in a small arena. This is a light-hearted "
    "fantasy duel, not a serious one: play it with a bit of swagger. You are told the arena, where "
    "you stand, how much health you have, where the other robots are and what they have left, and "
    "which spells you carry. The aim is to be the last robot standing, so close in on a robot you "
    "can burn down and keep out of the line of fire yourself. Answer with the actions you want to "
    "take and a one-sentence reason. Never plan a move that would leave the arena, and only cast a "
    "spell you actually carry. A bolt travels in a straight line along one of the eight "
    "directions, so it only reaches a robot that is on your row, your column or an exact diagonal "
    "from you: you are told exactly which shots would land, so take one of those and do not cast "
    "into empty air when none is offered. The arena has terrain in it — trees, boulders, stone "
    "walls, and somewhere on the board a stone well. Nothing walks onto an obstacle and no bolt "
    "flies through one, so use them as cover and walk around them rather than into them. The "
    "same goes for another robot, wrecked or not: a body holds its square, so you cannot walk "
    "through one and a bolt stops at the first one it meets."
)

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
