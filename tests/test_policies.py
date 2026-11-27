from dataclasses import replace

from tests.helpers import state, enemy, GAME
from fastcombat.policies import default_policy, POLICIES, WardenPolicy
from fastcombat.abilities import Action
from fastcombat.combat import damage_hero, add_stack
from fastcombat.enemy_ai import announce
from fastcombat.fight import run_fight
from fastcombat.numbers import load_numbers, load_fight

def act(s, hero):
    return default_policy(s.heroes[hero].cls).act(s, s.heroes[hero])

def test_warden_challenges_the_boss_whenever_it_has_no_taunt_cards():
    # A boss is never held by standing next to the Warden: only Taunt cards keep it on him.
    s = state(); o = enemy(s, "ogre", (4, 6))                         # next to the warden at (3, 6)
    a = act(s, "warden"); assert (a.ability, a.target) == ("challenge", "ogre1")
    o.pos = (8, 8)                                                    # 5 away, and nobody pulled it
    a = act(s, "warden"); assert (a.ability, a.target) == ("challenge", "ogre1")
    o.pos = (10, 6)                                                   # 7 away: out of Challenge's range 6
    assert act(s, "warden").ability != "challenge"
    o.pos = (4, 6); add_stack(o, "taunt", 1)                          # it has a Taunt card already
    assert act(s, "warden") == Action("auto", target="ogre1")

def test_a_warden_who_never_challenges_the_boss_is_the_same_warden_otherwise():
    # Rule 6 switched off, for the taunt:boss check. Nothing else changes.
    def act_as(name, s): return POLICIES[name]().act(s, s.heroes["warden"])
    s = state(); o = enemy(s, "ogre", (4, 6))                         # an untaunted boss next to him
    assert act_as("warden", s).ability == "challenge"
    assert act_as("warden_no_boss_taunt", s) == Action("auto", target="ogre1")
    w = enemy(s, "wolf", (5, 3))                                      # a loose add not coming for him
    a = act_as("warden_no_boss_taunt", s); assert (a.ability, a.target) == ("challenge", "wolf1")
    assert isinstance(POLICIES["warden_no_boss_taunt"](), WardenPolicy)

def test_warden_challenges_an_add_that_is_not_coming_for_him():
    s = state(); o = enemy(s, "ogre", (4, 6)); add_stack(o, "taunt", 3)   # the ogre is taunted
    w = enemy(s, "wolf", (5, 3))
    a = act(s, "warden"); assert (a.ability, a.target) == ("challenge", "wolf1")
    w.target = "warden"                                               # it is coming for him anyway
    assert act(s, "warden") == Action("auto", target="ogre1")
    g = enemy(s, "goblin", (5, 4)); assert act(s, "warden").ability != "challenge"   # fodder: any hit kills it

def test_warden_hooks_a_caster_that_shoots_him_from_afar():
    s = state(); o = enemy(s, "ogre", (4, 6)); add_stack(o, "taunt", 3)   # the ogre is taunted
    sh = enemy(s, "shaman", (6, 2)); sh.target = "warden"
    a = act(s, "warden"); assert (a.ability, a.target) == ("chain_hook", "shaman1")
    sh.target = "mage"                                                # after the mage: a Taunt first, it is cheaper
    a = act(s, "warden"); assert (a.ability, a.target) == ("challenge", "shaman1")

def test_rogue_saps_the_brute_on_round_one():
    s = state(); enemy(s, "brute", (3, 4))
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
    for party in (["warden", "rogue", "druid", "mage"], ["rogue", "rogue", "mage"],
                  ["warden", "druid"], ["mage"], ["warden", "rogue", "druid", "mage", "mage"]):
        for seed in range(5):
            r = run_fight(n, f, party, seed=seed)
            assert 1 <= r.rounds <= n.rules["max_rounds"]     # it ended, without an error

