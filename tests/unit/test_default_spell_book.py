from agent_showdown.modules.game import DefaultSpellBook


def test_every_robot_starts_with_a_fireball() -> None:
    spells = DefaultSpellBook().create_spells()

    assert [spell.describe().name for spell in spells] == ["fireball"]


def test_each_robot_gets_its_own_instances() -> None:
    book = DefaultSpellBook()

    first, second = book.create_spells(), book.create_spells()

    # A future spell may carry a cooldown, and two contestants must not share it.
    assert first[0] is not second[0]
