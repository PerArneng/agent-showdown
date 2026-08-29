from agent_showdown.interfaces.clock import Clock
from agent_showdown.interfaces.game import Board, Game, Scoreboard, SpellBook
from agent_showdown.modules.game.default_game import DefaultGame


class DefaultGameFactory:
    """Builds a fresh `DefaultGame` per match.

    The scoreboard it hands out is a singleton on purpose: the board resets between matches, the
    tally does not.
    """

    def __init__(self, clock: Clock, spell_book: SpellBook, scoreboard: Scoreboard) -> None:
        self._clock = clock
        self._spell_book = spell_book
        self._scoreboard = scoreboard

    def create(self, board: Board) -> Game:
        return DefaultGame(board, self._clock, self._spell_book, self._scoreboard)
