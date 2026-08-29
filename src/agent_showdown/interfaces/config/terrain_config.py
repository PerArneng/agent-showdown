from pydantic import BaseModel, ConfigDict


class TerrainConfig(BaseModel):
    """How much scenery a generated board carries. Every field is a plain number, so the YAML
    stays readable and a single knob can be turned without understanding the generator.

    Counts are inclusive ranges: the generator draws one number between the two.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    # False deals a bare board, which is what every match looked like before terrain existed.
    enabled: bool = True
    # Stone-wall structures. One structure is a connected run that may turn at right angles.
    min_walls: int = 1
    max_walls: int = 2
    # Cells laid in one direction before the wall turns.
    min_run: int = 2
    max_run: int = 4
    # Right-angle turns a single structure may take.
    max_turns: int = 2
    # A one-in-`gap_in` chance of leaving a doorway instead of turning. Zero means no doorways.
    gap_in: int = 4
    min_trees: int = 2
    max_trees: int = 5
    min_boulders: int = 2
    max_boulders: int = 5
    # Whether the board gets its well. There is never more than one — it is the landmark of
    # the arena, and a field of them would be neither, so this is a flag and not a range.
    well: bool = True
    # Whether a fresh layout is dealt for every round rather than once per match. Off: cover that
    # moved every round left nothing worth taking, and a match is more interesting fought over
    # ground that holds still. The machinery stays, so this is a one-line switch either way.
    redeal_each_round: bool = False
