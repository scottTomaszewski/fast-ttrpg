"""How a hero plays: where to move, and what to do.

A policy answers two questions for one hero each party turn: in the move
step, which square to go to (`move`), and in the act step, what to do
(`act`). The round loop in `fight.py` asks, and checks the answers: a move
that is too far or onto someone does not happen, and an action that is not
allowed is the same as doing nothing.

Each class plays by a short list of rules, read from the top: the first
rule that applies wins. Every rule that uses an ability only applies when
the ability can be used right now (`abilities.can_use`); if it cannot, the
next rule is read. Each class's list is in its docstring below, and the
code follows it in the same order, one block for each rule.

The lists are written the way a good player of an online game (an MMO)
plays: every button has a reason to be pressed, and the big ones are kept
for the moment they are for.

Some rules use a word that means the same for every class:

- The focus is the enemy to attack. Never one that is stunned, sapped or
  sheeped, while any enemy is not. First an enemy that has announced a
  mend; then the other enemies that are not a boss, lowest HP first; then
  the boss. If two are just as good, the nearer one, then the one whose id
  comes first. When every enemy left is stunned, sapped or sheeped, the
  focus is chosen the same way from the stunned ones, and only when none
  is stunned, from the sapped or sheeped ones: a hit wakes a sapped or
  sheeped enemy, so nobody breaks one while there is anything else to
  hit, but nobody waits for its cards to run out either.
- When a rule names an ability aimed at the focus, the focus is chosen
  the same way but only from enemies that are not fodder; if there are
  none, the rule is skipped. Auto-attacks use the normal focus, fodder
  too. So a 1-HP goblin gets an auto-attack, not a Backstab.
- An add is an enemy that is not the boss. An elite is an add the fight
  file marks as one (like the brute).
- Haul up: a hero next to a downed ally hauls them up, unless a Druid is
  up and has a Seed (then the Druid will heal them).
- Stunned: a hero with stun cards cannot move or act this party turn, so
  they stay put and do nothing, before rule 1 of their list. The one
  exception is the Mage's Ice Block (her rule 1), which a stunned hero
  may still use. A hero in an Ice Block also stays put and does nothing.
- Moving: never end on a square where a blast or a stomp is going to land
  (danger) if a free square out of it is in reach. A hero who is in the
  middle of a cast, or of a channel they must stand still for
  (Evocation), and is safe, stays put. So does a hero next to a downed
  ally they will haul up: that comes before where a class likes to stand.
- The shield plan: the boss has announced a blast that lands this round,
  the Guardian stands in its area, the boss has Taunt cards, he is not
  about to haul anyone up, and he can pay for Shield Plant. Then he will
  plant his shield this turn (Guardian rule 3), so he stays where he is
  in the move step instead of stepping out. Everyone can see that coming,
  so for every hero the squares behind him (where Shield Plant covers
  them, against the boss's square) are not danger from that blast: an
  ally hitting an enemy there, or one who cannot move, stays behind the
  shield instead of running.
- An answered cast is a boss cast that is already dealt with this turn: a
  blast a Guardian planted his shield against, a heavy hit on a hero who
  holds a Last Stand card, or a stomp with nobody in its area but a
  Guardian taking it while a Druid is up to Cleanse him (or nobody at
  all). Nobody spends an interrupt on it.
- An enemy is about to be hit when a hero's cast or channel that does
  damage (Firebolt, Arcane Volley) is aimed at it, or it stands in the
  marked area of a hero's blast (Meteor). Nobody saps or sheeps it: the
  hit would wake it.

An ally is a hero who is up (not down and not out), unless a rule says
otherwise: "a downed ally" is one who is down. "Lowest" for allies means
the lowest share of their max HP. A squishy hero is a Druid or a Mage.
"""

from dataclasses import replace
from typing import Protocol

from fastcombat.abilities import Action, can_use
from fastcombat.casting import moving_ends
from fastcombat.combat import BROKEN_BY_DAMAGE
from fastcombat.grid import Pos, adjacent, approach, behind, distance, within
from fastcombat.numbers import AbilitySpec
from fastcombat.opening import NONE, Opening, can_open
from fastcombat.targeting import held
from fastcombat.units import BAD_STACKS, Enemy, FightState, Hero

# How the policies play. These are not game rules: they are how careful or
# greedy each class is, and can be changed to try another way of playing.
# Shares of max HP are written as 0.35 for 35%.
INTERCEDE_AT = 0.6  # Guardian: guard an ally at 60% HP or less
SHOUT_ENEMIES = 2  # Guardian: Challenging Shout when this many loose adds near him go for allies
SLAM_TAUNT_CARDS = 2  # Guardian: Shield Slam only while the boss has this many Taunt cards or more...
SLAM_ALLIES_ABOVE = 0.75  # ...and every ally is above 75% HP
SWIFTMEND_AT = 0.35  # Druid: Swiftmend an ally at 35% HP or less
WILD_GROWTH_AT = 0.70  # Druid: allies at 70% HP or less count for Wild Growth
WILD_GROWTH_ALLIES = 2  # Druid: Wild Growth when it covers this many of them
REGROWTH_AT = 0.60  # Druid: Regrowth an ally at 60% HP or less
REJUVENATION_AT = 0.80  # Druid: Rejuvenation on an ally at 80% HP or less...
REJUVENATION_ENERGY = 6  # ...when the Druid has this much energy or more
VANISH_AT = 0.40  # Rogue: Vanish at 40% HP or less when something is after her
SAP_ABOVE = 0.50  # Rogue: Sap an elite only above half its HP; a hurt one gets a Backstab
HIDDEN_WAIT_ROUNDS = 2  # Rogue: wait hidden this many rounds at most for an elite out of reach
CHEAP_SHOT_AT = 0.50  # Rogue: Cheap Shot an add on a squishy hero at half HP or less
MAGE_SAFE_GAP = 5  # Mage: likes to stand this far from every enemy; farther is no better
METEOR_ENEMIES = 3  # Mage: Meteor when it would hit this many enemies
QUICKEN_ROUND = 5  # Mage: the first Quicken from this round on...
QUICKEN_BURN = 0.35  # ...and a second one when the boss is down to 35% HP or less
QUICKEN_MOST = 2  # Mage: never more Quickens than this in one fight
VOLLEY_TAUNT_CARDS = 3  # Mage: if Arcane Volley is Loud, only on a focus with this many Taunt cards
ICE_BLOCK_AT = 0.35  # Mage: Ice Block when stunned or rooted at 35% HP or less with an enemy next to her
EVOCATION_BELOW = 6  # Mage: Evocation with less mana than this (a whole Arcane Volley)


class Policy(Protocol):
    """How one hero plays. A policy may also have `opening(state, hero)`,
    which gives back the Rogue's `Opening` before round 1 (see
    `opening.py`). A policy without it opens with none.

    A policy is made fresh for each fight (`run_fight` and the `fastcombat`
    command both do this), so nothing it remembers carries over. A policy
    that remembers something still forgets it if it sees the round go
    back down, in case someone plays two fights with one policy.
    """

    def move(self, state: FightState, hero: Hero) -> Pos: ...
    def act(self, state: FightState, hero: Hero) -> Action: ...


class AutoOnly:
    """Walk to the nearest living enemy that is not controlled, and auto-attack it.

    It never uses an ability. Nearest is counted in steps; if two enemies
    are just as near, the one whose id comes first. A stunned, sapped or
    sheeped enemy is left alone while any other enemy is left (see
    `_nearest_enemy`). With no enemy to go for, it stays put and does
    nothing.
    """

    def move(self, state: FightState, hero: Hero) -> Pos:
        enemy = _nearest_enemy(state, hero)
        if enemy is None:
            return hero.pos
        return approach(
            hero.pos,
            enemy.pos,
            state.numbers.rules["hero_move"],
            state.occupied(),
            state.fight.width,
            state.fight.height,
            reach=state.numbers.heroes[hero.cls].attack_range,
        )

    def act(self, state: FightState, hero: Hero) -> Action:
        enemy = _nearest_enemy(state, hero)
        reach = state.numbers.heroes[hero.cls].attack_range
        if enemy is None or distance(hero.pos, enemy.pos) > reach:
            return Action("none")
        return Action("auto", target=enemy.id)


class _ClassPolicy:
    """What the four class policies share: the moving rules.

    A class says where it likes to stand in `where_to`. Before that is
    asked: a stunned hero, or one in an Ice Block, cannot move and stays
    put. A hero in the middle of a cast (or of a channel they must stand
    still for) stays put, and so does a hero next to a downed ally they
    will haul up; those two only while they are safe: someone standing in
    danger still gets out of it.
    """

    hauls_up = True

    def move(self, state: FightState, hero: Hero) -> Pos:
        if hero.stunned or hero.iced:
            return hero.pos
        if moving_ends(state, hero) or (self.hauls_up and _haul_up(state, hero)):
            return _stay(state, hero)
        return self.where_to(state, hero)

    def where_to(self, state: FightState, hero: Hero) -> Pos:
        raise NotImplementedError


