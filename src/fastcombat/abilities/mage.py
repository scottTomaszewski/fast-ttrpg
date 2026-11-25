"""The Mage's seven abilities. The Mage stands far back and does the big
damage, to one enemy or to a whole area. It can also hold enemies in place,
turn one into a sheep, hop away, and make the whole party attack faster.

Each ability's numbers (what it costs, how long it takes, how far it
reaches, its dice and how many cards it gives) are in the numbers file.

Three words used below. A cast takes a round or more and lands at the top of
a later party turn; Firebolt, Meteor and Polymorph are casts. A channel
makes one hit in each act step, and each hit is paid for on its own; Arcane
Volley is a channel (see `casting.py`). The area of a blast is every square
within its radius of the square it is aimed at.
"""

from fastcombat.abilities import Action, check, effect, target_enemy
from fastcombat.combat import add_stack, control, damage_enemy, damage_hero
from fastcombat.grid import adjacent, within
from fastcombat.numbers import AbilitySpec
from fastcombat.units import FightState, Hero


@check("arcane_volley")
def _arcane_volley_needs_an_enemy(
    state: FightState, mage: Hero, spec: AbilitySpec, action: Action
) -> bool:
    return target_enemy(state, action) is not None


@effect("arcane_volley")
def arcane_volley(
    state: FightState, mage: Hero, spec: AbilitySpec, action: Action
) -> None:
    """One hit of the channel on its enemy. Each hit is Loud on its own."""
    _hit(state, mage, spec, action)


@check("firebolt")
def _firebolt_needs_an_enemy(
    state: FightState, mage: Hero, spec: AbilitySpec, action: Action
) -> bool:
    return target_enemy(state, action) is not None


@effect("firebolt")
def firebolt(state: FightState, mage: Hero, spec: AbilitySpec, action: Action) -> None:
    """One big hit on one enemy, when the cast lands."""
    _hit(state, mage, spec, action)


@check("meteor")
def _meteor_needs_a_centre(
    state: FightState, mage: Hero, spec: AbilitySpec, action: Action
) -> bool:
    return action.pos is not None


@effect("meteor")
def meteor(state: FightState, mage: Hero, spec: AbilitySpec, action: Action) -> None:
    """The blast lands: one roll, and everyone in the area takes all of it.

    That is every living enemy there, and every hero there who is up, the
    Mage too. For a hero it counts as a blast, so Bulwark makes it smaller.
    A hero who is down is left alone.
    """
    amount = state.dice.roll_many(*spec.dice, spec.bonus)
    area = within(action.pos, spec.radius, state.fight.width, state.fight.height)
    for enemy in state.living_enemies():
        if enemy.pos in area:
            damage_enemy(state, mage.id, enemy, amount, loud=spec.loud)
    for hero in state.up_heroes():
        if hero.pos in area:
            damage_hero(state, hero, amount, attacker=None, blast=True)


@effect("frost_ring")
def frost_ring(
    state: FightState, mage: Hero, spec: AbilitySpec, action: Action
) -> None:
    """Rooted cards on every living enemy next to the Mage.

    While the cards last, the enemy cannot move. A boss gets them too:
    being rooted is not a stun, so the enemy can still attack.
    """
    for enemy in state.living_enemies():
        if adjacent(enemy.pos, mage.pos):
            add_stack(enemy, "rooted", spec.cards)


@check("blink")
def _blink_needs_a_free_square(
    state: FightState, mage: Hero, spec: AbilitySpec, action: Action
) -> bool:
    """A square on the map where nobody stands. The reach is checked for every ability."""
    if action.pos is None:
        return False
    x, y = action.pos
    on_map = 0 <= x < state.fight.width and 0 <= y < state.fight.height
    return on_map and action.pos not in state.occupied()


@effect("blink")
def blink(state: FightState, mage: Hero, spec: AbilitySpec, action: Action) -> None:
    """The Mage is on that square at once, without walking there."""
    mage.pos = action.pos


@effect("quicken")
def quicken(state: FightState, mage: Hero, spec: AbilitySpec, action: Action) -> None:
    """Quicken cards on every hero who is up, the Mage too.

    While the cards last, their auto-attacks roll two dice (see
    `fight.auto_attack`).
    """
    for hero in state.up_heroes():
        add_stack(hero, "quicken", spec.cards)


@check("polymorph")
def _polymorph_needs_an_enemy_that_is_not_a_boss(
    state: FightState, mage: Hero, spec: AbilitySpec, action: Action
) -> bool:
    enemy = target_enemy(state, action)
    return enemy is not None and enemy.spec.tier != "boss"


@effect("polymorph")
def polymorph(state: FightState, mage: Hero, spec: AbilitySpec, action: Action) -> None:
    """The enemy is a sheep: it does nothing until its cards run out or it is hit.

    Only one enemy is a sheep at a time, so when this lands, any other
    sheep turns back.
    """
    target = state.enemies[action.target]
    for enemy in state.enemies.values():
        if enemy is not target:
            enemy.stacks.pop("sheep", None)
    control(state, target, "sheep", spec.cards)


def _hit(state: FightState, mage: Hero, spec: AbilitySpec, action: Action) -> None:
    """One hit with the ability's dice and bonus on the enemy `action` is aimed at."""
    amount = state.dice.roll_many(*spec.dice, spec.bonus)
    damage_enemy(state, mage.id, state.enemies[action.target], amount, loud=spec.loud)
