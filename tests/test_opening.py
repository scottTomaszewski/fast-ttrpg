import pytest

from tests.helpers import state, enemy, GAME
from fastcombat.abilities.rogue import landing
from fastcombat.combat import add_stack
from fastcombat.fight import run_fight
from fastcombat.grid import adjacent
from fastcombat.numbers import load_numbers, load_fight
from fastcombat.opening import NONE, Opening, can_open, open_fight
from fastcombat.policies import AutoOnly

N = load_numbers(GAME / "numbers.toml")
F = load_fight(GAME / "fights" / "ogre_warlord.toml")
PARTY = ["guardian", "rogue", "druid", "mage"]


class Opens:
    """A Rogue who makes one set opening, then only auto-attacks."""

    def __init__(self, opening):
        self.chosen = opening

    def opening(self, state, hero):
        return self.chosen

    def move(self, state, hero):
        return AutoOnly().move(state, hero)

    def act(self, state, hero):
        return AutoOnly().act(state, hero)


def test_a_sneak_that_works_starts_her_next_to_the_enemy_still_hidden():
    s = state(rolls=[4]); r = s.heroes["rogue"]                     # d6, 4 or more
    b = enemy(s, "brute", (10, 7)); square = landing(s, r, b)       # where Shadowstep would land her
    assert open_fight(s, r, Opening("sneak", "brute1"))
    assert adjacent(r.pos, b.pos) and r.pos == square == (9, 7)     # the free square nearest her start at (2, 5)
    assert r.hidden and r.resource == 10 and s.tally.openings["rogue"] == "sneak"

def test_a_sneak_that_fails_leaves_her_spotted_on_her_start_square():
    s = state(rolls=[3]); r = s.heroes["rogue"]; enemy(s, "brute", (10, 7))
    assert open_fight(s, r, Opening("sneak", "brute1"))
    assert r.pos == (2, 5) and not r.hidden and r.resource == 10
    assert s.tally.openings["rogue"] == "spotted"

def test_the_stealth_check_comes_from_the_rules():
    s = state(rolls=[5]); r = s.heroes["rogue"]; enemy(s, "brute", (10, 7))
    s.numbers.rules["sneak_target"] = 6
    open_fight(s, r, Opening("sneak", "brute1")); assert not r.hidden
    s = state(rolls=[2]); r = s.heroes["rogue"]; enemy(s, "brute", (10, 7))
    s.numbers.rules["sneak_die"] = 2; s.numbers.rules["sneak_target"] = 2
    open_fight(s, r, Opening("sneak", "brute1")); assert r.hidden and r.pos != (2, 5)

def test_shadowstep_in_always_works_and_costs_shadowsteps_energy():
    s = state(rolls=[]); r = s.heroes["rogue"]; b = enemy(s, "brute", (10, 7))   # no die is rolled
    assert open_fight(s, r, Opening("shadowstep", "brute1"))
    assert adjacent(r.pos, b.pos) and r.hidden
    assert r.resource == 10 - N.abilities["shadowstep"].cost
    assert s.tally.openings["rogue"] == "shadowstep"
    assert s.tally.uses["rogue"] == {}                              # not a use of Shadowstep

def test_shadowstep_in_needs_the_energy_to_pay_for_it():
    s = state(); r = s.heroes["rogue"]; enemy(s, "brute", (10, 7))
    r.resource = N.abilities["shadowstep"].cost - 1
    assert not can_open(s, r, Opening("shadowstep", "brute1"))
    assert can_open(s, r, Opening("sneak", "brute1"))

def test_an_opening_on_a_boss_a_dead_enemy_or_a_crowded_one_is_refused():
    s = state(rolls=[]); r = s.heroes["rogue"]
    enemy(s, "ogre", (11, 6))
    for kind in ("sneak", "shadowstep"):
        assert not can_open(s, r, Opening(kind, "ogre1"))
    assert not open_fight(s, r, Opening("sneak", "ogre1"))           # refused: nothing happens, no die
    assert r.pos == (2, 5) and r.hidden and s.tally.openings["rogue"] == "none"
    w = enemy(s, "wolf", (8, 8)); w.dead = True
    assert not can_open(s, r, Opening("shadowstep", "wolf1"))
    assert not can_open(s, r, Opening("sneak", "nobody"))
    b = enemy(s, "brute", (0, 0))                                   # a corner, with all three squares by it taken
    for square in ((1, 0), (0, 1), (1, 1)):
        enemy(s, "goblin", square)
    assert not can_open(s, r, Opening("sneak", b.id))

def test_only_a_hidden_rogue_can_open():
    s = state(); enemy(s, "brute", (10, 7))
    assert not can_open(s, s.heroes["guardian"], Opening("sneak", "brute1"))
    r = s.heroes["rogue"]; r.hidden = False
    assert not can_open(s, r, Opening("shadowstep", "brute1"))

def test_none_is_always_allowed_and_an_unknown_opening_is_an_error():
    s = state(); r = s.heroes["rogue"]
    assert can_open(s, r, NONE) and open_fight(s, r, NONE) and s.tally.openings["rogue"] == "none"
    with pytest.raises(ValueError):
        can_open(s, r, Opening("charge", None))

def test_a_policy_without_an_opening_starts_hidden_where_she_is():
    r = run_fight(N, F, PARTY, {"rogue": AutoOnly()}, seed=5)
    assert r.tally.openings == {"rogue": "none"}

def test_the_opening_happens_in_run_fight_before_round_1_and_the_same_seed_gives_the_same_result():
    results = {}
    for seed in range(12):
        a = run_fight(N, F, PARTY, {"rogue": Opens(Opening("sneak", "brute1"))}, seed=seed)
        b = run_fight(N, F, PARTY, {"rogue": Opens(Opening("sneak", "brute1"))}, seed=seed)
        assert a.tally.openings == b.tally.openings and a.rounds == b.rounds and a.tally.damage == b.tally.damage
        results[seed] = a.tally.openings["rogue"]
    assert set(results.values()) == {"sneak", "spotted"}            # the die really is rolled
    r = run_fight(N, F, PARTY, {"rogue": Opens(Opening("shadowstep", "brute1"))}, seed=1)
    assert r.tally.openings == {"rogue": "shadowstep"}

def test_two_rogues_each_open_in_id_order():
    s = state(("rogue", "rogue"), rolls=[]); enemy(s, "brute", (10, 7))
    r1, r2 = s.heroes["rogue"], s.heroes["rogue2"]
    open_fight(s, r1, Opening("shadowstep", "brute1")); open_fight(s, r2, Opening("shadowstep", "brute1"))
    assert adjacent(r1.pos, (10, 7)) and adjacent(r2.pos, (10, 7)) and r1.pos != r2.pos

def test_a_sapped_enemy_losing_its_turn_is_counted():
    from fastcombat.enemy_ai import gm_turn
    s = state(); w = enemy(s, "wolf", (10, 3)); add_stack(w, "sap", 2)
    gm_turn(s); gm_turn(s); gm_turn(s)
    assert s.tally.rounds_out == {"sap": 2}