# The numbers are first guesses and nobody wins the whole fight yet; winning
# it is the tuning task's job. So the kit is checked two other ways.
def kit_against_auto(f, seeds=30):
    n = load_numbers(GAME / "numbers.toml"); party = ["warden", "rogue", "druid", "mage"]
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
from fastcombat.policies import AutoOnly, WardenNoBossTaunt, RoguePolicy, DruidPolicy, MagePolicy
from fastcombat.units import Announced, Cast

def test_the_registry_and_the_default_for_a_class_with_no_policy():
    assert POLICIES == {"warden": WardenPolicy, "rogue": RoguePolicy, "druid": DruidPolicy,
                        "mage": MagePolicy, "auto": AutoOnly,
                        "warden_no_boss_taunt": WardenNoBossTaunt}
    assert isinstance(default_policy("bard"), AutoOnly)
    assert isinstance(default_policy("druid"), DruidPolicy)

def test_no_policy_ever_asks_for_an_ability_it_cannot_use():
    n = load_numbers(GAME / "numbers.toml"); f = load_fight(GAME / "fights" / "ogre_warlord.toml")
    refused = []

    class Checked:
        def __init__(self, cls): self.policy = default_policy(cls)
        def move(self, s, hero): return self.policy.move(s, hero)
        def act(self, s, hero):
            a = self.policy.act(s, hero)
            if a.kind == "ability" and not can_use(s, hero, a.ability, a):
                refused.append((s.round, hero.id, a))
            return a

    party = ["warden", "rogue", "druid", "mage", "mage"]
    for seed in range(10):
        policies = {h: Checked(h.rstrip("2")) for h in ("warden", "rogue", "druid", "mage", "mage2")}
        run_fight(n, f, party, policies=policies, seed=seed)
    assert refused == []

def heavy_on_warden(s, dice=(6, 6)):
    o = enemy(s, "ogre", (4, 6)); add_stack(o, "taunt", 3)
    o.announced = Announced("skull_crusher", "heavy", s.round + 1, "warden", frozenset(), dice)

def test_warden_braces_with_unbroken_only_when_the_heavy_hit_could_drop_them():
    s = state(); heavy_on_warden(s); w = s.heroes["warden"]; w.resource = 10
    w.hp = 36; assert act(s, "warden").ability == "unbroken"         # 6d6 can roll 36
    w.hp = 37; assert act(s, "warden").ability != "unbroken"
    add_stack(w, "guarded", 1, 4)                                    # each hit 4 smaller: at most 32
    w.hp = 32; assert act(s, "warden").ability == "unbroken"
    w.hp = 33; assert act(s, "warden").ability != "unbroken"

def test_warden_without_the_grit_for_unbroken_reads_on():
    s = state(); heavy_on_warden(s); w = s.heroes["warden"]; w.hp = 10; w.resource = 4
    assert act(s, "warden").ability != "unbroken"

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

def test_mage_never_drops_a_meteor_on_a_hero():
    s = state()
    for square in ((8, 4), (8, 5), (8, 6), (9, 5)):
        enemy(s, "goblin", square)
    a = act(s, "mage")
    assert (a.ability, a.pos) == ("meteor", (7, 4))                 # the first square, in (x, y) order, that covers all four
    s.heroes["rogue"].pos = (6, 2)                                  # 2 from (7, 4): that square is out now
    a = act(s, "mage")
    assert a.ability == "meteor" and a.pos != (7, 4) and all(
        max(abs(a.pos[0] - h.pos[0]), abs(a.pos[1] - h.pos[1])) > 2 for h in s.heroes.values())

def test_druid_centres_wild_growth_to_cover_the_most_hurt_allies():
    s = state()
    for name in ("warden", "rogue", "druid", "mage"):
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

def test_warden_does_not_disrupt_a_caster_that_is_already_stopped():
    s = state(); sh = mending_shaman(s, (4, 6))                     # next to the Warden at (3, 6)
    assert act(s, "warden").ability == "disrupt"
    add_stack(sh, "sap", 2)
    assert act(s, "warden").ability != "disrupt"

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
