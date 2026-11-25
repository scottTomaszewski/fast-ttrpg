from dataclasses import replace
from tests.helpers import state, enemy
from tests.test_warden import use
from fastcombat.casting import land_casts, continue_cast
from fastcombat.combat import add_stack, top_of_party_turn_cards
from fastcombat.targeting import can_move
from fastcombat.units import Announced
from fastcombat.casting import drop_cast

def test_each_volley_hit_is_loud():
    s = state(rolls=[1, 1, 1, 1, 1, 1]); m = s.heroes["mage"]; o = enemy(s, "ogre", (8, 5))
    add_stack(o, "taunt", 2); use(s, "mage", "arcane_volley", "ogre1")
    continue_cast(s, m); continue_cast(s, m)
    assert o.hp == 320 - 6 and "taunt" not in o.stacks and o.pulled_by == "mage" and m.resource == 24

def test_meteor_marks_its_area_and_hits_friend_and_foe():
    s = state(rolls=[1] * 8); m = s.heroes["mage"]
    w = enemy(s, "wolf", (8, 5)); g = enemy(s, "goblin", (9, 6)); s.heroes["rogue"].pos = (8, 6)
    use(s, "mage", "meteor", pos=(8, 5)); assert (9, 6) in s.marked["mage"]
    continue_cast(s, m); land_casts(s)
    assert w.hp == 8 and g.dead and s.heroes["rogue"].hp == 28 and m.resource == 20 and "mage" not in s.marked

def test_frost_ring_roots_adjacent_enemies():
    s = state(); w = enemy(s, "wolf", (2, 4)); w.pulled_by = "mage"
    use(s, "mage", "frost_ring"); assert w.stacks["rooted"].cards == 2 and not can_move(s, w)

def test_polymorph_is_one_sheep_at_a_time_and_never_the_boss():
    s = state(); a = enemy(s, "wolf", (8, 5)); b = enemy(s, "wolf", (8, 7)); enemy(s, "ogre", (9, 6))
    use(s, "mage", "polymorph", "wolf1"); land_casts(s); assert a.stacks["sheep"].cards == 4
    use(s, "mage", "polymorph", "wolf2"); land_casts(s)
    assert "sheep" in b.stacks and "sheep" not in a.stacks
    assert not use(s, "mage", "polymorph", "ogre1")

def test_quicken_goes_on_the_whole_party():
    s = state(); use(s, "mage", "quicken")
    assert all(h.stacks["quicken"].cards == 2 for h in s.heroes.values())

def test_disrupt_breaks_a_cast_at_range_for_the_mage_only_then_cools_down():
    s = state(); sh = enemy(s, "shaman", (9, 5))
    sh.announced = Announced("mend", "mend", s.round + 1, None, frozenset(), (0, 0), heal=25)
    assert not use(s, "rogue", "disrupt", "shaman1")      # too far for melee
    assert use(s, "mage", "disrupt", "shaman1") and sh.announced is None
    sh.announced = Announced("mend", "mend", s.round + 1, None, frozenset(), (0, 0), heal=25)
    assert not use(s, "mage", "disrupt", "shaman1")
    for _ in range(3): top_of_party_turn_cards(s)
    assert use(s, "mage", "disrupt", "shaman1")

def test_blink_will_not_land_on_someone():
    s = state(); assert not use(s, "mage", "blink", pos=s.heroes["rogue"].pos)
    assert use(s, "mage", "blink", pos=(1, 1)) and s.heroes["mage"].pos == (1, 1)

# --- When the Mage's abilities say no, and the smaller rules ------------------

AIMED = ("arcane_volley", "firebolt", "polymorph", "disrupt")

def mend():
    """A heal the shaman has announced, to land next round."""
    return Announced("mend", "mend", 2, "ogre1", frozenset(), (0, 0), heal=25)

def test_the_mages_aimed_abilities_are_only_for_enemies():
    s = state(); m = s.heroes["mage"]
    for ability in AIMED:
        assert not use(s, "mage", ability, "warden") and not use(s, "mage", ability)
    assert m.resource == 30 and m.cast is None and "cd:disrupt" not in m.stacks

def test_firebolt_lands_next_turn_and_is_not_loud():
    s = state(rolls=[1, 2, 3, 4]); m = s.heroes["mage"]; w = enemy(s, "wolf", (8, 5))
    assert use(s, "mage", "firebolt", "wolf1") and w.hp == 16 and m.resource == 30
    land_casts(s)
    assert w.hp == 16 - 10 and m.resource == 26 and w.pulled_by is None and m.cast is None

def test_meteor_needs_a_centre():
    s = state(); m = s.heroes["mage"]
    assert not use(s, "mage", "meteor") and m.cast is None and "mage" not in s.marked

def test_meteor_needs_a_centre_on_the_map():
    s = state(); m = s.heroes["mage"]                   # at (1, 5); both squares are in reach
    assert not use(s, "mage", "meteor", pos=(-1, 5)) and not use(s, "mage", "meteor", pos=(1, -2))
    assert m.cast is None and "mage" not in s.marked
    assert use(s, "mage", "meteor", pos=(0, 5))

