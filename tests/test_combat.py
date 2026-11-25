import pytest
from dataclasses import replace
from tests.helpers import state, enemy, GAME
from fastcombat.combat import *
from fastcombat.numbers import load_numbers, load_fight
from fastcombat.units import Announced, Cast, new_state

def test_shielded_ignores_small_hits():
    s = state(); b = enemy(s, "brute", (8, 8))
    assert damage_enemy(s, "rogue", b, 4) == 0 and b.hp == 30
    assert damage_enemy(s, "rogue", b, 5) == 5 and b.hp == 25

def test_fodder_dies_to_any_hit():
    s = state(); g = enemy(s, "goblin", (8, 8))
    damage_enemy(s, "mage", g, 1); assert g.dead

def test_damage_wakes_a_sapped_enemy():
    s = state(); w = enemy(s, "wolf", (8, 8)); add_stack(w, "sap", 4)
    damage_enemy(s, "mage", w, 1); assert "sap" not in w.stacks

def test_guarded_takes_damage_off():
    s = state(); m = s.heroes["mage"]; add_stack(m, "guarded", 1, 4)
    assert damage_hero(s, m, 6, attacker=None) == 2

def test_unbroken_stops_at_one():
    s = state(); w = s.heroes["warden"]; add_stack(w, "unbroken", 1)
    damage_hero(s, w, 999, attacker=None); assert w.hp == 1 and not w.down

def test_warden_gains_grit_when_attacked():
    s = state(); w = s.heroes["warden"]; o = enemy(s, "wolf", (4, 6))
    damage_hero(s, w, 4, attacker=o); assert w.resource == 3

def test_going_down_and_bleeding_out():
    s = state(); m = s.heroes["mage"]
    damage_hero(s, m, 99, attacker=None)
    assert m.down and m.stacks["bleeding"].cards == 3
    for _ in range(3): top_of_party_turn_cards(s)
    assert m.out

def test_any_heal_gets_you_up_with_a_wound():
    s = state(); m = s.heroes["mage"]; damage_hero(s, m, 99, attacker=None)
    heal_hero(s, "druid", m, 7)
    assert not m.down and m.hp == 7 and m.wounds == 1

def test_each_wound_shortens_the_next_bleed():
    s = state(); m = s.heroes["mage"]; m.wounds = 2
    damage_hero(s, m, 99, attacker=None); assert m.stacks["bleeding"].cards == 1
    s2 = state(); m2 = s2.heroes["mage"]; m2.wounds = 3
    damage_hero(s2, m2, 99, attacker=None); assert m2.out

def test_heal_cards_heal_one_card_a_turn():
    s = state(); w = s.heroes["warden"]; w.hp = 40; add_stack(w, "rejuvenation", 4, 4)
    top_of_party_turn_cards(s)
    assert w.hp == 44 and w.stacks["rejuvenation"].cards == 3

def test_a_second_rogue_gets_its_own_id_and_square():
    s = state(party=("rogue", "rogue"))
    assert set(s.heroes) == {"rogue", "rogue2"}
    assert s.heroes["rogue"].pos != s.heroes["rogue2"].pos and s.warden() is None


# More tests, for the details later steps rely on.

def files():
    return load_numbers(GAME / "numbers.toml"), load_fight(GAME / "fights" / "ogre_warlord.toml")

def test_a_new_fight_puts_everyone_in_place():
    n, f = files(); s = new_state(n, f, ["warden", "rogue", "druid", "mage"], seed=1)
    assert s.round == 1 and s.heroes["warden"].pos == (3, 6) and s.heroes["mage"].hp == 28
    assert s.heroes["warden"].resource == 2 and s.heroes["mage"].resource == 30
    assert s.heroes["rogue"].hidden and not s.heroes["druid"].hidden
    assert list(s.enemies) == ["ogre1", "brute1", "shaman1", "shaman2", "wolf1", "wolf2"]
    assert s.enemies["ogre1"].hp == 320 and s.enemies["wolf2"].pos == (10, 9)

def test_repeats_and_classes_with_no_start_square_take_the_extra_squares_in_order():
    n, f = files(); f = replace(f, hero_starts={"warden": (3, 6)})
    s = new_state(n, f, ["mage", "warden", "mage", "mage"], seed=1)
    assert [(h.id, h.pos) for h in s.heroes.values()] == [
        ("mage", (2, 7)), ("warden", (3, 6)), ("mage2", (1, 6)), ("mage3", (2, 6))]

def test_a_party_that_cannot_be_placed_says_why():
    n, f = files()
    with pytest.raises(ValueError, match="'wizard' is not a hero"):
        new_state(n, f, ["wizard"], seed=1)
    with pytest.raises(ValueError, match="start squares"):
        new_state(n, f, ["mage"] * 6, seed=1)

def test_the_test_state_has_no_enemies_and_ids_count_up_per_type():
    s = state(); assert s.enemies == {}
    ids = [enemy(s, t, (8, y)).id for y, t in enumerate(["wolf", "goblin", "wolf"])]
    assert ids == ["wolf1", "goblin1", "wolf2"] and s.enemies["wolf2"].hp == 16

