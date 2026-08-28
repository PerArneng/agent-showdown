import pytest

from agent_showdown.interfaces.agent_client import AgentClientError
from agent_showdown.interfaces.game import (
    Board,
    Direction,
    GameView,
    Move,
    Movement,
    PlayerTurn,
    Position,
)
from agent_showdown.modules.builtin_agents import SimpleStrandsPlayer
from tests.fakes import ScriptedTurnPlanner

_VIEW = GameView(
    board=Board(width=3, height=4),
    position=Position(x=1, y=2),
    round_number=7,
)
_TURN = PlayerTurn(
    reasoning="heading for the middle",
    movement=Movement(moves=(Move(direction=Direction.UP), Move(direction=Direction.LEFT))),
)


def test_get_name_round_trips() -> None:
    player = SimpleStrandsPlayer("agent-1", ScriptedTurnPlanner([_TURN]), max_moves=4)

    assert player.get_name() == "agent-1"


def test_take_turn_returns_what_the_planner_planned() -> None:
    player = SimpleStrandsPlayer("agent-1", ScriptedTurnPlanner([_TURN]), max_moves=4)

    turn = player.take_turn(_VIEW)

    assert turn.reasoning == "heading for the middle"
    assert [move.direction for move in turn.movement.moves] == [Direction.UP, Direction.LEFT]


def test_the_prompt_describes_the_board_the_position_and_the_round() -> None:
    planner = ScriptedTurnPlanner([_TURN])

    SimpleStrandsPlayer("agent-1", planner, max_moves=4).take_turn(_VIEW)

    prompt = planner.prompts[0]
    assert "Round 7" in prompt
    assert "3 wide" in prompt and "4 tall" in prompt
    assert "(1,2)" in prompt


def test_the_prompt_names_every_legal_direction_and_the_move_budget() -> None:
    planner = ScriptedTurnPlanner([_TURN])

    SimpleStrandsPlayer("agent-1", planner, max_moves=4).take_turn(_VIEW)

    prompt = planner.prompts[0]
    for direction in Direction:
        assert direction.value in prompt
    assert "at most 4 moves" in prompt


def test_a_planner_failure_propagates_to_the_game() -> None:
    planner = ScriptedTurnPlanner(fails_with="the model is unreachable")
    player = SimpleStrandsPlayer("agent-1", planner, max_moves=4)

    with pytest.raises(AgentClientError):
        player.take_turn(_VIEW)
