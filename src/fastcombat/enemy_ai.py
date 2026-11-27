"""The GM turn: what the enemies do.

The GM turn has five steps, in this order:

1. Enemy casts that were announced last GM turn land (`land_announced`).
2. Enemies due to arrive this round come in.
3. Each enemy, in id order, picks who to attack, moves, and attacks. Then
   the boss throws, if its script has a throw due this round (`throw`).
4. The boss, and any enemy that heals it, announce what they will do next
   (`announce`).
5. One card comes off every stack on every enemy.

The boss plays a script from the fight file. Each step in the script comes
up first in one round, then again every few rounds. A blast or a heavy hit
is announced one GM turn before it lands, so the heroes have a party turn
to get out of the way, get ready for it, or break it with Disrupt or a
stun. A throw is not announced: it happens at once, in the boss's turn.
"""

from fastcombat.combat import add_stack, damage_hero, tick_stacks
from fastcombat.grid import adjacent, approach, distance, nearest_free, within
from fastcombat.numbers import ScriptStep
from fastcombat.targeting import can_move, choose_target, seen_heroes
from fastcombat.units import CONTROL_STACKS, Announced, Enemy, FightState, Hero


def gm_turn(state: FightState) -> None:
    """Play the GM turn: all five steps above."""
    land_announced(state)
    _spawn(state)
    for enemy in sorted(state.living_enemies(), key=lambda enemy: enemy.id):
        if enemy.controlled:
            # A stunned, sapped or sheeped enemy does nothing, so it is
            # attacking nobody: it forgets who it went for last turn, and
            # any pull on it is used up, as a pull is after a normal turn.
            enemy.target = None
            enemy.pulled_by = None
            _count_turn_lost(state, enemy)
        else:
            _take_turn(state, enemy)
    announce(state)
    for enemy in state.living_enemies():
        tick_stacks(enemy)


def _count_turn_lost(state: FightState, enemy: Enemy) -> None:
    """Write down, for the report, which control cards cost `enemy` this turn."""
    lost = state.tally.rounds_out
    for name in CONTROL_STACKS:
        if name in enemy.stacks:
            lost[name] = lost.get(name, 0) + 1


def land_announced(state: FightState) -> None:
    """Step 1: enemy casts announced last GM turn land now.

    A blast makes one roll, and every hero who is up and still in its area
    takes all of it; someone who walked out is safe. A heavy hit lands on
    the hero it was aimed at, if they are still up. A mend heals every
    living boss, never past its full HP. A cast is used up once it lands.

    An enemy that is stunned, sapped or sheeped now loses its cast, and it
    does not land.
    """
    for enemy in sorted(state.living_enemies(), key=lambda enemy: enemy.id):
        cast = enemy.announced
        if cast is None or cast.lands_round != state.round:
            continue
        enemy.announced = None
        if not enemy.controlled:
            _land(state, enemy, cast)


def announce(state: FightState) -> None:
    """Step 4: enemies announce their casts, one GM turn before they land.

    The boss announces at most one move from its script: the first blast or
    heavy hit that is due this round. A blast covers every square near
    where the boss stands now, and those squares are marked on the map (see
    `FightState.danger_squares`). A heavy hit is aimed at the hero the boss
    went for this turn. If it went for nobody, or that hero is not up any
    more, it has no heavy hit to announce, and the next move due is looked
    at instead.

    An enemy that heals the boss (one with `cast_every` in the fight file,
    like the shaman) announces a mend when one is due, unless it is
    stunned, sapped or sheeped.

    An enemy with a cast already waiting announces nothing new.
    """
    for enemy in sorted(state.living_enemies(), key=lambda enemy: enemy.id):
        if enemy.announced is None and enemy.spec.tier == "boss":
            enemy.announced = _boss_cast(state, enemy)
        if enemy.announced is None and _mend_due(state, enemy):
            enemy.announced = Announced(
                "mend",
                "mend",
                state.round + 1,
                None,
                frozenset(),
                (0, 0),
                heal=enemy.spec.cast_heal,
            )


def throw(state: FightState, boss: Enemy, step: ScriptStep) -> None:
    """The boss throws something (like the boulder) at one hero not next to it.

    A die with one side for each hero who is up, not hidden, and not next
    to the boss picks who, counting them in id order. Taunts make no
    difference: a throw is not the boss's attack, so it gives a Guardian no
    grit either. If there is no such hero, nothing is thrown and no die is
    rolled.
    """
    far = sorted(
        (hero for hero in seen_heroes(state) if not adjacent(hero.pos, boss.pos)),
        key=lambda hero: hero.id,
    )
    if not far:
        return
    hero = far[state.dice.roll(len(far)) - 1]
    damage_hero(state, hero, state.dice.roll_many(*step.dice), attacker=None)


