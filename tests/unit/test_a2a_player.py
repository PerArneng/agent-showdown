import json

import pytest
from pydantic import ValidationError

from agent_showdown.interfaces.agent_client import AgentClientError
from agent_showdown.interfaces.game import Board, Direction, GameView, Position
from agent_showdown.modules.game import A2APlayer, A2APlayerFactory
from tests.fakes import ScriptedAgentClient

_VIEW = GameView(
    board=Board(width=3, height=3),
    position=Position(x=1, y=1),
    round_number=2,
)
_TURN = '{"movement": {"moves": [{"direction": "UP"}, {"direction": "DOWN_LEFT"}]}}'


def test_get_name_round_trips() -> None:
    assert A2APlayer("agent-1", "ctx", ScriptedAgentClient([_TURN])).get_name() == "agent-1"


def test_take_turn_parses_the_reply_into_a_validated_turn() -> None:
    player = A2APlayer("agent-1", "ctx", ScriptedAgentClient([_TURN]))

    moves = player.take_turn(_VIEW).movement.moves

    assert [move.direction for move in moves] == [Direction.UP, Direction.DOWN_LEFT]


def test_take_turn_sends_the_view_as_json_under_the_context_id() -> None:
    client = ScriptedAgentClient([_TURN])
    player = A2APlayer("agent-1", "game-7", client)

    player.take_turn(_VIEW)

    context_id, payload = client.sent[0]
    assert context_id == "game-7"
    assert json.loads(payload) == {
        "board": {"width": 3, "height": 3},
        "position": {"x": 1, "y": 1},
        "round_number": 2,
    }


def test_a_malformed_reply_raises() -> None:
    player = A2APlayer("agent-1", "ctx", ScriptedAgentClient(["not json at all"]))

    with pytest.raises(ValidationError):
        player.take_turn(_VIEW)


def test_a_reply_naming_an_unknown_direction_raises() -> None:
    reply = '{"movement": {"moves": [{"direction": "SIDEWAYS"}]}}'
    player = A2APlayer("agent-1", "ctx", ScriptedAgentClient([reply]))

    with pytest.raises(ValidationError):
        player.take_turn(_VIEW)


def test_a_dead_agent_propagates_its_error() -> None:
    player = A2APlayer("agent-1", "ctx", ScriptedAgentClient(fails_with="connection refused"))

    with pytest.raises(AgentClientError):
        player.take_turn(_VIEW)


def test_the_factory_uses_the_player_name_as_the_context_id() -> None:
    client = ScriptedAgentClient([_TURN])

    player = A2APlayerFactory(client).create("agent-2")
    player.take_turn(_VIEW)

    assert player.get_name() == "agent-2"
    assert client.sent[0][0] == "agent-2"
