from dataclasses import replace

from tests.helpers import state, enemy, GAME
from fastcombat.policies import default_policy, POLICIES, GuardianPolicy
from fastcombat.abilities import Action
from fastcombat.combat import damage_hero, add_stack
from fastcombat.enemy_ai import announce
from fastcombat.fight import run_fight
from fastcombat.numbers import load_numbers, load_fight

def act(s, hero):
    return default_policy(s.heroes[hero].cls).act(s, s.heroes[hero])

def elite(s, type, pos):
    # In the real fight the brute is an elite; the frozen copy has no elites, so a test makes one.
    e = enemy(s, type, pos); e.spec = replace(e.spec, tier="elite")
    return e

def test_guardian_taunts_the_boss_whenever_it_has_no_taunt_cards():
    # A boss is never held by standing next to the Guardian: only Taunt cards keep it on him.
    s = state(); o = enemy(s, "ogre", (4, 6))                         # next to the guardian at (3, 6)
    a = act(s, "guardian"); assert (a.ability, a.target) == ("taunt", "ogre1")
    o.pos = (8, 8)                                                    # 5 away, and nobody pulled it
    a = act(s, "guardian"); assert (a.ability, a.target) == ("taunt", "ogre1")
    o.pos = (10, 6)                                                   # 7 away: out of Taunt's range 6
    assert act(s, "guardian").ability != "taunt"
    o.pos = (4, 6); add_stack(o, "taunt", 1)                          # it has a Taunt card already
    assert act(s, "guardian") == Action("auto", target="ogre1")

def test_a_guardian_who_never_taunts_the_boss_is_the_same_guardian_otherwise():
    # Rule 6 switched off, for the taunt:boss check. Nothing else changes.
    def act_as(name, s): return POLICIES[name]().act(s, s.heroes["guardian"])
    s = state(); o = enemy(s, "ogre", (4, 6))                         # an untaunted boss next to him
    assert act_as("guardian", s).ability == "taunt"
    assert act_as("guardian_no_boss_taunt", s) == Action("auto", target="ogre1")
    w = enemy(s, "wolf", (5, 3))                                      # a loose add not coming for him
    a = act_as("guardian_no_boss_taunt", s); assert (a.ability, a.target) == ("taunt", "wolf1")
    assert isinstance(POLICIES["guardian_no_boss_taunt"](), GuardianPolicy)

def test_guardian_taunts_an_add_that_is_not_coming_for_him():
    s = state(); o = enemy(s, "ogre", (4, 6)); add_stack(o, "taunt", 3)   # the ogre is taunted
    w = enemy(s, "wolf", (5, 3))
    a = act(s, "guardian"); assert (a.ability, a.target) == ("taunt", "wolf1")
    w.target = "guardian"                                               # it is coming for him anyway
    assert act(s, "guardian") == Action("auto", target="ogre1")
    g = enemy(s, "goblin", (5, 4)); assert act(s, "guardian").ability != "taunt"   # fodder: any hit kills it

def test_guardian_grips_a_caster_that_shoots_from_afar_whoever_it_is_after():
    s = state(); o = enemy(s, "ogre", (4, 6)); add_stack(o, "taunt", 3)   # the ogre is taunted
    sh = enemy(s, "shaman", (6, 2)); sh.target = "guardian"
    a = act(s, "guardian"); assert (a.ability, a.target) == ("grip", "shaman1")
    sh.target = "mage"                                                # a Taunt would leave it shooting from afar
    a = act(s, "guardian"); assert (a.ability, a.target) == ("grip", "shaman1")

def test_rogue_saps_the_brute_on_round_one():
    s = state(); elite(s, "brute", (3, 4))
    a = act(s, "rogue"); assert (a.ability, a.target) == ("sap", "brute1")

def test_druid_drops_everything_for_a_downed_ally():
    s = state(); s.heroes["druid"].seeds = 1; damage_hero(s, s.heroes["mage"], 99, attacker=None)
    a = act(s, "druid"); assert (a.ability, a.target) == ("swiftmend", "mage")

def test_rogue_hauls_up_when_the_druid_has_no_seed():
    s = state(); m = s.heroes["mage"]; m.pos = (1, 5); damage_hero(s, m, 99, attacker=None)
    a = act(s, "rogue"); assert (a.kind, a.target) == ("haul_up", "mage")

def test_mage_interrupts_the_shaman_before_anything_else():
    s = state(); enemy(s, "ogre", (11, 6)); enemy(s, "shaman", (9, 5)); s.round = 2; announce(s)
    a = act(s, "mage"); assert (a.ability, a.target) == ("disrupt", "shaman1")

def test_heroes_walk_out_of_an_announced_blast():
    s = state(); enemy(s, "ogre", (4, 5)); s.round = 3; announce(s)
    r = s.heroes["rogue"]; dest = default_policy("rogue").move(s, r)
    assert dest not in s.danger_squares()

def test_any_party_plays_the_real_fight_to_an_end():
    n = load_numbers(GAME / "numbers.toml"); f = load_fight(GAME / "fights" / "ogre_warlord.toml")
    for party in (["guardian", "rogue", "druid", "mage"], ["rogue", "rogue", "mage"],
                  ["guardian", "druid"], ["mage"], ["guardian", "rogue", "druid", "mage", "mage"]):
        for seed in range(5):
            r = run_fight(n, f, party, seed=seed)
            assert 1 <= r.rounds <= n.rules["max_rounds"]     # it ended, without an error

# The numbers are first guesses and nobody wins the whole fight yet; winning
# it is the tuning task's job. So the kit is checked two other ways.
def kit_against_auto(f, seeds=30):
    n = load_numbers(GAME / "numbers.toml"); party = ["guardian", "rogue", "druid", "mage"]
    auto = {h: POLICIES["auto"]() for h in party}
    smart = [run_fight(n, f, party, seed=i) for i in range(seeds)]
    dumb = [run_fight(n, f, party, policies=auto, seed=i) for i in range(seeds)]
    return smart, dumb

def test_the_full_kit_outlasts_and_outdamages_auto_attacks():
    smart, dumb = kit_against_auto(load_fight(GAME / "fights" / "ogre_warlord.toml"))
    def damage(results): return sum(sum(r.tally.damage.values()) for r in results) / len(results)
    def rounds(results): return sum(r.rounds for r in results) / len(results)
    assert damage(smart) > damage(dumb)
    assert rounds(smart) > rounds(dumb)

