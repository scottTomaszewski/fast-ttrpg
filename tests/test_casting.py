import pytest
from dataclasses import replace
from tests.helpers import state, enemy
from fastcombat import abilities as ab
from fastcombat.abilities import Action, use_ability, can_use, effect, check, cost, keeps_hiding
from fastcombat.casting import land_casts, continue_cast, drop_cast, may_move
from fastcombat.combat import top_of_party_turn_cards

@pytest.fixture
def s():
    st = state(party=("mage",))
    hits = []
    spec = st.numbers.abilities["firebolt"]
    st.numbers.abilities["t_bolt"] = replace(spec, id="t_bolt", cast=2, cost=4)
    st.numbers.abilities["t_beam"] = replace(spec, id="t_beam", cast=0, hits=3, cost=2)
    st.numbers.abilities["t_kick"] = replace(spec, id="t_kick", cast=0, cost=0, cooldown=3)
    for name in ("t_bolt", "t_beam", "t_kick"):
        effect(name)(lambda state, hero, spec, action: hits.append(action.target))
    st.hits = hits
    yield st
    for name in ("t_bolt", "t_beam", "t_kick"):
        ab.EFFECTS.pop(name, None)

def test_a_two_round_cast_takes_two_actions_and_lands_the_turn_after(s):
    m = s.heroes["mage"]; w = enemy(s, "wolf", (6, 5))
    assert use_ability(s, m, Action("ability", "t_bolt", "wolf1"))
    assert m.resource == 30 and not may_move(m)
    land_casts(s); assert s.hits == []          # top of turn T+1: not yet
    continue_cast(s, m)                         # act step T+1
    land_casts(s)                               # top of turn T+2
    assert s.hits == ["wolf1"] and m.resource == 26 and m.cast is None

def test_a_cancelled_cast_costs_nothing(s):
    m = s.heroes["mage"]; enemy(s, "wolf", (6, 5))
    use_ability(s, m, Action("ability", "t_bolt", "wolf1")); drop_cast(s, m)
    land_casts(s); assert s.hits == [] and m.resource == 30 and may_move(m)

def test_a_cast_fizzles_free_if_the_target_died(s):
    m = s.heroes["mage"]; w = enemy(s, "wolf", (6, 5))
    use_ability(s, m, Action("ability", "t_bolt", "wolf1")); continue_cast(s, m)
    w.dead = True; land_casts(s)
    assert s.hits == [] and m.resource == 30 and m.cast is None

def test_a_channel_hits_now_pays_per_hit_and_allows_moving(s):
    m = s.heroes["mage"]; enemy(s, "wolf", (6, 5))
    use_ability(s, m, Action("ability", "t_beam", "wolf1"))
    assert s.hits == ["wolf1"] and m.resource == 28 and may_move(m)
    continue_cast(s, m); continue_cast(s, m)
    assert len(s.hits) == 3 and m.resource == 24 and m.cast is None

def test_out_of_range_or_too_poor_is_refused(s):
    m = s.heroes["mage"]; enemy(s, "wolf", (15, 11))
    assert not can_use(s, m, "t_bolt", Action("ability", "t_bolt", "wolf1"))
    enemy(s, "wolf", (6, 5)); m.resource = 3
    assert not can_use(s, m, "t_bolt", Action("ability", "t_bolt", "wolf2"))

def test_a_cooldown_is_a_card_stack_on_the_hero(s):
    m = s.heroes["mage"]; enemy(s, "wolf", (6, 5)); a = Action("ability", "t_kick", "wolf1")
    assert use_ability(s, m, a) and not can_use(s, m, "t_kick", a)
    for _ in range(3): top_of_party_turn_cards(s)
    assert can_use(s, m, "t_kick", a)


# --- The core's own rules, each pinned with a throwaway ability --------------

@pytest.fixture
def new_ability():
    """Makes throwaway abilities for one test, and forgets them after it.

    `new_ability(st, "t_x", ...)` copies Firebolt (a Mage ability that costs
    4 and reaches 10) into a new ability "t_x", with the changes given. It
    happens at once unless `cast` says otherwise. Using it writes its target
    down in `st.hits`.
    """
    names = []

    def make(st, name, **changes):
        spec = st.numbers.abilities["firebolt"]
        st.numbers.abilities[name] = replace(spec, **({"id": name, "cast": 0} | changes))
        if not hasattr(st, "hits"):
            st.hits = []
        effect(name)(lambda state, hero, spec, action: st.hits.append(action.target))
        names.append(name)

    yield make
    for name in names:
        for table in (ab.EFFECTS, ab.CHECKS, ab.COSTS):
            table.pop(name, None)
        ab.KEEPS_HIDING.discard(name)

def mage_and_wolf():
    """A fight with only the Mage, at (1, 5), and a wolf 5 squares away."""
    s = state(party=("mage",)); enemy(s, "wolf", (6, 5))
    return s, s.heroes["mage"]

