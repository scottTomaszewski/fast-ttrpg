import pytest
from tests.helpers import state, enemy
from tests.test_guardian import use
from fastcombat.enemy_ai import gm_turn, announce, land_announced, throw
from fastcombat.combat import add_stack, damage_hero

def boss_state(round, rolls=None):
    s = state(rolls=rolls); o = enemy(s, "ogre", (4, 6)); s.round = round; return s, o

def boulder(s):
    """The throw step in the boss's script."""
    return next(step for step in s.fight.boss_script if step.kind == "throw")

def test_ground_slam_is_announced_a_turn_ahead_and_marked():
    s, o = boss_state(3); announce(s)
    assert o.announced.name == "ground_slam" and o.announced.lands_round == 4
    assert (2, 6) in s.danger_squares() and (7, 6) not in s.danger_squares()

def test_the_slam_misses_anyone_who_walked_out():
    s, o = boss_state(3, rolls=[4, 4, 4]); announce(s); s.round = 4
    s.heroes["rogue"].pos = (9, 9); land_announced(s)
    assert s.heroes["guardian"].hp == 48 and s.heroes["rogue"].hp == 36 and o.announced is None

def test_skull_crusher_hits_the_bosss_target_and_last_stand_survives_it():
    s, o = boss_state(5, rolls=[6] * 6); o.target = "guardian"; announce(s)
    assert o.announced.kind == "heavy"
    s.heroes["guardian"].hp = 20; s.heroes["guardian"].resource = 10
    use(s, "guardian", "last_stand"); s.round = 6; land_announced(s)
    assert s.heroes["guardian"].hp == 1

def test_an_interrupted_mend_heals_nothing():
    s, o = boss_state(2); sh = enemy(s, "shaman", (9, 5)); o.hp = 100; announce(s)
    assert sh.announced.kind == "mend"
    use(s, "mage", "disrupt", "shaman1"); s.round = 3; land_announced(s); assert o.hp == 100

def test_a_mend_that_lands_heals_the_boss():
    s, o = boss_state(2); enemy(s, "shaman", (9, 5)); o.hp = 100; announce(s)
    s.round = 3; land_announced(s); assert o.hp == 125

def test_the_boulder_ignores_taunts_and_never_picks_someone_next_to_the_boss():
    # The rolls, in the order the GM turn makes them: the ogre's melee hit on
    # the Guardian (2d6: 3, 3), then the die that picks who the boulder hits (1 of
    # the 3 heroes not next to the ogre: the druid), then the boulder (2d6: 5, 5).
    s, o = boss_state(2, rolls=[3, 3, 1, 5, 5]); use(s, "guardian", "taunt", "ogre1")
    before = {h.id: h.hp for h in s.heroes.values()}; gm_turn(s)
    hurt = [h.id for h in s.heroes.values() if h.hp < before[h.id] and h.id != "guardian"]
    assert len(hurt) == 1

# --- Who a controlled enemy attacks, and what happens to its cast -------------

def test_a_controlled_enemy_is_attacking_nobody():
    s = state(); w = enemy(s, "wolf", (4, 6)); w.target = "guardian"   # from its last turn
    add_stack(w, "stun", 1); gm_turn(s)
    assert w.target is None and s.heroes["guardian"].hp == 60

@pytest.mark.parametrize("card", ["sap", "sheep"])
def test_a_sapped_or_sheeped_shamans_mend_does_not_land_and_is_cleared(card):
    s, o = boss_state(2); sh = enemy(s, "shaman", (9, 5)); o.hp = 100; announce(s)
    assert sh.announced.kind == "mend"
    add_stack(sh, card, 1); s.round = 3; land_announced(s)
    assert o.hp == 100 and sh.announced is None

def test_a_controlled_shaman_announces_no_mend():
    s, o = boss_state(2); sh = enemy(s, "shaman", (9, 5)); add_stack(sh, "sap", 1)
    announce(s); assert sh.announced is None
    sh.stacks.clear(); announce(s); assert sh.announced.kind == "mend"

def test_a_mend_never_heals_the_boss_past_its_max():
    s, o = boss_state(2); enemy(s, "shaman", (9, 5)); o.hp = 310; announce(s)
    s.round = 3; land_announced(s); assert o.hp == 320

# --- Aiming the heavy hit -----------------------------------------------------

def test_the_skull_crusher_is_only_aimed_at_a_hero_who_is_up():
    s, o = boss_state(5)
    announce(s); assert o.announced is None                              # it went for nobody
    o.target = "guardian"; damage_hero(s, s.heroes["guardian"], 99, attacker=None)
    announce(s); assert o.announced is None                              # it went for someone now down
    o.target = "mage"; announce(s)
    assert (o.announced.kind, o.announced.target) == ("heavy", "mage")

def test_a_skull_crusher_on_a_hero_who_went_down_since_rolls_nothing():
    s, o = boss_state(5, rolls=[]); o.target = "guardian"; announce(s)    # any roll would fail the test
    assert o.announced.target == "guardian"
    damage_hero(s, s.heroes["guardian"], 99, attacker=None); s.round = 6; land_announced(s)
    assert o.announced is None and s.heroes["guardian"].stacks["bleeding"].cards == 3

# --- The boulder --------------------------------------------------------------

def test_the_boulder_picks_in_id_order_from_the_heroes_not_next_to_the_boss():
    # The druid steps next to the ogre (like the Guardian), which leaves the mage
    # and the rogue, in id order. The rolls: 1 picks the first of the two (the
    # mage), then the boulder (2d6: 2, 3).
    s, o = boss_state(2, rolls=[1, 2, 3]); s.heroes["druid"].pos = (5, 6)
    throw(s, o, boulder(s))
    assert {h.id: h.hp for h in s.heroes.values()} == {"guardian": 60, "rogue": 36, "druid": 36, "mage": 23}