def test_the_full_kit_wins_more_of_a_smaller_fight():
    f = load_fight(GAME / "fights" / "ogre_warlord.toml")
    small = replace(f, spawns=[s for s in f.spawns if s.type in ("ogre", "brute", "wolf")])
    assert [s.type for s in small.spawns] == ["ogre", "brute", "wolf", "wolf"]
    smart, dumb = kit_against_auto(small)
    assert sum(r.won for r in smart) > sum(r.won for r in dumb)


# --- More tests: the shared rules and the edges of the lists -----------------

from fastcombat.abilities import can_use
from fastcombat.policies import AutoOnly, GuardianNoBossTaunt, RoguePolicy, DruidPolicy, MagePolicy
from fastcombat.units import Announced, Cast, new_state
from fastcombat.opening import NONE, can_open

def test_the_registry_and_the_default_for_a_class_with_no_policy():
    assert POLICIES == {"guardian": GuardianPolicy, "rogue": RoguePolicy, "druid": DruidPolicy,
                        "mage": MagePolicy, "auto": AutoOnly,
                        "guardian_no_boss_taunt": GuardianNoBossTaunt}
    assert isinstance(default_policy("bard"), AutoOnly)
    assert isinstance(default_policy("druid"), DruidPolicy)

def test_no_policy_ever_asks_for_an_ability_it_cannot_use():
    n = load_numbers(GAME / "numbers.toml"); f = load_fight(GAME / "fights" / "ogre_warlord.toml")
    refused = []

    openings = []
    # The frozen copy has no elites; with the brute made one, the Rogues open on it.
    f = replace(f, enemy_types={**f.enemy_types, "brute": replace(f.enemy_types["brute"], tier="elite")})

    class Checked:
        def __init__(self, cls): self.policy = default_policy(cls)
        def move(self, s, hero): return self.policy.move(s, hero)
        def act(self, s, hero):
            a = self.policy.act(s, hero)
            if a.kind == "ability" and not can_use(s, hero, a.ability, a):
                refused.append((s.round, hero.id, a))
            return a
        def opening(self, s, hero):
            pick = getattr(self.policy, "opening", None)
            o = pick(s, hero) if pick else NONE
            openings.append(o.kind)
            if not can_open(s, hero, o):
                refused.append((0, hero.id, o))
            return o

    for party in (["guardian", "rogue", "druid", "mage", "mage"],
                  ["guardian", "rogue", "rogue", "druid", "mage"]):
        ids = list(new_state(n, f, party, seed=0).heroes)
        for seed in range(10):
            policies = {h: Checked(cls) for h, cls in zip(ids, party)}
            run_fight(n, f, party, policies=policies, seed=seed)
    assert refused == []
    assert "shadowstep" in openings and openings.count("none") < len(openings)   # openings were really made

def heavy_on_guardian(s, dice=(6, 6)):
    o = enemy(s, "ogre", (4, 6)); add_stack(o, "taunt", 3)
    o.announced = Announced("skull_crusher", "heavy", s.round + 1, "guardian", frozenset(), dice)

def test_guardian_braces_with_last_stand_when_the_heavy_hit_and_the_boss_could_drop_him():
    # 6d6 can roll 36, and then the taunted ogre hits him for up to 2d6+2 = 14: 50 in all.
    s = state(); heavy_on_guardian(s); w = s.heroes["guardian"]; w.resource = 10
    w.hp = 50; assert act(s, "guardian").ability == "last_stand"
    w.hp = 51; assert act(s, "guardian").ability != "last_stand"
    add_stack(w, "guarded", 1, 4)                                    # each of the two hits 4 smaller: at most 42
    w.hp = 42; assert act(s, "guardian").ability == "last_stand"
    w.hp = 43; assert act(s, "guardian").ability != "last_stand"
    del w.stacks["guarded"]; del s.enemies["ogre1"].stacks["taunt"]  # untaunted, it hits someone else after
    w.hp = 36; assert act(s, "guardian").ability == "last_stand"
    w.hp = 37; assert act(s, "guardian").ability != "last_stand"

def test_guardian_without_the_grit_for_last_stand_reads_on():
    s = state(); heavy_on_guardian(s); w = s.heroes["guardian"]; w.hp = 10; w.resource = 4
    assert act(s, "guardian").ability != "last_stand"

def test_a_hero_mid_cast_stays_put_unless_standing_in_danger():
    s = state(); m = s.heroes["mage"]; enemy(s, "wolf", (12, 2))
    m.cast = Cast("meteor", None, (12, 2), 1, 0, False)
    assert default_policy("mage").move(s, m) == m.pos
    s.marked["druid"] = frozenset({m.pos})                         # a blast is coming down on her
    dest = default_policy("mage").move(s, m)
    assert dest != m.pos and dest not in s.danger_squares()

def test_a_hero_next_to_a_downed_ally_stays_to_haul_them_up():
    s = state(); enemy(s, "wolf", (12, 2)); damage_hero(s, s.heroes["mage"], 99, attacker=None)
    r = s.heroes["rogue"]                                           # at (2, 5), next to the mage at (1, 5)
    assert default_policy("rogue").move(s, r) == r.pos
    s.heroes["druid"].seeds = 1                                     # now the Druid will heal her
    assert default_policy("rogue").move(s, r) != r.pos

def test_mage_meteors_three_enemies_unless_a_hero_there_cannot_walk_out():
    s = state()
    for square in ((8, 4), (8, 5), (9, 5)):
        enemy(s, "goblin", square)
    a = act(s, "mage")
    assert (a.ability, a.pos) == ("meteor", (7, 3))                 # the first square, in (x, y) order, that covers all three
    s.heroes["rogue"].pos = (6, 2)                                  # in the area, but she can walk out of it
    a = act(s, "mage"); assert (a.ability, a.pos) == ("meteor", (7, 3))
    s.heroes["guardian"].pos = (7, 4)                               # next to two of them: he is holding them there
    a = act(s, "mage"); assert (a.ability, a.pos) == ("meteor", (10, 3))   # the only square that leaves him out
    damage_hero(s, s.heroes["druid"], 99, attacker=None)
    s.heroes["druid"].pos = (10, 4)                                 # a downed hero cannot walk out either
    assert act(s, "mage").ability != "meteor"
    s = state(party=("mage",)); m = s.heroes["mage"]; m.pos = (5, 4)
    for square in ((7, 4), (7, 5), (7, 3)):
        enemy(s, "goblin", square)
    a = act(s, "mage"); assert a.ability == "meteor"
    assert max(abs(a.pos[0] - 5), abs(a.pos[1] - 4)) > 2            # never on herself: she stands still to cast