def test_meteor_is_a_blast_and_spares_a_hero_who_is_down():
    s = state(rolls=[1] * 8); m = s.heroes["mage"]; r = s.heroes["rogue"]; d = s.heroes["druid"]
    r.pos = (8, 6); add_stack(r, "bulwark", 1, 8)       # Bulwark only softens a blast
    d.pos = (9, 5); d.hp = 0; d.down = True; add_stack(d, "bleeding", 3)
    use(s, "mage", "meteor", pos=(8, 5)); continue_cast(s, m); land_casts(s)
    assert r.hp == 36 and d.down and d.stacks["bleeding"].cards == 3

def test_meteor_hits_out_to_the_edge_of_its_marked_area_and_no_farther():
    s = state(rolls=[1] * 8); m = s.heroes["mage"]
    edge = enemy(s, "wolf", (10, 7)); past = enemy(s, "wolf", (11, 5))   # 2 and 3 from the centre
    use(s, "mage", "meteor", pos=(8, 5))
    assert edge.pos in s.marked["mage"] and past.pos not in s.marked["mage"]
    continue_cast(s, m); land_casts(s)
    assert edge.hp == 8 and past.hp == 16

def test_meteor_is_loud_only_when_the_file_says_so():
    for loud in (False, True):
        s = state(rolls=[1] * 8); m = s.heroes["mage"]; w = enemy(s, "wolf", (8, 5))
        s.numbers.abilities["meteor"] = replace(s.numbers.abilities["meteor"], loud=loud)
        use(s, "mage", "meteor", pos=(8, 5)); continue_cast(s, m); land_casts(s)
        assert w.hp == 8 and w.pulled_by == ("mage" if loud else None)

def test_firebolt_and_meteor_add_their_bonus_once():
    for name, target, pos, hp in (("firebolt", "wolf1", None, 16 - 4 - 3), ("meteor", None, (8, 5), 16 - 8 - 3)):
        s = state(rolls=[1] * 8); m = s.heroes["mage"]; w = enemy(s, "wolf", (8, 5))
        s.numbers.abilities[name] = replace(s.numbers.abilities[name], bonus=3)
        use(s, "mage", name, target, pos); continue_cast(s, m); land_casts(s)
        assert w.hp == hp

def test_meteor_on_the_mages_own_square_hits_the_mage_too():
    s = state(party=("mage",), rolls=[1] * 8); m = s.heroes["mage"]
    use(s, "mage", "meteor", pos=m.pos); continue_cast(s, m); land_casts(s)
    assert m.hp == 28 - 8

def test_frost_ring_roots_a_boss_too_but_nothing_two_squares_off_or_dead():
    s = state(); o = enemy(s, "ogre", (2, 6)); far = enemy(s, "wolf", (3, 5))
    dead = enemy(s, "wolf", (0, 4)); dead.dead = True
    assert use(s, "mage", "frost_ring")
    assert o.stacks["rooted"].cards == 2 and "rooted" not in far.stacks and "rooted" not in dead.stacks

def test_blink_stays_on_the_map_free_of_enemies_and_within_reach():
    s = state(); m = s.heroes["mage"]; enemy(s, "wolf", (4, 5))   # the Mage is at (1, 5); the reach is 6
    for square in ((-1, 5), (4, 5), (8, 5)):
        assert not use(s, "mage", "blink", pos=square)
    assert not use(s, "mage", "blink")
    assert m.pos == (1, 5) and m.resource == 30
    assert use(s, "mage", "blink", pos=(7, 5)) and m.pos == (7, 5) and m.resource == 28

def test_quicken_skips_a_hero_who_is_down_or_out():
    s = state(); s.heroes["rogue"].down = True; s.heroes["druid"].out = True
    assert use(s, "mage", "quicken")
    assert "quicken" in s.heroes["mage"].stacks and "quicken" in s.heroes["warden"].stacks
    assert "quicken" not in s.heroes["rogue"].stacks and "quicken" not in s.heroes["druid"].stacks

def test_a_second_polymorph_only_frees_the_first_sheep_when_it_lands():
    s = state(); m = s.heroes["mage"]; a = enemy(s, "wolf", (8, 5)); enemy(s, "wolf", (8, 7))
    use(s, "mage", "polymorph", "wolf1"); land_casts(s)
    use(s, "mage", "polymorph", "wolf2"); assert "sheep" in a.stacks
    drop_cast(s, m)                                     # the second cast is broken before it lands
    land_casts(s); assert "sheep" in a.stacks

def test_disrupt_needs_an_announced_cast():
    s = state(); m = s.heroes["mage"]; enemy(s, "shaman", (9, 5))
    assert not use(s, "mage", "disrupt", "shaman1") and "cd:disrupt" not in m.stacks

def test_any_hero_can_disrupt_next_to_them_and_a_boss_cast_breaks_too():
    s = state(); r = s.heroes["rogue"]; sh = enemy(s, "shaman", (3, 5)); sh.announced = mend()
    assert use(s, "rogue", "disrupt", "shaman1") and sh.announced is None and "cd:disrupt" in r.stacks
    o = enemy(s, "ogre", (9, 5))
    o.announced = Announced("skull_crusher", "heavy", 2, "warden", frozenset(), (6, 6))
    assert use(s, "mage", "disrupt", "ogre1") and o.announced is None
