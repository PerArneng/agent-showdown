import threading
import time
from collections.abc import Callable
from datetime import datetime

from agent_showdown.interfaces.game import (
    Action,
    ActionKind,
    Board,
    Direction,
    GameListener,
    Player,
    PlayerTurn,
    Position,
)
from agent_showdown.modules.engine import DefaultEngine
from agent_showdown.modules.game import (
    DefaultGameFactory,
    DefaultPlayerRegistry,
    DefaultScoreboard,
    DefaultSpellBook,
    DummyPlayerFactory,
    LogGameListener,
    SnapshotGameListener,
)
from agent_showdown.modules.log import AnsiLogFormatter, DefaultLogger
from tests.fakes import (
    FixedRandomizer,
    FrozenClock,
    InMemoryConsole,
    RecordingGameListener,
    ScriptedAgentRoster,
)

_INFO = "2025-09-10 \x1b[32mINFO\x1b[0m "
_WARNING = "2025-09-10 \x1b[33mWARNING\x1b[0m "

# The built-in agent, with the model replaced by a script. No test ever reaches a model.
_PLANNED = PlayerTurn(
    reasoning="walking the diagonal",
    actions=(Action(kind=ActionKind.MOVE, direction=Direction.UP_LEFT),),
)
_AGENT_NAMES = ("simple-strands-vllm", "simple-strands-lmstudio")


class Arena:
    """An engine and everything around it, with fakes at the edges.

    The arena never returns on its own, so every test drives it the way the server does: on a
    thread, stopped by something the test controls.
    """

    def __init__(self, *extra_listeners: GameListener, max_rounds: int = 2) -> None:
        self.console = InMemoryConsole()
        self.registry = DefaultPlayerRegistry()
        self.snapshots = SnapshotGameListener()
        self.recorder = RecordingGameListener()
        clock = FrozenClock(datetime(2025, 9, 10))
        logger = DefaultLogger(clock=clock, formatter=AnsiLogFormatter(), console=self.console)
        self.dummies = DummyPlayerFactory(
            randomizer=FixedRandomizer([3, 1]), clock=clock, think_time=0.0
        )
        self.engine = DefaultEngine(
            logger=logger,
            game_factory=DefaultGameFactory(clock, DefaultSpellBook(), DefaultScoreboard()),
            game_listeners=[
                LogGameListener(logger),
                self.recorder,
                *extra_listeners,
                self.snapshots,
            ],
            snapshot_source=self.snapshots,
            player_registry=self.registry,
            max_rounds=max_rounds,
        )
        self._thread = threading.Thread(target=self.engine.run_arena, daemon=True)

    def agents(self) -> list[Player]:
        return list(ScriptedAgentRoster(_AGENT_NAMES, [_PLANNED]).create_players())

    def run_until(self, done: threading.Event, seconds: float = 5.0) -> None:
        """Play until whatever the test is waiting for happens, then stop and join."""
        self._thread.start()
        done.wait(timeout=seconds)
        self.engine.stop_arena()
        self._thread.join(timeout=seconds)

    def matches_started(self) -> int:
        return self.recorder.names().count("game_started")


class After:
    """Sets an event once a callback has fired `count` times."""

    def __init__(self, count: int) -> None:
        self.reached = threading.Event()
        self._count = count
        self._seen = 0

    def fire(self) -> None:
        self._seen += 1
        if self._seen >= self._count:
            self.reached.set()


class GatedPlayer:
    """Blocks in the middle of its turn until the test lets it go.

    A match on a frozen clock is over in microseconds, so there is no way to interrupt one from
    outside without a contestant that can be held still.
    """

    def __init__(self, name: str) -> None:
        self._name = name
        self.asked = threading.Event()
        self.release = threading.Event()

    def get_name(self) -> str:
        return self._name

    def take_turn(self, view: object) -> PlayerTurn:
        self.asked.set()
        self.release.wait(timeout=5.0)
        return PlayerTurn(reasoning="", actions=())


class OnEvent:
    """A listener that runs one callback on one kind of event, like the web frontend does.

    Everything else is swallowed, so it satisfies `GameListener` without spelling out sixteen
    empty methods.
    """

    def __init__(self, name: str, act: Callable[..., None]) -> None:
        self._name = name
        self._act = act

    def __getattr__(self, name: str) -> Callable[..., None]:
        if name == self._name:
            return self._act
        return lambda *args, **kwargs: None