def test_druid_centres_wild_growth_to_cover_the_most_hurt_allies():
    s = state()
    for name in ("guardian", "rogue", "druid", "mage"):
        h = s.heroes[name]; h.hp = h.max_hp * 7 // 10                # every one at 70% or less
        add_stack(h, "rejuvenation", 2, 4)                          # so rule 9 does not come first
    s.heroes["druid"].resource = 10
    a = act(s, "druid")
    assert a.ability == "wild_growth"
    covered = [h for h in s.heroes.values()
               if max(abs(a.pos[0] - h.pos[0]), abs(a.pos[1] - h.pos[1])) <= 2]
    assert len(covered) == 4


# --- The controller's rulings: Shadowstep, Shadowmeld, and fodder ------------

def test_rogue_shadowsteps_to_a_focus_past_her_move_but_in_reach():
    s = state()                                                     # the Rogue is at (2, 5); move 6, Shadowstep range 8
    w = enemy(s, "wolf", (9, 5))                                    # 7 away
    a = act(s, "rogue"); assert (a.ability, a.target) == ("shadowstep", "wolf1")
    w.pos = (8, 5)                                                  # 6 away: she can walk there
    assert act(s, "rogue").ability != "shadowstep"
    w.pos = (11, 5)                                                 # 9 away: out of Shadowstep's range
    assert act(s, "rogue").ability != "shadowstep"

def test_druid_shadowmelds_only_from_an_enemy_that_can_reach_her():
    s = state(); w = enemy(s, "wolf", (2, 8))                       # next to the Druid at (1, 7)
    assert act(s, "druid").ability == "shadowmeld"
    add_stack(w, "rooted", 1)                                       # rooted: it cannot come at her
    assert act(s, "druid").ability != "shadowmeld"
    del w.stacks["rooted"]; add_stack(w, "sap", 2)                  # controlled: it does nothing
    assert act(s, "druid").ability != "shadowmeld"
    del w.stacks["sap"]; w.pos = (15, 0); w.pulled_by = "druid"     # pulled, but 14 away: move 7 + range 1 is too short
    assert act(s, "druid").ability != "shadowmeld"
    w.pos = (9, 7)                                                  # pulled, 8 away: it can just reach her
    assert act(s, "druid").ability == "shadowmeld"

def test_rogue_auto_attacks_fodder_and_saves_eviscerate_for_a_real_enemy():
    s = state(); r = s.heroes["rogue"]; r.hidden = False; r.combo = 5
    enemy(s, "goblin", (3, 4))                                      # next to the Rogue at (2, 5)
    a = act(s, "rogue"); assert (a.kind, a.target) == ("auto", "goblin1")
    enemy(s, "brute", (3, 5))                                       # also next to her, more HP than the goblin
    a = act(s, "rogue"); assert (a.ability, a.target) == ("eviscerate", "brute1")

def test_rogue_does_not_backstab_fodder_from_hiding():
    s = state(); enemy(s, "goblin", (3, 4))                         # the Rogue starts hidden
    a = act(s, "rogue"); assert (a.kind, a.target) == ("auto", "goblin1")

def test_mage_auto_attacks_fodder_and_firebolts_a_real_enemy():
    s = state(); enemy(s, "goblin", (8, 5))                         # 7 from the Mage at (1, 5)
    a = act(s, "mage"); assert (a.kind, a.target) == ("auto", "goblin1")
    enemy(s, "ogre", (11, 6))                                       # 10 away: in Firebolt's range
    a = act(s, "mage"); assert (a.ability, a.target) == ("firebolt", "ogre1")


# --- Before tuning: the heroes play sensibly -----------------------------------

from fastcombat.abilities import Action, use_ability

def test_rogue_walks_to_her_ability_focus_not_to_fodder():
    s = state(); r = s.heroes["rogue"]                              # at (2, 5), move 6
    enemy(s, "goblin", (2, 10))                                     # the focus: 1 HP
    w = enemy(s, "wolf", (8, 5))                                    # the ability focus: not fodder
    dest = default_policy("rogue").move(s, r)
    assert max(abs(dest[0] - w.pos[0]), abs(dest[1] - w.pos[1])) == 1
    w.dead = True                                                   # no ability focus left
    dest = default_policy("rogue").move(s, r)
    assert max(abs(dest[0] - 2), abs(dest[1] - 10)) == 1            # so she goes for the goblin

def test_rogue_waits_for_shadowstep_when_walking_is_too_short():
    s = state(); r = s.heroes["rogue"]                              # at (2, 5), move 6, Shadowstep range 8
    w = enemy(s, "wolf", (10, 5))                                   # 8 away: a walk ends 2 short
    assert default_policy("rogue").move(s, r) == r.pos              # she stays...
    a = act(s, "rogue"); assert (a.ability, a.target) == ("shadowstep", "wolf1")   # ...and steps in
    w.pos = (9, 5)                                                  # 7 away: she can walk next to it
    assert default_policy("rogue").move(s, r) == (8, 5)
    w.pos = (11, 5)                                                 # 9 away: out of Shadowstep's range
    assert default_policy("rogue").move(s, r) != r.pos
    w.pos = (10, 5); r.resource = 0                                 # in range, but she cannot pay
    assert default_policy("rogue").move(s, r) != r.pos

def mending_shaman(s, pos):
    sh = enemy(s, "shaman", pos)
    sh.announced = Announced("mend", "mend", s.round + 1, None, frozenset(), (0, 0), 25)
    return sh

def test_mage_does_not_disrupt_a_caster_that_is_already_stopped():
    s = state(); enemy(s, "ogre", (11, 6))
    sh1 = mending_shaman(s, (9, 5)); add_stack(sh1, "sheep", 4)     # a sheep's mend fizzles anyway
    assert act(s, "mage").ability != "disrupt"
    mending_shaman(s, (9, 7))                                       # this one is free
    a = act(s, "mage"); assert (a.ability, a.target) == ("disrupt", "shaman2")

def test_guardian_does_not_disrupt_a_caster_that_is_already_stopped():
    s = state(); sh = mending_shaman(s, (4, 6))                     # next to the Guardian at (3, 6)
    assert act(s, "guardian").ability == "disrupt"
    add_stack(sh, "sap", 2)
    assert act(s, "guardian").ability != "disrupt"

