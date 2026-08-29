from datetime import datetime

from agent_showdown.interfaces.clock import Clock
from agent_showdown.interfaces.game import (
    Action,
    ActionKind,
    Board,
    Direction,
    GameView,
    Opponent,
    PlayerStats,
    PlayerTurn,
    Position,
)
from agent_showdown.modules.game import DefaultGame, DefaultScoreboard, DefaultSpellBook
from tests.fakes import FrozenClock, RecordingGameListener, ScriptedClock


def _move(direction: Direction) -> Action:
    return Action(kind=ActionKind.MOVE, direction=direction)


def _cast(direction: Direction, spell: str = "fireball") -> Action:
    return Action(kind=ActionKind.CAST, direction=direction, spell=spell)


class ScriptedPlayer:
    """Plays a fixed plan every round, so the game under test stays deterministic."""

    def __init__(self, name: str, *directions: Direction, reasoning: str = "") -> None:
        self._name = name
        self._turn = PlayerTurn(
            reasoning=reasoning, actions=tuple(_move(direction) for direction in directions)
        )
        self.views: list[GameView] = []

    def get_name(self) -> str:
        return self._name

    def take_turn(self, view: GameView) -> PlayerTurn:
        self.views.append(view)
        return self._turn


class PlanningPlayer:
    """Plays one given plan every round, moves and casts alike."""

    def __init__(self, name: str, *actions: Action) -> None:
        self._name = name
        self._turn = PlayerTurn(reasoning="", actions=actions)
        self.views: list[GameView] = []

    def get_name(self) -> str:
        return self._name

    def take_turn(self, view: GameView) -> PlayerTurn:
        self.views.append(view)
        return self._turn


class IdlePlayer:
    """Stands still. Something to shoot at."""

    def __init__(self, name: str) -> None:
        self._name = name

    def get_name(self) -> str:
        return self._name

    def take_turn(self, view: GameView) -> PlayerTurn:
        return PlayerTurn(reasoning="", actions=())


def _game(clock: Clock | None = None, board: Board | None = None) -> DefaultGame:
    # A frozen clock makes every turn take zero seconds, which keeps the durations out of the way
    # of the tests that are about something else. `ScriptedClock` is for the ones that are not.
    return DefaultGame(
        board if board is not None else Board(width=3, height=3),
        clock if clock is not None else FrozenClock(datetime(2025, 9, 10)),
        DefaultSpellBook(),
        DefaultScoreboard(),
    )


def test_register_player_emits_player_joined_with_the_start_position() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)

    game.register_player(ScriptedPlayer("a"), Position(x=1, y=1))

    assert listener.events == [("player_joined", ("a", Position(x=1, y=1)))]


def test_a_listener_added_after_registration_misses_the_join() -> None:
    game, listener = _game(), RecordingGameListener()
    game.register_player(ScriptedPlayer("a"), Position(x=1, y=1))

    game.add_listener(listener)

    assert listener.events == []


def test_every_listener_receives_the_identical_event_sequence() -> None:
    game = _game()
    first, second = RecordingGameListener(), RecordingGameListener()
    game.add_listener(first)
    game.add_listener(second)
    game.register_player(ScriptedPlayer("a", Direction.RIGHT), Position(x=0, y=0))

    game.start(max_rounds=2)

    assert first.events == second.events
    assert first.events != []


def test_a_game_without_listeners_still_runs() -> None:
    game = _game()
    player = ScriptedPlayer("a", Direction.RIGHT)
    game.register_player(player, Position(x=0, y=0))

    game.start(max_rounds=2)

    assert len(player.views) == 2


def test_a_move_updates_the_position_and_reports_source_and_destination() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(ScriptedPlayer("a", Direction.RIGHT), Position(x=0, y=0))

    game.start(max_rounds=1)

    assert ("player_moved", ("a", Position(x=0, y=0), Position(x=1, y=0))) in listener.events


def test_moves_apply_in_order_and_emit_one_event_each() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(
        ScriptedPlayer("a", Direction.RIGHT, Direction.DOWN), Position(x=0, y=0)
    )

    game.start(max_rounds=1)

    moves = [event for event in listener.events if event[0] == "player_moved"]
    assert moves == [
        ("player_moved", ("a", Position(x=0, y=0), Position(x=1, y=0))),
        ("player_moved", ("a", Position(x=1, y=0), Position(x=1, y=1))),
    ]


