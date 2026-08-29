from collections.abc import Callable

from agent_showdown.interfaces.clock import Clock
from agent_showdown.interfaces.game import (
    Action,
    ActionKind,
    Board,
    Direction,
    GameListener,
    GameView,
    Opponent,
    Player,
    PlayerTurn,
    Position,
    Scoreboard,
    Spell,
    SpellBook,
)
from agent_showdown.modules.game.deltas import DELTAS

# A turn is one plan. This stops a single greedy agent from hogging a round.
_MAX_ACTIONS_PER_TURN = 8
# What every robot walks onto the board with, and the number a health bar is a fraction of.
_MAX_HEALTH = 100


class DefaultGame:
    """One match on one board. Pure: no IO, no randomness; time only through the injected clock."""

    def __init__(
        self, board: Board, clock: Clock, spell_book: SpellBook, scoreboard: Scoreboard
    ) -> None:
        self._board = board
        self._clock = clock
        self._spell_book = spell_book
        # Shared across every match of a series, which is the whole point: wins, eliminations and
        # deaths would reset with the board otherwise.
        self._scoreboard = scoreboard
        self._listeners: list[GameListener] = []
        self._players: list[Player] = []
        self._positions: dict[Player, Position] = {}
        # Keyed by object like `_positions`, because two contestants may share a name. A fresh
        # game is built per match, so these cannot leak from one game into the next.
        self._health: dict[Player, int] = {}
        self._spells: dict[Player, tuple[Spell, ...]] = {}
        self._stopping = False

    def add_listener(self, listener: GameListener) -> None:
        self._listeners.append(listener)

    def register_player(self, player: Player, position: Position) -> None:
        self._players.append(player)
        self._positions[player] = position
        self._health[player] = _MAX_HEALTH
        self._spells[player] = self._spell_book.create_spells()
        self._emit(lambda listener: listener.player_joined(player, position))

    def stop(self) -> None:
        """Read by the round and turn loops, both on the thread playing the game, so no lock."""
        self._stopping = True

    def start(self, max_rounds: int) -> None:
        self._emit(lambda listener: listener.game_started(self._board, max_rounds))
        rounds_played = 0
        for round_number in range(1, max_rounds + 1):
            if self._stopping or self._is_decided():
                break
            rounds_played = round_number
            self._play_round(round_number)
        self._award_win()
        self._emit(lambda listener: listener.game_ended(rounds_played))

    def _play_round(self, round_number: int) -> None:
        self._emit(lambda listener: listener.round_started(round_number))
        for player in self._turn_order(round_number):
            # Checked between turns too: a hundred rounds of slow agents is a long time to wait
            # for a shutdown, and a match is over the moment one robot is left.
            if self._stopping or self._is_decided():
                return
            self._play_turn(player, round_number)

    def _turn_order(self, round_number: int) -> list[Player]:
        """Registration order, rotated one seat per round.

        Going first is an advantage — a bolt fired before a robot acts can end its turn before it
        has one — so the first seat is passed along rather than being a permanent head start.
        Derived from the round number rather than drawn, so the game stays pure and a rotation
        needs no randomizer.
        """
        if not self._players:
            return []
        start = (round_number - 1) % len(self._players)
        return [*self._players[start:], *self._players[:start]]

    def _play_turn(self, player: Player, round_number: int) -> None:
        self._emit(lambda listener: listener.player_turn_started(player))
        if not self._is_alive(player):
            # Never asked for a plan: no model call, and no near-zero turn dragging its average
            # down. The stats still go out, so a corpse keeps reporting what it achieved.
            self._emit(lambda listener: listener.player_dead(player))
            self._emit(lambda listener: listener.player_turn_ended(player, 0.0))
            self._report_stats(player)
            return
        started_at = self._clock.now()
        try:
            self._plan_and_apply(player, round_number)
        finally:
            # In `finally`, so a refused or exploding turn still reports what it cost.
            seconds = (self._clock.now() - started_at).total_seconds()
            self._emit(lambda listener: listener.player_turn_ended(player, seconds))
            self._scoreboard.record_turn(player, seconds)
            self._report_stats(player)

    def _plan_and_apply(self, player: Player, round_number: int) -> None:
        try:
            turn = player.take_turn(self._view(player, round_number))
        except Exception as error:  # A remote player fails in ways we cannot enumerate.
            self._fail_turn(player, f"{type(error).__name__}: {error}")
            return
        # Before the plan is judged, so an over-long plan still says what it was for.
        if turn.reasoning:
            self._emit(lambda listener: listener.player_reasoned(player, turn.reasoning))
        reason = self._refusal(player, turn)
        if reason is not None:
            self._fail_turn(player, reason)
            return
        for action in turn.actions:
            if action.kind is ActionKind.CAST:
                self._cast(player, action)
            else:
                self._move(player, action.direction)

    def _refusal(self, player: Player, turn: PlayerTurn) -> str | None:
        """Judge the plan whole, so nobody is given a partial turn they did not ask for."""
        if len(turn.actions) > _MAX_ACTIONS_PER_TURN:
            return f"planned {len(turn.actions)} actions, the limit is {_MAX_ACTIONS_PER_TURN}"
        for action in turn.actions:
            if action.kind is ActionKind.CAST and self._spell(player, action.spell) is None:
                return f"cast an unknown spell {action.spell!r}"
        return None

    def _view(self, player: Player, round_number: int) -> GameView:
        return GameView(
            board=self._board,
            position=self._positions[player],
            round_number=round_number,
            health=self._health[player],
            # The eliminated are shown too, at zero health: their bodies still block a fireball.
            opponents=tuple(
                Opponent(
                    name=other.get_name(),
                    position=self._positions[other],
                    health=self._health[other],
                )
                for other in self._players
                if other is not player
            ),
            spells=tuple(spell.describe() for spell in self._spells[player]),
        )

    def _report_stats(self, player: Player) -> None:
        stats = self._scoreboard.stats_for(player)
        self._emit(lambda listener: listener.player_stats(player, stats))

    def _fail_turn(self, player: Player, reason: str) -> None:
        self._emit(lambda listener: listener.turn_failed(player, reason))

    def _move(self, player: Player, direction: Direction) -> None:
        source = self._positions[player]
        dx, dy = DELTAS[direction]
        destination = Position(x=source.x + dx, y=source.y + dy)
        if not self._is_on_board(destination):
            self._emit(lambda listener: listener.move_blocked(player, source, direction))
            return
        self._positions[player] = destination
        self._emit(lambda listener: listener.player_moved(player, source, destination))

    def _cast(self, player: Player, action: Action) -> None:
        spell = self._spell(player, action.spell)
        if spell is None:  # Judged before anything was applied; here for the type only.
            return
        origin = self._positions[player]
        occupied = frozenset(
            self._positions[other]
            for other in self._players
            if other is not player and self._is_alive(other)
        )
        effect = spell.cast(origin, action.direction, self._board, occupied)
        name = action.spell
        self._emit(
            lambda listener: listener.spell_cast(
                player, name, origin, action.direction, effect.path
            )
        )
        if effect.impact is None:
            return
        for target in self._players:
            if self._is_alive(target) and self._positions[target] == effect.impact:
                self._damage(target, player, name, effect.damage, effect.impact)

    def _damage(
        self, target: Player, source: Player, spell: str, damage: int, position: Position
    ) -> None:
        health = max(0, self._health[target] - damage)
        self._health[target] = health
        self._emit(
            lambda listener: listener.player_hit(target, source, spell, damage, position)
        )
        self._emit(lambda listener: listener.player_updated(target, health))
        if health > 0:
            return
        self._scoreboard.record_death(target)
        if source is not target:  # A robot that burns itself down eliminates nobody.
            self._scoreboard.record_elimination(source)

    def _award_win(self) -> None:
        if not self._is_contested():
            return
        winner = self._winner()
        if winner is None:
            return
        self._scoreboard.record_win(winner)
        # Reported straight away, so the new tally does not wait for the next match to show up.
        self._report_stats(winner)

    def _winner(self) -> Player | None:
        """The last robot standing.

        If the rounds ran out with several still up, the healthiest one alone at the top takes
        it, and an outright tie awards nobody.
        """
        standing = [player for player in self._players if self._is_alive(player)]
        if len(standing) == 1:
            return standing[0]
        if not standing:
            return None
        best = max(self._health[player] for player in standing)
        leaders = [player for player in standing if self._health[player] == best]
        return leaders[0] if len(leaders) == 1 else None

    def _spell(self, player: Player, name: str) -> Spell | None:
        for spell in self._spells[player]:
            if spell.describe().name == name:
                return spell
        return None

    def _is_alive(self, player: Player) -> bool:
        return self._health[player] > 0

    def _is_decided(self) -> bool:
        """A contested match with one robot left, or none, has nothing more to play out."""
        if not self._is_contested():
            return False
        return sum(1 for player in self._players if self._is_alive(player)) <= 1

    def _is_contested(self) -> bool:
        """A lone robot is not in a fight, so it neither wins nor ends the match by standing."""
        return len(self._players) > 1

    def _is_on_board(self, position: Position) -> bool:
        return 0 <= position.x < self._board.width and 0 <= position.y < self._board.height

    def _emit(self, notify: Callable[[GameListener], None]) -> None:
        for listener in self._listeners:
            notify(listener)
