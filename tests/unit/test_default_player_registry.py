import threading

from agent_showdown.interfaces.game import GameView, PlayerTurn
from agent_showdown.modules.game import DefaultPlayerRegistry


class NamedPlayer:
    """The registry only ever asks a player its name."""

    def __init__(self, name: str) -> None:
        self._name = name

    def get_name(self) -> str:
        return self._name

    def take_turn(self, view: GameView) -> PlayerTurn:
        return PlayerTurn(reasoning="", actions=())


def test_an_empty_arena_has_nobody_in_it() -> None:
    assert DefaultPlayerRegistry().players() == ()


def test_registering_keeps_the_order_robots_joined_in() -> None:
    registry = DefaultPlayerRegistry()

    registry.register(NamedPlayer("a"))
    registry.register(NamedPlayer("b"))

    assert [player.get_name() for player in registry.players()] == ["a", "b"]


def test_unregistering_removes_the_robot_and_says_it_did() -> None:
    registry = DefaultPlayerRegistry()
    registry.register(NamedPlayer("a"))
    registry.register(NamedPlayer("b"))

    assert registry.unregister("a") is True
    assert [player.get_name() for player in registry.players()] == ["b"]


def test_unregistering_somebody_who_never_joined_says_so() -> None:
    registry = DefaultPlayerRegistry()

    assert registry.unregister("nobody") is False


def test_the_roster_handed_out_is_a_copy() -> None:
    registry = DefaultPlayerRegistry()
    registry.register(NamedPlayer("a"))

    before = registry.players()
    registry.register(NamedPlayer("b"))

    # The arena plays the match it was handed, whatever happens to the roster meanwhile.
    assert len(before) == 1


def test_waiting_returns_at_once_when_somebody_is_already_in() -> None:
    registry = DefaultPlayerRegistry()
    registry.register(NamedPlayer("a"))

    assert registry.await_players(timeout=5.0) is True


def test_waiting_on_an_empty_arena_times_out() -> None:
    assert DefaultPlayerRegistry().await_players(timeout=0.01) is False


def test_a_registration_wakes_whoever_is_waiting() -> None:
    registry = DefaultPlayerRegistry()
    woke = threading.Event()

    def wait() -> None:
        if registry.await_players(timeout=5.0):
            woke.set()

    waiter = threading.Thread(target=wait)
    waiter.start()
    registry.register(NamedPlayer("late"))
    waiter.join(timeout=5.0)

    # Woken by the registration rather than by the timeout: a paused arena resumes at once.
    assert woke.is_set()
