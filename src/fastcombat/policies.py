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

Some rules use a word that means the same for every class:

- The focus is the enemy to attack. Never one that is stunned, sapped or
  sheeped. First an enemy that has announced a mend; then the other
  enemies that are not a boss, lowest HP first; then the boss. If two are
  just as good, the nearer one, then the one whose id comes first.
- When a rule names an ability aimed at the focus, the focus is chosen
  the same way but only from enemies that are not fodder; if there are
  none, the rule is skipped. Auto-attacks use the normal focus, fodder
  too. So a 1-HP goblin gets an auto-attack, not a Backstab.
- Haul up: a hero next to a downed ally hauls them up, unless a Druid is
  up and has a Seed (then the Druid will heal them).
- Moving: never end on a square where a blast is going to land
  (`state.danger_squares()`) if a free square out of it is in reach. A
  hero who is in the middle of a cast, and safe, stays put. So does a
  hero next to a downed ally they will haul up: that comes before where
  a class likes to stand.

An ally is a hero who is up (not down and not out), unless a rule says
otherwise: "a downed ally" is one who is down. "Lowest" for allies means
the lowest share of their max HP.
"""

from typing import Protocol

from fastcombat.abilities import Action, can_use
from fastcombat.grid import Pos, adjacent, approach, distance, within
from fastcombat.targeting import held
from fastcombat.units import Enemy, FightState, Hero

# How the policies play. These are not game rules: they are how careful or
# greedy each class is, and can be changed to try another way of playing.
# Shares of max HP are written as 0.35 for 35%.
INTERCEDE_AT = 0.5  # Warden: guard an ally at half HP or less
WAR_CRY_ENEMIES = 3  # Warden: War Cry when this many loose enemies are near
SWIFTMEND_AT = 0.35  # Druid: Swiftmend an ally at 35% HP or less
WILD_GROWTH_AT = 0.70  # Druid: allies at 70% HP or less count for Wild Growth
WILD_GROWTH_ALLIES = 3  # Druid: Wild Growth when it covers this many of them
REGROWTH_AT = 0.60  # Druid: Regrowth an ally at 60% HP or less
REJUVENATION_AT = 0.80  # Druid: Rejuvenation on an ally at 80% HP or less...
REJUVENATION_ENERGY = 6  # ...when the Druid has this much energy or more
MAGE_SAFE_GAP = 5  # Mage: likes to stand this far from every enemy; farther is no better
METEOR_ENEMIES = 4  # Mage: Meteor when it would hit this many enemies
QUICKEN_ROUND = 5  # Mage: Quicken from this round on
VOLLEY_TAUNT_CARDS = 3  # Mage: Arcane Volley only on a focus with this many Taunt cards


class Policy(Protocol):
    def move(self, state: FightState, hero: Hero) -> Pos: ...
    def act(self, state: FightState, hero: Hero) -> Action: ...


class AutoOnly:
    """Walk to the nearest living enemy that is not controlled, and auto-attack it.

    It never uses an ability. Nearest is counted in steps; if two enemies
    are just as near, the one whose id comes first. A stunned, sapped or
    sheeped enemy is left alone. With no enemy to go for, it stays put and
    does nothing.
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
    asked: a hero in the middle of a cast stays put, and so does a hero
    next to a downed ally they will haul up. Either way, only while they
    are safe: someone standing in danger still gets out of it.
    """

    hauls_up = True

    def move(self, state: FightState, hero: Hero) -> Pos:
        if _mid_cast(hero) or (self.hauls_up and _haul_up(state, hero)):
            return _stay(state, hero)
        return self.where_to(state, hero)

    def where_to(self, state: FightState, hero: Hero) -> Pos:
        raise NotImplementedError


class WardenPolicy(_ClassPolicy):
    """The Warden. Move: to a square next to the boss (or to the nearest
    enemy if there is no boss), out of danger if possible.

    1. Haul up.
    2. A boss heavy hit is announced on me and it could take me to 0 at its
       maximum roll: Unbroken.
    3. A boss blast is announced and at least one ally stands in its area:
       Bulwark, against the blast coming from the boss's square.
    4. An enemy next to me has an announced cast and is not controlled (a
       stunned, sapped or sheeped enemy's cast never lands): Disrupt.
    5. An ally (not a Warden) at half HP or less is the target of an enemy
       with no Taunt cards: Intercede on the lowest such ally.
    6. The boss has no Taunt cards: Challenge the boss.
    7. Three or more enemies that are neither held nor taunted nor
       controlled are within War Cry's radius: War Cry.
    8. An enemy that is not a boss, and is neither held, taunted nor
       controlled, is in range: Chain Hook the one closest to any ally who
       is not a Warden.
    9. Auto-attack the focus if it is next to me, or else the lowest-HP
       enemy next to me that is not controlled.
    """

    def where_to(self, state: FightState, warden: Hero) -> Pos:
        goal = _boss(state) or _nearest_enemy(state, warden)
        if goal is None:
            return _stay(state, warden)
        return _go(state, warden, goal.pos, reach=1)

    def act(self, state: FightState, warden: Hero) -> Action:
        boss = _boss(state)
        allies = [h for h in _up_heroes(state) if h.cls != "warden"]

        # 1. Haul up.
        if action := _haul_up(state, warden):
            return action

        # 2. A boss heavy hit on me that could take me to 0: Unbroken.
        cast = boss.announced if boss else None
        if cast and cast.kind == "heavy" and cast.target == warden.id:
            most = cast.dice[0] * cast.dice[1]
            guarded = warden.stacks.get("guarded")
            if guarded is not None:
                most -= guarded.value
            if most >= warden.hp:
                if action := _ability(state, warden, "unbroken"):
                    return action

        # 3. A boss blast with an ally in its area: Bulwark against it.
        if cast and cast.kind == "blast" and any(a.pos in cast.area for a in allies):
            if action := _ability(state, warden, "bulwark", pos=boss.pos):
                return action

        # 4. An enemy next to me has an announced cast and is not controlled: Disrupt.
        casting = _first(_casting(_enemies_next_to(state, warden)))
        if casting is not None:
            if action := _ability(state, warden, "disrupt", casting.id):
                return action

        # 5. A hurt ally is the target of an enemy with no Taunt cards: Intercede.
        hunted = {
            e.target for e in state.living_enemies() if "taunt" not in e.stacks
        }
        guard = _lowest(
            a for a in allies if a.id in hunted and _share(a) <= INTERCEDE_AT
        )
        if guard is not None:
            if action := _ability(state, warden, "intercede", guard.id):
                return action

        # 6. The boss has no Taunt cards: Challenge the boss.
        if boss is not None and "taunt" not in boss.stacks:
            if action := _ability(state, warden, "challenge", boss.id):
                return action

        # 7. Three or more loose enemies near me: War Cry.
        near = within(
            warden.pos,
            state.numbers.abilities["war_cry"].radius,
            state.fight.width,
            state.fight.height,
        )
        loose = [e for e in state.living_enemies() if _loose(state, e)]
        if sum(1 for e in loose if e.pos in near) >= WAR_CRY_ENEMIES:
            if action := _ability(state, warden, "war_cry"):
                return action

        # 8. A loose enemy that is not a boss is in range: Chain Hook the one
        # closest to an ally.
        reach = state.numbers.abilities["chain_hook"].range
        hookable = [
            e
            for e in loose
            if e.spec.tier != "boss" and distance(warden.pos, e.pos) <= reach
        ]
        if hookable:
            spots = [a.pos for a in allies]
            hook = min(hookable, key=lambda e: (_gap(e.pos, spots), e.id))
            if action := _ability(state, warden, "chain_hook", hook.id):
                return action

        # 9. Auto-attack the focus if next to me, else the lowest-HP enemy next to me.
        if action := _auto(state, warden, _focus(state, warden)):
            return action
        return _auto(state, warden, _weakest_next_to(state, warden)) or Action("none")


class RoguePolicy(_ClassPolicy):
    """The Rogue. Move: next to the focus her abilities aim at (not fodder),
    or next to the normal focus if there is no such enemy; a square also out
    of danger, if possible. In round 1, while hidden, a shielded enemy that
    can be reached this move comes first, so it can be sapped. If walking
    cannot take her next to the ability focus, but rule 9 can (it is farther
    than her move, within Shadowstep's range, and Shadowstep can be used
    now), she stays put and Shadowsteps in the act step.

    1. Haul up.
    2. Hidden, round 1, and a shielded enemy is next to me (or reachable
       next turn): Sap it, once it is next to me.
    3. An enemy next to me has an announced cast and is not controlled:
       Disrupt, else Cheap Shot.
    4. An enemy is pulled by me: Vanish.
    5. Hidden: Backstab the focus.
    6. Full combo points, and the focus is not the boss, or it is the boss
       with Taunt cards: Eviscerate.
    7. Full combo points, and an enemy next to me that is not a boss and
       not controlled has a Druid or a Mage as its target: Kidney Shot.
    8. Backstab the focus.
    9. The focus is farther than my move and within Shadowstep's range:
       Shadowstep.
    10. Auto-attack the normal focus (fodder too) if it is next to me; or
        else the focus my abilities aim at, if it is next to me; or else the
        lowest-HP enemy next to me that is not controlled.
    """

    def where_to(self, state: FightState, rogue: Hero) -> Pos:
        shielded = _shielded_to_sap(state, rogue)
        if shielded is not None:
            return _go(state, rogue, shielded.pos, reach=1)
        target = _ability_focus(state, rogue)
        if target is None:
            target = _focus(state, rogue)  # only fodder is left
            if target is None:
                return _stay(state, rogue)
            return _go(state, rogue, target.pos, reach=1)
        dest = _go(state, rogue, target.pos, reach=1)
        if not adjacent(dest, target.pos) and _shadowstep(state, rogue, target):
            return _stay(state, rogue)  # rule 9 takes her there in the act step
        return dest

    def act(self, state: FightState, rogue: Hero) -> Action:
        focus = _ability_focus(state, rogue)  # for the abilities aimed at the focus
        full = rogue.combo >= state.numbers.rules["combo_max"]

        # 1. Haul up.
        if action := _haul_up(state, rogue):
            return action

        # 2. Hidden in round 1, with a shielded enemy next to me: Sap it.
        shielded = _shielded_to_sap(state, rogue)
        if shielded is not None and adjacent(rogue.pos, shielded.pos):
            if action := _ability(state, rogue, "sap", shielded.id):
                return action

        # 3. An enemy next to me has an announced cast and is not controlled:
        # Disrupt, else Cheap Shot.
        casting = _first(_casting(_enemies_next_to(state, rogue)))
        if casting is not None:
            if action := _ability(state, rogue, "disrupt", casting.id):
                return action
            if action := _ability(state, rogue, "cheap_shot", casting.id):
                return action

        # 4. An enemy is pulled by me: Vanish.
        if any(e.pulled_by == rogue.id for e in state.living_enemies()):
            if action := _ability(state, rogue, "vanish"):
                return action

        # 5. Hidden: Backstab the focus.
        if rogue.hidden and focus is not None:
            if action := _ability(state, rogue, "backstab", focus.id):
                return action

        # 6. Full combo points on a focus that is not an untaunted boss: Eviscerate.
        if full and focus is not None:
            if focus.spec.tier != "boss" or "taunt" in focus.stacks:
                if action := _ability(state, rogue, "eviscerate", focus.id):
                    return action

        # 7. Full combo points, and an enemy next to me is after a Druid or a Mage:
        # Kidney Shot.
        if full:
            hunter = _first(
                e
                for e in _enemies_next_to(state, rogue)
                if e.spec.tier != "boss"
                and not e.controlled
                and _target_class(state, e) in ("druid", "mage")
            )
            if hunter is not None:
                if action := _ability(state, rogue, "kidney_shot", hunter.id):
                    return action

        # 8. Backstab the focus.
        if focus is not None:
            if action := _ability(state, rogue, "backstab", focus.id):
                return action

        # 9. The focus is farther than my move, and within Shadowstep's range:
        # Shadowstep.
        if focus is not None:
            if action := _shadowstep(state, rogue, focus):
                return action

        # 10. Auto-attack the normal focus if it is next to me (fodder too), else
        # the ability focus if it is next to me, else the weakest enemy next to me.
        if action := _auto(state, rogue, _focus(state, rogue)):
            return action
        if action := _auto(state, rogue, focus):
            return action
        return _auto(state, rogue, _weakest_next_to(state, rogue)) or Action("none")


class DruidPolicy(_ClassPolicy):
    """The Druid. Move: within Rejuvenation range of the Warden (or of the
    lowest-HP ally if there is no Warden), and as far from the nearest enemy
    as that allows. While an ally is down, within reach of them instead.

    1. An ally is down: Swiftmend them, else Nourish them.
    2. An enemy that is pulled by me or next to me could reach me this GM
       turn (its distance to me is at most its move plus its range), and
       is neither controlled nor rooted: Shadowmeld.
    3. An ally is at 35% HP or less: Swiftmend.
    4. In the middle of a cast: continue.
    5. The Warden is up without Rejuvenation cards: Rejuvenation.
    6. Three or more allies at 70% HP or less fit in one Wild Growth area:
       Wild Growth, centred to cover the most.
    7. An ally is at 60% HP or less: Regrowth on the lowest.
    8. An ally has poison: Cleanse.
    9. An ally at 80% HP or less has no Rejuvenation cards and I have 6 or
       more energy: Rejuvenation.
    10. An ally is below full HP: Nourish the lowest.
    11. Auto-attack the focus if it is in range.
    """

    hauls_up = False  # the Druid heals a downed ally from afar instead

    def where_to(self, state: FightState, druid: Hero) -> Pos:
        downed = _first(_downed(state))
        if downed is not None:
            anchor, reach = downed, state.numbers.abilities["swiftmend"].range
        else:
            others = [h for h in _up_heroes(state) if h is not druid]
            anchor = state.warden() or _lowest(others)
            reach = state.numbers.abilities["rejuvenation"].range
        if anchor is None:
            return _stay(state, druid)
        threats = [e.pos for e in state.living_enemies()]
        return _stand(state, druid, anchor.pos, reach, lambda square: -_gap(square, threats))

    def act(self, state: FightState, druid: Hero) -> Action:
        allies = _up_heroes(state)
        abilities = state.numbers.abilities

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

        # 4. In the middle of a cast: continue.
        if druid.cast is not None:
            return Action("continue")

        # 5. The Warden is up without Rejuvenation cards: Rejuvenation.
        warden = state.warden()
        if warden is not None and "rejuvenation" not in warden.stacks:
            if action := _ability(state, druid, "rejuvenation", warden.id):
                return action

        # 6. Three or more hurt allies fit in one Wild Growth area: Wild Growth.
        hurt = [a for a in allies if _share(a) <= WILD_GROWTH_AT]
        spec = abilities["wild_growth"]
        centre, count = _best_centre(state, druid.pos, spec.range, spec.radius, hurt)
        if count >= WILD_GROWTH_ALLIES:
            if action := _ability(state, druid, "wild_growth", pos=centre):
                return action

        # 7. An ally is at 60% HP or less: Regrowth on the lowest.
        low = _lowest(a for a in allies if _share(a) <= REGROWTH_AT)
        if low is not None:
            if action := _ability(state, druid, "regrowth", low.id):
                return action

        # 8. An ally has poison: Cleanse.
        poisoned = _first(a for a in allies if "poison" in a.stacks)
        if poisoned is not None:
            if action := _ability(state, druid, "cleanse", poisoned.id):
                return action

        # 9. An ally at 80% HP or less has no Rejuvenation cards, and I have
        # the energy: Rejuvenation.
        bare = _lowest(
            a
            for a in allies
            if _share(a) <= REJUVENATION_AT and "rejuvenation" not in a.stacks
        )
        if bare is not None and druid.resource >= REJUVENATION_ENERGY:
            if action := _ability(state, druid, "rejuvenation", bare.id):
                return action

        # 10. An ally is below full HP: Nourish the lowest.
        scratched = _lowest(a for a in allies if a.hp < a.max_hp)
        if scratched is not None:
            if action := _ability(state, druid, "nourish", scratched.id):
                return action

        # 11. Auto-attack the focus if it is in range.
        return _auto(state, druid, _focus(state, druid)) or Action("none")


class MagePolicy(_ClassPolicy):
    """The Mage. Move: in spell range of the focus, and as far from the
    nearest enemy as she can get this move, up to 5 squares: any square 5
    or more from every enemy is just as good as another. While casting (not
    channelling), stay still unless standing in danger.

    1. Haul up.
    2. In the middle of a cast or a channel: continue.
    3. An enemy that is not controlled is next to me and not rooted: Frost Ring.
    4. An enemy in range has an announced cast and is not controlled:
       Disrupt.
    5. No enemy is a sheep, no hero is in the middle of casting Polymorph
       (another Mage's sheep is on its way), and at least two enemies are
       alive that are not controlled, not a boss and not fodder: Polymorph
       the one of them with the most HP that nobody is next to.
    6. Some square in range has four or more living enemies, and no hero,
       within Meteor's radius: Meteor on the square that covers the most.
    7. Round 5 or later, every hero is up, and no hero has Quicken cards:
       Quicken.
    8. The focus has three or more Taunt cards: Arcane Volley.
    9. Firebolt the focus.
    10. Auto-attack the focus if it is in range.
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

        # 1. Haul up.
        if action := _haul_up(state, mage):
            return action

        # 2. In the middle of a cast or a channel: continue.
        if mage.cast is not None:
            return Action("continue")

        # 3. A loose enemy next to me that is not rooted: Frost Ring.
        if any(
            not e.controlled and "rooted" not in e.stacks
            for e in _enemies_next_to(state, mage)
        ):
            if action := _ability(state, mage, "frost_ring"):
                return action

        # 4. An enemy in range has an announced cast and is not controlled: Disrupt.
        for casting in _casting(sorted(enemies, key=lambda e: e.id)):
            if action := _ability(state, mage, "disrupt", casting.id):
                return action

        # 5. No sheep yet, none on its way, and two or more enemies worth one:
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
            ]
            sheep = min(alone, key=lambda e: (-e.hp, e.id), default=None)
            if sheep is not None:
                if action := _ability(state, mage, "polymorph", sheep.id):
                    return action

        # 6. A square in range with four or more enemies and no hero: Meteor.
        spec = state.numbers.abilities["meteor"]
        heroes = [h.pos for h in state.heroes.values() if not h.out]

        def no_hero_near(square: Pos) -> bool:
            return _gap(square, heroes) > spec.radius

        centre, count = _best_centre(
            state, mage.pos, spec.range, spec.radius, enemies, allowed=no_hero_near
        )
        if count >= METEOR_ENEMIES:
            if action := _ability(state, mage, "meteor", pos=centre):
                return action

        # 7. Round 5 or later, everyone up, nobody quickened: Quicken.
        everyone_up = all(h.up for h in state.heroes.values())
        if (
            state.round >= QUICKEN_ROUND
            and everyone_up
            and not any("quicken" in h.stacks for h in state.heroes.values())
        ):
            if action := _ability(state, mage, "quicken"):
                return action

        # 8. The focus has three or more Taunt cards: Arcane Volley.
        taunt = focus.stacks.get("taunt") if focus else None
        if taunt is not None and taunt.cards >= VOLLEY_TAUNT_CARDS:
            if action := _ability(state, mage, "arcane_volley", focus.id):
                return action

        # 9. Firebolt the focus.
        if focus is not None:
            if action := _ability(state, mage, "firebolt", focus.id):
                return action

        # 10. Auto-attack the focus if it is in range (fodder too).
        return _auto(state, mage, _focus(state, mage)) or Action("none")


# Every policy by name, so one can be picked by its name.
POLICIES: dict[str, type] = {
    "warden": WardenPolicy,
    "rogue": RoguePolicy,
    "druid": DruidPolicy,
    "mage": MagePolicy,
    "auto": AutoOnly,
}


def default_policy(cls: str) -> Policy:
    """The policy a hero of class `cls` plays by when nobody picks one.

    Each of the four classes has its own. Any other class only auto-attacks.
    """
    if cls in ("warden", "rogue", "druid", "mage"):
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
        for enemy in state.living_enemies()
        if not enemy.controlled and (fodder or enemy.spec.tier != "fodder")
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


# --- Moving --------------------------------------------------------------------


def _mid_cast(hero: Hero) -> bool:
    """True while a cast (not a channel) is going: moving would end it."""
    return hero.cast is not None and not hero.cast.is_channel


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
    danger = state.danger_squares()
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
    danger = state.danger_squares()
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
) -> Action | None:
    """The action that uses `ability`, if it can be used right now. Otherwise None."""
    action = Action("ability", ability, target, pos)
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
    """The nearest living enemy that is not controlled (ties: by id), or None."""
    free = [enemy for enemy in state.living_enemies() if not enemy.controlled]
    return min(free, key=lambda enemy: (distance(hero.pos, enemy.pos), enemy.id), default=None)