def test_a_diagonal_moves_both_axes_and_up_decreases_y() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(ScriptedPlayer("a", Direction.UP_RIGHT), Position(x=1, y=1))

    game.start(max_rounds=1)

    assert ("player_moved", ("a", Position(x=1, y=1), Position(x=2, y=0))) in listener.events


def test_a_move_off_the_board_is_blocked_and_leaves_the_position_untouched() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(ScriptedPlayer("a", Direction.LEFT, Direction.RIGHT), Position(x=0, y=0))

    game.start(max_rounds=1)

    assert listener.events[1:] == [
        ("game_started", (Board(width=3, height=3), 1)),
        ("round_started", (1,)),
        ("player_turn_started", ("a",)),
        ("move_blocked", ("a", Position(x=0, y=0), Direction.LEFT)),
        ("player_moved", ("a", Position(x=0, y=0), Position(x=1, y=0))),
        ("player_turn_ended", ("a", 0.0)),
        ("player_stats", ("a", PlayerStats(turns=1, total_seconds=0.0, average_seconds=0.0))),
        ("game_ended", (1,)),
    ]


def test_start_emits_one_round_started_per_round_between_start_and_end() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)

    game.start(max_rounds=4)

    assert listener.names() == ["game_started"] + ["round_started"] * 4 + ["game_ended"]


def test_players_are_asked_in_registration_order_and_see_their_own_position() -> None:
    game = _game()
    first, second = ScriptedPlayer("a"), ScriptedPlayer("b")
    game.register_player(first, Position(x=0, y=0))
    game.register_player(second, Position(x=2, y=2))

    game.start(max_rounds=1)

    assert first.views[0].position == Position(x=0, y=0)
    assert second.views[0].position == Position(x=2, y=2)
    assert first.views[0].round_number == 1
    assert first.views[0].board == Board(width=3, height=3)


class ExplodingPlayer:
    """Fails the way a dead remote agent would."""

    def __init__(self, name: str) -> None:
        self._name = name

    def get_name(self) -> str:
        return self._name

    def take_turn(self, view: GameView) -> PlayerTurn:
        raise RuntimeError("connection refused")


def test_a_player_that_raises_fails_its_turn_without_killing_the_game() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(ExplodingPlayer("boom"), Position(x=1, y=1))

    game.start(max_rounds=2)

    assert ("turn_failed", ("boom", "RuntimeError: connection refused")) in listener.events
    assert listener.names()[-1] == "game_ended"
    assert listener.names().count("turn_failed") == 2


def test_one_failing_player_does_not_stop_the_others() -> None:
    game = _game()
    listener = RecordingGameListener()
    game.add_listener(listener)
    survivor = ScriptedPlayer("ok", Direction.RIGHT)
    game.register_player(ExplodingPlayer("boom"), Position(x=1, y=1))
    game.register_player(survivor, Position(x=0, y=0))

    game.start(max_rounds=1)

    assert len(survivor.views) == 1
    assert ("player_moved", ("ok", Position(x=0, y=0), Position(x=1, y=0))) in listener.events


def test_an_over_long_plan_fails_the_turn_and_moves_nothing() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    greedy = ScriptedPlayer("greedy", *([Direction.RIGHT] * 9))
    game.register_player(greedy, Position(x=0, y=0))

    game.start(max_rounds=1)

    assert ("turn_failed", ("greedy", "planned 9 actions, the limit is 8")) in listener.events
    assert [event for event in listener.events if event[0] == "player_moved"] == []


def test_a_plan_exactly_at_the_limit_is_allowed() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    # Eight moves that stay on a 3x3 board: a lap around the edge.
    lap = [Direction.RIGHT, Direction.RIGHT, Direction.DOWN, Direction.DOWN,
           Direction.LEFT, Direction.LEFT, Direction.UP, Direction.UP]
    game.register_player(ScriptedPlayer("laps", *lap), Position(x=0, y=0))

    game.start(max_rounds=1)

    assert listener.names().count("turn_failed") == 0
    assert listener.names().count("player_moved") == 8


