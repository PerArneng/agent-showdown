"""The point of the A2A spike: a remote-agent player competing in a real game.

Everything here runs in memory. No network, no new dependencies -- `ScriptedAgentClient`
stands in for the HTTP transport that will eventually speak A2A JSON-RPC.
"""

import json
from datetime import datetime

from agent_showdown.interfaces.game import Board, Position
from agent_showdown.modules.game import (
    A2APlayerFactory,
    DefaultGame,
    DefaultScoreboard,
    DefaultSpellBook,
    DummyPlayerFactory,
    LogGameListener,
)
from agent_showdown.modules.log import AnsiLogFormatter, DefaultLogger
from tests.fakes import (
    FixedRandomizer,
    FrozenClock,
    InMemoryConsole,
    RecordingGameListener,
    ScriptedAgentClient,
)

# The remote agent walks right, then down, then right again.
_REPLIES = [
    '{"reasoning": "east first", "actions": [{"kind": "move", "direction": "RIGHT"}]}',
    '{"reasoning": "then south", "actions": [{"kind": "move", "direction": "DOWN"}]}',
    '{"reasoning": "east again", "actions": [{"kind": "move", "direction": "RIGHT"}]}',
]


def _log_listener(console: InMemoryConsole) -> LogGameListener:
    return LogGameListener(
        DefaultLogger(
            clock=FrozenClock(datetime(2025, 9, 10)),
            formatter=AnsiLogFormatter(),
            console=console,
        )
    )


def test_a_remote_agent_plays_alongside_a_local_dummy() -> None:
    console, recorder = InMemoryConsole(), RecordingGameListener()
    client = ScriptedAgentClient(_REPLIES)
    game = DefaultGame(
        Board(width=5, height=5),
        FrozenClock(datetime(2025, 9, 10)),
        DefaultSpellBook(),
        DefaultScoreboard(),
    )
    game.add_listener(_log_listener(console))
    game.add_listener(recorder)
    game.register_player(A2APlayerFactory(client).create("agent-1"), Position(x=0, y=0))
    game.register_player(
        DummyPlayerFactory(
            FixedRandomizer([3]), FrozenClock(datetime(2025, 9, 10)), think_time=0.0
        ).create("dummy-1"),
        Position(x=4, y=4),
    )

    game.start(max_rounds=3)

    # The remote player moved exactly as its agent scripted: (0,0) -> (1,0) -> (1,1) -> (2,1).
    agent_moves = [
        event[1] for event in recorder.events
        if event[0] == "player_moved" and event[1][0] == "agent-1"
    ]
    assert agent_moves == [
        ("agent-1", Position(x=0, y=0), Position(x=1, y=0)),
        ("agent-1", Position(x=1, y=0), Position(x=1, y=1)),
        ("agent-1", Position(x=1, y=1), Position(x=2, y=1)),
    ]
    assert recorder.names().count("turn_failed") == 0
    assert any("player agent-1 moved from (0,0) to (1,0)" in line for line in console.lines)


def test_the_agent_is_asked_once_per_round_under_a_stable_context_id() -> None:
    client = ScriptedAgentClient(_REPLIES)
    game = DefaultGame(
        Board(width=5, height=5),
        FrozenClock(datetime(2025, 9, 10)),
        DefaultSpellBook(),
        DefaultScoreboard(),
    )
    game.register_player(A2APlayerFactory(client).create("agent-1"), Position(x=0, y=0))

    game.start(max_rounds=3)

    assert [context_id for context_id, _ in client.sent] == ["agent-1"] * 3
    views = [json.loads(payload) for payload in client.payloads()]
    assert [view["round_number"] for view in views] == [1, 2, 3]
    # Each view shows the agent where its own previous move left it.
    assert [view["position"] for view in views] == [
        {"x": 0, "y": 0},
        {"x": 1, "y": 0},
        {"x": 1, "y": 1},
    ]
    assert views[0]["board"] == {"width": 5, "height": 5}


def test_a_dead_agent_fails_its_turns_but_the_game_finishes() -> None:
    console, recorder = InMemoryConsole(), RecordingGameListener()
    client = ScriptedAgentClient(fails_with="connection refused")
    game = DefaultGame(
        Board(width=5, height=5),
        FrozenClock(datetime(2025, 9, 10)),
        DefaultSpellBook(),
        DefaultScoreboard(),
    )
    game.add_listener(_log_listener(console))
    game.add_listener(recorder)
    game.register_player(A2APlayerFactory(client).create("agent-1"), Position(x=0, y=0))

    game.start(max_rounds=2)

    assert recorder.names().count("turn_failed") == 2
    assert recorder.names()[-1] == "game_ended"
    assert any(
        "player agent-1 failed its turn: AgentClientError: connection refused" in line
        for line in console.lines
    )