class GuardianPolicy(_ClassPolicy):
    """The Guardian. Move: to a square next to the boss (or to the nearest
    enemy if there is no boss), out of danger if possible. When the shield
    plan is on, he stays where he is instead. When the boss's Stomp lands
    this round on his square, he stays to take it (like a tank in an MMO)
    if a Druid is up to Cleanse the stun, or if he is holding an add there
    (an enemy that is not the boss and not controlled, next to him) that
    would get loose if he stepped out. Everyone else steps out of it.

    An enemy next to the Guardian is already held: it must attack him. So the
    Guardian spends a turn on a Taunt or a pull only for an enemy that would
    otherwise go for someone else. Anything else costs him an auto-attack
    and does nothing. A boss is never held that way: only Taunt cards keep
    it on him, so he keeps Taunt cards on it (rule 6). A loose enemy is one
    that is neither held, taunted nor controlled.

    He keeps grit for his emergency buttons. While an ally (not a Guardian)
    is at 60% HP or less, he keeps enough for Intercede. Rule 9 is the
    everyday one: he only uses it if the grit left after paying is still
    that much. (Rules 7 and 8 are not everyday: they take adds off his
    allies.) He keeps nothing back for Last Stand ahead of time: like
    every hero, he plays only on what a player at the table can see, and
    nobody knows a heavy hit is coming until the boss announces it. Once
    it is announced, rule 2 comes first and spends the grit.

    1. Haul up.
    2. A boss heavy hit is announced on me and it could take me to 0: its
       biggest roll, plus the boss's own biggest hit later in that GM turn
       if it has Taunt cards (one Last Stand card covers the whole GM turn):
       Last Stand.
    3. The shield plan is on: Shield Plant, against the blast coming from
       the boss's square.
    4. An enemy next to me has an announced cast that is not answered, and
       is not controlled (a stunned, sapped or sheeped enemy's cast never
       lands): Disrupt.
    5. An ally (not a Guardian) at 60% HP or less is the target of an enemy
       with no Taunt cards: Intercede on the lowest such ally.
    6. The boss has no Taunt cards: Taunt the boss.
    7. Two or more loose adds within Challenging Shout's radius are going for
       someone else (fodder too, like a goblin wave): Challenging Shout.
    8. A loose add is in Grip's range, and it attacks from farther than one
       square away (like the shaman), or it is next to a squishy hero it is
       going for (like a wolf that ran past me): Grip the one closest to any
       ally who is not a Guardian. Next to me it is held, for as long as it
       stays there, and I can Disrupt its casts.
    9. A loose add that is not fodder, and is not already going for me, is
       in Taunt's range: Taunt the one closest to any ally who is not a
       Guardian. (Fodder dies to any hit, so it is not worth the grit.)
    10. Nothing needs me: the boss has 2 or more Taunt cards (or there is
        no boss), every ally (not a Guardian) is above 75% HP, and no add
        is loose. Then Shield Slam instead of an auto-attack: the boss if
        it is next to me, else the lowest-HP enemy next to me that is not
        fodder and not controlled. It is free, gives grit and has a
        cooldown, so it is the filler for when things go very well.
    11. Auto-attack the focus if it is next to me, or else the lowest-HP
        enemy next to me that is not controlled.
    """

    taunts_boss = True  # rule 6; `GuardianNoBossTaunt` switches it off

    def where_to(self, state: FightState, guardian: Hero) -> Pos:
        plan = _shield_plan(state)
        if plan is not None and plan[0] is guardian:
            return guardian.pos
        if _takes_the_stomp(state, guardian):
            return guardian.pos
        goal = _boss(state) or _nearest_enemy(state, guardian)
        if goal is None:
            return _stay(state, guardian)
        return _go(state, guardian, goal.pos, reach=1)

    def act(self, state: FightState, guardian: Hero) -> Action:
        boss = _boss(state)
        allies = [h for h in _up_heroes(state) if h.cls != "guardian"]
        spots = [a.pos for a in allies]
        abilities = state.numbers.abilities

        # Stunned: nothing (see the top of this file).
        if guardian.stunned:
            return Action("none")

        # 1. Haul up.
        if action := _haul_up(state, guardian):
            return action

        # 2. A boss heavy hit on me that could take me to 0: Last Stand.
        cast = boss.announced if boss else None
        if cast and cast.kind == "heavy" and cast.target == guardian.id:
            if _heavy_could_drop(state, guardian, cast.dice):
                if action := _ability(state, guardian, "last_stand"):
                    return action

        # 3. The shield plan is on: Shield Plant against the boss's blast.
        plan = _shield_plan(state)
        if plan is not None and plan[0] is guardian:
            if action := _ability(state, guardian, "shield_plant", pos=plan[1]):
                return action

        # 4. An enemy next to me has an announced cast nobody answered: Disrupt.
        casting = _first(_casting(state, _enemies_next_to(state, guardian)))
        if casting is not None:
            if action := _ability(state, guardian, "disrupt", casting.id):
                return action

        # 5. A hurt ally is the target of an enemy with no Taunt cards: Intercede.
        hunted = {
            e.target for e in state.living_enemies() if "taunt" not in e.stacks
        }
        guard = _lowest(
            a for a in allies if a.id in hunted and _share(a) <= INTERCEDE_AT
        )
        if guard is not None:
            if action := _ability(state, guardian, "intercede", guard.id):
                return action

        # 6. The boss has no Taunt cards: Taunt it.
        if self.taunts_boss and boss is not None and "taunt" not in boss.stacks:
            if action := _ability(state, guardian, "taunt", boss.id):
                return action

        loose = [
            e for e in state.living_enemies() if e.spec.tier != "boss" and _loose(state, e)
        ]

        # 7. Two or more loose adds near me are going for someone else:
        # Challenging Shout.
        shout = abilities["challenging_shout"]
        near = within(guardian.pos, shout.radius, state.fight.width, state.fight.height)
        wandering = [e for e in loose if e.pos in near and e.target != guardian.id]
        if len(wandering) >= SHOUT_ENEMIES:
            if action := _ability(state, guardian, "challenging_shout"):
                return action

        # 8. A loose add that hits from afar, or one on a squishy hero: Grip the
        # one closest to an ally.
        reach = abilities["grip"].range
        grippable = [
            e
            for e in loose
            if distance(guardian.pos, e.pos) <= reach
            and (e.spec.range > 1 or _on_a_squishy(state, e))
        ]
        if grippable:
            grip = min(grippable, key=lambda e: (_gap(e.pos, spots), e.id))
            if action := _ability(state, guardian, "grip", grip.id):
                return action

        # 9. A loose add (not fodder) that is not coming for me: Taunt the one
        # closest to an ally, if I still keep my emergency grit after paying.
        reach = abilities["taunt"].range
        hunting = [
            e
            for e in loose
            if e.spec.tier != "fodder"
            and e.target != guardian.id
            and distance(guardian.pos, e.pos) <= reach
        ]
        spare = guardian.resource - abilities["taunt"].cost >= _grit_to_keep(state)
        if hunting and spare:
            add = min(hunting, key=lambda e: (_gap(e.pos, spots), e.id))
            if action := _ability(state, guardian, "taunt", add.id):
                return action

        # 10. Nothing needs me: Shield Slam the boss, or the weakest add on me.
        taunt = boss.stacks.get("taunt") if boss else None
        boss_held = boss is None or (taunt is not None and taunt.cards >= SLAM_TAUNT_CARDS)
        all_well = all(_share(a) > SLAM_ALLIES_ABOVE for a in allies)
        if boss_held and all_well and not loose:
            slam = boss if boss is not None and adjacent(boss.pos, guardian.pos) else None
            if slam is None:
                slam = _weakest_next_to(state, guardian, fodder=False)
            if slam is not None:
                if action := _ability(state, guardian, "shield_slam", slam.id):
                    return action

        # 11. Auto-attack the focus if next to me, else the lowest-HP enemy next to me.
        if action := _auto(state, guardian, _focus(state, guardian)):
            return action
        return _auto(state, guardian, _weakest_next_to(state, guardian)) or Action("none")


class GuardianNoBossTaunt(GuardianPolicy):
    """The Guardian with rule 6 switched off: he never Taunts the boss.

    Everything else is the same. It is not a way to play: the `taunt:boss`
    check plays it to see how many wins taunting the boss is worth.
    """

    taunts_boss = False