def _up_heroes(state: FightState) -> list[Hero]:
    """Every hero who is up, in id order."""
    return sorted(state.up_heroes(), key=lambda hero: hero.id)


def _enemies_next_to(state: FightState, hero: Hero) -> list[Enemy]:
    """Every living enemy next to `hero`, in id order."""
    near = [e for e in state.living_enemies() if adjacent(e.pos, hero.pos)]
    return sorted(near, key=lambda e: e.id)


def _weakest_next_to(state: FightState, hero: Hero) -> Enemy | None:
    """The enemy next to `hero` with the least HP that is not controlled (ties: by id)."""
    free = [e for e in _enemies_next_to(state, hero) if not e.controlled]
    return min(free, key=lambda e: (e.hp, e.id), default=None)


def _loose(state: FightState, enemy: Enemy) -> bool:
    """Neither held by the Warden, nor taunted, nor controlled."""
    return not held(state, enemy) and "taunt" not in enemy.stacks and not enemy.controlled


def _casting(enemies: list[Enemy]) -> list[Enemy]:
    """The enemies in `enemies` worth a Disrupt: an announced cast, and not controlled.

    A stunned, sapped or sheeped enemy loses its cast anyway (see
    `enemy_ai.land_announced`), so a Disrupt on it would be wasted.
    """
    return [e for e in enemies if e.announced is not None and not e.controlled]


