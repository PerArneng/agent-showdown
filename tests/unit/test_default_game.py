from datetime import datetime

from agent_showdown.interfaces.game import (
    Board,
    Direction,
    GameView,
    Move,
    Movement,
    PlayerStats,
    PlayerTurn,
    Position,
)
from agent_showdown.modules.game import DefaultGame
from tests.fakes import FrozenClock, RecordingGameListener, ScriptedClock


class ScriptedPlayer:
    """Plays a fixed plan every round, so the game under test stays deterministic."""

    def __init__(self, name: str, *directions: Direction, reasoning: str = "") -> None:
        self._name = name
        self._turn = PlayerTurn(
            reasoning=reasoning,
            movement=Movement(moves=tuple(Move(direction=d) for d in directions)),
        )
        self.views: list[GameView] = []

    def get_name(self) -> str:
        return self._name

    def take_turn(self, view: GameView) -> PlayerTurn:
        self.views.append(view)
        return self._turn


def _game() -> DefaultGame:
    # A frozen clock makes every turn take zero seconds, which keeps the durations out of the way
    # of the tests that are about something else. `ScriptedClock` is for the ones that are not.
    return DefaultGame(Board(width=3, height=3), FrozenClock(datetime(2025, 9, 10)))


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

    assert ("turn_failed", ("greedy", "planned 9 moves, the limit is 8")) in listener.events
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
    game, listener = DefaultGame(Board(width=3, height=3), clock), RecordingGameListener()
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
    game, listener = DefaultGame(Board(width=3, height=3), clock), RecordingGameListener()
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
    game, listener = DefaultGame(Board(width=3, height=3), clock), RecordingGameListener()
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
