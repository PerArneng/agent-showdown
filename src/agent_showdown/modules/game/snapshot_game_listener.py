from agent_showdown.interfaces.game import (
    Board,
    Direction,
    GameSnapshot,
    Player,
    PlayerSnapshot,
    PlayerStats,
    Position,
)


class SnapshotGameListener:
    """Keeps the current game as a value, for clients that connect after it started.

    Concurrency: the game thread writes and HTTP threads read, but there is no lock. Every write
    *replaces* the snapshot with a new frozen one rather than mutating it, and rebinding one
    attribute is atomic — so a reader sees either the old value or the new one, never a half-built
    board. This is the same rule the client follows with `ClientState`, for the same reason.
    """

    def __init__(self) -> None:
        self._snapshot = GameSnapshot()

    def snapshot(self) -> GameSnapshot:
        return self._snapshot

    def game_started(self, board: Board, max_rounds: int) -> None:
        # A new game starts from nothing, so a reload does not inherit the last one's players.
        self._snapshot = GameSnapshot(board=board, max_rounds=max_rounds)

    def player_joined(self, player: Player, position: Position) -> None:
        self._snapshot = self._with_player(
            PlayerSnapshot(name=player.get_name(), position=position)
        )

    def round_started(self, round_number: int) -> None:
        self._snapshot = self._snapshot.model_copy(
            update={"round_number": round_number, "playing": True}
        )

    def player_turn_started(self, player: Player) -> None:
        """Thinking changes nothing yet. The time it takes lands when the turn ends."""

    def player_turn_ended(self, player: Player, seconds: float) -> None:
        self._snapshot = self._with_player(
            self._player(player.get_name()).model_copy(update={"think_seconds": seconds})
        )

    def player_stats(self, player: Player, stats: PlayerStats) -> None:
        """Not kept: the stream carries the totals and nothing renders them yet."""

    def player_dead(self, player: Player) -> None:
        """Health already says so. The stream carries the skip."""

    def player_moved(self, player: Player, source: Position, destination: Position) -> None:
        self._snapshot = self._with_player(
            self._player(player.get_name()).model_copy(update={"position": destination})
        )

    def player_reasoned(self, player: Player, reasoning: str) -> None:
        self._snapshot = self._with_player(
            self._player(player.get_name()).model_copy(update={"reasoning": reasoning})
        )

    def spell_cast(
        self,
        player: Player,
        spell: str,
        origin: Position,
        direction: Direction,
        path: tuple[Position, ...],
    ) -> None:
        """A bolt is transient. What it did lands as `player_updated`."""

    def player_hit(
        self, player: Player, source: Player, spell: str, damage: int, position: Position
    ) -> None:
        """The damage it did arrives as `player_updated`, which is the state worth keeping."""

    def player_updated(self, player: Player, health: int) -> None:
        self._snapshot = self._with_player(
            self._player(player.get_name()).model_copy(update={"health": health})
        )

    def move_blocked(self, player: Player, position: Position, direction: Direction) -> None:
        """Nothing moved, so the snapshot is already right."""

    def turn_failed(self, player: Player, reason: str) -> None:
        """A failed turn changes no position. The stream carries the reason."""

    def game_ended(self, rounds_played: int) -> None:
        self._snapshot = self._snapshot.model_copy(update={"playing": False})

    def _player(self, name: str) -> PlayerSnapshot:
        for player in self._snapshot.players:
            if player.name == name:
                return player
        return PlayerSnapshot(name=name, position=Position(x=0, y=0))

    def _with_player(self, player: PlayerSnapshot) -> GameSnapshot:
        others = tuple(known for known in self._snapshot.players if known.name != player.name)
        return self._snapshot.model_copy(update={"players": (*others, player)})