def test_a_turn_with_reasoning_reports_it_before_the_moves() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    player = ScriptedPlayer("a", Direction.UP, reasoning="north looks open")
    game.register_player(player, Position(x=1, y=1))

    game.start(max_rounds=1)

    assert listener.events[4] == ("player_reasoned", ("a", "north looks open"))
    assert listener.names()[5] == "player_moved"


def test_a_turn_without_reasoning_reports_nothing() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(ScriptedPlayer("a", Direction.UP), Position(x=1, y=1))

    game.start(max_rounds=1)

    assert "player_reasoned" not in listener.names()


def test_an_over_long_plan_still_reports_the_reasoning_behind_it() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    plan = (Direction.UP,) * 9
    game.register_player(ScriptedPlayer("a", *plan, reasoning="sprinting"), Position(x=1, y=1))

    game.start(max_rounds=1)

    assert listener.names()[4:6] == ["player_reasoned", "turn_failed"]


def test_a_turn_is_bracketed_by_a_started_and_an_ended_event() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(ScriptedPlayer("a", Direction.UP), Position(x=1, y=1))

    game.start(max_rounds=1)

    assert listener.names() == [
        "player_joined",
        "game_started",
        "round_started",
        "player_turn_started",
        "player_moved",
        "player_turn_ended",
        "player_stats",
        "game_ended",
    ]


def test_the_ended_event_carries_the_seconds_the_turn_took() -> None:
    clock = ScriptedClock(datetime(2025, 9, 10, 12, 0, 0), datetime(2025, 9, 10, 12, 0, 3))
    game, listener = _game(clock), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(ScriptedPlayer("slow", Direction.UP), Position(x=1, y=1))

    game.start(max_rounds=1)

    assert ("player_turn_ended", ("slow", 3.0)) in listener.events


def test_a_turn_that_raises_still_reports_that_it_ended() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(ExplodingPlayer("boom"), Position(x=1, y=1))

    game.start(max_rounds=1)

    assert listener.names()[3:6] == ["player_turn_started", "turn_failed", "player_turn_ended"]


def test_an_over_long_plan_still_reports_that_the_turn_ended() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(ScriptedPlayer("greedy", *([Direction.RIGHT] * 9)), Position(x=0, y=0))

    game.start(max_rounds=1)

    assert listener.names()[-3:-1] == ["player_turn_ended", "player_stats"]


def test_every_started_turn_is_matched_by_exactly_one_ended_turn() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(ExplodingPlayer("boom"), Position(x=1, y=1))
    game.register_player(ScriptedPlayer("ok", Direction.RIGHT), Position(x=0, y=0))

    game.start(max_rounds=3)

    assert listener.names().count("player_turn_started") == 6
    assert listener.names().count("player_turn_ended") == 6


def _stats(listener: RecordingGameListener, name: str) -> list[PlayerStats]:
    return [
        args[1]
        for event, args in listener.events
        if event == "player_stats" and args[0] == name
    ]


def test_the_stats_follow_the_turn_they_summarise() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(ScriptedPlayer("a", Direction.UP), Position(x=1, y=1))

    game.start(max_rounds=1)

    assert listener.names()[-3:-1] == ["player_turn_ended", "player_stats"]


def test_the_totals_accumulate_across_rounds_and_average_the_turns() -> None:
    # Three turns of 2, 4 and 6 seconds: an average of 4 over a total of 12.
    clock = ScriptedClock(
        datetime(2025, 9, 10, 12, 0, 0), datetime(2025, 9, 10, 12, 0, 2),
        datetime(2025, 9, 10, 12, 0, 2), datetime(2025, 9, 10, 12, 0, 6),
        datetime(2025, 9, 10, 12, 0, 6), datetime(2025, 9, 10, 12, 0, 12),
    )
    game, listener = _game(clock), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(ScriptedPlayer("a"), Position(x=1, y=1))

    game.start(max_rounds=3)

    assert _stats(listener, "a") == [
        PlayerStats(turns=1, total_seconds=2.0, average_seconds=2.0),
        PlayerStats(turns=2, total_seconds=6.0, average_seconds=3.0),
        PlayerStats(turns=3, total_seconds=12.0, average_seconds=4.0),
    ]


