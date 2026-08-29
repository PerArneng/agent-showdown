from pathlib import Path

import pytest

from agent_showdown.modules.config import DEFAULT_CONFIG_PATH, YamlConfigLoader
from tests.fakes import InMemoryFileSystem

_TWO_AGENTS = """
agents:
  - name: local
    base_url: http://localhost:1234/v1
    model_id: qwen/qwen3.8-27b
  - name: remote
    base_url: http://vllm.brain.home.arpa/v1
    model_id: qwen3.6-35b
    max_tokens: 8192
    timeout: 60.0
    max_actions: 2
    api_key: secret
"""


def _loader(files: dict[Path, str] | None = None) -> YamlConfigLoader:
    file_system = InMemoryFileSystem()
    file_system.files.update(files or {})
    return YamlConfigLoader(file_system)


def test_no_file_at_the_default_path_falls_back_to_the_built_in_agents() -> None:
    config = _loader().load(None)

    names = [agent.name for agent in config.agents]
    assert names == ["simple-strands-vllm", "simple-strands-lmstudio"]
    assert config.agents[1].base_url == "http://localhost:1234/v1"
    assert config.agents[1].model_id == "qwen/qwen3.8-27b"
    assert config.agents[1].max_tokens == 16384
    assert config.agents[1].thinking is False


def test_the_default_path_is_read_when_it_exists() -> None:
    config = _loader({DEFAULT_CONFIG_PATH: _TWO_AGENTS}).load(None)

    assert [agent.name for agent in config.agents] == ["local", "remote"]


def test_every_endpoint_field_round_trips() -> None:
    config = _loader({Path("custom.yaml"): _TWO_AGENTS}).load(Path("custom.yaml"))

    remote = config.agents[1]
    assert remote.base_url == "http://vllm.brain.home.arpa/v1"
    assert remote.model_id == "qwen3.6-35b"
    assert remote.api_key == "secret"
    assert remote.max_tokens == 8192
    assert remote.timeout == 60.0
    assert remote.max_actions == 2


def test_omitted_fields_take_their_defaults() -> None:
    config = _loader({DEFAULT_CONFIG_PATH: _TWO_AGENTS}).load(None)

    local = config.agents[0]
    assert (local.api_key, local.max_tokens, local.timeout, local.max_actions) == (
        "EMPTY",
        4096,
        300.0,
        4,
    )
    assert local.thinking is True  # thinking is on unless a config turns it off


def test_an_empty_file_changes_nothing() -> None:
    config = _loader({DEFAULT_CONFIG_PATH: "\n"}).load(None)

    assert [agent.name for agent in config.agents] == [
        "simple-strands-vllm",
        "simple-strands-lmstudio",
    ]


def test_a_named_path_that_does_not_exist_is_an_error() -> None:
    with pytest.raises(FileNotFoundError):
        _loader().load(Path("nowhere.yaml"))


def test_a_typoed_key_fails_loudly() -> None:
    document = "agents:\n  - name: a\n    base_url: u\n    model_id: m\n    tokens: 10\n"

    with pytest.raises(ValueError, match="not a valid config"):
        _loader({DEFAULT_CONFIG_PATH: document}).load(None)


def test_a_missing_required_field_fails_loudly() -> None:
    with pytest.raises(ValueError, match="not a valid config"):
        _loader({DEFAULT_CONFIG_PATH: "agents:\n  - name: a\n"}).load(None)


def test_broken_yaml_names_the_file() -> None:
    with pytest.raises(ValueError, match="not valid YAML"):
        _loader({DEFAULT_CONFIG_PATH: "agents: [oops\n"}).load(None)


def test_the_match_budget_defaults_without_a_file() -> None:
    config = _loader().load(None)

    # No dummies by default, so an arena with no reachable agents honestly pauses.
    assert (config.max_rounds, config.dummies) == (100, 0)


def test_the_match_budget_can_be_set_in_the_file() -> None:
    path = Path("/etc/agent-showdown.yaml")
    loader = _loader({path: "max_rounds: 5\ndummies: 2\n"})

    config = loader.load(path)

    assert (config.max_rounds, config.dummies) == (5, 2)
    # Naming one setting leaves the built-in roster in place.
    assert len(config.agents) == 2
