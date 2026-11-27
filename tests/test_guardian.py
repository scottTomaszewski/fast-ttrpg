from tests.helpers import state, enemy
from fastcombat.abilities import Action, use_ability
from fastcombat.targeting import choose_target
from fastcombat.combat import add_stack, damage_hero
from fastcombat.grid import adjacent

def use(s, hero, ability, target=None, pos=None):
    return use_ability(s, s.heroes[hero], Action("ability", ability, target, pos))

def test_taunt_puts_three_taunt_cards_on_and_costs_grit():
    s = state(); w = enemy(s, "wolf", (8, 6))
    assert use(s, "guardian", "taunt", "wolf1")
    assert w.stacks["taunt"].cards == 3 and s.heroes["guardian"].resource == 1

def test_challenging_shout_taunts_everything_near_for_one_turn():
    s = state(); s.heroes["guardian"].resource = 10
    a = enemy(s, "wolf", (5, 6)); b = enemy(s, "wolf", (6, 8)); far = enemy(s, "wolf", (12, 6))
    use(s, "guardian", "challenging_shout")
    assert a.stacks["taunt"].cards == 1 and b.stacks["taunt"].cards == 1 and "taunt" not in far.stacks

def test_grip_drags_a_loose_enemy_into_the_ring():
    s = state(); w = enemy(s, "wolf", (8, 6))
    assert use(s, "guardian", "grip", "wolf1")
    assert adjacent(w.pos, s.heroes["guardian"].pos) and choose_target(s, w).id == "guardian"

def test_grip_cannot_move_the_boss():
    s = state(); enemy(s, "ogre", (8, 6))
    assert not use(s, "guardian", "grip", "ogre1")

def test_intercede_leaps_guards_and_takes_the_attacker():
    s = state(); m = s.heroes["mage"]; w = enemy(s, "wolf", (1, 4))
    assert use(s, "guardian", "intercede", "mage")
    assert adjacent(s.heroes["guardian"].pos, m.pos)
    assert damage_hero(s, m, 6, attacker=None) == 2
    assert choose_target(s, w).id == "guardian"

def test_shield_plant_covers_allies_behind_the_shield_against_a_blast():
    s = state(); s.heroes["guardian"].resource = 10
    s.heroes["rogue"].pos = (2, 6)                      # directly behind, blast from the east
    use(s, "guardian", "shield_plant", pos=(6, 6))
    assert damage_hero(s, s.heroes["rogue"], 12, attacker=None, blast=True) == 4
    assert damage_hero(s, s.heroes["rogue"], 12, attacker=None, blast=False) == 12

def test_last_stand_keeps_the_guardian_on_one_hp():
    s = state(); w = s.heroes["guardian"]; w.resource = 10
    use(s, "guardian", "last_stand"); damage_hero(s, w, 500, attacker=None)
    assert w.hp == 1 and w.up

# --- When the Guardian's abilities say no, and where the Guardian lands ----------

def test_taunt_and_grip_are_only_for_enemies():
    s = state()
    assert not use(s, "guardian", "taunt", "rogue") and not use(s, "guardian", "taunt")
    assert not use(s, "guardian", "grip", "rogue") and not use(s, "guardian", "grip")
    assert s.heroes["guardian"].resource == 2 and s.heroes["rogue"].pos == (2, 5)

def test_grip_needs_a_free_square_next_to_the_guardian():
    s = state(); s.heroes["guardian"].pos = (0, 0)        # in the corner, with the party all round
    for name, square in (("rogue", (1, 0)), ("druid", (0, 1)), ("mage", (1, 1))):
        s.heroes[name].pos = square
    w = enemy(s, "wolf", (5, 5))
    assert not use(s, "guardian", "grip", "wolf1") and w.pos == (5, 5)

def test_grip_leaves_an_enemy_already_next_to_the_guardian_where_it_is():
    s = state(); w = enemy(s, "wolf", (4, 6))
    assert use(s, "guardian", "grip", "wolf1") and w.pos == (4, 6)

def test_intercede_is_only_for_an_ally_who_is_up():
    s = state(); r = s.heroes["rogue"]; enemy(s, "wolf", (5, 6))
    assert not use(s, "guardian", "intercede", "guardian")
    assert not use(s, "guardian", "intercede", "wolf1")
    r.down = True
    assert not use(s, "guardian", "intercede", "rogue")
    r.down = False; r.out = True
    assert not use(s, "guardian", "intercede", "rogue")
    assert s.heroes["guardian"].resource == 2 and s.heroes["guardian"].pos == (3, 6)

def test_intercede_from_next_to_the_ally_stays_put():
    s = state()                                         # the Guardian at (3, 6) is next to the rogue at (2, 5)
    assert use(s, "guardian", "intercede", "rogue")
    assert s.heroes["guardian"].pos == (3, 6) and "guarded" in s.heroes["rogue"].stacks

def test_intercede_with_no_free_square_by_the_ally_still_guards():
    s = state(); m = s.heroes["mage"]; m.pos = (0, 0)  # in the corner, with wolves all round
    for square in ((1, 0), (0, 1), (1, 1)):
        enemy(s, "wolf", square)
    assert use(s, "guardian", "intercede", "mage")
    assert s.heroes["guardian"].pos == (3, 6) and "guarded" in m.stacks and "interceded" in m.stacks

def test_shield_plant_needs_the_square_the_blast_comes_from():
    s = state(); s.heroes["guardian"].resource = 10
    assert not use(s, "guardian", "shield_plant") and s.heroes["guardian"].resource == 10

def test_shield_plant_covers_the_guardian_but_not_an_ally_in_front():
    s = state(); s.heroes["guardian"].resource = 10
    s.heroes["rogue"].pos = (4, 6)                      # between the Guardian and the blast
    use(s, "guardian", "shield_plant", pos=(6, 6))
    assert "shield_plant" in s.heroes["guardian"].stacks and "shield_plant" not in s.heroes["rogue"].stacks

# --- A new taunt never shortens an old one ------------------------------------

def test_challenging_shout_leaves_a_longer_taunt_as_it_is():
    s = state(); s.heroes["guardian"].resource = 10; w = enemy(s, "wolf", (5, 6))
    add_stack(w, "taunt", 3)
    assert use(s, "guardian", "challenging_shout") and w.stacks["taunt"].cards == 3

def test_the_taunt_ability_makes_a_shorter_taunt_as_long_as_its_own():
    s = state(); w = enemy(s, "wolf", (8, 6)); add_stack(w, "taunt", 1)
    assert use(s, "guardian", "taunt", "wolf1") and w.stacks["taunt"].cards == 3