def test_a_failed_turn_still_counts_toward_the_totals() -> None:
    clock = ScriptedClock(datetime(2025, 9, 10, 12, 0, 0), datetime(2025, 9, 10, 12, 0, 5))
    game, listener = _game(clock), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(ExplodingPlayer("boom"), Position(x=1, y=1))

    game.start(max_rounds=1)

    assert _stats(listener, "boom") == [
        PlayerStats(turns=1, total_seconds=5.0, average_seconds=5.0)
    ]


def test_each_player_accumulates_its_own_totals() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(ScriptedPlayer("a"), Position(x=0, y=0))
    game.register_player(ScriptedPlayer("b"), Position(x=2, y=2))

    game.start(max_rounds=2)

    assert [stats.turns for stats in _stats(listener, "a")] == [1, 2]
    assert [stats.turns for stats in _stats(listener, "b")] == [1, 2]


def test_the_turn_count_matches_the_rounds_played() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(ScriptedPlayer("a", Direction.UP), Position(x=1, y=1))

    game.start(max_rounds=4)

    assert _stats(listener, "a")[-1].turns == 4


def _shooter() -> PlanningPlayer:
    """Stands still and throws three bolts to its right every round."""
    return PlanningPlayer("a", *([_cast(Direction.RIGHT)] * 3))


def _health(listener: RecordingGameListener, name: str) -> list[int]:
    return [
        args[1]
        for event, args in listener.events
        if event == "player_updated" and args[0] == name
    ]


def test_a_robot_starts_the_match_on_full_health() -> None:
    game = _game()
    player = ScriptedPlayer("a")
    game.register_player(player, Position(x=1, y=1))

    game.start(max_rounds=1)

    assert player.views[0].health == 100


def test_a_robot_sees_every_other_robot_and_what_it_has_left() -> None:
    game = _game()
    shooter = PlanningPlayer("shooter", _cast(Direction.RIGHT))
    target = IdlePlayer("target")
    game.register_player(shooter, Position(x=0, y=0))
    game.register_player(target, Position(x=1, y=0))

    game.start(max_rounds=2)

    second = shooter.views[1]
    assert [opponent.name for opponent in second.opponents] == ["target"]
    assert second.opponents[0].position == Position(x=1, y=0)
    assert second.opponents[0].health == 90


def test_a_robot_is_told_the_spells_it_carries() -> None:
    game = _game()
    player = ScriptedPlayer("a")
    game.register_player(player, Position(x=1, y=1))

    game.start(max_rounds=1)

    assert [spell.name for spell in player.views[0].spells] == ["fireball"]


def test_a_fireball_reports_the_squares_it_travelled_through() -> None:
    game, listener = _game(board=Board(width=5, height=5)), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(PlanningPlayer("a", _cast(Direction.RIGHT)), Position(x=0, y=0))

    game.start(max_rounds=1)

    assert ("spell_cast", (
        "a",
        "fireball",
        Position(x=0, y=0),
        Direction.RIGHT,
        (Position(x=1, y=0), Position(x=2, y=0), Position(x=3, y=0)),
    )) in listener.events


def test_a_fireball_that_hits_nobody_reports_no_damage() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(PlanningPlayer("a", _cast(Direction.RIGHT)), Position(x=0, y=0))
    game.register_player(IdlePlayer("far"), Position(x=0, y=2))

    game.start(max_rounds=1)

    assert "player_hit" not in listener.names()
    assert "player_updated" not in listener.names()


def test_a_fireball_takes_ten_health_off_the_first_robot_in_its_way() -> None:
    game, listener = _game(board=Board(width=5, height=5)), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(PlanningPlayer("a", _cast(Direction.RIGHT)), Position(x=0, y=0))
    game.register_player(IdlePlayer("near"), Position(x=2, y=0))

    game.start(max_rounds=1)

    assert ("player_hit", ("near", "a", "fireball", 10, Position(x=2, y=0))) in listener.events
    assert _health(listener, "near") == [90]