class RoguePolicy(_ClassPolicy):
    """The Rogue. Move: next to the enemy her abilities are after, a square
    also out of danger if possible. That enemy is, the first that applies:
    the elite to go for from hiding (rule 3), while she has one; while she
    has full combo points, the nearest enemy worth an Eviscerate (an elite,
    or the boss while it has Taunt cards; rule 8); or else the focus her
    abilities aim at (not fodder), or the normal focus if there is no such
    enemy. If walking cannot take her next to it, but Shadowstep can (from
    the square she stays on, it is farther than her move, within
    Shadowstep's range, and Shadowstep can be used), she stays put
    (stepping out of danger if she must) and Shadowsteps in the act step.

    The elite to go for from hiding: while I am hidden, an elite that is
    awake (not stunned, sapped or sheeped). First one worth a Sap (more
    than half its HP, and not about to be hit), then the one that hits
    hardest, then the one with the most HP, then the nearest. I am hidden
    at the start of every fight, and again after a Vanish. If I have
    already waited 2 rounds in a row for it (rule 3) and still cannot get
    there, I give up on it until I am seen again or it comes in reach, and
    play the rest of the list.

    Before the fight (the opening, see `opening.py`): if an elite is there
    that nobody stands next to and that has a free square next to it, I
    pick the one that hits hardest (then the most HP, the nearest, by id)
    and get next to it, so round 1 starts with rule 3: a Sap. I Shadowstep
    in if, after paying for it and getting round 1's energy back, I can
    still pay for the Sap: it always works, and the Sap is the point. If I
    could not, I Sneak instead. With no such elite, no opening.

    1. Haul up.
    2. An enemy next to me has an announced cast that is not answered, and
       is not controlled: Disrupt; else, with full combo points and the
       caster an add that is not fodder, Kidney Shot (the longer stun);
       else Cheap Shot.
    3. I am hidden and there is an elite to go for: if it is next to me,
       Sap it if it is worth a Sap, else Backstab it (a Sap on an elite
       that is nearly dead, or about to be hit, is wasted); else Shadowstep
       next to it (that keeps me hidden); else wait (do nothing, so I stay
       hidden) while I walk to it.
    4. I am not hidden, and: the boss or an elite that is not controlled is
       pulled by me; or the boss went for me on its last turn; or I am at
       40% HP or less and an enemy that is not controlled went for me or is
       next to me: Vanish. (A goblin pulled onto me is not worth it.)
    5. Hidden: Backstab the focus.
    6. Full combo points, and an add next to me that is not fodder and not
       controlled is going for someone who is not a Guardian: Kidney Shot
       (the longer stun).
    7. An add next to me that is not fodder and not controlled is going for
       a squishy hero at half HP or less: Cheap Shot.
    8. Full combo points: Eviscerate an enemy next to me that is not
       controlled. First an elite or the boss while it has Taunt cards
       (Eviscerate is Loud: a boss with none would be pulled onto me), the
       one whose id comes first; else the focus, unless it is a boss with
       no Taunt cards.
    9. Backstab the focus.
    10. The focus is farther than my move and within Shadowstep's range:
        Shadowstep.
    11. Auto-attack the normal focus (fodder too) if it is next to me; or
        else the focus my abilities aim at, if it is next to me; or else the
        lowest-HP enemy next to me that is not controlled.

    This is the one policy that remembers something from round to round:
    how long the Rogue has waited hidden (rule 3). It is kept for each hero
    id and each elite, so one policy can play two Rogues, and a new elite
    gets its own wait after she gave up on another. It is forgotten when
    the round number goes down (a new fight).
    """

    def __init__(self) -> None:
        # By (hero id, elite id): the first and the last round of her wait in rule 3.
        self._waiting: dict[tuple[str, str], tuple[int, int]] = {}
        self._last_round = 0  # the last round seen, to tell when a new fight starts

    def opening(self, state: FightState, rogue: Hero) -> Opening:
        """Before round 1: get next to the elite worth opening on, if there is one.

        Shadowstep in if she can, and can still pay for the Sap in round 1
        after that round's energy comes back; else Sneak.
        """
        elites = [
            e
            for e in state.living_enemies()
            if e.spec.tier == "elite"
            and not any(adjacent(h.pos, e.pos) for h in state.heroes.values())
            and can_open(state, rogue, Opening("sneak", e.id))
        ]
        target = min(
            elites,
            key=lambda e: (-_hit_size(e), -e.hp, distance(rogue.pos, e.pos), e.id),
            default=None,
        )
        if target is None:
            return NONE
        step = Opening("shadowstep", target.id)
        spec = state.numbers.heroes[rogue.cls]
        abilities = state.numbers.abilities
        first_turn = min(spec.pool, rogue.resource - abilities["shadowstep"].cost + spec.regen)
        if can_open(state, rogue, step) and first_turn >= abilities["sap"].cost:
            return step
        return Opening("sneak", target.id)

    def where_to(self, state: FightState, rogue: Hero) -> Pos:
        target = self._elite_to_go_for(state, rogue)
        if target is None and _full_combo(state, rogue):
            target = _eviscerate_target(state, rogue)
        if target is None:
            target = _ability_focus(state, rogue)
        if target is None:
            target = _focus(state, rogue)  # only fodder is left
            if target is None:
                return _stay(state, rogue)
            return _go(state, rogue, target.pos, reach=1)
        dest = _go(state, rogue, target.pos, reach=1)
        if adjacent(dest, target.pos):
            return dest
        # Shadowstep can take her there in the act step, from the square she
        # stays on (out of danger, if she has to step out of it).
        stay = _stay(state, rogue)
        if _shadowstep(state, replace(rogue, pos=stay), target):
            return stay
        return dest

    def act(self, state: FightState, rogue: Hero) -> Action:
        self._memory(state)  # sees every round, so a new fight is never missed
        focus = _ability_focus(state, rogue)  # for the abilities aimed at the focus
        full = _full_combo(state, rogue)

        # Stunned: nothing (see the top of this file).
        if rogue.stunned:
            return Action("none")

        # 1. Haul up.
        if action := _haul_up(state, rogue):
            return action

        # 2. An enemy next to me has an announced cast nobody answered:
        # Disrupt, else Kidney Shot with full combo points, else Cheap Shot.
        casting = _first(_casting(state, _enemies_next_to(state, rogue)))
        if casting is not None:
            if action := _ability(state, rogue, "disrupt", casting.id):
                return action
            if full and casting.spec.tier not in ("boss", "fodder"):
                if action := _ability(state, rogue, "kidney_shot", casting.id):
                    return action
            if action := _ability(state, rogue, "cheap_shot", casting.id):
                return action

        # 3. Hidden, with an elite to go for: Sap it (or Backstab it if it is
        # nearly dead), else Shadowstep to it, else wait.
        elite = _hidden_elite(state, rogue)
        if elite is not None:
            if adjacent(rogue.pos, elite.pos):
                ability = "sap" if _worth_sapping(state, elite) else "backstab"
                if action := _ability(state, rogue, ability, elite.id):
                    return action
            elif action := _shadowstep(state, rogue, elite):
                return action
            else:
                self._wait(state, rogue, elite)
                if not self._gave_up(state, rogue, elite):
                    return Action("none")

        # 4. Pulled, chased by the boss, or low and chased: Vanish.
        if not rogue.hidden and _should_vanish(state, rogue):
            if action := _ability(state, rogue, "vanish"):
                return action

        # 5. Hidden: Backstab the focus.
        if rogue.hidden and focus is not None:
            if action := _ability(state, rogue, "backstab", focus.id):
                return action

        near = [
            e
            for e in _enemies_next_to(state, rogue)
            if e.spec.tier not in ("boss", "fodder") and not e.controlled
        ]

        # 6. Full combo points, and an add next to me is after someone who is
        # not a Guardian: Kidney Shot.
        if full:
            hunter = _first(
                e for e in near if _target_class(state, e) not in (None, "guardian")
            )
            if hunter is not None:
                if action := _ability(state, rogue, "kidney_shot", hunter.id):
                    return action

        # 7. An add next to me is after a squishy hero at half HP or less: Cheap Shot.
        hunter = _first(
            e
            for e in near
            if _target_class(state, e) in ("druid", "mage")
            and _share(state.heroes[e.target]) <= CHEAP_SHOT_AT
        )
        if hunter is not None:
            if action := _ability(state, rogue, "cheap_shot", hunter.id):
                return action

        # 8. Full combo points: Eviscerate an elite or a taunted boss next to me,
        # else the focus.
        if full:
            big = [
                e
                for e in _enemies_next_to(state, rogue)
                if not e.controlled and _worth_eviscerating(e)
            ]
            if focus is not None and (focus.spec.tier != "boss" or "taunt" in focus.stacks):
                big.append(focus)
            for finish in big:
                if action := _ability(state, rogue, "eviscerate", finish.id):
                    return action

        # 9. Backstab the focus.
        if focus is not None:
            if action := _ability(state, rogue, "backstab", focus.id):
                return action

        # 10. The focus is farther than my move, and within Shadowstep's range:
        # Shadowstep.
        if focus is not None:
            if action := _shadowstep(state, rogue, focus):
                return action

        # 11. Auto-attack the normal focus if it is next to me (fodder too), else
        # the ability focus if it is next to me, else the weakest enemy next to me.
        if action := _auto(state, rogue, _focus(state, rogue)):
            return action
        if action := _auto(state, rogue, focus):
            return action
        return _auto(state, rogue, _weakest_next_to(state, rogue)) or Action("none")

    def _elite_to_go_for(self, state: FightState, rogue: Hero) -> Enemy | None:
        """The move step's elite to go for from hiding (rule 3), or None.

        None also once she has given up waiting for it, unless it has come
        in reach: a walk ends next to it, or Shadowstep can take her there.
        """
        elite = _hidden_elite(state, rogue)
        if elite is None or not self._gave_up(state, rogue, elite):
            return elite
        if adjacent(_go(state, rogue, elite.pos, reach=1), elite.pos):
            return elite
        if _shadowstep(state, replace(rogue, pos=_stay(state, rogue)), elite):
            return elite
        return None

    def _wait(self, state: FightState, rogue: Hero, elite: Enemy) -> None:
        """Write down that this round she is hidden and `elite` is out of reach."""
        now = state.round
        waiting = self._memory(state)
        first, last = waiting.get((rogue.id, elite.id), (now, now))
        if last not in (now - 1, now):
            first = now  # a new wait: the last one did not go on to this round
        waiting[(rogue.id, elite.id)] = (first, now)

    def _gave_up(self, state: FightState, rogue: Hero, elite: Enemy) -> bool:
        """True once she has waited `HIDDEN_WAIT_ROUNDS` rounds in a row for `elite`
        before this one."""
        first, last = self._memory(state).get((rogue.id, elite.id), (0, -1))
        if last not in (state.round - 1, state.round):
            return False
        return state.round - first >= HIDDEN_WAIT_ROUNDS

    def _memory(self, state: FightState) -> dict[tuple[str, str], tuple[int, int]]:
        """The waits written down, forgotten first if the round went down (a new fight)."""
        if state.round < self._last_round:
            self._waiting.clear()
        self._last_round = state.round
        return self._waiting


