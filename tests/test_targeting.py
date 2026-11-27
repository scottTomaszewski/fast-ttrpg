from tests.helpers import state, enemy
from fastcombat.combat import add_stack, damage_enemy, damage_hero
from fastcombat.targeting import *
from fastcombat.units import Stack

def test_an_enemy_next_to_the_guardian_must_attack_the_guardian():
    s = state(); w = enemy(s, "wolf", (4, 6))          # guardian is at (3, 6)
    assert choose_target(s, w).id == "guardian" and not can_move(s, w)

def test_a_loose_wolf_goes_for_the_back_line():
    s = state(); w = enemy(s, "wolf", (10, 3))
    assert choose_target(s, w).id == "mage" and can_move(s, w)

def test_taunt_cards_work_at_any_distance():
    s = state(); w = enemy(s, "wolf", (10, 3)); add_stack(w, "taunt", 3)
    assert choose_target(s, w).id == "guardian"

def test_loud_strips_a_taunt_card_before_it_pulls():
    s = state(); s.heroes["rogue"].hidden = False                      # a hidden rogue's pull counts for nothing
    w = enemy(s, "wolf", (4, 6)); add_stack(w, "taunt", 1)
    damage_enemy(s, "rogue", w, 1, loud=True)
    assert "taunt" not in w.stacks and w.pulled_by is None
    damage_enemy(s, "rogue", w, 1, loud=True)
    assert w.pulled_by == "rogue"
    assert choose_target(s, w).id == "rogue" and can_move(s, w)   # beats the weak hold

def test_intercede_sends_untaunted_attackers_to_the_guardian():
    s = state(); w = enemy(s, "wolf", (10, 3)); add_stack(s.heroes["mage"], "interceded", 1)
    assert choose_target(s, w).id == "guardian"

def test_a_loud_heal_pulls_everything_with_no_hold():
    s = state(); near = enemy(s, "wolf", (4, 6)); far = enemy(s, "wolf", (10, 3))
    loud_heal(s, "druid")
    assert far.pulled_by == "druid" and near.pulled_by is None

def test_downed_heroes_are_ignored():
    s = state(); w = enemy(s, "wolf", (10, 3))
    damage_hero(s, s.heroes["mage"], 99, attacker=None)
    assert choose_target(s, w).id != "mage"

def test_with_no_guardian_taunted_enemies_fall_back_to_what_they_prefer():
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
    s = state(rolls=[]); s.heroes["rogue"].hidden = False             # any roll would fail the test
    a = enemy(s, "shaman", (10, 3)); add_stack(a, "taunt", 1)
    b = enemy(s, "shaman", (4, 6))                                     # next to the guardian
    c = enemy(s, "shaman", (10, 7)); c.pulled_by = "rogue"
    assert [choose_target(s, e).id for e in (a, b, c)] == ["guardian", "guardian", "rogue"]
    s2 = state(party=("mage",), rolls=[]); d = enemy(s2, "shaman", (10, 3))
    damage_hero(s2, s2.heroes["mage"], 99, attacker=None)
    assert choose_target(s2, d) is None
    s3 = state(rolls=[3]); e = enemy(s3, "shaman", (10, 3))
    assert choose_target(s3, e).id == "mage"                           # druid, guardian, mage (the rogue is hidden)
    assert s3.dice.rng.rolls == []                                     # one roll, used up

def test_a_pull_toward_a_hero_who_is_down_is_ignored():
    s = state(); loose = enemy(s, "wolf", (10, 3)); near = enemy(s, "wolf", (4, 6))
    loose.pulled_by = near.pulled_by = "rogue"
    damage_hero(s, s.heroes["rogue"], 99, attacker=None)
    assert choose_target(s, loose).id == "mage" and choose_target(s, near).id == "guardian"

def test_a_pull_by_a_hero_who_is_down_does_not_break_the_hold():
    s = state(); s.heroes["rogue"].hidden = False
    w = enemy(s, "wolf", (4, 6)); w.pulled_by = "rogue"                # next to the guardian
    assert can_move(s, w)
    damage_hero(s, s.heroes["rogue"], 99, attacker=None)
    assert not can_move(s, w) and choose_target(s, w).id == "guardian"

def test_nearest_and_backline_break_ties_by_id():
    s = state(); b = enemy(s, "brute", (2, 3))                         # 2 from the rogue and the mage
    assert choose_target(s, b).id == "mage"
    w = enemy(s, "wolf", (10, 3)); damage_hero(s, s.heroes["mage"], 99, attacker=None)
    assert choose_target(s, w).id == "druid"                           # druid and rogue both have 36 HP

def test_backline_goes_for_the_guardian_only_when_nobody_else_is_up():
    s = state(party=("guardian", "mage")); w = enemy(s, "wolf", (10, 3))
    damage_hero(s, s.heroes["mage"], 99, attacker=None)
    assert choose_target(s, w).id == "guardian"

def test_intercede_needs_a_guardian_who_is_up():
    s = state(party=("rogue", "mage")); w = enemy(s, "wolf", (10, 3))
    add_stack(s.heroes["mage"], "interceded", 1)
    assert choose_target(s, w).id == "mage"

def test_a_downed_guardian_holds_nothing():
    s = state(); w = enemy(s, "wolf", (4, 6))
    damage_hero(s, s.heroes["guardian"], 99, attacker=None)
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


