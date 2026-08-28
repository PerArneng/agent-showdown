from typing import Any

from agent_showdown.interfaces.config import AgentConfig
from agent_showdown.modules.builtin_agents import StrandsTurnPlanner

# Constructing a planner builds an OpenAI model object and opens no socket, so these tests
# stay in memory. `plan()` is never called: no test may reach a real model.
_CONFIG = AgentConfig(name="a", base_url="http://nowhere/v1", model_id="m")


def _params(config: AgentConfig) -> dict[str, Any]:
    params = StrandsTurnPlanner(config)._model.config["params"]
    assert isinstance(params, dict)
    return params


def test_thinking_is_left_to_the_model_by_default() -> None:
    assert _params(_CONFIG) == {"max_tokens": 4096}


def test_thinking_off_sends_both_servers_switches() -> None:
    # vLLM honours the Qwen chat-template switch and ignores `reasoning_effort`; LM Studio
    # does the reverse. Each ignores the other's field, so sending both is what makes one
    # config flag work against either server.
    params = _params(_CONFIG.model_copy(update={"thinking": False}))

    assert params["reasoning_effort"] == "none"
    assert params["extra_body"] == {"chat_template_kwargs": {"enable_thinking": False}}


def test_the_token_budget_comes_from_the_config() -> None:
    params = _params(_CONFIG.model_copy(update={"max_tokens": 512}))

    assert params["max_tokens"] == 512
