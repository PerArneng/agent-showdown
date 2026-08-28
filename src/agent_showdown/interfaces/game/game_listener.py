from typing import Protocol

from agent_showdown.interfaces.game.board import Board
from agent_showdown.interfaces.game.direction import Direction
from agent_showdown.interfaces.game.player import Player
from agent_showdown.interfaces.game.position import Position


class GameListener(Protocol):
    """Observes a game. Every event names the player it is about first."""

    def game_started(self, board: Board, max_rounds: int) -> None:
        """The game is about to run for `max_rounds` rounds."""
        ...

    def player_joined(self, player: Player, position: Position) -> None:
        """A player was registered at its starting position."""
        ...

    def round_started(self, round_number: int) -> None:
        """A new round begins. Rounds are numbered from 1."""
        ...

    def player_moved(self, player: Player, source: Position, destination: Position) -> None:
        """A player left `source` and now stands on `destination`."""
        ...

    def player_reasoned(self, player: Player, reasoning: str) -> None:
        """A player explained the turn it planned, before the moves are applied."""
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
