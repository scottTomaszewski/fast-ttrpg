import pytest
from dataclasses import replace
from tests.helpers import state, enemy
from fastcombat import abilities as ab
from fastcombat.abilities import Action, use_ability, can_use, effect
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
