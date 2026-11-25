import pytest
from pathlib import Path
from fastcombat.numbers import load_numbers, load_fight, NumbersError

GAME = Path(__file__).parent.parent / "game"

def test_the_real_files_load():
    n = load_numbers(GAME / "numbers.toml")
    f = load_fight(GAME / "fights" / "ogre_warlord.toml")
    assert n.heroes["mage"].pool == 30 and n.heroes["rogue"].regen == 3
    assert n.abilities["meteor"].cast == 2 and n.abilities["meteor"].dice == (8, 6)
    assert n.abilities["eviscerate"].loud is True
    assert len(n.abilities) == 28
    assert f.enemy_types["brute"].shielded == 5
    assert sum(1 for s in f.spawns if s.round == 6) == 6
    assert f.hero_starts["warden"] == (3, 6)

def test_an_override_changes_one_number():
    n = load_numbers(GAME / "numbers.toml", {"abilities.meteor.cost": 12})
    assert n.abilities["meteor"].cost == 12

def test_a_typo_names_the_place(tmp_path):
    text = (GAME / "numbers.toml").read_text().replace("cost = 10", "cots = 10")
    p = tmp_path / "n.toml"; p.write_text(text)
    with pytest.raises(NumbersError, match=r"abilities\.meteor\.cots"):
        load_numbers(p)

def test_a_missing_hero_number_names_the_place(tmp_path):
    text = (GAME / "numbers.toml").read_text().replace("hp = 28\n", "")
    p = tmp_path / "n.toml"; p.write_text(text)
    with pytest.raises(NumbersError, match=r"heroes\.mage\.hp"):
        load_numbers(p)

def test_an_override_for_something_that_is_not_there_fails():
    with pytest.raises(NumbersError, match=r"abilities\.meteor\.nope"):
        load_numbers(GAME / "numbers.toml", {"abilities.meteor.nope": 1})

def test_names_come_from_tables_and_left_out_numbers_take_defaults():
    n = load_numbers(GAME / "numbers.toml")
    f = load_fight(GAME / "fights" / "ogre_warlord.toml")
    assert n.abilities["meteor"].id == "meteor" and n.abilities["meteor"].alt == 0
    assert n.abilities["disrupt"].hero == "shared"
    assert n.rules["max_rounds"] == 60
    goblin = f.enemy_types["goblin"]
    assert (goblin.type, goblin.tier, goblin.hp, goblin.range) == ("goblin", "fodder", 1, 1)
    assert f.spawns[0].pos == (11, 6) and f.spawns[0].round == 0
    assert f.extra_starts[0] == (2, 7)
    assert [step.kind for step in f.boss_script] == ["blast", "heavy", "throw"]
    assert f.boss_script[0].dice == (3, 6) and f.boss_script[1].radius == 0

def test_an_override_can_set_dice_and_they_become_a_pair():
    n = load_numbers(GAME / "numbers.toml", {"abilities.meteor.dice": [9, 6]})
    assert n.abilities["meteor"].dice == (9, 6)

def test_an_override_for_a_rule_that_is_not_there_fails():
    with pytest.raises(NumbersError, match=r"rules\.max_round\b"):
        load_numbers(GAME / "numbers.toml", {"rules.max_round": 80})

@pytest.mark.parametrize("old, new, place", [
    ('resource = "mana"', 'resource = "manna"', r"heroes\.mage\.resource"),
    ('hero = "shared"', 'hero = "bard"', r"abilities\.disrupt\.hero"),
    ("dice = [8, 6]", "dice = 8", r"abilities\.meteor\.dice"),
    ("loud = true", "loud = 1", r"abilities\.eviscerate\.loud"),
])
def test_a_bad_value_in_the_numbers_file_names_the_place(tmp_path, old, new, place):
    text = (GAME / "numbers.toml").read_text()
    assert old in text
    p = tmp_path / "n.toml"; p.write_text(text.replace(old, new, 1))
    with pytest.raises(NumbersError, match=place):
        load_numbers(p)

@pytest.mark.parametrize("old, new, place", [
    ('tier = "boss"', 'tier = "bos"', r"enemy_types\.ogre\.tier"),
    ('prefers = "random"', 'prefers = "randum"', r"enemy_types\.shaman\.prefers"),
    ("poison_cards = 3", "poison_card = 3", r"enemy_types\.shaman\.poison_card"),
    ('type = "ogre"', 'type = "troll"', r"spawns\[0\]\.type"),
    ("pos = [11, 6]", "pos = [11]", r"spawns\[0\]\.pos"),
    ('kind = "heavy"', 'kind = "hevy"', r"boss_script\[1\]\.kind"),
    ("first = 5\n", "", r"boss_script\[1\]\.first"),
])
def test_a_bad_value_in_the_fight_file_names_the_place(tmp_path, old, new, place):
    text = (GAME / "fights" / "ogre_warlord.toml").read_text()
    assert old in text
    p = tmp_path / "f.toml"; p.write_text(text.replace(old, new, 1))
    with pytest.raises(NumbersError, match=place):
        load_fight(p)
