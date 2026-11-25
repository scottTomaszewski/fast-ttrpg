from tests.helpers import state, enemy
from fastcombat.combat import add_stack, damage_enemy, damage_hero
from fastcombat.targeting import *
from fastcombat.units import Stack

def test_an_enemy_next_to_the_warden_must_attack_the_warden():
    s = state(); w = enemy(s, "wolf", (4, 6))          # warden is at (3, 6)
    assert choose_target(s, w).id == "warden" and not can_move(s, w)

def test_a_loose_wolf_goes_for_the_back_line():
    s = state(); w = enemy(s, "wolf", (10, 3))
    assert choose_target(s, w).id == "mage" and can_move(s, w)

def test_taunt_cards_work_at_any_distance():
    s = state(); w = enemy(s, "wolf", (10, 3)); add_stack(w, "taunt", 3)
    assert choose_target(s, w).id == "warden"

def test_loud_strips_a_taunt_card_before_it_pulls():
    s = state(); w = enemy(s, "wolf", (4, 6)); add_stack(w, "taunt", 1)
    damage_enemy(s, "rogue", w, 1, loud=True)
    assert "taunt" not in w.stacks and w.pulled_by is None
    damage_enemy(s, "rogue", w, 1, loud=True)
    assert w.pulled_by == "rogue"
    assert choose_target(s, w).id == "rogue" and can_move(s, w)   # beats the weak hold

def test_intercede_sends_untaunted_attackers_to_the_warden():
    s = state(); w = enemy(s, "wolf", (10, 3)); add_stack(s.heroes["mage"], "interceded", 1)
    assert choose_target(s, w).id == "warden"

def test_a_loud_heal_pulls_everything_with_no_hold():
    s = state(); near = enemy(s, "wolf", (4, 6)); far = enemy(s, "wolf", (10, 3))
    loud_heal(s, "druid")
    assert far.pulled_by == "druid" and near.pulled_by is None

def test_downed_heroes_are_ignored():
    s = state(); w = enemy(s, "wolf", (10, 3))
    damage_hero(s, s.heroes["mage"], 99, attacker=None)
    assert choose_target(s, w).id != "mage"

def test_with_no_warden_taunted_enemies_fall_back_to_what_they_prefer():
    s = state(party=("rogue", "mage")); w = enemy(s, "wolf", (10, 3)); add_stack(w, "taunt", 3)
    assert choose_target(s, w).id == "mage"

def test_with_nobody_up_there_is_no_target():
    s = state(party=("mage",)); w = enemy(s, "wolf", (10, 3))
    damage_hero(s, s.heroes["mage"], 99, attacker=None)
    assert choose_target(s, w) is None


# More tests, for the details later steps rely on.

def test_a_loud_hit_the_shield_turns_aside_still_pulls():
    s = state(); b = enemy(s, "brute", (10, 3))                       # ignores hits below 5
    assert damage_enemy(s, "mage", b, 1, loud=True) == 0 and b.hp == 30
    assert b.pulled_by == "mage"

def test_a_loud_hit_that_kills_pulls_nothing_and_a_quiet_hit_does_nothing():
    s = state(); w = enemy(s, "wolf", (10, 3))
    damage_enemy(s, "mage", w, 99, loud=True); assert w.dead and w.pulled_by is None
    t = enemy(s, "wolf", (10, 5)); add_stack(t, "taunt", 2)
    damage_enemy(s, "mage", t, 1); damage_enemy(s, "mage", t, 1, auto=True)
    assert t.stacks["taunt"] == Stack(2) and t.pulled_by is None

def test_only_the_random_rule_rolls_a_die():
    s = state(rolls=[])                                               # any roll would fail the test
    a = enemy(s, "shaman", (10, 3)); add_stack(a, "taunt", 1)
    b = enemy(s, "shaman", (4, 6))                                     # next to the warden
    c = enemy(s, "shaman", (10, 7)); c.pulled_by = "rogue"
    assert [choose_target(s, e).id for e in (a, b, c)] == ["warden", "warden", "rogue"]
    s2 = state(party=("mage",), rolls=[]); d = enemy(s2, "shaman", (10, 3))
    damage_hero(s2, s2.heroes["mage"], 99, attacker=None)
    assert choose_target(s2, d) is None
    s3 = state(rolls=[2]); e = enemy(s3, "shaman", (10, 3))
    assert choose_target(s3, e).id == "mage"                           # druid, mage, rogue, warden
    assert s3.dice.rng.rolls == []                                     # one roll, used up

def test_a_pull_toward_a_hero_who_is_down_is_ignored():
    s = state(); loose = enemy(s, "wolf", (10, 3)); near = enemy(s, "wolf", (4, 6))
    loose.pulled_by = near.pulled_by = "rogue"
    damage_hero(s, s.heroes["rogue"], 99, attacker=None)
    assert choose_target(s, loose).id == "mage" and choose_target(s, near).id == "warden"

def test_a_pull_by_a_hero_who_is_down_does_not_break_the_hold():
    s = state(); w = enemy(s, "wolf", (4, 6)); w.pulled_by = "rogue"   # next to the warden
    assert can_move(s, w)
    damage_hero(s, s.heroes["rogue"], 99, attacker=None)
    assert not can_move(s, w) and choose_target(s, w).id == "warden"

def test_nearest_and_backline_break_ties_by_id():
    s = state(); b = enemy(s, "brute", (2, 3))                         # 2 from the rogue and the mage
    assert choose_target(s, b).id == "mage"
    w = enemy(s, "wolf", (10, 3)); damage_hero(s, s.heroes["mage"], 99, attacker=None)
    assert choose_target(s, w).id == "druid"                           # druid and rogue both have 36 HP

def test_backline_goes_for_the_warden_only_when_nobody_else_is_up():
    s = state(party=("warden", "mage")); w = enemy(s, "wolf", (10, 3))
    damage_hero(s, s.heroes["mage"], 99, attacker=None)
    assert choose_target(s, w).id == "warden"

def test_intercede_needs_a_warden_who_is_up():
    s = state(party=("rogue", "mage")); w = enemy(s, "wolf", (10, 3))
    add_stack(s.heroes["mage"], "interceded", 1)
    assert choose_target(s, w).id == "mage"

def test_a_downed_warden_holds_nothing():
    s = state(); w = enemy(s, "wolf", (4, 6))
    damage_hero(s, s.heroes["warden"], 99, attacker=None)
    assert not held(s, w) and can_move(s, w) and choose_target(s, w).id == "mage"

def test_roots_and_control_keep_an_enemy_in_place():
    s = state(); a = enemy(s, "wolf", (10, 3)); b = enemy(s, "wolf", (10, 5))
    add_stack(a, "rooted", 2); add_stack(b, "stun", 1); b.pulled_by = "mage"
    assert not can_move(s, a) and not can_move(s, b)

def test_a_loud_heal_leaves_taunted_and_dead_enemies_alone():
    s = state(); t = enemy(s, "wolf", (10, 3)); add_stack(t, "taunt", 1)
    d = enemy(s, "wolf", (10, 5)); d.dead = True
    loud_heal(s, "druid")
    assert t.pulled_by is None and d.pulled_by is None

def test_dropping_pulls_lets_go_of_one_hero_only():
    s = state(); a = enemy(s, "wolf", (10, 3)); b = enemy(s, "wolf", (10, 5)); c = enemy(s, "wolf", (10, 7))
    a.pulled_by = b.pulled_by = "rogue"; c.pulled_by = "mage"
    drop_pulls(s, "rogue")
    assert (a.pulled_by, b.pulled_by, c.pulled_by) == (None, None, "mage")