def test_rogue_does_not_disrupt_or_cheap_shot_a_caster_that_is_already_stopped():
    s = state(); r = s.heroes["rogue"]; r.hidden = False
    sh = mending_shaman(s, (3, 4))                                  # next to the Rogue at (2, 5)
    assert act(s, "rogue").ability == "disrupt"
    add_stack(sh, "stun", 1)
    assert act(s, "rogue").ability not in ("disrupt", "cheap_shot")

def test_two_mages_do_not_polymorph_the_same_enemy():
    s = state(("mage", "mage")); enemy(s, "brute", (10, 7)); enemy(s, "wolf", (10, 3))
    a = act(s, "mage"); assert (a.ability, a.target) == ("polymorph", "brute1")
    use_ability(s, s.heroes["mage"], a)                             # her sheep is on its way
    assert act(s, "mage2").ability != "polymorph"

def test_two_mages_fall_so_fast_that_the_second_meteor_may_never_land():
    # Two Mages alone lose in 3 or 4 rounds. In round 1 "mage" (first by id)
    # takes the Polymorph and "mage2" starts a Meteor, which lands in round 3.
    # In round 2 "mage" starts her own Meteor, which lands in round 4 only if
    # she is still up then. In a 3-round fight she is not, so one Mage doing
    # no damage is the fight being short, not a Mage that cannot play.
    # (Before the Polymorph fix, it was "mage2" who did nothing: both cast
    # the same Polymorph in round 1. Since the Mage backs off as far as she
    # can, "mage" sometimes lasts until round 4 and her Meteor lands.)
    n = load_numbers(GAME / "numbers.toml"); f = load_fight(GAME / "fights" / "ogre_warlord.toml")
    for seed in range(3):
        r = run_fight(n, f, ["mage", "mage"], seed=seed)
        assert not r.won and r.rounds <= 4 and r.tally.damage["mage2"] > 0
        if r.rounds == 3:
            assert r.tally.damage["mage"] == 0


# --- The final review: the Mage's standing square and the Rogue's rule 10 -------

def test_mage_backs_off_as_far_as_she_can_when_nowhere_is_five_away():
    s = state(party=("mage",)); m = s.heroes["mage"]               # at (1, 5), move 6
    for square in ((4, 0), (4, 5), (4, 11)):                        # every square in reach is 4 or less from one
        enemy(s, "wolf", square)
    dest = default_policy("mage").move(s, m)
    assert dest == (0, 4)                                           # 4 from the nearest wolf, one step away

def test_mage_counts_five_or_more_from_every_enemy_as_the_same():
    s = state(party=("mage",)); m = s.heroes["mage"]
    enemy(s, "wolf", (6, 5))                                        # already 5 away: farther is no better
    assert default_policy("mage").move(s, m) == m.pos

def test_rogue_hits_an_enemy_next_to_her_when_her_focus_is_far_away():
    s = state(); r = s.heroes["rogue"]; r.hidden = False; r.resource = 0   # no abilities, only auto-attacks
    enemy(s, "goblin", (12, 10))                                    # the focus: 1 HP, far away
    enemy(s, "brute", (3, 4)); enemy(s, "wolf", (2, 4))             # both next to her at (2, 5)
    assert act(s, "rogue") == Action("auto", target="wolf1")        # the ability focus, next to her
    s.enemies["wolf1"].pos = (10, 10)                               # the ability focus is far away too
    assert act(s, "rogue") == Action("auto", target="brute1")       # the weakest enemy next to her
    add_stack(s.enemies["brute1"], "stun", 1)
    assert act(s, "rogue") == Action("none")

def test_rogue_waits_for_shadowstep_only_if_she_could_still_use_it_after_stepping_out_of_danger():
    from fastcombat.grid import within
    s = state(); r = s.heroes["rogue"]                              # at (2, 5), move 6, Shadowstep range 8
    enemy(s, "wolf", (10, 5))                                       # 8 away: a walk ends 2 short
    s.marked["mage"] = frozenset(within((2, 5), 1, 16, 12))         # a blast is coming down on her
    # Stepping out of it puts her at (0, 3), 10 from the wolf: too far to Shadowstep.
    # So she walks toward the wolf instead of waiting.
    assert default_policy("rogue").move(s, r) == (8, 5)


# --- Bosses ignore the hold: the Rogue's Eviscerate on the boss -----------------

def test_rogue_eviscerates_the_boss_only_while_it_has_taunt_cards():
    s = state(); r = s.heroes["rogue"]; r.hidden = False; r.combo = 5
    o = enemy(s, "ogre", (3, 4))                                    # next to the Rogue at (2, 5)
    assert act(s, "rogue").ability != "eviscerate"                  # no Taunt cards: it would turn on her
    add_stack(o, "taunt", 2)
    a = act(s, "rogue"); assert (a.ability, a.target) == ("eviscerate", "ogre1")


# --- Every button for an MMO player's reason -------------------------------------

from fastcombat.grid import adjacent, distance, within
from fastcombat.units import Enemy

def quiet_volley(s):
    # The real numbers have a quiet Arcane Volley; the frozen copy still has a Loud one.
    s.numbers.abilities["arcane_volley"] = replace(s.numbers.abilities["arcane_volley"], loud=False)

def slam_coming(s, guardian_at=(4, 6), boss_at=(5, 6)):
    # The ogre announced a Ground Slam last GM turn: it lands this round, within 2 of the ogre.
    o = enemy(s, "ogre", boss_at); add_stack(o, "taunt", 3)
    s.heroes["guardian"].pos = guardian_at
    o.announced = Announced("ground_slam", "blast", s.round, None, frozenset(within(boss_at, 2, 16, 12)), (3, 6))
    return o

def test_guardian_plants_his_shield_against_a_slam_instead_of_stepping_out():
    s = state(); o = slam_coming(s); g = s.heroes["guardian"]; g.resource = 4
    assert default_policy("guardian").move(s, g) == (4, 6)          # he stays next to the boss
    a = act(s, "guardian"); assert (a.ability, a.pos) == ("shield_plant", (5, 6))
    g.resource = 3                                                   # he cannot pay for it: he steps out
    assert default_policy("guardian").move(s, g) not in s.danger_squares()
    a = act(s, "guardian"); assert (a.ability, a.target) == ("disrupt", "ogre1")   # still next to it: free
    g.resource = 4; del o.stacks["taunt"]                            # the boss is loose: Taunt it from outside
    g.pos = default_policy("guardian").move(s, g)
    assert g.pos not in s.danger_squares()
    a = act(s, "guardian"); assert (a.ability, a.target) == ("taunt", "ogre1")