def _land(state: FightState, enemy: Enemy, cast: Announced) -> None:
    """`enemy`'s announced `cast` happens now. See `land_announced`."""
    if cast.kind == "blast":
        amount = state.dice.roll_many(*cast.dice)
        for hero in state.up_heroes():
            if hero.pos in cast.area:
                damage_hero(state, hero, amount, attacker=enemy, blast=True)
    elif cast.kind == "heavy":
        hero = _up_hero(state, cast.target)
        if hero is not None:
            damage_hero(state, hero, state.dice.roll_many(*cast.dice), attacker=enemy)
    elif cast.kind == "mend":
        for boss in state.living_enemies():
            if boss.spec.tier == "boss":
                boss.hp = min(boss.spec.hp, boss.hp + cast.heal)
    else:
        raise ValueError(f"{enemy.id} announced a {cast.kind!r}: no such cast")


def _boss_cast(state: FightState, boss: Enemy) -> Announced | None:
    """The blast or heavy hit `boss` announces this round, or None. See `announce`.

    A throw in the script is never announced, so it is passed over here.
    """
    lands = state.round + 1
    for step in state.fight.boss_script:
        if not _due(state, step.first, step.every):
            continue
        if step.kind == "blast":
            area = within(boss.pos, step.radius, state.fight.width, state.fight.height)
            return Announced(
                step.name, "blast", lands, None, frozenset(area), step.dice
            )
        if step.kind == "heavy" and _up_hero(state, boss.target) is not None:
            return Announced(
                step.name, "heavy", lands, boss.target, frozenset(), step.dice
            )
    return None


def _mend_due(state: FightState, enemy: Enemy) -> bool:
    """True when `enemy` heals the boss, a mend is due this round, and nothing controls it."""
    spec = enemy.spec
    return (
        spec.cast_every > 0
        and not enemy.controlled
        and _due(state, spec.cast_first, spec.cast_every)
    )


def _due(state: FightState, first: int, every: int) -> bool:
    """True when something that comes up first in round `first`, then every
    `every` rounds, comes up this round."""
    return state.round >= first and (state.round - first) % every == 0


def _up_hero(state: FightState, hero_id: str | None) -> Hero | None:
    """The hero called `hero_id`, if there is one and they are up. Otherwise None."""
    hero = state.heroes.get(hero_id) if hero_id else None
    return hero if hero is not None and hero.up else None


def _spawn(state: FightState) -> None:
    """Step 2: every enemy due this round comes in on its square.

    If someone stands there, it comes in on the nearest free square instead.
    """
    for spawn in state.fight.spawns:
        if spawn.round != state.round:
            continue
        square = nearest_free(
            spawn.pos, state.occupied(), state.fight.width, state.fight.height
        )
        if square is not None:  # None only when the whole map is full
            state.add_enemy(spawn.type, square)


def _take_turn(state: FightState, enemy: Enemy) -> None:
    """Step 3, for one enemy: pick a target, move toward it, hit it if it can.

    The enemy writes down who it went for in `enemy.target`, for the heroes
    to see. A pull lasts one turn, so it is used up here. The boss then
    throws whatever its script has due this round.
    """
    target = choose_target(state, enemy)
    enemy.target = target.id if target is not None else None
    if target is not None:
        if can_move(state, enemy):
            enemy.pos = approach(
                enemy.pos,
                target.pos,
                enemy.spec.move,
                state.occupied(),
                state.fight.width,
                state.fight.height,
                reach=enemy.spec.range,
            )
        if distance(enemy.pos, target.pos) <= enemy.spec.range:
            _hit(state, enemy, target)
    if enemy.spec.tier == "boss":
        # Always the melee hit first, then the throw, so the dice are always
        # rolled in the same order, and the throw is aimed from where the
        # boss ended up after moving.
        for step in state.fight.boss_script:
            if step.kind == "throw" and _due(state, step.first, step.every):
                throw(state, enemy, step)
    enemy.pulled_by = None


def _hit(state: FightState, enemy: Enemy, hero: Hero) -> None:
    """`enemy` attacks `hero`.

    Most enemies hit for a set number. One with dice (like the boss) rolls
    them instead. A poisoner also hands over poison cards, unless the hit
    took the hero down.
    """
    spec = enemy.spec
    if spec.dice[0] > 0:
        amount = state.dice.roll_many(*spec.dice, spec.bonus)
    else:
        amount = spec.damage
    damage_hero(state, hero, amount, attacker=enemy)
    if spec.poison_cards > 0 and hero.up:
        add_stack(hero, "poison", spec.poison_cards, spec.poison_value)