class DruidPolicy(_ClassPolicy):
    """The Druid. Move: within Rejuvenation range of the Guardian (or of the
    lowest-HP ally if there is no Guardian), and as far from the nearest enemy
    as that allows. While an ally is down, within reach of them instead.

    A stun is worth a Cleanse when the stunned ally still has an act step
    to come this turn (they act after me: heroes act in id order), or when
    it lasts past this turn (more than one card). A one-card stun on an
    ally who has already acted comes off at the end of the turn anyway.

    1. An ally is down: Swiftmend them, else Nourish them.
    2. An enemy that is pulled by me or next to me could reach me this GM
       turn (its distance to me is at most its move plus its range), and
       is neither controlled nor rooted: Shadowmeld.
    3. An ally is at 35% HP or less: Swiftmend.
    4. An ally has a stun worth a Cleanse: Cleanse the stun. The Guardian
       first (the boss is on him), then by id.
    5. In the middle of a cast: continue.
    6. The Guardian is up without Rejuvenation cards: Rejuvenation.
    7. Two or more allies at 70% HP or less (after a blast, say) fit in one
       Wild Growth area: Wild Growth, centred to cover the most.
    8. An ally is at 60% HP or less: Regrowth on the lowest.
    9. An ally has some other bad card (poison, say; see
       `units.BAD_STACKS`): Cleanse it, the first in that list, on the
       first such ally by id.
    10. An ally at 80% HP or less has no Rejuvenation cards and I have 6 or
        more energy: Rejuvenation.
    11. An ally is below full HP: Nourish the lowest. It is free, so it is
        the filler whenever nothing better is needed.
    12. Auto-attack the focus if it is in range.
    """

    hauls_up = False  # the Druid heals a downed ally from afar instead

    def where_to(self, state: FightState, druid: Hero) -> Pos:
        downed = _first(_downed(state))
        if downed is not None:
            anchor, reach = downed, state.numbers.abilities["swiftmend"].range
        else:
            others = [h for h in _up_heroes(state) if h is not druid]
            anchor = state.guardian() or _lowest(others)
            reach = state.numbers.abilities["rejuvenation"].range
        if anchor is None:
            return _stay(state, druid)
        threats = [e.pos for e in state.living_enemies()]
        return _stand(state, druid, anchor.pos, reach, lambda square: -_gap(square, threats))

    def act(self, state: FightState, druid: Hero) -> Action:
        allies = _up_heroes(state)
        abilities = state.numbers.abilities

        # Stunned: nothing (see the top of this file).
        if druid.stunned:
            return Action("none")

        # 1. An ally is down: Swiftmend them, else Nourish them.
        downed = _first(_downed(state))
        if downed is not None:
            if action := _ability(state, druid, "swiftmend", downed.id):
                return action
            if action := _ability(state, druid, "nourish", downed.id):
                return action

        # 2. An enemy pulled by me or next to me could reach me this GM turn,
        # and is neither controlled nor rooted: Shadowmeld.
        if any(
            (e.pulled_by == druid.id or adjacent(e.pos, druid.pos))
            and distance(e.pos, druid.pos) <= e.spec.move + e.spec.range
            and not e.controlled
            and "rooted" not in e.stacks
            for e in state.living_enemies()
        ):
            if action := _ability(state, druid, "shadowmeld"):
                return action

        # 3. An ally is at 35% HP or less: Swiftmend.
        dying = _lowest(a for a in allies if _share(a) <= SWIFTMEND_AT)
        if dying is not None:
            if action := _ability(state, druid, "swiftmend", dying.id):
                return action

        # 4. An ally has a stun worth a Cleanse: Cleanse it, the Guardian first.
        stunned = sorted(
            (a for a in allies if _stun_worth_cleansing(druid, a)),
            key=lambda a: (a.cls != "guardian", a.id),
        )
        for ally in stunned:
            if action := _ability(state, druid, "cleanse", ally.id, card="stun"):
                return action

        # 5. In the middle of a cast: continue.
        if druid.cast is not None:
            return Action("continue")

        # 6. The Guardian is up without Rejuvenation cards: Rejuvenation.
        guardian = state.guardian()
        if guardian is not None and "rejuvenation" not in guardian.stacks:
            if action := _ability(state, druid, "rejuvenation", guardian.id):
                return action

        # 7. Two or more hurt allies fit in one Wild Growth area: Wild Growth.
        hurt = [a for a in allies if _share(a) <= WILD_GROWTH_AT]
        spec = abilities["wild_growth"]
        centre, count = _best_centre(state, druid.pos, spec.range, spec.radius, hurt)
        if count >= WILD_GROWTH_ALLIES:
            if action := _ability(state, druid, "wild_growth", pos=centre):
                return action

        # 8. An ally is at 60% HP or less: Regrowth on the lowest.
        low = _lowest(a for a in allies if _share(a) <= REGROWTH_AT)
        if low is not None:
            if action := _ability(state, druid, "regrowth", low.id):
                return action

        # 9. An ally has some other bad card: Cleanse it.
        for ally in allies:
            card = _first(n for n in BAD_STACKS if n != "stun" and n in ally.stacks)
            if card is not None:
                if action := _ability(state, druid, "cleanse", ally.id, card=card):
                    return action
                break

        # 10. An ally at 80% HP or less has no Rejuvenation cards, and I have
        # the energy: Rejuvenation.
        bare = _lowest(
            a
            for a in allies
            if _share(a) <= REJUVENATION_AT and "rejuvenation" not in a.stacks
        )
        if bare is not None and druid.resource >= REJUVENATION_ENERGY:
            if action := _ability(state, druid, "rejuvenation", bare.id):
                return action

        # 11. An ally is below full HP: Nourish the lowest.
        scratched = _lowest(a for a in allies if a.hp < a.max_hp)
        if scratched is not None:
            if action := _ability(state, druid, "nourish", scratched.id):
                return action

        # 12. Auto-attack the focus if it is in range.
        return _auto(state, druid, _focus(state, druid)) or Action("none")