def test_an_ally_behind_the_planted_shield_stays_where_she_is():
    s = state(); o = slam_coming(s); s.heroes["guardian"].resource = 4
    r = s.heroes["rogue"]; r.hidden = False; r.pos = (3, 4)         # 2 from the ogre: in the slam, behind the Guardian
    w = enemy(s, "wolf", (4, 4))                                    # her focus, next to her
    assert r.pos in s.danger_squares()
    assert default_policy("rogue").move(s, r) == (3, 4)             # the shield covers her: she keeps hitting
    s.heroes["guardian"].resource = 3                               # no shield coming: she runs
    dest = default_policy("rogue").move(s, r)
    assert dest not in s.danger_squares() and adjacent(dest, w.pos)

def test_nobody_interrupts_a_boss_cast_the_guardian_has_answered():
    s = state(); o = slam_coming(s); g = s.heroes["guardian"]
    r = s.heroes["rogue"]; r.hidden = False; r.pos = (6, 6)         # next to the ogre
    assert (act(s, "mage").ability, act(s, "rogue").ability) == ("disrupt", "disrupt")
    add_stack(g, "shield_plant", 1, 8)                              # he planted his shield against it
    assert act(s, "mage").ability != "disrupt" and act(s, "rogue").ability != "disrupt"
    o.announced = Announced("skull_crusher", "heavy", s.round, "guardian", frozenset(), (6, 6))
    assert act(s, "mage").ability == "disrupt"
    add_stack(g, "last_stand", 1)                                   # he braced for it
    assert act(s, "mage").ability != "disrupt"

def test_guardian_keeps_grit_for_intercede_while_an_ally_is_low():
    s = state(); o = enemy(s, "ogre", (4, 6)); add_stack(o, "taunt", 3)
    w = enemy(s, "wolf", (6, 2)); w.target = "mage"                 # loose, going for the Mage
    g = s.heroes["guardian"]; g.resource = 2                        # Taunt costs 1, Intercede 2
    s.heroes["druid"].hp = 20                                       # 20 of 36: 60% or less, and nothing is after her
    assert act(s, "guardian") == Action("auto", target="ogre1")     # a Taunt would leave too little to Intercede
    g.resource = 3
    a = act(s, "guardian"); assert (a.ability, a.target) == ("taunt", "wolf1")

def test_guardian_keeps_no_grit_for_a_heavy_hit_nobody_has_announced():
    # Round 5: the script will announce Skull Crusher this GM turn, but only the GM knows that.
    s = state(); s.round = 5
    o = enemy(s, "ogre", (4, 6)); add_stack(o, "taunt", 3)
    w = enemy(s, "wolf", (6, 2)); w.target = "mage"
    g = s.heroes["guardian"]; g.resource = 5; g.hp = 50             # 36 and then 14 could drop him
    a = act(s, "guardian"); assert (a.ability, a.target) == ("taunt", "wolf1")
    o.announced = Announced("skull_crusher", "heavy", s.round + 1, "guardian", frozenset(), (6, 6))
    assert act(s, "guardian").ability == "last_stand"               # now everyone can see it coming

def test_guardian_intercedes_for_an_ally_at_sixty_percent():
    s = state(); o = enemy(s, "ogre", (1, 8)); o.target = "druid"   # no Taunt cards, after the Druid
    d = s.heroes["druid"]
    d.hp = 22; assert act(s, "guardian").ability != "intercede"     # 22 of 36 is more than 60%
    d.hp = 21; a = act(s, "guardian"); assert (a.ability, a.target) == ("intercede", "druid")

def test_guardian_shouts_at_two_loose_adds_going_for_his_allies():
    s = state(); o = enemy(s, "ogre", (8, 8)); add_stack(o, "taunt", 3)
    s.heroes["guardian"].resource = 3                               # at (3, 6)
    g1 = enemy(s, "goblin", (5, 4)); g1.target = "mage"
    g2 = enemy(s, "goblin", (6, 6)); g2.target = "druid"            # both within 3 of him, neither next to him
    assert act(s, "guardian").ability == "challenging_shout"
    g2.target = "guardian"                                          # one is coming for him anyway
    assert act(s, "guardian").ability != "challenging_shout"

def test_guardian_grips_a_wolf_that_ran_past_him_onto_a_squishy_hero():
    s = state(); o = enemy(s, "ogre", (4, 6)); add_stack(o, "taunt", 3)
    w = enemy(s, "wolf", (2, 4)); w.target = "mage"                 # next to the Mage at (1, 5)
    a = act(s, "guardian"); assert (a.ability, a.target) == ("grip", "wolf1")
    w.pos = (6, 2)                                                  # not on her yet: a Taunt will do
    a = act(s, "guardian"); assert (a.ability, a.target) == ("taunt", "wolf1")

def test_rogue_saps_the_most_dangerous_elite_whenever_she_is_hidden():
    s = state(); s.round = 7; r = s.heroes["rogue"]                 # hidden (as after a Vanish), at (2, 5)
    b = elite(s, "brute", (3, 4))                                   # an elite that hits for 6
    w = elite(s, "wolf", (2, 4))                                    # an elite that hits for 4
    a = act(s, "rogue"); assert (a.ability, a.target) == ("sap", "brute1")
    add_stack(b, "sap", 4)                                          # the brute is out already
    a = act(s, "rogue"); assert (a.ability, a.target) == ("sap", "wolf1")
    r.hidden = False
    assert act(s, "rogue").ability != "sap"

def test_rogue_shadowsteps_to_the_elite_to_sap_and_waits_hidden_when_she_cannot_reach_it():
    s = state(); r = s.heroes["rogue"]                              # hidden at (2, 5); move 6, Shadowstep 8
    b = elite(s, "brute", (10, 5))                                  # 8 away
    assert default_policy("rogue").move(s, r) == r.pos              # she waits for Shadowstep...
    a = act(s, "rogue"); assert (a.ability, a.target) == ("shadowstep", "brute1")
    use_ability(s, r, a)
    assert r.hidden and adjacent(r.pos, b.pos)                      # ...and is still hidden, next to it
    r.pos = (2, 5); b.pos = (12, 5)                                 # 10 away: too far for Shadowstep
    assert act(s, "rogue") == Action("none")                        # she walks there, and stays hidden

