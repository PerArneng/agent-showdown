import pytest

from agent_showdown.interfaces.agent_client import AgentClientError
from agent_showdown.interfaces.game import (
    Action,
    ActionKind,
    Board,
    Direction,
    GameView,
    Opponent,
    PlayerTurn,
    Position,
    SpellInfo,
)
from agent_showdown.modules.builtin_agents import SimpleStrandsPlayer
from tests.fakes import ScriptedTurnPlanner

_FIREBALL = SpellInfo(
    name="fireball", description="A bolt of fire.", damage=10, range=3
)
_VIEW = GameView(
    board=Board(width=3, height=4),
    position=Position(x=1, y=2),
    round_number=7,
    health=70,
    opponents=(
        Opponent(name="rusty", position=Position(x=2, y=2), health=40),
        Opponent(name="scrapheap", position=Position(x=0, y=0), health=0),
    ),
    spells=(_FIREBALL,),
)
_TURN = PlayerTurn(
    reasoning="heading for the middle",
    actions=(
        Action(kind=ActionKind.MOVE, direction=Direction.UP),
        Action(kind=ActionKind.CAST, direction=Direction.LEFT, spell="fireball"),
    ),
)


def test_get_name_round_trips() -> None:
    player = SimpleStrandsPlayer("agent-1", ScriptedTurnPlanner([_TURN]), max_actions=4)

    assert player.get_name() == "agent-1"


def test_take_turn_returns_what_the_planner_planned() -> None:
    player = SimpleStrandsPlayer("agent-1", ScriptedTurnPlanner([_TURN]), max_actions=4)

    turn = player.take_turn(_VIEW)

    assert turn.reasoning == "heading for the middle"
    assert [action.direction for action in turn.actions] == [Direction.UP, Direction.LEFT]


def test_the_prompt_describes_the_board_the_position_and_the_round() -> None:
    planner = ScriptedTurnPlanner([_TURN])

    SimpleStrandsPlayer("agent-1", planner, max_actions=4).take_turn(_VIEW)

    prompt = planner.prompts[0]
    assert "Round 7" in prompt
    assert "3 wide" in prompt and "4 tall" in prompt
    assert "(1,2)" in prompt
    assert "70 health" in prompt


def test_the_prompt_names_every_legal_direction_and_the_move_budget() -> None:
    planner = ScriptedTurnPlanner([_TURN])

    SimpleStrandsPlayer("agent-1", planner, max_actions=4).take_turn(_VIEW)

    prompt = planner.prompts[0]
    for direction in Direction:
        assert direction.value in prompt
    assert "at most 4 actions" in prompt


def test_the_prompt_names_every_other_robot_and_what_it_has_left() -> None:
    planner = ScriptedTurnPlanner([_TURN])

    SimpleStrandsPlayer("agent-1", planner, max_actions=4).take_turn(_VIEW)

    prompt = planner.prompts[0]
    assert "rusty at (2,2), 40 health" in prompt
    # A scrapped robot is still worth naming: it blocks a fireball.
    assert "scrapheap at (0,0), scrapped" in prompt


def test_the_prompt_describes_the_spells_the_robot_carries() -> None:
    planner = ScriptedTurnPlanner([_TURN])

    SimpleStrandsPlayer("agent-1", planner, max_actions=4).take_turn(_VIEW)

    prompt = planner.prompts[0]
    assert '"fireball"' in prompt
    assert "10 damage" in prompt and "range 3 squares" in prompt


def test_a_planner_failure_propagates_to_the_game() -> None:
    planner = ScriptedTurnPlanner(fails_with="the model is unreachable")
    player = SimpleStrandsPlayer("agent-1", planner, max_actions=4)

    with pytest.raises(AgentClientError):
        player.take_turn(_VIEW)