class MagePolicy(_ClassPolicy):
    """The Mage. Move: in spell range of the focus, and as far from the
    nearest enemy as she can get this move, up to 5 squares: any square 5
    or more from every enemy is just as good as another. While casting (not
    channelling), or in Evocation, stay still unless standing in danger.

    Arcane Volley is her everyday damage spell; Firebolt is for a single
    big hit that is worth a round of casting. "I have the mana" means she
    can pay for all of the spell (every hit of Volley). Without it she is
    saving mana: she auto-attacks, and each hit gives some back.

    1. Ice Block, when (she may do this even while stunned):
       a. an enemy's announced cast lands this GM turn and hits me (a heavy
          hit aimed at me, or a blast or a stomp on my square: I did not or
          could not walk out of it in the move step), its biggest roll
          could take me to 0, nobody has answered it, and I cannot Disrupt
          it now (stunned, cooling down or out of reach); or
       b. I am stunned or rooted, at 35% HP or less, and an enemy that is
          not controlled is next to me.
    2. Haul up.
    3. In the middle of a cast (not a channel): continue.
    4. An enemy that is not controlled is next to me:
       a. one of them is an add that is not rooted: Frost Nova (it cannot
          follow me when I walk away);
       b. else Blink to a square that none of them can reach this GM turn
          (Frost Nova would not stop a boss, or they are rooted already);
       c. else Frost Nova.
    5. An enemy in range has an announced cast that is not answered, and is
       not controlled: Disrupt, even in the middle of a channel. A mend
       first (it undoes our damage), then by id.
    6. In the middle of a channel: continue, unless its enemy is sapped or
       sheeped now (the next hit would wake it) and some other enemy is
       left to hit: then the channel ends, and I read on. When every enemy
       left is asleep, I keep channelling. (Evocation has no enemy: I keep
       channelling it.)
    7. No enemy is a sheep, no hero is in the middle of casting Polymorph
       (another Mage's sheep is on its way), and at least two enemies are
       alive that are not controlled, not a boss and not fodder: Polymorph
       the one of them with the most HP that nobody is next to and that is
       not about to be hit.
    8. Some square in range has three or more enemies that are not
       controlled within Meteor's radius, no sapped or sheeped enemy there,
       and no hero there who could not walk out before it lands: Meteor on
       the square that covers the most. A sapped or sheeped enemy wakes up
       when it is hit, so Meteor never goes where it would wake one: the
       Sap or the sheep keeps a dangerous add out of the fight for longer
       than Meteor's extra damage on it is worth. Everyone sees the marked
       squares and walks out (see Moving), so a hero standing there now is
       no reason to wait, unless they cannot walk out: me (I stand still to
       cast), a downed hero, a hero in the middle of a longer cast, or the
       Guardian when an enemy it would hit is next to him (he is holding it
       there).
    9. Nobody has Quicken cards, every hero is up, I have Quickened fewer
       than 2 times this fight, and: it is round 5 or later, I have not
       Quickened yet, and the boss has Taunt cards (or there is no boss);
       or I have Quickened once and the boss is at 35% HP or less (the burn
       at the end): Quicken. (Quicken is benched for now, so `can_use`
       refuses it and this rule never applies in the real game. It is kept
       for when Quicken comes back.)
    10. I have less than 6 mana (not a whole Volley), and nothing needs me:
        no enemy that is not controlled is next to me, no blast or stomp is
        coming down on my square, no announced cast in my Disrupt range is
        waiting for an interrupt, and the boss has Taunt cards (or there is
        no boss): Evocation.
    11. The focus is an add whose HP is more than one Volley hit (on average)
        and no more than one Firebolt (on average), and I have the mana:
        Firebolt it. One big hit finishes it in one of my turns, where Volley
        would need two.
    12. Arcane Volley the focus, if I have the mana. If Volley is Loud, only
        on a focus with three or more Taunt cards: on anything else, Loud
        would pull it off the Guardian, or strip his Taunt.
    13. Volley would be Loud on the focus, and I have the mana: Firebolt the
        focus instead (Firebolt is not Loud).
    14. Auto-attack the focus if it is in range.
    """

    def where_to(self, state: FightState, mage: Hero) -> Pos:
        focus = _focus(state, mage)
        if focus is None:
            return _stay(state, mage)
        reach = state.numbers.abilities["firebolt"].range
        threats = [e.pos for e in state.living_enemies()]
        return _stand(
            state, mage, focus.pos, reach, lambda square: -min(_gap(square, threats), MAGE_SAFE_GAP)
        )

    def act(self, state: FightState, mage: Hero) -> Action:
        focus = _ability_focus(state, mage)  # for the spells aimed at the focus
        enemies = state.living_enemies()
        abilities = state.numbers.abilities

        def affords(ability: str) -> bool:
            """True if she can pay for all of `ability`: every hit of a channel."""
            spec = abilities[ability]
            return mage.resource >= spec.cost * max(1, spec.hits)

        # 1. A hit coming that could drop me and that I cannot stop, or stuck
        # and low next to an enemy: Ice Block (even while stunned).
        if _ice_block_now(state, mage):
            if action := _ability(state, mage, "ice_block"):
                return action

        # Stunned: nothing else (see the top of this file).
        if mage.stunned:
            return Action("none")

        # 2. Haul up.
        if action := _haul_up(state, mage):
            return action

        # 3. In the middle of a cast (not a channel): continue.
        if _mid_cast(mage):
            return Action("continue")

        # 4. An enemy is next to me: Frost Nova, else Blink, else Frost Nova.
        threats = [e for e in _enemies_next_to(state, mage) if not e.controlled]
        if threats:
            if any(e.spec.tier != "boss" and "rooted" not in e.stacks for e in threats):
                if action := _ability(state, mage, "frost_nova"):
                    return action
            square = _blink_square(state, mage, threats)
            if square is not None:
                if action := _ability(state, mage, "blink", pos=square):
                    return action
            if any("rooted" not in e.stacks for e in threats):
                if action := _ability(state, mage, "frost_nova"):
                    return action

        # 5. An enemy in range has an announced cast nobody answered: Disrupt,
        # a mend first.
        def mend_first(enemy: Enemy) -> tuple:
            return (enemy.announced.kind != "mend", enemy.id)

        for casting in sorted(_casting(state, enemies), key=mend_first):
            if action := _ability(state, mage, "disrupt", casting.id):
                return action

        # 6. In the middle of a channel: continue, unless its enemy is asleep now
        # and there is something else to hit.
        if mage.cast is not None:
            target = state.enemies.get(mage.cast.target) if mage.cast.target else None
            if target is None or not _asleep(target) or target in _to_hit(state):
                return Action("continue")

        # 7. No sheep yet, none on its way, and two or more enemies worth one:
        # Polymorph.
        worth = [
            e
            for e in enemies
            if not e.controlled and e.spec.tier not in ("boss", "fodder")
        ]
        sheep_coming = any(
            h.cast is not None and h.cast.ability == "polymorph"
            for h in state.heroes.values()
        )
        no_sheep = not any("sheep" in e.stacks for e in enemies) and not sheep_coming
        if no_sheep and len(worth) >= 2:
            alone = [
                e
                for e in worth
                if not any(adjacent(h.pos, e.pos) for h in _up_heroes(state))
                and not _about_to_be_hit(state, e)
            ]
            sheep = min(alone, key=lambda e: (-e.hp, e.id), default=None)
            if sheep is not None:
                if action := _ability(state, mage, "polymorph", sheep.id):
                    return action

        # 8. Three or more enemies in one area, and every hero there can walk
        # out of it: Meteor.
        centre, count = _meteor_centre(state, mage)
        if count >= METEOR_ENEMIES:
            if action := _ability(state, mage, "meteor", pos=centre):
                return action

        # 9. A good moment, and not too often: Quicken (benched for now).
        if _quicken_now(state, mage):
            if action := _ability(state, mage, "quicken"):
                return action

        # 10. Low on mana and nothing needs me: Evocation.
        if mage.resource < EVOCATION_BELOW and _nothing_needs_the_mage(state, mage):
            if action := _ability(state, mage, "evocation"):
                return action

        # 11. An add one Firebolt would finish, and Volley would need two hits:
        # Firebolt.
        volley, firebolt = abilities["arcane_volley"], abilities["firebolt"]
        if (
            focus is not None
            and focus.spec.tier != "boss"
            and _average(volley) < focus.hp <= _average(firebolt)
            and affords("firebolt")
        ):
            if action := _ability(state, mage, "firebolt", focus.id):
                return action

        # 12. Arcane Volley the focus, unless Loud would do harm.
        taunt = focus.stacks.get("taunt") if focus else None
        loud_is_safe = not volley.loud or (
            taunt is not None and taunt.cards >= VOLLEY_TAUNT_CARDS
        )
        if focus is not None and affords("arcane_volley"):
            if loud_is_safe:
                if action := _ability(state, mage, "arcane_volley", focus.id):
                    return action

        # 13. Volley would be Loud on the focus: Firebolt it instead.
        if focus is not None and not loud_is_safe and affords("firebolt"):
            if action := _ability(state, mage, "firebolt", focus.id):
                return action

        # 14. Auto-attack the focus if it is in range (fodder too).
        return _auto(state, mage, _focus(state, mage)) or Action("none")