def test_rogue_vanishes_from_the_boss_or_when_low_and_chased():
    s = state(); r = s.heroes["rogue"]; r.hidden = False
    o = enemy(s, "ogre", (3, 4)); o.target = "rogue"                # the boss went for her
    assert act(s, "rogue").ability == "vanish"
    o.target = "guardian"; b = elite(s, "brute", (2, 4)); b.target = "rogue"
    assert act(s, "rogue").ability != "vanish"                      # an elite, and she is at full HP: she fights it
    r.hp = 14                                                       # 14 of 36: 40% or less
    assert act(s, "rogue").ability == "vanish"

def test_rogue_kidney_shots_an_add_hurting_someone_and_eviscerates_an_elite():
    s = state(); r = s.heroes["rogue"]; r.hidden = False; r.combo = 5
    w = enemy(s, "wolf", (3, 4)); w.target = "druid"                # next to her, going for the Druid
    b = elite(s, "brute", (2, 4)); b.target = "guardian"
    a = act(s, "rogue"); assert (a.ability, a.target) == ("kidney_shot", "wolf1")
    w.target = "guardian"                                           # now both are on the Guardian
    a = act(s, "rogue"); assert (a.ability, a.target) == ("eviscerate", "brute1")   # the elite, not the focus

def test_rogue_cheap_shots_an_add_on_a_squishy_hero_who_is_hurt():
    s = state(); r = s.heroes["rogue"]; r.hidden = False
    m = s.heroes["mage"]; w = enemy(s, "wolf", (2, 4)); w.target = "mage"   # next to her and to the Mage
    assert act(s, "rogue").ability != "cheap_shot"                  # the Mage is at full HP
    m.hp = 14                                                       # half of 28
    a = act(s, "rogue"); assert (a.ability, a.target) == ("cheap_shot", "wolf1")

def test_rogue_with_full_combo_points_walks_to_an_elite():
    s = state(); r = s.heroes["rogue"]; r.hidden = False; r.combo = 5   # at (2, 5)
    w = enemy(s, "wolf", (2, 9)); b = elite(s, "brute", (7, 5))     # the wolf has less HP: it is the focus
    assert adjacent(default_policy("rogue").move(s, r), b.pos)
    r.combo = 4
    assert adjacent(default_policy("rogue").move(s, r), w.pos)

def test_druid_wild_growths_two_hurt_allies():
    s = state(); s.heroes["guardian"].hp = 36                       # 60%, at (3, 6)
    add_stack(s.heroes["guardian"], "rejuvenation", 2, 4)
    assert act(s, "druid").ability == "regrowth"                    # one hurt ally: a Regrowth
    s.heroes["rogue"].hp = 21                                       # 58%, at (2, 5)
    assert act(s, "druid").ability == "wild_growth"

def test_mage_volleys_her_focus_and_saves_mana_when_she_cannot_pay_for_all_of_it():
    s = state(); quiet_volley(s); enemy(s, "ogre", (11, 6))        # 10 from the Mage at (1, 5)
    a = act(s, "mage"); assert (a.ability, a.target) == ("arcane_volley", "ogre1")
    s.heroes["mage"].resource = 5                                   # three hits cost 6
    assert act(s, "mage") == Action("auto", target="ogre1")

def test_a_loud_volley_goes_only_on_a_well_taunted_focus_and_firebolt_takes_the_rest():
    s = state(); o = enemy(s, "ogre", (11, 6))                      # the frozen copy's Volley is Loud
    a = act(s, "mage"); assert (a.ability, a.target) == ("firebolt", "ogre1")
    add_stack(o, "taunt", 3)
    a = act(s, "mage"); assert (a.ability, a.target) == ("arcane_volley", "ogre1")

def test_mage_firebolts_an_add_one_big_hit_would_finish():
    s = state(); quiet_volley(s); w = enemy(s, "wolf", (9, 5))     # Volley hits for 7 on average, Firebolt for 14
    w.hp = 14; a = act(s, "mage"); assert (a.ability, a.target) == ("firebolt", "wolf1")
    w.hp = 15; assert act(s, "mage").ability == "arcane_volley"
    w.hp = 7; assert act(s, "mage").ability == "arcane_volley"

def test_mage_uses_frost_nova_on_an_add_and_blinks_away_from_a_boss_or_a_rooted_add():
    s = state(party=("mage",)); m = s.heroes["mage"]; m.pos = (5, 5)
    w = enemy(s, "wolf", (6, 5))
    assert act(s, "mage").ability == "frost_nova"
    add_stack(w, "rooted", 1)                                       # it cannot follow her, but it can still bite
    a = act(s, "mage"); assert a.ability == "blink" and distance(a.pos, w.pos) > 1
    w.dead = True; o = enemy(s, "ogre", (6, 6))                     # Frost Nova would not stop a boss's hits
    a = act(s, "mage"); assert a.ability == "blink"
    assert distance(a.pos, o.pos) > o.spec.move + o.spec.range      # out of its reach this GM turn

def test_mage_breaks_her_channel_to_disrupt_a_mend_before_a_boss_cast():
    s = state(); quiet_volley(s); enemy(s, "ogre", (11, 6)); s.round = 3; announce(s)   # a Ground Slam
    mending_shaman(s, (9, 5))
    s.heroes["mage"].cast = Cast("arcane_volley", "ogre1", None, 0, 2, True)
    a = act(s, "mage"); assert (a.ability, a.target) == ("disrupt", "shaman1")

def test_mage_quickens_once_when_the_boss_is_taunted_and_again_for_the_burn():
    s = state(); s.round = 5; o = enemy(s, "ogre", (11, 6))
    assert act(s, "mage").ability != "quicken"                      # the boss is not taunted
    add_stack(o, "taunt", 3)
    assert act(s, "mage").ability == "quicken"
    s.tally.count_use("mage", "quicken")                            # she has Quickened once
    assert act(s, "mage").ability != "quicken"
    o.hp = o.spec.hp * 35 // 100                                    # 35%: the burn at the end
    assert act(s, "mage").ability == "quicken"
    s.tally.count_use("mage", "quicken")
    assert act(s, "mage").ability != "quicken"                      # never a third


# --- The D3 review: only what the table sees, and the gaps it found ----------------

