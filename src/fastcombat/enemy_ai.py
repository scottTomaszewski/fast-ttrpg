"""The GM turn: what the enemies do.

The GM turn has five steps, in this order:

1. Enemy casts that were announced last GM turn land (`land_announced`).
2. Enemies due to arrive this round come in.
3. Each enemy, in id order, picks who to attack, moves, and attacks.
4. The boss announces what it will do next (`announce`).
5. One card comes off every stack on every enemy.
"""

from fastcombat.combat import add_stack, damage_hero, tick_stacks
from fastcombat.grid import approach, distance, nearest_free
from fastcombat.targeting import can_move, choose_target
from fastcombat.units import Enemy, FightState, Hero


def gm_turn(state: FightState) -> None:
    """Play the GM turn: all five steps above."""
    land_announced(state)
    _spawn(state)
    for enemy in sorted(state.living_enemies(), key=lambda enemy: enemy.id):
        if not enemy.controlled:  # a stunned, sapped or sheeped enemy does nothing
            _take_turn(state, enemy)
    announce(state)
    for enemy in state.living_enemies():
        tick_stacks(enemy)


def land_announced(state: FightState) -> None:
    """Step 1: enemy casts announced last GM turn land now.

    Not made yet: it comes with the boss's script. Until then nothing is
    ever announced, so there is nothing to land.
    """


def announce(state: FightState) -> None:
    """Step 4: the boss announces its next big moves, a turn before they land.

    Not made yet: it comes with the boss's script.
    """


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
    to see. A pull lasts one turn, so it is used up here.
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
