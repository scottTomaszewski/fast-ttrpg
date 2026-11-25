import re
import pytest
from dataclasses import FrozenInstanceError, fields, replace
from tests.helpers import GAME, REAL_GAME
from fastcombat.numbers import load_numbers, load_fight, NumbersError

def without(text, table, key):
    """The file's text with the `key = ...` line taken out of one [table]."""
    lines = text.splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if line.startswith(f"[{table}]"))
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("[")), len(lines))
    found = [i for i in range(start + 1, end) if lines[i].startswith(f"{key} =")]
    assert len(found) == 1, f"[{table}] should have one {key} line"
    del lines[found[0]]
    return "".join(lines)

def test_the_frozen_files_load():
    n = load_numbers(GAME / "numbers.toml")
    f = load_fight(GAME / "fights" / "ogre_warlord.toml")
    assert n.heroes["mage"].pool == 30 and n.heroes["rogue"].regen == 3
    assert n.abilities["meteor"].cast == 2 and n.abilities["meteor"].dice == (8, 6)
    assert n.abilities["eviscerate"].loud is True
    assert len(n.abilities) == 28
    assert f.enemy_types["brute"].shielded == 5
    assert sum(1 for s in f.spawns if s.round == 6) == 6
    assert f.hero_starts["warden"] == (3, 6)

def test_the_real_game_files_load():
    # Only that they load: the real numbers are tuned, so no number is checked.
    n = load_numbers(REAL_GAME / "numbers.toml")
    f = load_fight(REAL_GAME / "fights" / "ogre_warlord.toml")
    assert {"warden", "rogue", "druid", "mage"} <= set(n.heroes)
    assert len(f.spawns) >= 1

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
    assert (goblin.type, goblin.tier, goblin.dice, goblin.shielded) == ("goblin", "fodder", (0, 0), 0)
    assert f.spawns[0].pos == (11, 6) and f.spawns[0].round == 0
    assert f.extra_starts[0] == (2, 7)
    assert [step.kind for step in f.boss_script] == ["blast", "heavy", "throw"]
    assert f.boss_script[0].dice == (3, 6) and f.boss_script[1].radius == 0

def test_every_enemy_states_its_hp_move_and_range():
    f = load_fight(GAME / "fights" / "ogre_warlord.toml")
    got = {name: (e.hp, e.move, e.range) for name, e in f.enemy_types.items()}
    assert got == {
        "ogre": (320, 4, 1), "shaman": (24, 4, 8), "wolf": (16, 7, 1),
        "brute": (30, 4, 1), "goblin": (1, 5, 1),
    }

@pytest.mark.parametrize("key", ["hp", "move", "range"])
@pytest.mark.parametrize("name", ["ogre", "shaman", "wolf", "brute", "goblin"])
def test_an_enemy_without_hp_move_or_range_names_the_place(tmp_path, name, key):
    text = (GAME / "fights" / "ogre_warlord.toml").read_text()
    p = tmp_path / "f.toml"; p.write_text(without(text, f"enemy_types.{name}", key))
    with pytest.raises(NumbersError, match=rf"enemy_types\.{name}\.{key}: missing"):
        load_fight(p)

def test_an_ability_with_no_range_needs_no_reach():
    n = load_numbers(GAME / "numbers.toml")
    def reach(r): return {name for name, a in n.abilities.items() if a.range == r}
    assert reach(0) == {"war_cry", "bulwark", "unbroken", "vanish", "shadowmeld", "frost_ring", "quicken"}
    assert reach(1) == {"backstab", "eviscerate", "kidney_shot", "cheap_shot", "sap", "disrupt"}

@pytest.mark.parametrize("load", [load_numbers, load_fight])
def test_a_file_that_is_not_toml_names_the_file(tmp_path, load):
    p = tmp_path / "broken.toml"; p.write_text("[rules\nhero_move = 6\n")
    with pytest.raises(NumbersError, match=re.escape(str(p))):
        load(p)

def test_the_records_cannot_be_changed_by_mistake():
    n = load_numbers(GAME / "numbers.toml")
    f = load_fight(GAME / "fights" / "ogre_warlord.toml")
    records = [n, n.heroes["mage"], n.abilities["meteor"],
               f, f.enemy_types["ogre"], f.spawns[0], f.boss_script[0]]
    for record in records:
        with pytest.raises(FrozenInstanceError):
            setattr(record, fields(record)[0].name, None)

def test_replace_makes_a_changed_copy_of_an_enemy_and_a_fight():
    f = load_fight(GAME / "fights" / "ogre_warlord.toml")
    brute = f.enemy_types["brute"]
    tough = replace(brute, hp=10**6, damage=0)
    assert (tough.hp, tough.damage, tough.shielded, tough.move) == (10**6, 0, 5, 4)
    small = replace(f, hero_starts={"warden": (3, 6)}, enemy_types={**f.enemy_types, "brute": tough})
    assert small.hero_starts == {"warden": (3, 6)} and small.enemy_types["brute"].hp == 10**6
    assert small.spawns == f.spawns and small.name == f.name
    assert brute.hp == 30 and f.enemy_types["brute"].hp == 30   # the old ones are untouched

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

@pytest.mark.parametrize("old, new, place", [
    ("first = 3\nevery = 4", "first = 3\nevery = 0", r"boss_script\[0\]\.every"),
    ("first = 5\nevery = 5", "first = 5\nevery = -1", r"boss_script\[1\]\.every"),
    ("first = 2\nevery = 2", "first = 0\nevery = 2", r"boss_script\[2\]\.first"),
    ("cast_every = 4", "cast_every = -1", r"enemy_types\.shaman\.cast_every"),
])
def test_a_repeat_that_can_never_come_round_names_the_place(tmp_path, old, new, place):
    text = (GAME / "fights" / "ogre_warlord.toml").read_text()
    assert text.count(old) == 1
    p = tmp_path / "f.toml"; p.write_text(text.replace(old, new))
    with pytest.raises(NumbersError, match=place):
        load_fight(p)

def test_a_cast_every_of_zero_means_the_enemy_never_casts(tmp_path):
    text = (GAME / "fights" / "ogre_warlord.toml").read_text()
    p = tmp_path / "f.toml"; p.write_text(text.replace("cast_every = 4", "cast_every = 0"))
    assert load_fight(p).enemy_types["shaman"].cast_every == 0
