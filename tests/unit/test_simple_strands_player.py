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
        # Lined up LEFT to RIGHT on row 2 and one square away: a shot that would land.
        Opponent(
            name="rusty",
            position=Position(x=2, y=2),
            health=40,
            direction=Direction.RIGHT,
            distance=1,
        ),
        # Off any ray from (1,2), so no direction reaches it.
        Opponent(name="scrapheap", position=Position(x=0, y=0), health=0, distance=2),
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
    assert "70/100 health" in prompt


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
    assert "rusty at (2,2), 40/100 health" in prompt
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


def _prompt_for(view: GameView) -> str:
    planner = ScriptedTurnPlanner([_TURN])
    SimpleStrandsPlayer("agent-1", planner, max_actions=4).take_turn(view)
    return planner.prompts[0]


def test_the_prompt_says_which_robots_are_lined_up_and_which_are_not() -> None:
    askew = _VIEW.model_copy(
        update={
            "opponents": (
                *_VIEW.opponents,
                # Living, and on no ray from (1,2): the case the models kept firing at anyway.
                Opponent(name="askew", position=Position(x=2, y=0), health=100, distance=2),
            )
        }
    )

    prompt = _prompt_for(askew)

    assert "lined up RIGHT from you" in prompt
    assert "askew" in prompt and "not lined up, so no bolt can reach it" in prompt


def test_the_prompt_gives_the_bearing_so_closing_needs_no_arithmetic() -> None:
    prompt = _prompt_for(_VIEW)

    # rusty is at (2,2) and the robot at (1,2): one square to its right.
    assert "1 RIGHT" in prompt


def test_the_prompt_lists_the_shots_that_would_land() -> None:
    prompt = _prompt_for(_VIEW)

    assert "cast fireball RIGHT" in prompt
    assert "hits rusty 1 square away" in prompt
    # 40 health less 10 damage: what taking the shot would achieve.
    assert "leaving it on 30 health" in prompt


def test_a_robot_out_of_range_is_not_offered_as_a_shot() -> None:
    far = _VIEW.model_copy(
        update={
            "opponents": (
                Opponent(
                    name="distant",
                    position=Position(x=1, y=9),
                    health=100,
                    direction=Direction.DOWN,
                    distance=7,  # lined up, but beyond the fireball's range of 3
                ),
            )
        }
    )

    prompt = _prompt_for(far)

    assert "lined up DOWN from you" in prompt
    assert "No shot would land" in prompt


def test_a_scrapped_robot_is_not_offered_as_a_shot() -> None:
    corpse = _VIEW.model_copy(
        update={
            "opponents": (
                Opponent(
                    name="scrapheap",
                    position=Position(x=2, y=2),
                    health=0,
                    direction=Direction.RIGHT,
                    distance=1,
                ),
            )
        }
    )

    prompt = _prompt_for(corpse)

    assert "No shot would land" in prompt


def test_with_no_shot_the_prompt_says_not_to_waste_the_action() -> None:
    alone = _VIEW.model_copy(update={"opponents": ()})

    prompt = _prompt_for(alone)

    assert "would waste the action" in prompt


def test_the_prompt_states_the_alignment_rule_with_the_spell() -> None:
    # The rule travels with the spell, so a future spell can describe its own reach.
    fireball = _FIREBALL.model_copy(
        update={"description": "Only travels along the eight directions."}
    )

    prompt = _prompt_for(_VIEW.model_copy(update={"spells": (fireball,)}))

    assert "Only travels along the eight directions." in prompt
