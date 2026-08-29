from pydantic import BaseModel, ConfigDict


class AgentConfig(BaseModel):
    """One built-in contestant and the OpenAI-compatible endpoint it plays through."""

    # `extra="forbid"` on purpose: this model is filled from a hand-written file, so a typo'd
    # key must fail loudly instead of silently leaving a default in place.
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    base_url: str
    model_id: str
    # Servers that want no auth still refuse to start the OpenAI client without a value.
    api_key: str = "EMPTY"
    # A reasoning model spends this on thinking before it answers at all.
    max_tokens: int = 4096
    # A long prompt can prefill slowly on a box without CUDA graphs.
    timeout: float = 300.0
    # How many actions the prompt asks for. Must not exceed the game's own cap, or every
    # turn is refused whole.
    max_actions: int = 4
    # Whether the model may think before it answers. Off is dramatically faster: a turn that
    # takes minutes with thinking on lands in seconds with it off.
    thinking: bool = True