from fastcombat.grid import behind
from fastcombat.policies import HIDDEN_WAIT_ROUNDS

def test_rogue_saps_an_elite_with_more_than_half_its_hp_and_backstabs_a_hurt_one():
    s = state(); s.round = 7; r = s.heroes["rogue"]                 # hidden (as after a Vanish), at (2, 5)
    b = elite(s, "brute", (3, 4))                                   # 30 HP
    b.hp = 16; a = act(s, "rogue"); assert (a.ability, a.target) == ("sap", "brute1")
    b.hp = 15; a = act(s, "rogue"); assert (a.ability, a.target) == ("backstab", "brute1")   # half: not worth a Sap
    w = elite(s, "wolf", (2, 4))                                    # a healthy elite is worth the Sap more
    a = act(s, "rogue"); assert (a.ability, a.target) == ("sap", "wolf1")

def test_rogue_waits_hidden_for_an_elite_out_of_reach_only_so_long():
    s = state(); r = s.heroes["rogue"]; p = RoguePolicy()           # hidden at (2, 5); move 6, Shadowstep 8
    b = elite(s, "brute", (12, 5))                                  # 10 away: too far to Shadowstep
    w = enemy(s, "wolf", (3, 4))                                    # her focus, next to her
    assert HIDDEN_WAIT_ROUNDS == 2
    for s.round in (1, 2):
        assert distance(p.move(s, r), b.pos) == 4                   # she walks toward the elite...
        assert p.act(s, r) == Action("none")                        # ...and waits, hidden
    s.round = 3                                                     # two rounds waited: she gives up on it
    assert p.move(s, r) == r.pos                                    # she stays by her focus instead
    a = p.act(s, r); assert (a.ability, a.target) == ("backstab", "wolf1")
    s.round = 4; b.pos = (8, 5)                                     # the elite came in reach of a walk
    assert adjacent(p.move(s, r), b.pos)
    s.round = 6                                                     # hidden again later: a new wait
    b.pos = (12, 5)
    assert p.act(s, r) == Action("none")

def test_rogue_waits_again_for_a_new_elite_after_giving_up_on_another():
    s = state(); r = s.heroes["rogue"]; p = RoguePolicy()
    b = elite(s, "brute", (12, 5)); enemy(s, "wolf", (3, 4))
    for s.round in (1, 2, 3):
        p.act(s, r)
    a = p.act(s, r); assert a.ability == "backstab"                  # she gave up on the brute
    b.dead = True; elite(s, "brute", (12, 6))                        # a new elite, as far away
    assert p.act(s, r) == Action("none")                            # it gets its own wait

def test_rogue_forgets_her_waits_when_a_new_fight_starts():
    s = state(); r = s.heroes["rogue"]; p = RoguePolicy()
    b = elite(s, "brute", (12, 5)); enemy(s, "wolf", (3, 4))
    for s.round in (2, 3, 4):
        p.act(s, r)
    assert p.act(s, r).ability == "backstab"                        # gave up on brute1, in round 4
    s.round = 1; b.dead = True                                      # a new fight, with no elite at first
    p.act(s, r)
    s.round = 4; b.dead = False                                     # the elite turns up in round 4
    assert p.act(s, r) == Action("none")                            # a fresh wait, not the old one

def test_rogue_stops_a_cast_with_kidney_shot_when_disrupt_is_cooling_down():
    s = state(); r = s.heroes["rogue"]; r.hidden = False; r.combo = 5
    sh = mending_shaman(s, (3, 4))                                  # next to the Rogue at (2, 5)
    assert act(s, "rogue").ability == "disrupt"
    add_stack(r, "cd:disrupt", 2)                                   # Disrupt is cooling down
    a = act(s, "rogue"); assert (a.ability, a.target) == ("kidney_shot", "shaman1")
    r.combo = 4                                                     # not full: a Kidney Shot is no better
    a = act(s, "rogue"); assert (a.ability, a.target) == ("cheap_shot", "shaman1")

def test_rogue_never_kidney_shots_fodder():
    s = state(); r = s.heroes["rogue"]; r.hidden = False; r.combo = 5
    gob = enemy(s, "goblin", (3, 4)); gob.target = "druid"          # next to her, going for the Druid
    assert act(s, "rogue").ability != "kidney_shot"
    gob.announced = Announced("mend", "mend", s.round + 1, None, frozenset(), (0, 0), 25)
    add_stack(r, "cd:disrupt", 2)                                   # a casting goblin, and no Disrupt
    a = act(s, "rogue"); assert (a.ability, a.target) == ("cheap_shot", "goblin1")

def test_rogue_vanishes_from_a_pull_only_when_it_is_dangerous():
    s = state(); r = s.heroes["rogue"]; r.hidden = False             # at (2, 5), full HP
    gob = enemy(s, "goblin", (3, 4)); gob.pulled_by = "rogue"
    w = enemy(s, "wolf", (2, 4)); w.pulled_by = "rogue"
    assert act(s, "rogue").ability != "vanish"                      # a goblin and a wolf: she fights them
    b = elite(s, "brute", (1, 4)); b.pulled_by = "rogue"
    assert act(s, "rogue").ability == "vanish"                      # an elite is dangerous
    add_stack(b, "stun", 1)
    assert act(s, "rogue").ability != "vanish"                      # not while it is stunned
    r.hp = 14                                                       # 40% or less, with enemies next to her
    assert act(s, "rogue").ability == "vanish"

def test_mage_never_meteors_a_sapped_or_sheeped_enemy_awake():
    s = state()
    for square in ((8, 4), (8, 5), (9, 5)):
        enemy(s, "goblin", square)
    w = enemy(s, "wolf", (9, 4)); add_stack(w, "sap", 4)           # every square that covers the goblins covers it
    assert act(s, "mage").ability != "meteor"
    del w.stacks["sap"]; add_stack(w, "sheep", 4)
    assert act(s, "mage").ability != "meteor"
    del w.stacks["sheep"]; add_stack(w, "stun", 1)                  # a stun does not break when it is hit
    a = act(s, "mage"); assert (a.ability, a.pos) == ("meteor", (7, 3))

