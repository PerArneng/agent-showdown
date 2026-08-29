from agent_showdown.interfaces.game import GameView, PlayerTurn
from agent_showdown.modules.game import DefaultScoreboard


class NamedPlayer:
    """Only its identity matters here: the scoreboard keys by object, not by name."""

    def __init__(self, name: str) -> None:
        self._name = name

    def get_name(self) -> str:
        return self._name

    def take_turn(self, view: GameView) -> PlayerTurn:
        return PlayerTurn(reasoning="", actions=())


def test_a_player_it_has_never_seen_has_nothing_to_report() -> None:
    stats = DefaultScoreboard().stats_for(NamedPlayer("a"))

    assert (stats.turns, stats.total_seconds, stats.average_seconds) == (0, 0.0, 0.0)
    assert (stats.eliminations, stats.deaths, stats.wins) == (0, 0, 0)


def test_turns_accumulate_and_average_over_the_turns_taken() -> None:
    board, player = DefaultScoreboard(), NamedPlayer("a")

    board.record_turn(player, 2.0)
    board.record_turn(player, 4.0)

    stats = board.stats_for(player)
    assert (stats.turns, stats.total_seconds, stats.average_seconds) == (2, 6.0, 3.0)


def test_it_counts_eliminations_deaths_and_wins_separately() -> None:
    board, player = DefaultScoreboard(), NamedPlayer("a")

    board.record_elimination(player)
    board.record_elimination(player)
    board.record_death(player)
    board.record_win(player)

    stats = board.stats_for(player)
    assert (stats.eliminations, stats.deaths, stats.wins) == (2, 1, 1)


def test_two_contestants_that_share_a_name_keep_separate_tallies() -> None:
    board = DefaultScoreboard()
    first, second = NamedPlayer("twin"), NamedPlayer("twin")

    board.record_win(first)

    assert board.stats_for(first).wins == 1
    assert board.stats_for(second).wins == 0