# Every policy by name, so one can be picked by its name.
POLICIES: dict[str, type] = {
    "guardian": GuardianPolicy,
    "rogue": RoguePolicy,
    "druid": DruidPolicy,
    "mage": MagePolicy,
    "auto": AutoOnly,
    "guardian_no_boss_taunt": GuardianNoBossTaunt,
}


def default_policy(cls: str) -> Policy:
    """The policy a hero of class `cls` plays by when nobody picks one.

    Each of the four classes has its own. Any other class only auto-attacks.
    """
    if cls in ("guardian", "rogue", "druid", "mage"):
        return POLICIES[cls]()
    return AutoOnly()


# --- Shared rules ------------------------------------------------------------


def _focus(state: FightState, hero: Hero, fodder: bool = True) -> Enemy | None:
    """The enemy to attack (see the top of this file), or None if there is none.

    With `fodder=False` fodder enemies are left out: that is the focus for
    an ability (use `_ability_focus`).
    """

    def order(enemy: Enemy) -> tuple:
        mending = enemy.announced is not None and enemy.announced.kind == "mend"
        boss = enemy.spec.tier == "boss"
        return (not mending, boss, enemy.hp, distance(hero.pos, enemy.pos), enemy.id)

    free = [
        enemy
        for enemy in _to_hit(state)
        if fodder or enemy.spec.tier != "fodder"
    ]
    return min(free, key=order, default=None)


def _ability_focus(state: FightState, hero: Hero) -> Enemy | None:
    """The focus for an ability aimed at it: the same choice, but never fodder.

    None if every enemy left is fodder (or controlled): then the rule that
    wanted it is skipped, and an auto-attack can still go to the fodder.
    """
    return _focus(state, hero, fodder=False)


def _haul_up(state: FightState, hero: Hero) -> Action | None:
    """Haul up a downed ally next to me, unless a Druid who is up has a Seed."""
    if _druid_with_a_seed(state):
        return None
    downed = _first(ally for ally in _downed(state) if adjacent(ally.pos, hero.pos))
    return None if downed is None else Action("haul_up", target=downed.id)


def _druid_with_a_seed(state: FightState) -> bool:
    return any(h.cls == "druid" and h.seeds >= 1 for h in state.up_heroes())


def _downed(state: FightState) -> list[Hero]:
    """Every downed hero, the one with the fewest Bleeding cards left first."""
    downed = [hero for hero in state.heroes.values() if hero.down]
    return sorted(downed, key=lambda hero: (_bleeding(hero), hero.id))


def _bleeding(hero: Hero) -> int:
    stack = hero.stacks.get("bleeding")
    return 0 if stack is None else stack.cards


def _shield_plan(state: FightState) -> tuple[Hero, Pos] | None:
    """The shield plan (see the top of this file): the Guardian who will plant
    his shield this turn, and the square the blast comes from. None if there
    is no plan.

    What it looks at does not change between the move step and his act
    step, so the heroes who move before him and the ones who move after him
    all see the same plan, and he does what they planned round. (One rare
    case can change it: the Druid acts before him, and if she spends her
    last Seed, he hauls a downed ally up instead.)
    """
    guardian = state.guardian()
    boss = _boss(state)
    if guardian is None or boss is None:
        return None
    cast = boss.announced
    if cast is None or cast.kind != "blast" or cast.lands_round != state.round:
        return None
    if guardian.pos not in cast.area or "taunt" not in boss.stacks:
        return None
    if _haul_up(state, guardian) is not None:
        return None
    if _ability(state, guardian, "shield_plant", pos=boss.pos) is None:
        return None
    return guardian, boss.pos


def _answered(state: FightState, enemy: Enemy) -> bool:
    """True when `enemy`'s announced cast is already dealt with, so nobody
    spends an interrupt on it.

    A blast is answered once a Guardian has planted his shield this turn (the
    card comes off at the top of the next party turn, so a card means it
    was this turn). A heavy hit is answered when the hero it is aimed at
    holds a Last Stand card. A stomp is answered when the only heroes left
    in its area (everyone has moved by the act step) are Guardians taking
    it, and a Druid is up to Cleanse their stun; or when nobody is in it.
    """
    cast = enemy.announced
    if cast is None:
        return False
    if cast.kind == "stomp":
        inside = [h for h in state.up_heroes() if h.pos in cast.area]
        if not inside:
            return True
        return all(h.cls == "guardian" for h in inside) and _druid_to_cleanse(state)
    if cast.kind == "blast":
        return any(
            h.cls == "guardian" and "shield_plant" in h.stacks for h in state.up_heroes()
        )
    if cast.kind == "heavy":
        hero = state.heroes.get(cast.target) if cast.target else None
        return hero is not None and "last_stand" in hero.stacks
    return False


# --- The Guardian's grit -------------------------------------------------------


def _takes_the_stomp(state: FightState, guardian: Hero) -> bool:
    """True when the boss's Stomp lands this round on the Guardian's square
    and he stays to take it (see his move): a Druid is up to Cleanse him,
    or he is holding an add there (an enemy that is not the boss and not
    controlled, next to him) that would get loose if he stepped out."""
    boss = _boss(state)
    cast = boss.announced if boss else None
    if cast is None or cast.kind != "stomp" or cast.lands_round != state.round:
        return False
    if guardian.pos not in cast.area:
        return False
    if _druid_to_cleanse(state):
        return True
    return any(
        e.spec.tier != "boss" and not e.controlled for e in _enemies_next_to(state, guardian)
    )


def _druid_to_cleanse(state: FightState) -> bool:
    """True when a Druid is up and not stunned: she can Cleanse a stun next turn."""
    return any(h.cls == "druid" and not h.stunned for h in state.up_heroes())


def _grit_to_keep(state: FightState) -> int:
    """How much grit the Guardian keeps for an emergency button (see his list).

    Only what a player at the table can see counts: the HP of his allies.
    The boss's script is the GM's secret, so it is never read here.
    """
    if any(
        _share(a) <= INTERCEDE_AT for a in state.up_heroes() if a.cls != "guardian"
    ):
        return state.numbers.abilities["intercede"].cost
    return 0


def _heavy_could_drop(state: FightState, guardian: Hero, dice: tuple[int, int]) -> bool:
    """True when a heavy hit with these dice could take the Guardian to 0 in
    the GM turn it lands.

    That is the heavy hit at its biggest roll, and then, later in the same
    GM turn, the boss's own attack at its biggest, if the boss has Taunt
    cards (so it attacks him). One Last Stand card covers that whole GM
    turn. Guarded cards make each hit smaller by their value.
    """
    guarded = guardian.stacks.get("guarded")
    less = guarded.value if guarded is not None else 0
    most = max(0, dice[0] * dice[1] - less)
    boss = _boss(state)
    if boss is not None and "taunt" in boss.stacks:
        most += max(0, _hit_size(boss, biggest=True) - less)
    return most >= guardian.hp


# --- The Druid's Cleanse -------------------------------------------------------


def _stun_worth_cleansing(druid: Hero, ally: Hero) -> bool:
    """Druid rule 4: `ally` is stunned, and a Cleanse would give them back
    something: an act step still to come this turn (they act after me, in
    id order), or the stun lasts past this turn."""
    stun = ally.stacks.get("stun")
    return stun is not None and (ally.id > druid.id or stun.cards > 1)


# --- The Rogue's targets -------------------------------------------------------


def _full_combo(state: FightState, rogue: Hero) -> bool:
    return rogue.combo >= state.numbers.rules["combo_max"]


def _hidden_elite(state: FightState, rogue: Hero) -> Enemy | None:
    """While the Rogue is hidden: the elite to go for from hiding (see her
    list), or None. This does not know if she has given up waiting for it:
    `RoguePolicy._elite_to_go_for` does."""
    if not rogue.hidden:
        return None
    elites = [
        e for e in state.living_enemies() if e.spec.tier == "elite" and not e.controlled
    ]
    return min(
        elites,
        key=lambda e: (
            not _worth_sapping(state, e),
            -_hit_size(e),
            -e.hp,
            distance(rogue.pos, e.pos),
            e.id,
        ),
        default=None,
    )