def _joins(arena: "Arena") -> list[str]:
    return [args[0] for name, args in arena.recorder.events if name == "player_joined"]


def _wait_for(
    condition: Callable[[], bool], release: threading.Event | None = None, seconds: float = 5.0
) -> bool:
    """Poll until the arena has done the thing, rather than guessing at a sleep."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if release is not None:
            # Let the held contestant through a turn at a time, so matches keep turning over.
            release.set()
            release.clear()
        if condition():
            return True
        time.sleep(0.01)
    return False


def test_an_arena_with_nobody_in_it_pauses_instead_of_playing() -> None:
    paused = After(1)
    arena = Arena(
        OnEvent("arena_paused", paused.fire),
    )

    arena.run_until(paused.reached)

    assert "arena_paused" in arena.recorder.names()
    assert arena.matches_started() == 0
    assert _INFO + "arena paused: no robots registered" in arena.console.lines


def test_the_pause_is_announced_once_however_long_it_lasts() -> None:
    paused = After(1)
    arena = Arena(
        OnEvent("arena_paused", paused.fire),
    )

    arena.run_until(paused.reached)

    # The loop spins while empty; the event must not spin with it.
    assert arena.recorder.names().count("arena_paused") == 1


def test_registering_a_robot_resumes_a_paused_arena_with_no_browser_involved() -> None:
    paused, started = After(1), After(1)
    arena = Arena(
        OnEvent("arena_paused", paused.fire),
        OnEvent("game_started", lambda board, max_rounds: started.fire()),
    )
    arena._thread.start()
    paused.reached.wait(timeout=5.0)

    # Nothing presses a button: registering is the whole of it.
    arena.engine.register_player(arena.dummies.create("dummy-1"))
    started.reached.wait(timeout=5.0)
    arena.engine.stop_arena()
    arena._thread.join(timeout=5.0)

    names = arena.recorder.names()
    assert "arena_resumed" in names
    assert names.index("arena_resumed") < names.index("game_started")


def test_matches_run_back_to_back_for_as_long_as_the_arena_is_up() -> None:
    three = After(3)
    arena = Arena(
        OnEvent("game_started", lambda board, max_rounds: three.fire()),
    )
    for player in arena.agents():
        arena.engine.register_player(player)

    arena.run_until(three.reached)

    assert arena.matches_started() >= 3
    assert _INFO + "match 3 started" in arena.console.lines


def test_a_robot_that_joins_mid_match_is_seated_in_the_next_one() -> None:
    arena = Arena()
    early = GatedPlayer("early")
    arena.engine.register_player(early)
    arena._thread.start()
    early.asked.wait(timeout=5.0)

    # Joining while a match is in flight. A Game fixes its contestants when it starts, so this
    # one has to wait for the next.
    arena.engine.register_player(arena.dummies.create("late"))
    joined_late = _wait_for(lambda: "late" in _joins(arena), early.release)
    arena.engine.stop_arena()
    early.release.set()
    arena._thread.join(timeout=5.0)

    assert joined_late
    assert _joins(arena)[0] == "early"


def test_unregistering_the_last_robot_pauses_the_arena_again() -> None:
    paused = After(1)
    arena = Arena(OnEvent("arena_paused", paused.fire))
    arena.engine.register_player(arena.dummies.create("only"))
    arena._thread.start()

    arena.engine.unregister_player("only")
    paused.reached.wait(timeout=5.0)
    arena.engine.stop_arena()
    arena._thread.join(timeout=5.0)

    assert "arena_paused" in arena.recorder.names()


def test_new_game_cuts_the_match_short_and_deals_another() -> None:
    arena = Arena(max_rounds=50)
    held = GatedPlayer("held")
    arena.engine.register_player(held)
    arena._thread.start()
    held.asked.wait(timeout=5.0)

    arena.engine.new_game()
    held.release.set()
    dealt_again = _wait_for(lambda: arena.matches_started() >= 2)
    arena.engine.stop_arena()
    arena._thread.join(timeout=5.0)

    ended = [args[0] for name, args in arena.recorder.events if name == "game_ended"]
    # Abandoned in its first round rather than played out to fifty, and another followed it.
    assert ended[0] < 50
    assert dealt_again


def test_a_second_arena_on_the_same_engine_is_refused() -> None:
    started = After(1)
    arena = Arena(OnEvent("game_started", lambda board, max_rounds: started.fire()))
    arena.engine.register_player(arena.dummies.create("a"))
    arena._thread.start()
    started.reached.wait(timeout=5.0)

    arena.engine.run_arena()  # returns at once rather than playing a second arena

    arena.engine.stop_arena()
    arena._thread.join(timeout=5.0)
    assert _WARNING + "the arena is already running" in arena.console.lines


def test_the_snapshot_says_the_arena_is_idle_so_a_late_client_can_too() -> None:
    paused = After(1)
    arena = Arena(OnEvent("arena_paused", paused.fire))

    arena.run_until(paused.reached)

    assert arena.engine.game_snapshot().paused is True


def test_the_snapshot_describes_the_match_being_played() -> None:
    started = After(1)
    arena = Arena(OnEvent("game_started", lambda board, max_rounds: started.fire()))
    for player in arena.agents():
        arena.engine.register_player(player)

    arena.run_until(started.reached)

    snapshot = arena.engine.game_snapshot()
    assert snapshot.board == Board(width=10, height=10)
    # The contestants registered for this match, not the last one's, and starting it kept them.
    assert sorted(player.name for player in snapshot.players) == sorted(_AGENT_NAMES)


def test_robots_are_seated_on_their_own_corners() -> None:
    started = After(1)
    arena = Arena(
        OnEvent("game_started", lambda board, max_rounds: started.fire()),
    )
    for player in arena.agents():
        arena.engine.register_player(player)

    arena.run_until(started.reached)

    joins = [args for name, args in arena.recorder.events if name == "player_joined"]
    assert joins[0] == (_AGENT_NAMES[0], Position(x=0, y=0))
    assert joins[1] == (_AGENT_NAMES[1], Position(x=9, y=9))


def test_stopping_ends_the_arena_rather_than_the_process_waiting_it_out() -> None:
    started = After(1)
    arena = Arena(
        OnEvent("game_started", lambda board, max_rounds: started.fire()),
        max_rounds=1000,
    )
    arena.engine.register_player(arena.dummies.create("a"))
    arena._thread.start()
    started.reached.wait(timeout=5.0)

    arena.engine.stop_arena()
    arena._thread.join(timeout=5.0)

    assert not arena._thread.is_alive()
    assert arena.console.lines[-1] == _INFO + "arena stopped"


def test_entering_the_arena_is_announced_before_any_match_seats_the_robot() -> None:
    paused = After(1)
    arena = Arena(OnEvent("arena_paused", paused.fire))
    arena._thread.start()
    paused.reached.wait(timeout=5.0)

    arena.engine.register_player(arena.dummies.create("newcomer"))
    seated = _wait_for(lambda: "newcomer" in _joins(arena))
    arena.engine.stop_arena()
    arena._thread.join(timeout=5.0)

    names = arena.recorder.names()
    assert ("player_registered", ("newcomer",)) in arena.recorder.events
    # Entering the arena and being seated on a board are two different moments.
    assert names.index("player_registered") < names.index("player_joined")
    assert seated


def test_leaving_the_arena_is_announced() -> None:
    arena = Arena()
    arena.engine.register_player(arena.dummies.create("quitter"))

    arena.engine.unregister_player("quitter")

    assert ("player_unregistered", ("quitter",)) in arena.recorder.events


def test_leaving_when_you_never_entered_announces_nothing() -> None:
    arena = Arena()

    assert arena.engine.unregister_player("ghost") is False
    assert "player_unregistered" not in arena.recorder.names()


def test_the_snapshot_carries_the_arena_roster_even_while_paused() -> None:
    arena = Arena()
    arena.engine.register_player(arena.dummies.create("a"))
    arena.engine.register_player(arena.dummies.create("b"))

    # No match has been played, so nobody is on a board yet — but they are in the arena.
    snapshot = arena.engine.game_snapshot()

    assert snapshot.registered == ("a", "b")
    assert snapshot.players == ()


def test_the_roster_follows_robots_out_again() -> None:
    arena = Arena()
    arena.engine.register_player(arena.dummies.create("a"))
    arena.engine.register_player(arena.dummies.create("b"))

    arena.engine.unregister_player("a")

    assert arena.engine.game_snapshot().registered == ("b",)
