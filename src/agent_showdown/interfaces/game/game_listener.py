from typing import Protocol

from agent_showdown.interfaces.game.board import Board
from agent_showdown.interfaces.game.direction import Direction
from agent_showdown.interfaces.game.player import Player
from agent_showdown.interfaces.game.player_stats import PlayerStats
from agent_showdown.interfaces.game.position import Position


class GameListener(Protocol):
    """Observes a game. Every event names the player it is about first.

    The two arena methods are the exception: they are about the loop *around* the games rather
    than any one game. They live here so `ChannelGameListener` stays the only translator from a
    callback to an event — a second protocol and a second translator would cost more than the
    tidiness is worth.
    """

    def arena_paused(self) -> None:
        """No contestants are registered, so no match can start."""
        ...

    def arena_resumed(self) -> None:
        """Somebody registered, so matches begin again."""
        ...

    def player_registered(self, player: Player) -> None:
        """A robot entered the arena. It sits down in the next match, not the one in flight."""
        ...

    def player_unregistered(self, name: str) -> None:
        """A robot left the arena. Only its name is left to report it by."""
        ...

    def game_started(self, board: Board, max_rounds: int) -> None:
        """The game is about to run for `max_rounds` rounds."""
        ...

    def player_joined(self, player: Player, position: Position) -> None:
        """A player was registered at its starting position."""
        ...

    def round_started(self, round_number: int) -> None:
        """A new round begins. Rounds are numbered from 1."""
        ...

    def player_turn_started(self, player: Player) -> None:
        """A player was handed its view and is now thinking."""
        ...

    def player_turn_ended(self, player: Player, seconds: float) -> None:
        """A player's turn is over, after `seconds`, whether it planned or failed."""
        ...

    def player_stats(self, player: Player, stats: PlayerStats) -> None:
        """A player's running totals, right after one of its turns ended."""
        ...

    def player_dead(self, player: Player) -> None:
        """A player's turn came round but it has no health left, so it was skipped."""
        ...

    def player_moved(self, player: Player, source: Position, destination: Position) -> None:
        """A player left `source` and now stands on `destination`."""
        ...

    def player_reasoned(self, player: Player, reasoning: str) -> None:
        """A player explained the turn it planned, before the moves are applied."""
        ...

    def spell_cast(
        self,
        player: Player,
        spell: str,
        origin: Position,
        direction: Direction,
        path: tuple[Position, ...],
    ) -> None:
        """A player cast `spell`, which travelled `path` from `origin`."""
        ...

    def player_hit(
        self, player: Player, source: Player, spell: str, damage: int, position: Position
    ) -> None:
        """`player` was hit on `position` by `source`'s spell, for `damage`."""
        ...

    def player_updated(self, player: Player, health: int) -> None:
        """A player's health changed. Zero means eliminated."""
        ...

    def move_blocked(self, player: Player, position: Position, direction: Direction) -> None:
        """A move would have left the board, so the player stayed on `position`."""
        ...

    def turn_failed(self, player: Player, reason: str) -> None:
        """A player could not be asked for a turn, or answered with something unusable."""
        ...

    def game_ended(self, rounds_played: int) -> None:
        """The game is over."""
        ...
