from agent_showdown.interfaces.clock import Clock
from agent_showdown.interfaces.game import (
    Board,
    BoardFactory,
    Game,
    Scoreboard,
    SpellBook,
)
from agent_showdown.modules.game.default_game import DefaultGame


class DefaultGameFactory:
    """Builds a fresh `DefaultGame` per match.

    The scoreboard it hands out is a singleton on purpose: the board resets between matches, the
    tally does not.
    """

    def __init__(
        self,
        clock: Clock,
        spell_book: SpellBook,
        scoreboard: Scoreboard,
        board_factory: BoardFactory,
        redeal_each_round: bool,
    ) -> None:
        self._clock = clock
        self._spell_book = spell_book
        self._scoreboard = scoreboard
        self._board_factory = board_factory
        self._redeal_each_round = redeal_each_round

    def create(self, board: Board) -> Game:
        # The flag is read here rather than in the game, so the game domain never has to import
        # the application's config to answer one question about itself.
        return DefaultGame(
            board,
            self._clock,
            self._spell_book,
            self._scoreboard,
            self._board_factory if self._redeal_each_round else None,
        )