def test_a_robot_standing_behind_another_is_safe() -> None:
    game, listener = _game(board=Board(width=5, height=5)), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(PlanningPlayer("a", _cast(Direction.RIGHT)), Position(x=0, y=0))
    game.register_player(IdlePlayer("front"), Position(x=1, y=0))
    game.register_player(IdlePlayer("behind"), Position(x=2, y=0))

    game.start(max_rounds=1)

    assert _health(listener, "front") == [90]
    assert _health(listener, "behind") == []


def test_a_fireball_reaches_three_squares_and_no_further() -> None:
    game, listener = _game(board=Board(width=6, height=6)), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(PlanningPlayer("a", _cast(Direction.RIGHT)), Position(x=0, y=0))
    game.register_player(IdlePlayer("just-out"), Position(x=4, y=0))

    game.start(max_rounds=1)

    assert "player_hit" not in listener.names()


def test_the_hit_is_reported_before_the_health_it_changed() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(PlanningPlayer("a", _cast(Direction.RIGHT)), Position(x=0, y=0))
    game.register_player(IdlePlayer("b"), Position(x=1, y=0))

    game.start(max_rounds=1)

    names = listener.names()
    assert names[names.index("spell_cast") : names.index("spell_cast") + 3] == [
        "spell_cast",
        "player_hit",
        "player_updated",
    ]


def test_damage_accumulates_until_a_robot_is_scrapped() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(PlanningPlayer("a", _cast(Direction.RIGHT)), Position(x=0, y=0))
    game.register_player(IdlePlayer("b"), Position(x=1, y=0))

    game.start(max_rounds=12)

    assert _health(listener, "b") == [90, 80, 70, 60, 50, 40, 30, 20, 10, 0]


def test_health_never_falls_below_zero() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    # Two bolts a turn, so the last of them lands on a robot already at 10.
    game.register_player(
        PlanningPlayer("a", _cast(Direction.RIGHT), _cast(Direction.RIGHT)),
        Position(x=0, y=0),
    )
    game.register_player(IdlePlayer("b"), Position(x=1, y=0))

    game.start(max_rounds=9)

    assert _health(listener, "b")[-1] == 0


def test_a_scrapped_robot_is_skipped_and_never_asked_for_a_plan() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    # Registered first, so it is asked before the shooter can finish it off in the same round.
    target = ScriptedPlayer("b")
    game.register_player(target, Position(x=1, y=0))
    game.register_player(_shooter(), Position(x=0, y=0))
    # A third robot, out of the line of fire, so the match carries on past the kill.
    game.register_player(IdlePlayer("bystander"), Position(x=2, y=2))

    game.start(max_rounds=5)

    # Four rounds of three bolts brings it to zero, so it is only asked in those four.
    assert len(target.views) == 4
    assert ("player_dead", ("b",)) in listener.events


def test_a_skipped_turn_is_still_bracketed_and_still_reports_stats() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(IdlePlayer("b"), Position(x=1, y=0))
    game.register_player(_shooter(), Position(x=0, y=0))
    game.register_player(IdlePlayer("bystander"), Position(x=2, y=2))

    game.start(max_rounds=5)

    names = listener.names()
    dead = names.index("player_dead")
    assert names[dead - 1 : dead + 3] == [
        "player_turn_started",
        "player_dead",
        "player_turn_ended",
        "player_stats",
    ]


def test_a_skipped_turn_does_not_count_towards_the_totals() -> None:
    # Every turn takes two seconds, so a skipped turn counted would drag the average down.
    instants = [datetime(2025, 9, 10, 12, 0, second) for second in range(0, 60, 2)]
    game, listener = _game(ScriptedClock(*instants)), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(IdlePlayer("b"), Position(x=1, y=0))
    game.register_player(_shooter(), Position(x=0, y=0))
    game.register_player(IdlePlayer("bystander"), Position(x=2, y=2))

    game.start(max_rounds=6)

    scrapped = _stats(listener, "b")[-1]
    assert scrapped.turns == 4
    assert scrapped.average_seconds == 2.0


def test_casting_a_spell_the_robot_does_not_carry_fails_the_turn_whole() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(
        PlanningPlayer("a", _move(Direction.RIGHT), _cast(Direction.UP, spell="meteor")),
        Position(x=0, y=0),
    )

    game.start(max_rounds=1)

    assert ("turn_failed", ("a", "cast an unknown spell 'meteor'")) in listener.events
    assert "player_moved" not in listener.names()
    assert "spell_cast" not in listener.names()


