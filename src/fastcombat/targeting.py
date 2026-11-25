"""Who an enemy attacks, and whether it may walk away.

Nobody keeps track of anger or threat. An enemy's target comes from a short
list of rules, read from the top; the first one that names a hero who is up
wins:

1. Taunt cards on the enemy: it must go for the Warden, wherever they are.
2. A pull: a Loud hero made it angry, so it goes for that hero.
3. A hold: it is standing next to the Warden, so it must hit the Warden.
4. Otherwise it goes for whoever its kind likes best (see `choose_target`).

"The Warden" is always the first Warden in the party who is up.
"""

from fastcombat.grid import adjacent, distance
from fastcombat.units import Enemy, FightState, Hero


def held(state: FightState, enemy: Enemy) -> bool:
    """True when the enemy stands next to the Warden (the weak hold)."""
    warden = state.warden()
    return warden is not None and adjacent(enemy.pos, warden.pos)


def choose_target(state: FightState, enemy: Enemy) -> Hero | None:
    """The hero `enemy` attacks this turn, or None when no hero is up.

    After the rules at the top of this file pick a hero, one more rule:
    if that hero has Interceded cards, the enemy has no Taunt cards, and the
    Warden is up, the Warden steps in and is attacked instead.
    """
    up = sorted(state.up_heroes(), key=lambda hero: hero.id)
    if not up:
        return None
    warden = state.warden()
    target = _first_rule_that_names_a_hero(state, enemy, warden, up)
    if (
        "interceded" in target.stacks
        and "taunt" not in enemy.stacks
        and warden is not None
    ):
        return warden
    return target


def _first_rule_that_names_a_hero(
    state: FightState, enemy: Enemy, warden: Hero | None, up: list[Hero]
) -> Hero:
    """Rules 1 to 4. `up` is every hero who is up, in id order, and is never empty."""
    if "taunt" in enemy.stacks and warden is not None:
        return warden
    puller = state.heroes.get(enemy.pulled_by) if enemy.pulled_by else None
    if puller is not None and puller.up:
        return puller
    if held(state, enemy):
        return warden
    if enemy.spec.prefers == "nearest":
        return min(up, key=lambda hero: (distance(enemy.pos, hero.pos), hero.id))
    if enemy.spec.prefers == "backline":
        # The weakest hero who is not a Warden. A Warden only if nobody else is up.
        others = [hero for hero in up if hero.cls != "warden"] or up
        return min(others, key=lambda hero: (hero.max_hp, hero.id))
    # "random": a die with one side for each hero who is up.
    return up[state.dice.roll(len(up)) - 1]


def can_move(state: FightState, enemy: Enemy) -> bool:
    """False when the enemy must stay where it is this turn.

    A hold keeps it next to the Warden, unless a pull is dragging it away.
    Rooted cards keep it in place, and so does a stun, sap or sheep.
    """
    if held(state, enemy) and enemy.pulled_by is None:
        return False
    return "rooted" not in enemy.stacks and not enemy.controlled


def apply_loud(state: FightState, hero_id: str, enemy: Enemy) -> None:
    """`hero_id` hit `enemy` with something Loud.

    If the enemy has Taunt cards, one comes off. If it has none, it is
    pulled: it goes for that hero on its next turn.
    """
    taunt = enemy.stacks.get("taunt")
    if taunt is None:
        enemy.pulled_by = hero_id
        return
    taunt.cards -= 1
    if taunt.cards <= 0:
        del enemy.stacks["taunt"]


def loud_heal(state: FightState, hero_id: str) -> None:
    """A Loud heal by `hero_id` pulls every living enemy that nothing holds.

    An enemy with Taunt cards, or one standing next to the Warden, stays put.
    """
    for enemy in state.living_enemies():
        if "taunt" not in enemy.stacks and not held(state, enemy):
            enemy.pulled_by = hero_id


def drop_pulls(state: FightState, hero_id: str) -> None:
    """Every enemy pulled by `hero_id` lets go of them."""
    for enemy in state.enemies.values():
        if enemy.pulled_by == hero_id:
            enemy.pulled_by = None