def test_the_boulder_with_nobody_to_aim_at_rolls_nothing():
    s, o = boss_state(2, rolls=[])                                       # any roll would fail the test
    for name in ("rogue", "druid", "mage"):                              # the guardian is next to the ogre
        damage_hero(s, s.heroes[name], 99, attacker=None)
    throw(s, o, boulder(s)); assert s.heroes["guardian"].hp == 60

def test_the_boss_hits_first_and_throws_second():
    # The ogre's melee hit on the Guardian (2d6: 1, 1, plus 2), then the die that
    # picks who the boulder hits (3 of 3: the rogue), then the boulder (2d6: 6, 6).
    s, o = boss_state(2, rolls=[1, 1, 3, 6, 6]); s.heroes["rogue"].hidden = False; gm_turn(s)
    assert s.heroes["guardian"].hp == 56 and s.heroes["rogue"].hp == 24

def test_the_boulder_comes_only_on_its_rounds():
    s, o = boss_state(3, rolls=[3, 3])                                   # just the ogre's melee hit
    gm_turn(s); assert s.heroes["guardian"].hp == 52 and s.heroes["mage"].hp == 28

def test_the_boulder_never_picks_a_hidden_hero():
    # Not next to the ogre: druid, mage, rogue. The mage is hidden here, so
    # the die picks from the druid and the rogue only: 2 of 2 is the rogue.
    # Then the boulder (2d6: 2, 3).
    s, o = boss_state(2, rolls=[2, 2, 3])
    s.heroes["rogue"].hidden = False; s.heroes["mage"].hidden = True
    throw(s, o, boulder(s))
    assert s.heroes["rogue"].hp == 31 and s.heroes["mage"].hp == 28

def test_a_blast_still_hits_a_hidden_hero_in_its_area():
    s, o = boss_state(3, rolls=[4, 4, 4]); announce(s); s.round = 4
    r = s.heroes["rogue"]; r.pos = (5, 5); assert r.hidden
    land_announced(s)
    assert r.hp == 36 - 12


# --- The ogre's Stomp (a step added to the frozen fight here; the real fight has it) ---

from dataclasses import replace
from fastcombat.numbers import ScriptStep
from fastcombat.fight import party_turn

STOMP = ScriptStep("stomp", "stomp", first=8, every=6, dice=(1, 6), radius=1, stun=1)

def stomp_state(rolls=None):
    s, o = boss_state(8, rolls=rolls)
    s.fight = replace(s.fight, boss_script=[*s.fight.boss_script, STOMP]); return s, o

def test_stomp_is_announced_on_the_squares_next_to_the_boss():
    s, o = stomp_state(); announce(s)
    assert o.announced.kind == "stomp" and o.announced.lands_round == 9 and o.announced.stun == 1
    assert (3, 6) in s.danger_squares() and (2, 6) not in s.danger_squares()

def test_stomp_hits_and_stuns_every_hero_next_to_the_boss():
    s, o = stomp_state(rolls=[4]); announce(s); s.round = 9
    g, r = s.heroes["guardian"], s.heroes["rogue"]; r.pos = (5, 7)  # both next to the ogre at (4, 6)
    land_announced(s)
    assert g.hp == 56 and r.hp == 32                                # one roll, a blast: no grit
    assert g.stacks["stun"].cards == 1 and r.stacks["stun"].cards == 1 and g.resource == 2
    assert "stun" not in s.heroes["mage"].stacks                    # far away

def test_a_hero_who_walked_out_of_a_stomp_is_not_stunned():
    s, o = stomp_state(rolls=[4]); announce(s); s.round = 9
    s.heroes["guardian"].pos = (2, 6); land_announced(s)
    assert "stun" not in s.heroes["guardian"].stacks

def test_a_stomp_costs_the_stunned_hero_his_next_party_turn():
    s, o = stomp_state(rolls=[4, 5]); announce(s); s.round = 9; land_announced(s)
    g = s.heroes["guardian"]; assert g.stunned
    from tests.test_fight import Plays, idle
    from fastcombat.abilities import Action
    s.round = 10; party_turn(s, idle(s, guardian=Plays(Action("auto", target="ogre1"), dest=(3, 7))))
    assert g.pos == (3, 6) and o.hp == 320 and not g.stunned        # lost the turn; the card is gone

def test_disrupt_or_a_stun_breaks_a_stomp():
    s, o = stomp_state(); announce(s)
    assert use(s, "mage", "disrupt", "ogre1") and o.announced is None
    s, o = stomp_state(); announce(s); s.round = 9
    from fastcombat.combat import control
    control(s, o, "stun", 1); land_announced(s)                     # a stun breaks a boss's cast
    assert "stun" not in s.heroes["guardian"].stacks

def test_the_real_ogre_stomps_three_times_in_twenty_rounds_never_with_another_move():
    from tests.helpers import REAL_GAME
    from fastcombat.numbers import load_fight
    f = load_fight(REAL_GAME / "fights" / "ogre_warlord.toml")
    steps = {step.name: step for step in f.boss_script}
    def rounds(step): return {r for r in range(1, 21) if r >= step.first and (r - step.first) % step.every == 0}
    stomps = rounds(steps["stomp"])
    assert 2 <= len(stomps) <= 3
    assert not stomps & (rounds(steps["ground_slam"]) | rounds(steps["skull_crusher"]))
    assert steps["stomp"].kind == "stomp" and steps["stomp"].stun >= 1