def test_an_ability_with_no_reach_works_at_any_distance(new_ability):
    s = state(party=("mage",)); m = s.heroes["mage"]; enemy(s, "wolf", (15, 11))
    new_ability(s, "t_far", range=0)
    assert use_ability(s, m, Action("ability", "t_far", "wolf1")) and s.hits == ["wolf1"]

def test_a_square_out_of_reach_is_refused(new_ability):
    s = state(party=("mage",)); m = s.heroes["mage"]   # at (1, 5); the reach is 10
    new_ability(s, "t_spot")
    assert can_use(s, m, "t_spot", Action("ability", "t_spot", pos=(11, 5)))
    assert not can_use(s, m, "t_spot", Action("ability", "t_spot", pos=(12, 5)))

def test_a_downed_hero_can_be_targeted_and_an_out_hero_cannot(new_ability):
    s = state(party=("mage", "druid")); m = s.heroes["mage"]; d = s.heroes["druid"]
    new_ability(s, "t_help"); a = Action("ability", "t_help", "druid")
    d.down = True
    assert can_use(s, m, "t_help", a)
    d.down = False; d.out = True
    assert not can_use(s, m, "t_help", a)

def test_another_class_ability_is_refused_and_a_shared_one_is_allowed(new_ability):
    s, m = mage_and_wolf()
    new_ability(s, "t_rogue_only", hero="rogue"); new_ability(s, "t_anyone", hero="shared")
    assert not can_use(s, m, "t_rogue_only", Action("ability", "t_rogue_only", "wolf1"))
    assert can_use(s, m, "t_anyone", Action("ability", "t_anyone", "wolf1"))

def test_an_extra_rule_that_says_no_refuses(new_ability):
    s, m = mage_and_wolf()
    new_ability(s, "t_never"); check("t_never")(lambda state, hero, spec, action: False)
    assert not use_ability(s, m, Action("ability", "t_never", "wolf1"))
    assert s.hits == [] and m.resource == 30

def test_a_cost_rule_takes_the_place_of_the_cost_in_the_file(new_ability):
    s, m = mage_and_wolf(); a = Action("ability", "t_pricey", "wolf1")
    new_ability(s, "t_pricey"); cost("t_pricey")(lambda state, hero, spec, action: 7)
    m.resource = 5                                     # enough for the file's 4, not for 7
    assert not can_use(s, m, "t_pricey", a)
    m.resource = 30
    assert use_ability(s, m, a) and m.resource == 23

def test_an_area_cast_marks_its_squares_until_it_lands(new_ability):
    s = state(party=("mage",)); m = s.heroes["mage"]
    new_ability(s, "t_blast", cast=1, radius=1)
    assert use_ability(s, m, Action("ability", "t_blast", pos=(6, 5)))
    assert s.marked["mage"] == {(x, y) for x in (5, 6, 7) for y in (4, 5, 6)}
    land_casts(s)
    assert "mage" not in s.marked and m.cast is None and m.resource == 26

def test_hiding_ends_after_an_ability(new_ability):
    s, m = mage_and_wolf(); m.hidden = True
    new_ability(s, "t_poke")
    assert use_ability(s, m, Action("ability", "t_poke", "wolf1")) and not m.hidden

def test_hiding_ends_as_soon_as_a_cast_starts(new_ability):
    s, m = mage_and_wolf(); m.hidden = True
    new_ability(s, "t_slow", cast=2)
    assert use_ability(s, m, Action("ability", "t_slow", "wolf1"))
    assert m.cast is not None and not m.hidden

@pytest.mark.parametrize("hidden_before", [True, False])
def test_an_ability_that_keeps_hiding_leaves_hiding_as_it_set_it(new_ability, hidden_before):
    s = state(party=("mage",)); m = s.heroes["mage"]; m.hidden = hidden_before
    new_ability(s, "t_hide", range=0)

    @keeps_hiding("t_hide")
    @effect("t_hide")
    def hide(state, hero, spec, action):
        hero.hidden = True

    assert use_ability(s, m, Action("ability", "t_hide")) and m.hidden

def test_a_channel_ends_free_when_its_target_gets_out_of_reach(new_ability):
    s, m = mage_and_wolf(); w = s.enemies["wolf1"]
    new_ability(s, "t_ray", hits=3, cost=2)
    use_ability(s, m, Action("ability", "t_ray", "wolf1"))
    assert s.hits == ["wolf1"] and m.resource == 28
    w.pos = (12, 5)                                    # 11 from the Mage; the reach is 10
    continue_cast(s, m)
    assert s.hits == ["wolf1"] and m.resource == 28 and m.cast is None

def test_a_channel_on_a_square_ends_free_when_the_hero_walks_out_of_reach(new_ability):
    s = state(party=("mage",)); m = s.heroes["mage"]
    new_ability(s, "t_rain", hits=3, cost=2, radius=1)
    use_ability(s, m, Action("ability", "t_rain", pos=(11, 5)))
    assert m.resource == 28
    m.pos = (0, 5)                                     # 11 from the square; the reach is 10
    continue_cast(s, m)
    assert len(s.hits) == 1 and m.resource == 28 and m.cast is None