def _worth_sapping(state: FightState, enemy: Enemy) -> bool:
    """More than half its HP, and not about to be hit (the hit would wake it)."""
    return _enemy_share(enemy) > SAP_ABOVE and not _about_to_be_hit(state, enemy)


def _eviscerate_target(state: FightState, rogue: Hero) -> Enemy | None:
    """Where the Rogue walks with full combo points: the nearest enemy worth an
    Eviscerate that is not controlled (ties: by id), or None if there is none."""
    worth = [e for e in state.living_enemies() if not e.controlled and _worth_eviscerating(e)]
    return min(worth, key=lambda e: (distance(rogue.pos, e.pos), e.id), default=None)


def _worth_eviscerating(enemy: Enemy) -> bool:
    """An elite, or the boss while it has Taunt cards."""
    if enemy.spec.tier == "boss":
        return "taunt" in enemy.stacks
    return enemy.spec.tier == "elite"


def _should_vanish(state: FightState, rogue: Hero) -> bool:
    """Rogue rule 4: pulled by the boss or an elite, chased by the boss, or low and chased."""
    enemies = [e for e in state.living_enemies() if not e.controlled]
    if any(e.pulled_by == rogue.id and e.spec.tier in ("boss", "elite") for e in enemies):
        return True
    chasers = [e for e in enemies if e.target == rogue.id]
    if any(e.spec.tier == "boss" for e in chasers):
        return True
    if _share(rogue) > VANISH_AT:
        return False
    close = [e for e in _enemies_next_to(state, rogue) if not e.controlled]
    return bool(chasers or close)


def _hit_size(enemy: Enemy, biggest: bool = False) -> float:
    """How hard one of `enemy`'s attacks hits: on average, or at its biggest roll."""
    spec = enemy.spec
    if spec.dice[0] > 0:
        face = spec.dice[1] if biggest else (spec.dice[1] + 1) / 2
        return spec.dice[0] * face + spec.bonus
    return spec.damage


# --- The Mage's choices --------------------------------------------------------


def _meteor_centre(state: FightState, mage: Hero) -> tuple[Pos | None, int]:
    """Mage rule 8: the best square for Meteor and how many enemies it would hit.

    Only enemies that are not controlled are counted. A square is left out
    if a hero who could not walk out stands within Meteor's radius of it,
    or a sapped or sheeped enemy does (the hit would wake it up).
    """
    spec = state.numbers.abilities["meteor"]
    guardians = [h for h in state.up_heroes() if h.cls == "guardian"]
    enemies = [e for e in state.living_enemies() if not e.controlled]
    sleeping = [e.pos for e in state.living_enemies() if _asleep(e)]
    stuck = [
        h.pos
        for h in state.heroes.values()
        if h is mage
        or h.down
        or (h.up and h.cast is not None and not h.cast.is_channel and h.cast.actions_left > 0)
    ]

    def allowed(square: Pos) -> bool:
        if _gap(square, stuck) <= spec.radius or _gap(square, sleeping) <= spec.radius:
            return False
        for guardian in guardians:
            if distance(square, guardian.pos) <= spec.radius and any(
                adjacent(e.pos, guardian.pos) and distance(square, e.pos) <= spec.radius
                for e in enemies
            ):
                return False  # he is holding an enemy it would hit
        return True

    return _best_centre(state, mage.pos, spec.range, spec.radius, enemies, allowed=allowed)


def _ice_block_now(state: FightState, mage: Hero) -> bool:
    """Mage rule 1: is this the moment for Ice Block?"""
    for enemy in state.living_enemies():
        cast = enemy.announced
        if cast is None or cast.lands_round != state.round or enemy.controlled:
            continue
        on_me = (cast.kind == "heavy" and cast.target == mage.id) or (
            cast.kind in ("blast", "stomp") and mage.pos in cast.area
        )
        if not on_me or _answered(state, enemy):
            continue
        most = cast.dice[0] * cast.dice[1]
        for name, kinds in (("guarded", ("heavy", "blast", "stomp")), ("shield_plant", ("blast", "stomp"))):
            if name in mage.stacks and cast.kind in kinds:
                most -= mage.stacks[name].value
        if most < mage.hp:
            continue
        if _ability(state, mage, "disrupt", enemy.id) is None:
            return True
    stuck = mage.stunned or "rooted" in mage.stacks
    near = any(not e.controlled for e in _enemies_next_to(state, mage))
    return stuck and near and _share(mage) <= ICE_BLOCK_AT


def _nothing_needs_the_mage(state: FightState, mage: Hero) -> bool:
    """Mage rule 10: nothing needs her this turn, so she can stand still for Evocation."""
    if any(not e.controlled for e in _enemies_next_to(state, mage)):
        return False
    if mage.pos in _danger(state):
        return False
    reach = state.numbers.abilities["disrupt"].alt
    if any(distance(mage.pos, e.pos) <= reach for e in _casting(state, state.living_enemies())):
        return False
    boss = _boss(state)
    return boss is None or "taunt" in boss.stacks


def _quicken_now(state: FightState, mage: Hero) -> bool:
    """Mage rule 9: is this a good moment for Quicken?"""
    heroes = list(state.heroes.values())
    if not all(h.up for h in heroes) or any("quicken" in h.stacks for h in heroes):
        return False
    used = state.tally.uses[mage.id].get("quicken", 0)
    boss = _boss(state)
    if used == 0:
        taunted = boss is None or "taunt" in boss.stacks
        return state.round >= QUICKEN_ROUND and taunted
    burn = boss is not None and boss.hp <= QUICKEN_BURN * boss.spec.hp
    return used < QUICKEN_MOST and burn


def _blink_square(state: FightState, mage: Hero, threats: list[Enemy]) -> Pos | None:
    """Where Blink should take the Mage away from `threats`, or None if nowhere will do.

    A square will do if it is free, on the map, within Blink's range, out of
    danger, and none of `threats` can reach it this GM turn (its move plus
    its range; a rooted enemy only its range). Of those she picks one in
    spell range of the focus if she can, then the one farthest from every
    enemy (5 or more is as good as farther), then the nearest, then the first
    in (x, y) order.
    """
    spec = state.numbers.abilities["blink"]
    danger = _danger(state)
    taken = state.occupied()
    enemies = [e.pos for e in state.living_enemies()]
    focus = _focus(state, mage)
    spell = state.numbers.abilities["firebolt"].range

    def reach(enemy: Enemy) -> int:
        move = 0 if "rooted" in enemy.stacks else enemy.spec.move
        return move + enemy.spec.range

    squares = [
        square
        for square in within(mage.pos, spec.range, state.fight.width, state.fight.height)
        if square not in taken
        and square not in danger
        and all(distance(square, e.pos) > reach(e) for e in threats)
    ]
    if not squares:
        return None
    return min(
        squares,
        key=lambda square: (
            focus is not None and distance(square, focus.pos) > spell,
            -min(_gap(square, enemies), MAGE_SAFE_GAP),
            distance(mage.pos, square),
            square,
        ),
    )


def _average(spec: AbilitySpec) -> float:
    """The average of one hit of an ability: its dice and its bonus."""
    count, sides = spec.dice
    return count * (sides + 1) / 2 + spec.bonus


# --- Moving --------------------------------------------------------------------


def _mid_cast(hero: Hero) -> bool:
    """True while a cast (not a channel) is going: moving would end it."""
    return hero.cast is not None and not hero.cast.is_channel


def _danger(state: FightState) -> set[Pos]:
    """The squares a hero keeps off: where a blast is going to land.

    That is `state.danger_squares()`, except that while the shield plan is
    on, the squares behind the Guardian's shield are safe from the boss's
    blast (they are still danger if another blast covers them).
    """
    plan = _shield_plan(state)
    if plan is None:
        return state.danger_squares()
    guardian, source = plan
    boss = _boss(state)
    radius = state.numbers.abilities["shield_plant"].radius
    shelter = behind(guardian.pos, source, radius, state.fight.width, state.fight.height)
    other: set[Pos] = set()
    for enemy in state.living_enemies():
        if enemy is not boss and enemy.announced is not None:
            other |= enemy.announced.area
    for area in state.marked.values():
        other |= area
    return other | (boss.announced.area - shelter)


def _go(state: FightState, hero: Hero, goal: Pos, reach: int) -> Pos:
    """Walk toward a square within `reach` of `goal`, ending out of danger if possible.

    The walk is `grid.approach`. If it would end in danger, the hero goes
    instead to the safe square in reach that is closest to where they
    wanted to be (the fewest steps away, if several are just as close).
    """
    dest = approach(
        hero.pos,
        goal,
        state.numbers.rules["hero_move"],
        state.occupied() - {hero.pos},
        state.fight.width,
        state.fight.height,
        reach=reach,
    )
    danger = _danger(state)
    if dest not in danger:
        return dest
    safe = [square for square in _squares_in_reach(state, hero) if square not in danger]
    if not safe:
        return dest
    return min(
        safe,
        key=lambda square: (
            max(0, distance(square, goal) - reach),
            distance(hero.pos, square),
            square,
        ),
    )


