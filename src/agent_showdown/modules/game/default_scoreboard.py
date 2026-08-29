from agent_showdown.interfaces.game import Player, PlayerStats


class DefaultScoreboard:
    """Running totals per contestant. Mutable, and the only thing that outlives a match.

    Keyed by `Player` object rather than by name, like the rest of the game, so two contestants
    that share a name keep separate tallies. Only the thread playing the game touches it.
    """

    def __init__(self) -> None:
        self._turns: dict[Player, int] = {}
        self._seconds: dict[Player, float] = {}
        self._eliminations: dict[Player, int] = {}
        self._deaths: dict[Player, int] = {}
        self._wins: dict[Player, int] = {}

    def record_turn(self, player: Player, seconds: float) -> None:
        self._turns[player] = self._turns.get(player, 0) + 1
        self._seconds[player] = self._seconds.get(player, 0.0) + seconds

    def record_elimination(self, player: Player) -> None:
        self._eliminations[player] = self._eliminations.get(player, 0) + 1

    def record_death(self, player: Player) -> None:
        self._deaths[player] = self._deaths.get(player, 0) + 1

    def record_win(self, player: Player) -> None:
        self._wins[player] = self._wins.get(player, 0) + 1

    def stats_for(self, player: Player) -> PlayerStats:
        turns = self._turns.get(player, 0)
        total = self._seconds.get(player, 0.0)
        # The average is assembled here, beside the counters, because `PlayerStats` is data and
        # holds no behaviour. Before the first turn there is nothing to average.
        return PlayerStats(
            turns=turns,
            total_seconds=total,
            average_seconds=total / turns if turns else 0.0,
            eliminations=self._eliminations.get(player, 0),
            deaths=self._deaths.get(player, 0),
            wins=self._wins.get(player, 0),
        )
