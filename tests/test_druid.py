from tests.helpers import state, enemy
from tests.test_guardian import use
from fastcombat.casting import land_casts
from fastcombat.combat import damage_hero, add_stack
from fastcombat.grid import distance

def test_rejuvenation_does_not_stack():
    s = state(); w = s.heroes["guardian"]; s.heroes["druid"].resource = 10
    use(s, "druid", "rejuvenation", "guardian"); w.stacks["rejuvenation"].cards = 1
    use(s, "druid", "rejuvenation", "guardian")
    assert w.stacks["rejuvenation"].cards == 4 and s.heroes["druid"].resource == 6

def test_regrowth_lands_next_turn_heals_gives_a_seed_and_is_loud():
    from fastcombat.casting import land_casts
    s = state(rolls=[2, 2, 2]); w = s.heroes["guardian"]; w.hp = 20; far = enemy(s, "wolf", (12, 2))
    use(s, "druid", "regrowth", "guardian"); assert w.hp == 20
    land_casts(s)
    assert w.hp == 30 and s.heroes["druid"].seeds == 1 and far.pulled_by == "druid"

def test_swiftmend_needs_a_seed_and_is_free_on_a_badly_hurt_ally():
    s = state(rolls=[3, 3]); d = s.heroes["druid"]; m = s.heroes["mage"]; m.hp = 10
    assert not use(s, "druid", "swiftmend", "mage")
    d.seeds = 1; assert use(s, "druid", "swiftmend", "mage")
    assert m.hp == 18 and d.seeds == 0 and d.resource == 10

def test_swiftmend_gets_a_downed_ally_up():
    s = state(rolls=[3, 3]); m = s.heroes["mage"]; s.heroes["druid"].seeds = 1
    damage_hero(s, m, 99, attacker=None); use(s, "druid", "swiftmend", "mage")
    assert m.up and m.hp == 8 and m.wounds == 1

def test_wild_growth_gives_two_cards_to_allies_in_the_area():
    s = state(); use(s, "druid", "wild_growth", pos=(2, 6))
    assert s.heroes["guardian"].stacks["wild_growth"].cards == 2
    assert s.heroes["rogue"].stacks["wild_growth"].value == 4

def test_nourish_heals_the_roll_and_the_top_face_gives_energy_back():
    s = state(rolls=[6]); d = s.heroes["druid"]; d.resource = 4; w = s.heroes["guardian"]; w.hp = 30
    use(s, "druid", "nourish", "guardian"); assert w.hp == 36 and d.resource == 6

def test_cleanse_removes_poison():
    s = state(); m = s.heroes["mage"]; add_stack(m, "poison", 3, 2)
    use(s, "druid", "cleanse", "mage"); assert "poison" not in m.stacks

def test_shadowmeld_drops_pulls_and_backs_off():
    s = state(); w = enemy(s, "wolf", (2, 7)); w.pulled_by = "druid"; before = s.heroes["druid"].pos
    use(s, "druid", "shadowmeld"); assert w.pulled_by is None and s.heroes["druid"].pos != before

# --- When the Druid's abilities say no, and the smaller rules -----------------

AIMED = ("rejuvenation", "regrowth", "swiftmend", "cleanse", "nourish")

def test_the_druids_aimed_abilities_are_only_for_heroes():
    s = state(); d = s.heroes["druid"]; d.seeds = 1
    w = enemy(s, "wolf", (2, 7)); add_stack(w, "poison", 3, 2)   # in reach, and poisoned: only the target is wrong
    for ability in AIMED:
        assert not use(s, "druid", ability, "wolf1") and not use(s, "druid", ability)
    assert d.resource == 10 and d.seeds == 1 and d.cast is None and "poison" in w.stacks

def test_the_druid_may_heal_themself():
    s = state(rolls=[3, 3]); d = s.heroes["druid"]; d.hp = 10; d.seeds = 1
    assert use(s, "druid", "rejuvenation", "druid") and "rejuvenation" in d.stacks
    assert use(s, "druid", "swiftmend", "druid") and d.hp == 18

def test_rejuvenation_is_not_for_a_downed_ally():
    s = state(); m = s.heroes["mage"]; damage_hero(s, m, 99, attacker=None)
    assert not use(s, "druid", "rejuvenation", "mage")
    assert "rejuvenation" not in m.stacks and s.heroes["druid"].resource == 10

def test_regrowth_gets_up_an_ally_who_went_down_while_it_was_cast():
    s = state(rolls=[2, 2, 2]); m = s.heroes["mage"]
    use(s, "druid", "regrowth", "mage"); damage_hero(s, m, 99, attacker=None)
    land_casts(s)
    assert m.up and m.hp == 10 and m.wounds == 1 and s.tally.healing["druid"] == 10

