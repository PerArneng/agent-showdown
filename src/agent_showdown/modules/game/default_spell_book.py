from agent_showdown.interfaces.game import Spell
from agent_showdown.modules.game.fire_ball_spell import FireBallSpell


class DefaultSpellBook:
    """What every robot walks onto the board carrying."""

    def create_spells(self) -> tuple[Spell, ...]:
        # A fresh instance per robot, so a future spell may carry per-robot state such as a
        # cooldown without two contestants sharing it.
        return (FireBallSpell(),)