def test_enemy_cards_come_off_one_a_turn_and_a_hit_breaks_sheep_but_not_stun():
    s = state(); w = enemy(s, "wolf", (8, 8)); add_stack(w, "taunt", 2); add_stack(w, "stun", 1)
    assert w.controlled
    tick_stacks(w); assert w.stacks == {"taunt": Stack(1)} and not w.controlled
    add_stack(w, "taunt", 3); assert w.stacks["taunt"].cards == 3      # a new stack replaces the old
    add_stack(w, "sheep", 4); add_stack(w, "stun", 1)
    damage_enemy(s, "mage", w, 1)
    assert "sheep" not in w.stacks and w.controlled                     # still stunned

def test_bulwark_only_softens_blasts_and_any_attack_gives_grit():
    s = state(); w = s.heroes["warden"]; o = enemy(s, "ogre", (4, 6)); add_stack(w, "bulwark", 1, 8)
    assert damage_hero(s, w, 10, attacker=o, blast=True) == 2 and w.resource == 2   # a blast gives none
    assert damage_hero(s, w, 10, attacker=o) == 10 and w.resource == 3
    add_stack(w, "guarded", 1, 4)
    assert damage_hero(s, w, 3, attacker=o) == 0 and w.resource == 4    # no damage, still grit

def test_the_tally_counts_only_real_damage_and_healing():
    s = state(); t = s.tally
    assert t.damage == {"warden": 0, "rogue": 0, "druid": 0, "mage": 0}
    assert t.lowest_hp["mage"] == 1.0 and t.resource_by_round["mage"] == [] and t.times_down["mage"] == 0
    w = enemy(s, "wolf", (8, 8)); g = enemy(s, "goblin", (9, 8))
    assert damage_enemy(s, "rogue", w, 10, auto=True) == 10
    assert damage_enemy(s, "rogue", w, 50) == 6 and w.dead              # only 6 HP were left
    assert damage_enemy(s, "rogue", w, 5) == 0                           # it is already dead
    assert damage_enemy(s, "mage", g, 9) == 1                            # a goblin has 1 HP
    assert t.damage["rogue"] == 16 and t.auto_damage["rogue"] == 10 and t.damage["mage"] == 1
    m = s.heroes["mage"]; damage_hero(s, m, 21, attacker=None)          # 28 down to 7
    assert t.lowest_hp["mage"] == 0.25
    assert heal_hero(s, "druid", m, 30) == 21 and t.healing["druid"] == 21 and m.hp == 28

def test_going_down_drops_everything_and_a_downed_hero_takes_no_more_hits():
    s = state(); m = s.heroes["mage"]; r = s.heroes["rogue"]
    m.cast = Cast("meteor", None, (8, 5), 1, 0, False); s.marked["mage"] = frozenset({(8, 5)})
    add_stack(m, "quicken", 2)
    assert damage_hero(s, m, 99, attacker=None) == 28
    assert m.cast is None and "mage" not in s.marked and list(m.stacks) == ["bleeding"]
    assert s.tally.times_down["mage"] == 1 and s.tally.lowest_hp["mage"] == 0
    top_of_party_turn_cards(s)
    assert damage_hero(s, m, 99, attacker=None) == 0                     # the bleeding does not restart
    assert m.stacks["bleeding"].cards == 2 and s.tally.times_down["mage"] == 1
    damage_hero(s, r, 99, attacker=None); assert not r.hidden

def test_heal_cards_are_credited_to_the_druid_and_poison_hurts():
    s = state(); w = s.heroes["warden"]; w.hp = 40
    add_stack(w, "wild_growth", 2, 4); add_stack(w, "poison", 3, 2)
    top_of_party_turn_cards(s)
    assert w.hp == 42 and s.tally.healing["druid"] == 4 and w.resource == 2   # poison is no attack
    s2 = state(party=("warden",)); w2 = s2.heroes["warden"]; w2.hp = 40
    add_stack(w2, "rejuvenation", 4, 4); top_of_party_turn_cards(s2)
    assert s2.tally.healing["warden"] == 4                               # no Druid: your own

def test_poison_that_takes_you_down_does_not_also_take_a_bleeding_card():
    s = state(); m = s.heroes["mage"]; m.hp = 2; add_stack(m, "poison", 3, 2)
    top_of_party_turn_cards(s)
    assert m.down and m.stacks == {"bleeding": Stack(3)}

def test_who_stands_where_and_which_squares_are_dangerous():
    s = state(party=("warden", "mage")); m = s.heroes["mage"]
    w = enemy(s, "wolf", (8, 8)); g = enemy(s, "goblin", (9, 9))
    damage_hero(s, m, 99, attacker=None); damage_enemy(s, "warden", g, 1)
    assert s.occupied() == {(3, 6), (1, 5), (8, 8)}                    # a downed hero still takes up a square
    assert [h.id for h in s.up_heroes()] == ["warden"] and s.living_enemies() == [w]
    for _ in range(3): top_of_party_turn_cards(s)
    assert m.out and not m.down and s.occupied() == {(3, 6), (8, 8)}
    assert heal_hero(s, "warden", m, 10) == 0 and m.out                 # nobody comes back from out
    w.announced = Announced("slam", "blast", 2, None, frozenset({(1, 1)}), (3, 6))
    g.announced = Announced("slam", "blast", 2, None, frozenset({(5, 5)}), (3, 6))   # g is dead
    s.marked["warden"] = frozenset({(2, 2)})
    assert s.danger_squares() == {(1, 1), (2, 2)}
