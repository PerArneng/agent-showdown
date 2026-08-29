from typing import Protocol

from agent_showdown.interfaces.game.player import Player
from agent_showdown.interfaces.game.player_stats import PlayerStats


class Scoreboard(Protocol):
    """Running totals per contestant, across every match of a series.

    The one mutable thing in the domain, and deliberately so: a `Game` is built fresh per match, so
    a tally kept there would reset every time. Players are keyed by object, like everywhere else in
    the game, because two contestants may share a name.
    """

    def record_turn(self, player: Player, seconds: float) -> None:
        """Count one finished turn and what it cost."""
        ...

    def record_elimination(self, player: Player) -> None:
        """Count one opponent this player brought to zero health."""
        ...

    def record_death(self, player: Player) -> None:
        """Count one time this player was brought to zero health."""
        ...

    def record_win(self, player: Player) -> None:
        """Count one match this player won."""
        ...

    def stats_for(self, player: Player) -> PlayerStats:
        """Return everything counted so far for this player."""
        ...
