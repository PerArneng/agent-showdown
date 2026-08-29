from agent_showdown.interfaces.config import AgentConfig
from agent_showdown.modules.builtin_agents import SimpleStrandsPlayer, SimpleStrandsRoster

# Building a planner constructs an OpenAI model object and nothing else, so no test here
# opens a socket: `plan()` is never called.
_CONFIGS = (
    AgentConfig(name="local", base_url="http://localhost:1234/v1", model_id="qwen/qwen3.8-27b"),
    AgentConfig(name="remote", base_url="http://elsewhere/v1", model_id="qwen3.6-35b"),
)


def test_one_player_per_config_in_configuration_order() -> None:
    players = SimpleStrandsRoster(_CONFIGS).create_players()

    assert [player.get_name() for player in players] == ["local", "remote"]


def test_each_player_gets_its_own_planner() -> None:
    players = SimpleStrandsRoster(_CONFIGS).create_players()

    first, second = players
    assert isinstance(first, SimpleStrandsPlayer)
    assert isinstance(second, SimpleStrandsPlayer)
    assert first._planner is not second._planner


def test_the_move_budget_comes_from_the_config() -> None:
    config = AgentConfig(name="a", base_url="http://x/v1", model_id="m", max_actions=2)

    player = SimpleStrandsRoster([config]).create_players()[0]

    assert isinstance(player, SimpleStrandsPlayer)
    assert player._max_actions == 2


def test_an_empty_roster_fields_nobody() -> None:
    assert SimpleStrandsRoster([]).create_players() == []
