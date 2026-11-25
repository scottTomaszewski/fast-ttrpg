from tests.helpers import state, enemy
from tests.test_warden import use
from fastcombat.combat import add_stack
from fastcombat.units import Announced

def near(s, type="wolf"):
    return enemy(s, type, (3, 5))        # adjacent to the rogue at (2, 5) and the warden at (3, 6)

def test_backstab_from_hiding_doubles_and_works_on_anyone():
    s = state(party=("rogue",), rolls=[3, 4]); w = enemy(s, "brute", (3, 5))
    assert use(s, "rogue", "backstab", "brute1")
    assert w.hp == 30 - 14 and s.heroes["rogue"].combo == 1 and not s.heroes["rogue"].hidden

def test_backstab_needs_the_enemy_to_be_busy_with_someone_else():
    s = state(party=("rogue",)); s.heroes["rogue"].hidden = False; near(s)
    assert not use(s, "rogue", "backstab", "wolf1")
    s2 = state(); s2.heroes["rogue"].hidden = False; near(s2)   # held by the warden
    assert use(s2, "rogue", "backstab", "wolf1")

def test_eviscerate_spends_every_point_and_is_loud():
    s = state(rolls=[2, 2, 2]); r = s.heroes["rogue"]; r.combo = 3; w = near(s)
    add_stack(w, "taunt", 2); use(s, "rogue", "eviscerate", "wolf1")
    assert w.hp == 10 and r.combo == 0 and w.stacks["taunt"].cards == 1

def test_kidney_shot_stuns_two_rounds_at_full_points():
    s = state(); r = s.heroes["rogue"]; r.combo = 5; w = near(s)
    use(s, "rogue", "kidney_shot", "wolf1"); assert w.stacks["stun"].cards == 2
    s2 = state(); s2.heroes["rogue"].combo = 2; w2 = near(s2)
    use(s2, "rogue", "kidney_shot", "wolf1"); assert w2.stacks["stun"].cards == 1

def test_sap_only_from_hiding_and_never_on_a_boss():
    s = state(); w = near(s); assert use(s, "rogue", "sap", "wolf1") and w.stacks["sap"].cards == 4
    assert not use(s, "rogue", "sap", "wolf1")            # no longer hidden
    s2 = state(); near(s2, "ogre"); assert not use(s2, "rogue", "sap", "ogre1")

def test_vanish_drops_the_pull_and_hides():
    s = state(); r = s.heroes["rogue"]; r.hidden = False; w = near(s); w.pulled_by = "rogue"
    use(s, "rogue", "vanish"); assert w.pulled_by is None and r.hidden

def test_a_stun_breaks_a_boss_cast_but_does_not_stun_the_boss():
    s = state(); o = near(s, "ogre")
    o.announced = Announced("skull_crusher", "heavy", s.round + 1, "warden", frozenset(), (6, 6))
    use(s, "rogue", "cheap_shot", "ogre1")
    assert o.announced is None and "stun" not in o.stacks

def test_shadowstep_lands_next_to_the_enemy():
    s = state(); enemy(s, "wolf", (9, 5)); use(s, "rogue", "shadowstep", "wolf1")
    assert s.heroes["rogue"].pos in {(8, 4), (8, 5), (8, 6)}

# --- When the Rogue's abilities say no, and the smaller rules ------------------

AIMED = ("backstab", "eviscerate", "kidney_shot", "cheap_shot", "sap", "shadowstep")

def test_the_rogues_aimed_abilities_are_only_for_enemies():
    s = state(); r = s.heroes["rogue"]; r.combo = 3   # hidden, with points: only the target is wrong
    for ability in AIMED:
        assert not use(s, "rogue", ability, "warden") and not use(s, "rogue", ability)
    assert r.resource == 10 and r.combo == 3 and r.hidden and r.pos == (2, 5)

def test_backstab_on_an_enemy_going_for_someone_else_or_taunted():
    s = state(party=("rogue", "mage")); r = s.heroes["rogue"]; r.hidden = False; w = near(s)
    w.target = "rogue"; assert not use(s, "rogue", "backstab", "wolf1")
    w.target = "mage"; assert use(s, "rogue", "backstab", "wolf1")
    s2 = state(party=("rogue",)); s2.heroes["rogue"].hidden = False; w2 = near(s2)
    add_stack(w2, "taunt", 1); assert use(s2, "rogue", "backstab", "wolf1")

def test_backstab_not_from_hiding_hits_once_and_combo_points_stop_at_the_most():
    s = state(rolls=[3, 4]); r = s.heroes["rogue"]; r.hidden = False; r.combo = 5; w = near(s)
    assert use(s, "rogue", "backstab", "wolf1") and w.hp == 16 - 7 and r.combo == 5

def test_eviscerate_and_kidney_shot_need_a_combo_point():
    s = state(); near(s)
    assert not use(s, "rogue", "eviscerate", "wolf1") and not use(s, "rogue", "kidney_shot", "wolf1")
    assert s.heroes["rogue"].resource == 10

def test_kidney_shot_is_not_for_a_boss():
    s = state(); r = s.heroes["rogue"]; r.combo = 5; near(s, "ogre")
    assert not use(s, "rogue", "kidney_shot", "ogre1") and r.combo == 5

def test_cheap_shot_stuns_and_breaks_the_cast_of_an_enemy_that_is_not_a_boss():
    s = state(); w = near(s, "shaman")
    w.announced = Announced("mend", "mend", s.round + 1, "ogre1", frozenset(), (0, 0), heal=25)
    assert use(s, "rogue", "cheap_shot", "shaman1")
    assert w.stacks["stun"].cards == 1 and w.announced is None

def test_only_a_stun_clears_an_announced_cast():
    s = state(); w = near(s, "shaman")
    w.announced = Announced("mend", "mend", s.round + 1, "ogre1", frozenset(), (0, 0), heal=25)
    assert use(s, "rogue", "sap", "shaman1") and w.announced is not None

def test_shadowstep_needs_a_free_square_next_to_the_enemy():
    s = state(); w = enemy(s, "wolf", (0, 0))           # in the corner, with wolves all round
    for square in ((1, 0), (0, 1), (1, 1)):
        enemy(s, "wolf", square)
    assert not use(s, "rogue", "shadowstep", "wolf1")
    assert s.heroes["rogue"].pos == (2, 5) and s.heroes["rogue"].resource == 10 and w.pos == (0, 0)

def test_shadowstep_from_next_to_the_enemy_stays_put():
    s = state(); near(s)                                # the wolf at (3, 5) is next to the rogue
    assert use(s, "rogue", "shadowstep", "wolf1") and s.heroes["rogue"].pos == (2, 5)

def test_vanish_lets_go_only_of_the_rogues_own_pulls():
    s = state(); w = near(s); w.pulled_by = "mage"
    assert use(s, "rogue", "vanish") and w.pulled_by == "mage"
