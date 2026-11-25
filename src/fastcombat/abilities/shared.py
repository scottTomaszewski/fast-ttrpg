"""Abilities every hero has, whatever their class. So far there is one: Disrupt.

Disrupt is the interrupt. It breaks a cast an enemy has announced, so that
cast never lands. Most heroes have to stand next to the enemy to use it; a
Mage reaches much farther. After using it, a hero has to wait a few turns
before using it again. How far it reaches, for a Mage and for everyone
else, and how long the wait is, are in the numbers file.
"""

from fastcombat.abilities import Action, check, effect, target_enemy
from fastcombat.numbers import AbilitySpec
from fastcombat.units import FightState, Hero


@check("disrupt")
def _disrupt_needs_an_enemy_with_an_announced_cast(
    state: FightState, hero: Hero, spec: AbilitySpec, action: Action
) -> bool:
    enemy = target_enemy(state, action)
    return enemy is not None and enemy.announced is not None


@effect("disrupt")
def disrupt(state: FightState, hero: Hero, spec: AbilitySpec, action: Action) -> None:
    """The enemy's announced cast is broken: it will not land."""
    state.enemies[action.target].announced = None
