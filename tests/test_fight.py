import pytest
from tests.helpers import state, enemy, GAME
from fastcombat.numbers import load_numbers, load_fight
from fastcombat.fight import run_fight, party_turn, auto_attack
from fastcombat.enemy_ai import gm_turn
from fastcombat.policies import AutoOnly
from fastcombat.combat import add_stack
from dataclasses import replace
from fastcombat import abilities as ab
from fastcombat.abilities import Action, effect
from fastcombat.combat import damage_hero
from fastcombat.grid import distance
from fastcombat.numbers import Spawn
from fastcombat.units import Cast, Stack

N = load_numbers(GAME / "numbers.toml")
F = load_fight(GAME / "fights" / "ogre_warlord.toml")
WOLF_ONLY = replace(F, spawns=[s for s in F.spawns if s.type == "wolf"], boss_script=[])
NO_ENEMY_DAMAGE = replace(F, spawns=[s for s in F.spawns if s.type == "brute"], boss_script=[],
    enemy_types={**F.enemy_types, "brute": replace(F.enemy_types["brute"], hp=10**6, damage=0)})

def test_rogue_builds_combo_points_and_a_crit_gives_two():
    s = state(rolls=[3, 6, 2]); r = s.heroes["rogue"]; w = enemy(s, "wolf", (3, 5))
    auto_attack(s, r, w); assert r.combo == 1 and w.hp == 13
    auto_attack(s, r, w); assert r.combo == 3 and w.hp == 5

def test_the_combo_points_for_a_hit_come_from_the_rules():
    s = state(rolls=[3]); r = s.heroes["rogue"]; w = enemy(s, "wolf", (3, 5))
    s.numbers.rules["combo_per_hit"] = 2
    auto_attack(s, r, w); assert r.combo == 2

def test_quicken_rolls_two_dice():
    s = state(rolls=[3, 4]); r = s.heroes["rogue"]; w = enemy(s, "wolf", (3, 5))
    add_stack(r, "quicken", 2); auto_attack(s, r, w); assert w.hp == 9

def test_a_held_enemy_stays_and_hits_the_warden():
    s = state(); w = enemy(s, "wolf", (4, 6)); gm_turn(s)
    assert w.pos == (4, 6) and s.heroes["warden"].hp == 56 and s.heroes["warden"].resource == 3

def test_a_stunned_enemy_does_nothing_and_the_card_comes_off_after():
    s = state(); w = enemy(s, "wolf", (4, 6)); add_stack(w, "stun", 1); gm_turn(s)
    assert s.heroes["warden"].hp == 60 and "stun" not in w.stacks