def _shadowstep(state: FightState, rogue: Hero, focus: Enemy) -> Action | None:
    """Rogue rule 9: Shadowstep to `focus` if it is farther than her move, within
    Shadowstep's range, and Shadowstep can be used now. Otherwise None.

    The move step asks this too, so she waits for it instead of walking.
    """
    gap = distance(rogue.pos, focus.pos)
    if state.numbers.rules["hero_move"] < gap <= state.numbers.abilities["shadowstep"].range:
        return _ability(state, rogue, "shadowstep", focus.id)
    return None


def _shielded_to_sap(state: FightState, rogue: Hero) -> Enemy | None:
    """In round 1, while hidden: a shielded enemy (not a boss) the Rogue can get
    next to this move.

    The nearest one, then by id. None if there is none, or it is not round 1,
    or the Rogue is not hidden.
    """
    if state.round != 1 or not rogue.hidden:
        return None
    reach = state.numbers.rules["hero_move"] + 1
    shielded = [
        e
        for e in state.living_enemies()
        if e.spec.shielded > 0
        and e.spec.tier != "boss"
        and not e.controlled
        and distance(rogue.pos, e.pos) <= reach
    ]
    return min(shielded, key=lambda e: (distance(rogue.pos, e.pos), e.id), default=None)


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