def _stay(state: FightState, hero: Hero) -> Pos:
    """Stay put, unless standing in danger: then step to the nearest safe square."""
    return _go(state, hero, hero.pos, reach=0)


def _stand(state: FightState, hero: Hero, goal: Pos, reach: int, worse) -> Pos:
    """Stand within `reach` of `goal`, out of danger, and as good as `worse` says.

    `worse(square)` is smaller for a better square. Of the squares in reach
    this move, the hero picks one out of danger first, then one within
    `reach` of `goal`, then the best by `worse`, then the fewest steps away.
    If no square in reach is close enough to `goal`, the hero walks toward
    it instead (see `_go`).
    """
    danger = _danger(state)
    squares = _squares_in_reach(state, hero)
    if all(distance(square, goal) > reach for square in squares):
        return _go(state, hero, goal, reach)
    return min(
        squares,
        key=lambda square: (
            square in danger,
            distance(square, goal) > reach,
            worse(square),
            distance(hero.pos, square),
            square,
        ),
    )


def _squares_in_reach(state: FightState, hero: Hero) -> list[Pos]:
    """Every square the hero may move to this turn, their own square too.

    That is what the round loop allows: on the map, no farther than
    `hero_move`, and nobody standing there.
    """
    taken = state.occupied() - {hero.pos}
    near = within(
        hero.pos, state.numbers.rules["hero_move"], state.fight.width, state.fight.height
    )
    return sorted(square for square in near if square not in taken)


# --- Small helpers -------------------------------------------------------------


def _ability(
    state: FightState,
    hero: Hero,
    ability: str,
    target: str | None = None,
    pos: Pos | None = None,
    card: str | None = None,
) -> Action | None:
    """The action that uses `ability`, if it can be used right now. Otherwise None."""
    action = Action("ability", ability, target, pos, card)
    return action if can_use(state, hero, ability, action) else None


def _auto(state: FightState, hero: Hero, enemy: Enemy | None) -> Action | None:
    """An auto-attack on `enemy`, if it is in the hero's reach. Otherwise None."""
    reach = state.numbers.heroes[hero.cls].attack_range
    if enemy is None or distance(hero.pos, enemy.pos) > reach:
        return None
    return Action("auto", target=enemy.id)


def _boss(state: FightState) -> Enemy | None:
    """The living boss (the first by id, if there are several), or None."""
    bosses = [e for e in state.living_enemies() if e.spec.tier == "boss"]
    return min(bosses, key=lambda e: e.id, default=None)


def _nearest_enemy(state: FightState, hero: Hero) -> Enemy | None:
    """The nearest of the enemies to hit (see `_to_hit`; ties: by id), or None."""
    return min(
        _to_hit(state), key=lambda enemy: (distance(hero.pos, enemy.pos), enemy.id), default=None
    )


def _to_hit(state: FightState) -> list[Enemy]:
    """The living enemies a hero may attack (see the focus at the top of this file).

    Those that are not controlled. If every one is, the stunned ones; if
    none is stunned, the sapped or sheeped ones.
    """
    living = state.living_enemies()
    return (
        [e for e in living if not e.controlled]
        or [e for e in living if not _asleep(e)]
        or living
    )


def _asleep(enemy: Enemy) -> bool:
    """Sapped or sheeped: it wakes the moment it takes any damage."""
    return any(name in enemy.stacks for name in BROKEN_BY_DAMAGE)


def _about_to_be_hit(state: FightState, enemy: Enemy) -> bool:
    """True when a hero's cast or channel that does damage is aimed at
    `enemy`, or it stands in a hero's marked blast area. A Sap or a sheep
    on it now would only be woken."""
    abilities = state.numbers.abilities
    for hero in state.heroes.values():
        cast = hero.cast
        if cast is not None and cast.target == enemy.id and abilities[cast.ability].dice[0] > 0:
            return True
    return any(enemy.pos in area for area in state.marked.values())


def _up_heroes(state: FightState) -> list[Hero]:
    """Every hero who is up, in id order."""
    return sorted(state.up_heroes(), key=lambda hero: hero.id)


def _enemies_next_to(state: FightState, hero: Hero) -> list[Enemy]:
    """Every living enemy next to `hero`, in id order."""
    near = [e for e in state.living_enemies() if adjacent(e.pos, hero.pos)]
    return sorted(near, key=lambda e: e.id)


def _weakest_next_to(state: FightState, hero: Hero, fodder: bool = True) -> Enemy | None:
    """The enemy next to `hero` with the least HP that is not controlled (ties: by id).

    With `fodder=False` fodder is left out (for an ability aimed at it).
    """
    free = [
        e
        for e in _enemies_next_to(state, hero)
        if not e.controlled and (fodder or e.spec.tier != "fodder")
    ]
    return min(free, key=lambda e: (e.hp, e.id), default=None)


def _loose(state: FightState, enemy: Enemy) -> bool:
    """Neither held by the Guardian, nor taunted, nor controlled."""
    return not held(state, enemy) and "taunt" not in enemy.stacks and not enemy.controlled


def _casting(state: FightState, enemies: list[Enemy]) -> list[Enemy]:
    """The enemies in `enemies` worth an interrupt: an announced cast that is
    not answered, and not controlled.

    A stunned, sapped or sheeped enemy loses its cast anyway (see
    `enemy_ai.land_announced`), so a Disrupt on it would be wasted. So
    would one on a cast a Guardian has already answered (see `_answered`).
    """
    return [
        e
        for e in enemies
        if e.announced is not None and not e.controlled and not _answered(state, e)
    ]


def _shadowstep(state: FightState, rogue: Hero, target: Enemy) -> Action | None:
    """Shadowstep to `target` if it is farther than her move, within
    Shadowstep's range, and Shadowstep can be used now. Otherwise None.

    The move step asks this too, so she waits for it instead of walking. It
    asks with a copy of the Rogue on the square she would stay on, so the
    answer is the one the act step will get from there.
    """
    gap = distance(rogue.pos, target.pos)
    if state.numbers.rules["hero_move"] < gap <= state.numbers.abilities["shadowstep"].range:
        return _ability(state, rogue, "shadowstep", target.id)
    return None


def _on_a_squishy(state: FightState, enemy: Enemy) -> bool:
    """True when `enemy` is going for a Druid or a Mage and is next to them."""
    hero = state.heroes.get(enemy.target) if enemy.target else None
    return hero is not None and hero.cls in ("druid", "mage") and adjacent(hero.pos, enemy.pos)


def _target_class(state: FightState, enemy: Enemy) -> str | None:
    """The class of the hero `enemy` is going for, or None."""
    hero = state.heroes.get(enemy.target) if enemy.target else None
    return None if hero is None else hero.cls


def _best_centre(
    state: FightState,
    origin: Pos,
    reach: int,
    radius: int,
    units: list,
    allowed=lambda square: True,
) -> tuple[Pos | None, int]:
    """The square within `reach` of `origin` whose area covers the most `units`.

    The area is every square within `radius` of it. Only squares that
    `allowed` says yes to count. Gives back the square and how many it
    covers; if several cover just as many, the first in (x, y) order wins.
    (None, 0) when there is no square to choose.
    """
    best, most = None, 0
    for square in sorted(within(origin, reach, state.fight.width, state.fight.height)):
        if not allowed(square):
            continue
        count = sum(1 for unit in units if distance(square, unit.pos) <= radius)
        if count > most:
            best, most = square, count
    return best, most


def _share(hero: Hero) -> float:
    """The hero's HP as a share of their max HP: 1.0 is full."""
    return hero.hp / hero.max_hp


def _enemy_share(enemy: Enemy) -> float:
    """The enemy's HP as a share of its max HP: 1.0 is full."""
    return enemy.hp / enemy.spec.hp


def _lowest(heroes) -> Hero | None:
    """The hero with the lowest share of their max HP (ties: by id), or None."""
    return min(heroes, key=lambda hero: (_share(hero), hero.id), default=None)


def _gap(square: Pos, others: list[Pos]) -> int | float:
    """How far `square` is from the nearest of `others`. Endless when there are none."""
    return min((distance(square, other) for other in others), default=float("inf"))


def _first(items):
    """The first of `items`, or None. Lists of enemies and heroes are in id order."""
    items = list(items)
    return items[0] if items else None