def test_moves_and_casts_apply_in_the_order_they_were_planned() -> None:
    game, listener = _game(board=Board(width=5, height=5)), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(
        PlanningPlayer("a", _move(Direction.DOWN), _cast(Direction.RIGHT)),
        Position(x=0, y=0),
    )
    game.register_player(IdlePlayer("b"), Position(x=1, y=1))

    game.start(max_rounds=1)

    assert listener.names().index("player_moved") < listener.names().index("spell_cast")
    # It only reaches "b" from the square it moved to, so the order really was applied.
    assert _health(listener, "b") == [90]


def test_the_match_ends_as_soon_as_one_robot_is_left_standing() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(
        PlanningPlayer("a", *([_cast(Direction.RIGHT)] * 5)), Position(x=0, y=0)
    )
    game.register_player(IdlePlayer("b"), Position(x=1, y=0))

    game.start(max_rounds=100)

    # Ten bolts at five a round, so the second round finishes it.
    assert ("game_ended", (2,)) in listener.events
    assert listener.names().count("round_started") == 2


def test_the_last_robot_standing_wins_the_match() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(
        PlanningPlayer("a", *([_cast(Direction.RIGHT)] * 5)), Position(x=0, y=0)
    )
    game.register_player(IdlePlayer("b"), Position(x=1, y=0))

    game.start(max_rounds=100)

    assert _stats(listener, "a")[-1].wins == 1
    assert _stats(listener, "b")[-1].wins == 0


def test_a_kill_counts_an_elimination_for_the_caster_and_a_death_for_the_target() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(IdlePlayer("b"), Position(x=1, y=0))
    game.register_player(_shooter(), Position(x=0, y=0))
    # A third robot keeps the match alive, so the scrapped one still reports its tally.
    game.register_player(IdlePlayer("bystander"), Position(x=2, y=2))

    game.start(max_rounds=6)

    assert _stats(listener, "a")[-1].eliminations == 1
    assert _stats(listener, "a")[-1].deaths == 0
    assert _stats(listener, "b")[-1].deaths == 1
    assert _stats(listener, "b")[-1].eliminations == 0


def test_when_the_rounds_run_out_the_healthiest_robot_wins() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(PlanningPlayer("a", _cast(Direction.RIGHT)), Position(x=0, y=0))
    game.register_player(IdlePlayer("b"), Position(x=1, y=0))

    game.start(max_rounds=2)

    assert _stats(listener, "a")[-1].wins == 1
    assert _stats(listener, "b")[-1].wins == 0


def test_a_match_that_ends_level_awards_nobody() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(IdlePlayer("a"), Position(x=0, y=0))
    game.register_player(IdlePlayer("b"), Position(x=2, y=2))

    game.start(max_rounds=2)

    assert _stats(listener, "a")[-1].wins == 0
    assert _stats(listener, "b")[-1].wins == 0


def test_a_lone_robot_neither_wins_nor_ends_the_match_early() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(ScriptedPlayer("a", Direction.RIGHT), Position(x=0, y=0))

    game.start(max_rounds=3)

    assert ("game_ended", (3,)) in listener.events
    assert _stats(listener, "a")[-1].wins == 0


def test_stop_ends_the_match_at_the_next_turn_boundary() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(ScriptedPlayer("a", Direction.RIGHT), Position(x=0, y=0))
    game.stop()

    game.start(max_rounds=10)

    assert listener.names() == ["player_joined", "game_started", "game_ended"]
    assert ("game_ended", (0,)) in listener.events


def _turn_order(listener: RecordingGameListener) -> list[str]:
    return [args[0] for name, args in listener.events if name == "player_turn_started"]


def test_the_first_seat_is_passed_along_one_robot_per_round() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    for name, seat in (("a", (0, 0)), ("b", (2, 0)), ("c", (0, 2))):
        game.register_player(IdlePlayer(name), Position(x=seat[0], y=seat[1]))

    game.start(max_rounds=4)

    assert _turn_order(listener) == [
        "a", "b", "c",
        "b", "c", "a",
        "c", "a", "b",
        "a", "b", "c",
    ]