# --- A hidden hero is never picked (the controller's ruling) ------------------
# The Rogue starts every fight hidden.

def test_a_hidden_hero_is_passed_over_by_what_an_enemy_prefers():
    s = state(); b = enemy(s, "brute", (3, 4))                         # next to the rogue at (2, 5)
    assert s.heroes["rogue"].hidden and choose_target(s, b).id == "guardian"    # 2 away, like the mage; "guardian" comes first
    s.heroes["rogue"].hidden = False
    assert choose_target(s, b).id == "rogue"
    w = enemy(s, "wolf", (10, 3)); s.heroes["mage"].hidden = True       # the back line's weakest is hidden
    assert choose_target(s, w).id == "druid"

def test_the_random_pick_counts_only_the_heroes_who_are_seen():
    s = state(rolls=[3]); sh = enemy(s, "shaman", (10, 3))
    assert choose_target(s, sh).id == "mage"                            # druid, guardian, mage: 3 of 3
    s2 = state(rolls=[4]); s2.heroes["rogue"].hidden = False; sh2 = enemy(s2, "shaman", (10, 3))
    assert choose_target(s2, sh2).id == "rogue"                         # druid, guardian, mage, rogue: 4 of 4

def test_a_pull_by_a_hidden_hero_counts_as_no_pull():
    s = state(); loose = enemy(s, "wolf", (10, 3)); near = enemy(s, "wolf", (4, 6))
    loose.pulled_by = near.pulled_by = "rogue"                          # the rogue is hidden
    assert choose_target(s, loose).id == "mage"
    assert choose_target(s, near).id == "guardian" and not can_move(s, near)

def test_an_enemy_with_only_hidden_heroes_to_go_for_has_no_target():
    s = state(party=("rogue",)); w = enemy(s, "wolf", (3, 5))
    assert choose_target(s, w) is None

def test_a_hidden_guardian_is_never_the_one_an_intercede_hands_on_to():
    # A Guardian cannot hide in the game today; this pins the rule for when one can.
    s = state(); w = enemy(s, "wolf", (10, 3)); add_stack(s.heroes["mage"], "interceded", 1)
    assert choose_target(s, w).id == "guardian"
    s.heroes["guardian"].hidden = True
    assert choose_target(s, w).id == "mage"


# --- Bosses ignore the hold: only Taunt cards keep a boss on the Guardian -------
# The owner's decision, so the Guardian has to taunt the boss.

def test_a_boss_next_to_the_guardian_is_not_held():
    s = state(); s.heroes["druid"].pos = (5, 5)
    o = enemy(s, "ogre", (4, 6))                       # next to the guardian at (3, 6) and the druid
    assert not held(s, o) and can_move(s, o)
    assert choose_target(s, o).id == "druid"           # nearest: both 1 away, the druid's id comes first
    w = enemy(s, "wolf", (4, 7))                       # a wolf there is held, as before
    assert held(s, w) and not can_move(s, w) and choose_target(s, w).id == "guardian"

def test_taunt_cards_still_hold_a_boss():
    s = state(); s.heroes["druid"].pos = (5, 5)        # without the cards the ogre would pick the druid
    o = enemy(s, "ogre", (4, 6)); add_stack(o, "taunt", 1)
    assert choose_target(s, o).id == "guardian"

def test_a_loud_heal_pulls_a_boss_next_to_the_guardian_with_no_taunt_cards():
    s = state(); o = enemy(s, "ogre", (4, 6)); w = enemy(s, "wolf", (4, 7))   # both next to the guardian
    loud_heal(s, "druid")
    assert o.pulled_by == "druid" and w.pulled_by is None
    t = state(); o2 = enemy(t, "ogre", (4, 6)); add_stack(o2, "taunt", 2)
    loud_heal(t, "druid")
    assert o2.pulled_by is None

def test_a_loud_hit_takes_boss_loud_cards_off_a_boss_and_one_off_anything_else():
    s = state(); assert s.numbers.rules["boss_loud_cards"] == 1
    o = enemy(s, "ogre", (10, 3)); w = enemy(s, "wolf", (10, 7))
    add_stack(o, "taunt", 3); add_stack(w, "taunt", 3)
    damage_enemy(s, "mage", o, 1, loud=True); damage_enemy(s, "mage", w, 1, loud=True)
    assert o.stacks["taunt"].cards == 2 and w.stacks["taunt"].cards == 2
    s.numbers.rules["boss_loud_cards"] = 2
    damage_enemy(s, "mage", o, 1, loud=True); damage_enemy(s, "mage", w, 1, loud=True)
    assert "taunt" not in o.stacks and o.pulled_by is None          # 2 of 2 cards gone, no pull
    assert w.stacks["taunt"].cards == 1                              # not a boss: always 1
    damage_enemy(s, "mage", o, 1, loud=True)
    assert o.pulled_by == "mage"                                     # no cards left now: it pulls

def test_a_loud_hit_on_a_boss_with_fewer_cards_takes_what_is_there_and_does_not_pull():
    s = state(); s.numbers.rules["boss_loud_cards"] = 2
    o = enemy(s, "ogre", (10, 3)); add_stack(o, "taunt", 1)
    damage_enemy(s, "mage", o, 1, loud=True)
    assert "taunt" not in o.stacks and o.pulled_by is None