def test_the_druid_moves_before_the_guardian_and_still_stays_behind_his_shield():
    s = state(); slam_coming(s); g = s.heroes["guardian"]; g.resource = 4
    d = s.heroes["druid"]; d.pos = (3, 6)                           # in the slam, behind the Guardian at (4, 6)
    assert d.pos in s.danger_squares() and d.pos in behind(g.pos, (5, 6), s.numbers.abilities["shield_plant"].radius, 16, 12)
    d.cast = Cast("regrowth", "guardian", None, 1, 0, False)        # mid-cast: she stays put if she is safe
    assert sorted(s.heroes).index("druid") < sorted(s.heroes).index("guardian")
    assert default_policy("druid").move(s, d) == (3, 6)             # the plan covers her: she stays
    g.resource = 3                                                  # no shield coming: she gets out
    assert default_policy("druid").move(s, d) not in s.danger_squares()


# --- The Rogue's opening, and not breaking our own Sap or sheep ----------------

from fastcombat.opening import NONE, Opening, can_open

def test_rogue_opens_by_shadowstepping_in_next_to_the_elite_that_hits_hardest():
    s = state(); r = s.heroes["rogue"]
    elite(s, "wolf", (10, 3)); elite(s, "brute", (10, 7)); enemy(s, "shaman", (13, 3))
    o = RoguePolicy().opening(s, r)
    assert o == Opening("shadowstep", "brute1") and can_open(s, r, o)   # the brute hits for 6, the wolf for 4

def test_rogue_has_no_opening_without_an_elite_or_only_on_a_boss():
    s = state(); r = s.heroes["rogue"]
    enemy(s, "ogre", (11, 6)); enemy(s, "wolf", (10, 3))
    assert RoguePolicy().opening(s, r) == NONE

def test_rogue_sneaks_when_shadowstepping_in_would_leave_her_short_of_the_sap():
    s = state(); r = s.heroes["rogue"]; elite(s, "brute", (10, 7))
    r.resource = 2                                                  # 2 - 2 + 3 back in round 1 = 3: a Sap
    assert RoguePolicy().opening(s, r).kind == "shadowstep"
    r.resource = 1                                                  # cannot pay for Shadowstep
    assert RoguePolicy().opening(s, r) == Opening("sneak", "brute1")
    s.numbers.abilities["sap"] = replace(s.numbers.abilities["sap"], cost=4)
    r.resource = 2                                                  # 3 in round 1 is not a Sap at 4
    assert RoguePolicy().opening(s, r).kind == "sneak"

def test_a_second_rogue_leaves_the_elite_the_first_one_is_next_to():
    s = state(("rogue", "rogue")); b = elite(s, "brute", (10, 7)); w = elite(s, "wolf", (10, 3))
    s.heroes["rogue"].pos = (9, 7)                                  # the first Rogue opened next to the brute
    assert RoguePolicy().opening(s, s.heroes["rogue2"]) == Opening("shadowstep", "wolf1")
    w.pos = (9, 6)                                                  # she is next to both now
    assert RoguePolicy().opening(s, s.heroes["rogue2"]) == NONE

def test_after_the_opening_round_1_is_a_sap():
    s = state(); r = s.heroes["rogue"]; b = elite(s, "brute", (10, 7))
    from fastcombat.opening import open_fight
    open_fight(s, r, RoguePolicy().opening(s, r))
    assert default_policy("rogue").move(s, r) == r.pos
    a = act(s, "rogue"); assert (a.ability, a.target) == ("sap", "brute1")

def test_nobody_hits_a_sapped_or_sheeped_enemy_while_anything_else_is_left():
    s = state(); quiet_volley(s)
    b = enemy(s, "brute", (4, 7)); add_stack(b, "sap", 20)          # next to the Guardian at (3, 6)
    w = enemy(s, "wolf", (10, 9)); add_stack(w, "stun", 1)         # 9 from the Mage at (1, 5)
    assert act(s, "guardian").kind == "none"                        # nothing awake next to him
    a = act(s, "mage"); assert (a.ability, a.target) == ("arcane_volley", "wolf1")   # the stunned wolf first
    w.dead = True                                                   # only the sapped brute is left: hit it
    assert act(s, "guardian") == Action("auto", target="brute1")
    a = act(s, "mage"); assert (a.ability, a.target) == ("arcane_volley", "brute1")

def test_mage_ends_a_volley_whose_enemy_was_sapped_after_it_began():
    s = state(); quiet_volley(s); m = s.heroes["mage"]
    w = enemy(s, "wolf", (8, 5)); enemy(s, "wolf", (9, 8))
    m.cast = Cast("arcane_volley", "wolf1", None, 0, 2, True)       # two hits to come on wolf1
    assert act(s, "mage") == Action("continue")
    add_stack(w, "sap", 20)                                         # the Rogue sapped it
    a = act(s, "mage"); assert a.kind != "continue" and a.target != "wolf1"

def test_mage_keeps_channelling_on_a_sapped_enemy_when_it_is_the_only_one_left():
    s = state(); quiet_volley(s); m = s.heroes["mage"]
    w = enemy(s, "wolf", (8, 5)); add_stack(w, "sap", 20)
    m.cast = Cast("arcane_volley", "wolf1", None, 0, 2, True)       # nothing else to hit
    assert act(s, "mage") == Action("continue")
    w2 = enemy(s, "wolf", (9, 8)); add_stack(w2, "sheep", 12)       # every enemy left is asleep
    assert act(s, "mage") == Action("continue")

def test_rogue_does_not_sap_an_elite_a_hit_is_on_its_way_to():
    s = state(); r = s.heroes["rogue"]; b = elite(s, "brute", (3, 4))   # next to her at (2, 5), hidden
    s.heroes["mage"].cast = Cast("firebolt", "brute1", None, 0, 0, False)   # lands at the top of next turn
    a = act(s, "rogue"); assert (a.ability, a.target) == ("backstab", "brute1")
    s.heroes["mage"].cast = None
    s.marked["mage"] = frozenset(within((4, 4), 2, 16, 12))         # a Meteor is coming down on it
    assert act(s, "rogue").ability == "backstab"
    del s.marked["mage"]
    assert act(s, "rogue").ability == "sap"

def test_mage_does_not_sheep_an_enemy_a_meteor_is_coming_down_on():
    s = state(); enemy(s, "shaman", (9, 3)); enemy(s, "wolf", (9, 8))
    a = act(s, "mage"); assert (a.ability, a.target) == ("polymorph", "shaman1")
    s.marked["mage2"] = frozenset(within((9, 3), 2, 16, 12))        # another Mage's Meteor
    a = act(s, "mage"); assert (a.ability, a.target) == ("polymorph", "wolf1")