def test_every_robot_leads_the_same_number_of_rounds_over_a_full_cycle() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    for name, seat in (("a", (0, 0)), ("b", (2, 0)), ("c", (0, 2))):
        game.register_player(IdlePlayer(name), Position(x=seat[0], y=seat[1]))

    game.start(max_rounds=6)

    leaders = _turn_order(listener)[::3]
    assert sorted(leaders) == ["a", "a", "b", "b", "c", "c"]


def test_the_first_round_still_runs_in_registration_order() -> None:
    game, listener = _game(), RecordingGameListener()
    game.add_listener(listener)
    game.register_player(IdlePlayer("a"), Position(x=0, y=0))
    game.register_player(IdlePlayer("b"), Position(x=2, y=0))

    game.start(max_rounds=1)

    assert _turn_order(listener) == ["a", "b"]


def _opponents(player: ScriptedPlayer | PlanningPlayer) -> dict[str, Opponent]:
    return {opponent.name: opponent for opponent in player.views[0].opponents}


def test_a_robot_is_told_how_far_away_each_other_robot_is() -> None:
    game = _game(board=Board(width=10, height=10))
    watcher = ScriptedPlayer("watcher")
    game.register_player(watcher, Position(x=4, y=4))
    game.register_player(IdlePlayer("straight"), Position(x=4, y=7))
    game.register_player(IdlePlayer("diagonal"), Position(x=6, y=6))
    game.register_player(IdlePlayer("askew"), Position(x=7, y=6))

    game.start(max_rounds=1)

    seen = _opponents(watcher)
    # A diagonal counts as one step, exactly as a move does.
    assert seen["straight"].distance == 3
    assert seen["diagonal"].distance == 2
    assert seen["askew"].distance == 3


def test_a_robot_is_told_which_way_a_bolt_would_have_to_be_fired() -> None:
    game = _game(board=Board(width=10, height=10))
    watcher = ScriptedPlayer("watcher")
    game.register_player(watcher, Position(x=4, y=4))
    game.register_player(IdlePlayer("below"), Position(x=4, y=7))
    game.register_player(IdlePlayer("diagonal"), Position(x=6, y=6))

    game.start(max_rounds=1)

    seen = _opponents(watcher)
    assert seen["below"].direction is Direction.DOWN
    assert seen["diagonal"].direction is Direction.DOWN_RIGHT


def test_a_robot_on_no_ray_is_reported_as_unreachable() -> None:
    game = _game(board=Board(width=10, height=10))
    watcher = ScriptedPlayer("watcher")
    game.register_player(watcher, Position(x=4, y=4))
    game.register_player(IdlePlayer("askew"), Position(x=7, y=6))

    game.start(max_rounds=1)

    # (3,2) away is neither straight nor an exact diagonal, so nothing can reach it.
    assert _opponents(watcher)["askew"].direction is None


def test_the_geometry_matches_where_a_fireball_actually_goes() -> None:
    """The view must not promise a shot the rules would not deliver."""
    board = Board(width=10, height=10)
    game, listener = _game(board=board), RecordingGameListener()
    game.add_listener(listener)
    watcher = PlanningPlayer("watcher", _cast(Direction.DOWN_RIGHT))
    game.register_player(watcher, Position(x=4, y=4))
    game.register_player(IdlePlayer("diagonal"), Position(x=6, y=6))
    game.register_player(IdlePlayer("bystander"), Position(x=0, y=9))

    game.start(max_rounds=1)

    promised = _opponents(watcher)["diagonal"]
    assert promised.direction is Direction.DOWN_RIGHT and promised.distance == 2
    assert _health(listener, "diagonal") == [90]


def test_a_robot_is_told_what_full_health_is() -> None:
    game = _game()
    watcher = ScriptedPlayer("watcher")
    game.register_player(watcher, Position(x=0, y=0))
    game.register_player(IdlePlayer("other"), Position(x=2, y=2))

    game.start(max_rounds=1)

    # Without a maximum, a robot cannot tell whether 40 health is healthy or nearly dead.
    assert watcher.views[0].max_health == 100
