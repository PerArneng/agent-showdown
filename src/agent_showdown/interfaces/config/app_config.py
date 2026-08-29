from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.config.agent_config import AgentConfig

# The roster a run plays with when no config file is found.
_DEFAULT_AGENTS = (
    AgentConfig(
        name="simple-strands-vllm",
        base_url="http://vllm.brain.home.arpa/v1",
        model_id="qwen3.6-35b",
        max_tokens=16384,
        thinking=False,
    ),
    AgentConfig(
        name="simple-strands-lmstudio",
        base_url="http://localhost:1234/v1",
        model_id="qwen/qwen3.8-27b",
        # 32k of context and a ~200 token prompt, so half the window can go to thinking.
        max_tokens=16384,
        thinking=False,
    ),
)


class AppConfig(BaseModel):
    """Everything a run can be told from outside. Defaults make a missing file harmless."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    agents: tuple[AgentConfig, ...] = _DEFAULT_AGENTS
    # How many matches a series plays before the board goes quiet.
    max_games: int = 10
    # Rounds per match, so every robot gets at most this many turns. A match ends sooner once
    # one robot is left standing.
    max_rounds: int = 100