def test_regrowth_on_an_ally_who_is_out_by_then_costs_nothing_and_gives_nothing():
    s = state(); d = s.heroes["druid"]; far = enemy(s, "wolf", (12, 2))
    use(s, "druid", "regrowth", "mage"); s.heroes["mage"].out = True
    land_casts(s)
    assert d.resource == 10 and d.seeds == 0 and far.pulled_by is None and d.cast is None

def test_regrowth_seeds_stop_at_the_most_a_druid_can_hold():
    s = state(rolls=[2, 2, 2]); d = s.heroes["druid"]; d.seeds = 2
    use(s, "druid", "regrowth", "guardian"); land_casts(s)
    assert d.seeds == 2

def test_swiftmend_costs_full_price_on_an_ally_at_half_hp_or_more():
    s = state(rolls=[1, 1, 1, 1]); d = s.heroes["druid"]; d.seeds = 2; m = s.heroes["mage"]
    m.hp = 14; assert use(s, "druid", "swiftmend", "mage") and d.resource == 8   # 14 is half of 28
    m.hp = 13; assert use(s, "druid", "swiftmend", "mage") and d.resource == 8   # below half: free
    assert d.seeds == 0

def test_wild_growth_skips_heroes_who_are_down_out_or_outside_and_does_not_stack():
    s = state(); d = s.heroes["druid"]; add_stack(d, "wild_growth", 1, 4)
    s.heroes["guardian"].pos = (8, 6)                                   # outside the area
    damage_hero(s, s.heroes["mage"], 99, attacker=None); s.heroes["rogue"].out = True
    assert use(s, "druid", "wild_growth", pos=(2, 6))
    assert d.stacks["wild_growth"].cards == 2
    assert all("wild_growth" not in s.heroes[h].stacks for h in ("guardian", "mage", "rogue"))

def test_wild_growth_needs_a_centre():
    s = state(); assert not use(s, "druid", "wild_growth") and s.heroes["druid"].resource == 10

def test_cleanse_needs_poison_and_takes_off_only_the_poison():
    s = state(); m = s.heroes["mage"]; add_stack(m, "rejuvenation", 4, 4)
    assert not use(s, "druid", "cleanse", "mage") and s.heroes["druid"].resource == 10
    add_stack(m, "poison", 3, 2)
    assert use(s, "druid", "cleanse", "mage") and "poison" not in m.stacks and "rejuvenation" in m.stacks

def test_nourish_heals_on_a_one_and_energy_stops_at_the_pool():
    s = state(rolls=[1, 6]); d = s.heroes["druid"]; d.resource = 9; w = s.heroes["guardian"]; w.hp = 30
    use(s, "druid", "nourish", "guardian"); assert w.hp == 31 and d.resource == 9   # a 1 does not miss
    use(s, "druid", "nourish", "guardian"); assert w.hp == 37 and d.resource == 10

def test_nourish_gets_a_downed_ally_up():
    s = state(rolls=[4]); m = s.heroes["mage"]; damage_hero(s, m, 99, attacker=None)
    assert use(s, "druid", "nourish", "mage") and m.up and m.hp == 4

def test_shadowmeld_lets_go_only_of_the_druids_own_pulls_and_moves_its_squares():
    s = state(); d = s.heroes["druid"]; w = enemy(s, "wolf", (2, 7)); w.pulled_by = "mage"
    assert use(s, "druid", "shadowmeld")
    assert w.pulled_by == "mage" and distance((1, 7), d.pos) == 3 and distance(d.pos, w.pos) == 3

def test_shadowmeld_never_walks_through_anyone():
    s = state(); d = s.heroes["druid"]; d.pos = (0, 0)                # in the corner, boxed in
    s.heroes["mage"].pos = (0, 1); s.heroes["rogue"].pos = (1, 1); w = enemy(s, "wolf", (1, 0))
    w.pulled_by = "druid"
    assert use(s, "druid", "shadowmeld") and d.pos == (0, 0) and w.pulled_by is None

def test_shadowmeld_does_not_run_from_a_dead_enemy():
    s = state(); w = enemy(s, "wolf", (2, 7)); w.dead = True
    assert use(s, "druid", "shadowmeld") and s.heroes["druid"].pos == (1, 7)

def test_nourish_rolls_its_dice_count_and_adds_its_bonus():
    from dataclasses import replace
    s = state(rolls=[3, 4, 2, 6]); d = s.heroes["druid"]; d.resource = 4; w = s.heroes["guardian"]; w.hp = 30
    s.numbers.abilities["nourish"] = replace(s.numbers.abilities["nourish"], dice=(2, 6), bonus=1)
    use(s, "druid", "nourish", "guardian"); assert w.hp == 30 + 3 + 4 + 1 and d.resource == 4
    use(s, "druid", "nourish", "guardian"); assert w.hp == 38 + 2 + 6 + 1 and d.resource == 6   # any die on its top face
