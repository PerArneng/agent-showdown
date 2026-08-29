from typing import Literal

from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.game.player_stats import PlayerStats


class PlayerStatsEvent(BaseModel):
    """A player's running totals, reported after each of its turns ends."""

    model_config = ConfigDict(frozen=True)

    type: Literal["player_stats"] = "player_stats"
    player: str
    stats: PlayerStats