def test_nobody_ever_shares_a_square():
    s = state()
    for i in range(8): enemy(s, "wolf", (10 + i % 4, 2 + i // 4))
    for _ in range(6):
        party_turn(s, {h: AutoOnly() for h in s.heroes}); gm_turn(s); s.round += 1
        spots = [h.pos for h in s.heroes.values() if not h.out] + [e.pos for e in s.living_enemies()]
        assert len(spots) == len(set(spots))

def test_same_seed_same_fight():
    a = run_fight(N, WOLF_ONLY, ["warden", "rogue", "druid", "mage"], seed=7)
    b = run_fight(N, WOLF_ONLY, ["warden", "rogue", "druid", "mage"], seed=7)
    assert (a.won, a.rounds, a.tally.damage) == (b.won, b.rounds, b.tally.damage)

def test_four_heroes_beat_two_wolves():
    r = run_fight(N, WOLF_ONLY, ["warden", "rogue", "druid", "mage"], seed=1)
    assert r.won and not r.timeout and r.rounds < 20

def test_a_fight_nobody_can_finish_stops_as_a_timeout_and_a_loss():
    r = run_fight(N, NO_ENEMY_DAMAGE, ["warden"], seed=1)
    assert r.timeout and not r.won and r.rounds == N.rules["max_rounds"]


# More tests, for the details later steps rely on.

class Plays:
    """A policy that always does the same thing: moves to `dest` (or stays) and does `action`."""

    def __init__(self, action=Action("none"), dest=None):
        self.action, self.dest = action, dest

    def move(self, state, hero):
        return self.dest or hero.pos

    def act(self, state, hero):
        return self.action


def idle(s, **plays):
    """Every hero stands still and does nothing, except the ones named."""
    return {h: plays.get(h, Plays()) for h in s.heroes}


@pytest.fixture
def beam():
    """A throwaway Mage channel, "t_beam" (Arcane Volley's numbers). Gives back what it hit."""
    hits = []
    effect("t_beam")(lambda state, hero, spec, action: hits.append(action.target))
    yield hits
    ab.EFFECTS.pop("t_beam", None)


def add_beam(s):
    s.numbers.abilities["t_beam"] = replace(s.numbers.abilities["arcane_volley"], id="t_beam")


# Auto-attacks

def test_each_class_gets_its_crit_hook_and_never_goes_over_the_cap():
    s = state(rolls=[8, 2, 6, 1, 6, 2, 4, 3, 6, 2]); h = s.heroes
    w = enemy(s, "wolf", (4, 6)); w.hp = 999; r = enemy(s, "wolf", (3, 5)); r.hp = 999
    h["druid"].seeds = 1; h["mage"].resource = 20; h["rogue"].combo = 4
    auto_attack(s, h["warden"], w); assert h["warden"].resource == 3     # one grit
    auto_attack(s, h["druid"], w); assert h["druid"].seeds == 2          # a Seed
    auto_attack(s, h["druid"], w); assert h["druid"].seeds == 2          # seeds_max is 2
    auto_attack(s, h["mage"], w); assert h["mage"].resource == 22        # two mana
    auto_attack(s, h["rogue"], r); assert h["rogue"].combo == 5          # combo_max is 5

def test_a_miss_does_nothing_but_still_gives_the_rogue_away():
    s = state(rolls=[1]); r = s.heroes["rogue"]; w = enemy(s, "wolf", (3, 5))
    assert r.hidden
    auto_attack(s, r, w)
    assert w.hp == 16 and r.combo == 0 and not r.hidden

def test_quickened_dice_are_one_hit_so_together_they_can_beat_a_shield():
    s = state(rolls=[3, 4]); r = s.heroes["rogue"]; b = enemy(s, "brute", (3, 5))  # ignores hits below 5
    add_stack(r, "quicken", 2); auto_attack(s, r, b)
    assert b.hp == 23 and r.combo == 2 and s.tally.auto_damage["rogue"] == 7

def test_an_auto_attack_out_of_reach_or_on_a_dead_or_missing_enemy_rolls_nothing():
    s = state(rolls=[]); r = s.heroes["rogue"]                           # any roll would fail the test
    far = enemy(s, "wolf", (10, 3)); auto_attack(s, r, far)
    assert far.hp == 16 and r.hidden
    enemy(s, "wolf", (3, 5)).dead = True
    party_turn(s, idle(s, rogue=Plays(Action("auto", target="wolf2")),
                       warden=Plays(Action("auto", target="wolf9"))))
    assert r.hidden


# The enemy turn

def test_a_loose_wolf_runs_at_the_mage_and_says_who_it_is_after():
    s = state(); w = enemy(s, "wolf", (10, 3)); gm_turn(s)
    assert w.target == "mage" and distance(w.pos, (1, 5)) == 2 and s.heroes["mage"].hp == 28

def test_an_enemy_that_gets_there_hits_the_same_turn_and_the_pull_is_used_up():
    s = state(); w = enemy(s, "wolf", (8, 5)); w.pulled_by = "druid"
    gm_turn(s)
    assert w.target == "druid" and distance(w.pos, (1, 7)) == 1 and s.heroes["druid"].hp == 32
    assert w.pulled_by is None

def test_a_shaman_poisons_who_it_hits():
    s = state(rolls=[2]); sh = enemy(s, "shaman", (9, 5)); gm_turn(s)  # the die picks the mage
    m = s.heroes["mage"]
    assert sh.pos == (9, 5) and m.hp == 25 and m.stacks["poison"] == Stack(3, 2)

def test_an_enemy_with_dice_rolls_its_hit():
    s = state(rolls=[3, 4]); enemy(s, "ogre", (4, 6)); gm_turn(s)
    assert s.heroes["warden"].hp == 51                                   # 2d6 + 2

def test_an_enemy_behind_a_crowd_still_closes_in():
    s = state(party=("mage",))                                           # the mage is at (1, 5)
    for square in [(0, 4), (1, 4), (2, 4), (0, 5), (2, 5), (0, 6), (1, 6), (2, 6)]:
        add_stack(enemy(s, "wolf", square), "stun", 1)                   # a ring of stunned wolves
    back = enemy(s, "wolf", (10, 5)); gm_turn(s)
    assert distance(back.pos, (1, 5)) == 2 and s.heroes["mage"].hp == 28

def test_spawns_come_in_on_their_round_and_step_aside_from_a_taken_square():
    s = state(party=("mage",)); damage_hero(s, s.heroes["mage"], 99, attacker=None)  # nobody to go for
    enemy(s, "wolf", (15, 3))
    s.round = 5; gm_turn(s); assert len(s.living_enemies()) == 1
    s.round = 6; gm_turn(s)
    goblins = [e.pos for e in s.living_enemies() if e.spec.type == "goblin"]
    assert goblins == [(14, 3), (15, 4), (15, 5), (15, 6), (15, 7), (15, 8)]


# The party turn

def test_the_top_of_the_turn_gives_resource_back_up_to_the_pool():
    s = state(); s.heroes["rogue"].resource = 9; s.heroes["mage"].resource = 10
    party_turn(s, idle(s))
    assert s.heroes["rogue"].resource == 10 and s.heroes["mage"].resource == 11
    assert s.tally.resource_by_round == {"warden": [2], "rogue": [10], "druid": [10], "mage": [11]}

def test_a_finished_cast_lands_after_the_resource_comes_back(beam):
    s = state(); add_beam(s); enemy(s, "wolf", (10, 3)); m = s.heroes["mage"]
    m.resource = 1; m.cast = Cast("t_beam", "wolf1", None, 0, 0, False)  # costs 2, no act steps left
    party_turn(s, idle(s))
    assert beam == ["wolf1"] and m.cast is None and m.resource == 0

def test_a_hero_who_cannot_pay_for_anything_has_a_starved_round():
    s = state(); h = s.heroes
    h["warden"].resource = 0                                             # Challenge, the cheapest, costs 1
    h["rogue"].resource = 0                                              # gets 3 back; Shadowstep costs 2
    damage_hero(s, h["mage"], 99, attacker=None); h["mage"].resource = 0  # down: not counted
    party_turn(s, idle(s))
    assert s.tally.starved_rounds == {"warden": 1, "rogue": 0, "druid": 0, "mage": 0}
    assert s.tally.resource_by_round["mage"] == [0]

def test_a_hero_moves_only_within_reach_and_never_onto_someone_or_off_the_map():
    s = state(); h = s.heroes
    party_turn(s, idle(s, rogue=Plays(dest=(15, 5)), druid=Plays(dest=(1, 5)),
                       mage=Plays(dest=(4, 4)), warden=Plays(dest=(3, -1))))
    assert [h[x].pos for x in ("rogue", "druid", "mage", "warden")] == [(2, 5), (1, 7), (4, 4), (3, 6)]

def test_moving_breaks_a_cast_but_not_a_channel(beam):
    s = state(); add_beam(s); enemy(s, "wolf", (10, 3)); h = s.heroes
    h["mage"].cast = Cast("t_beam", "wolf1", None, 0, 3, True)
    h["rogue"].cast = Cast("t_beam", "wolf1", None, 1, 0, False)
    party_turn(s, idle(s, mage=Plays(Action("continue"), (2, 4)), rogue=Plays(Action("continue"), (3, 4))))
    assert h["rogue"].pos == (3, 4) and h["rogue"].cast is None
    assert h["mage"].pos == (2, 4) and beam == ["wolf1"] and h["mage"].cast.hits_left == 2

def test_continue_keeps_a_cast_going_and_anything_else_ends_it():
    s = state(); h = s.heroes
    h["druid"].cast = Cast("regrowth", "warden", None, 1, 0, False)
    h["mage"].cast = Cast("firebolt", None, None, 1, 0, False)
    s.marked["mage"] = frozenset({(8, 8)})
    party_turn(s, idle(s, druid=Plays(Action("continue"))))
    assert h["druid"].cast.actions_left == 0 and h["mage"].cast is None and s.marked == {}

def test_an_ability_is_used_and_one_that_is_refused_is_the_same_as_doing_nothing(beam):
    s = state(); add_beam(s); enemy(s, "wolf", (10, 3)); m = s.heroes["mage"]
    zap = idle(s, mage=Plays(Action("ability", "t_beam", "wolf1")))
    party_turn(s, zap); assert beam == ["wolf1"] and m.cast.hits_left == 2
    m.resource = 0                                                       # 1 back is not enough
    party_turn(s, zap); assert beam == ["wolf1"] and m.cast is None

def test_hauling_up_needs_a_downed_ally_next_to_you():
    s = state(); m = s.heroes["mage"]; damage_hero(s, m, 99, attacker=None)
    haul = Plays(Action("haul_up", target="mage"))
    party_turn(s, idle(s, druid=haul))                                   # the druid is 2 away
    assert m.down and m.stacks["bleeding"].cards == 2                    # one card off, at the end
    party_turn(s, idle(s, rogue=haul))                                   # the rogue is next to her
    assert m.up and m.hp == 5 and m.wounds == 1

def test_the_last_bleeding_card_still_leaves_a_whole_party_turn_to_save_you():
    s = state(); m = s.heroes["mage"]; m.wounds = 2; damage_hero(s, m, 99, attacker=None)
    party_turn(s, idle(s, rogue=Plays(Action("haul_up", target="mage"))))
    assert m.up
    s = state(); m = s.heroes["mage"]; m.wounds = 2; damage_hero(s, m, 99, attacker=None)
    party_turn(s, idle(s))
    assert m.out

def test_auto_only_leaves_controlled_enemies_alone():
    s = state(); h = s.heroes
    add_stack(enemy(s, "wolf", (3, 5)), "stun", 1); enemy(s, "wolf", (4, 7))
    assert AutoOnly().act(s, h["rogue"]) == Action("none")               # wolf2 is 2 away
    assert AutoOnly().act(s, h["warden"]) == Action("auto", target="wolf2")
    assert AutoOnly().move(s, h["rogue"]) != h["rogue"].pos
    s.enemies["wolf2"].dead = True
    assert AutoOnly().move(s, h["rogue"]) == h["rogue"].pos and AutoOnly().act(s, h["rogue"]) == Action("none")


# A whole fight

def test_the_result_says_who_played_and_how_it_ended():
    party = ["warden", "rogue", "druid", "mage"]
    r = run_fight(N, WOLF_ONLY, party, seed=3)
    assert r.party == party and r.seed == 3 and set(r.end_resource) == set(party)
    assert all(len(seen) == r.rounds for seen in r.tally.resource_by_round.values())

def test_each_hero_plays_the_policy_given_for_them():
    plays = {"warden": AutoOnly(), "rogue": AutoOnly(), "druid": AutoOnly(), "mage": Plays()}
    r = run_fight(N, WOLF_ONLY, ["warden", "rogue", "druid", "mage"], policies=plays, seed=1)
    assert r.tally.damage["mage"] == 0 and r.tally.damage["druid"] > 0

def test_heroes_with_no_policy_given_play_their_class_policy():
    r = run_fight(N, WOLF_ONLY, ["warden", "rogue", "druid", "mage"], policies={"mage": Plays()}, seed=1)
    assert r.tally.damage["mage"] == 0 and r.tally.healing["druid"] > 0   # only the Druid's own policy heals

def test_the_fight_is_lost_when_nobody_is_up():
    r = run_fight(N, WOLF_ONLY, ["mage"], policies={"mage": AutoOnly()}, seed=1)
    assert not r.won and not r.timeout and r.rounds < N.rules["max_rounds"]

def test_the_party_has_not_won_while_an_enemy_is_still_to_come():
    late = replace(F, spawns=[Spawn("goblin", (15, 3), round=1)], boss_script=[])
    r = run_fight(N, late, ["warden", "rogue", "druid", "mage"], seed=1)
    assert r.won and r.rounds >= 2                                       # it comes in during round 1's GM turn
