from agent_showdown.interfaces.game import GameEndedEvent, RoundStartedEvent
from agent_showdown.modules.event_channel import QueueEventChannel

# Long enough to be a real wait, short enough that the suite stays fast.
_TIMEOUT = 0.05


def test_every_subscriber_gets_every_event() -> None:
    channel = QueueEventChannel()
    first = channel.subscribe()
    second = channel.subscribe()

    channel.publish(RoundStartedEvent(round_number=3))

    assert first.poll(_TIMEOUT) == RoundStartedEvent(round_number=3)
    assert second.poll(_TIMEOUT) == RoundStartedEvent(round_number=3)


def test_events_arrive_in_order() -> None:
    channel = QueueEventChannel()
    subscription = channel.subscribe()

    channel.publish(RoundStartedEvent(round_number=1))
    channel.publish(GameEndedEvent(rounds_played=1))

    assert subscription.poll(_TIMEOUT) == RoundStartedEvent(round_number=1)
    assert subscription.poll(_TIMEOUT) == GameEndedEvent(rounds_played=1)


def test_poll_returns_none_when_nothing_is_published() -> None:
    subscription = QueueEventChannel().subscribe()

    assert subscription.poll(_TIMEOUT) is None


def test_a_subscription_misses_events_published_before_it_existed() -> None:
    channel = QueueEventChannel()
    channel.publish(RoundStartedEvent(round_number=1))

    late = channel.subscribe()

    assert late.poll(_TIMEOUT) is None


def test_closing_stops_delivery_and_leaves_other_subscribers_alone() -> None:
    channel = QueueEventChannel()
    closed = channel.subscribe()
    open_one = channel.subscribe()
    closed.close()

    channel.publish(RoundStartedEvent(round_number=1))

    assert closed.poll(_TIMEOUT) is None
    assert open_one.poll(_TIMEOUT) == RoundStartedEvent(round_number=1)


def test_closing_twice_is_harmless() -> None:
    subscription = QueueEventChannel().subscribe()

    subscription.close()
    subscription.close()


def test_publishing_with_no_subscribers_is_harmless() -> None:
    QueueEventChannel().publish(GameEndedEvent(rounds_played=10))


def test_a_subscription_exposes_nothing_beyond_its_contract() -> None:
    # The channel used to fill the queue by calling a public `offer` that no Protocol declared,
    # which meant nothing could stand in for the subscription.
    subscription = QueueEventChannel().subscribe()

    surface = {name for name in dir(subscription) if not name.startswith("_")}

    assert surface == {"poll", "close"}
