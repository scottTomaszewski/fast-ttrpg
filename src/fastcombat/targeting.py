"""Who an enemy attacks, and whether it may walk away.

Nobody keeps track of anger or threat. An enemy's target comes from a short
list of rules, read from the top; the first one that names a hero who is up
wins:

1. Taunt cards on the enemy: it must go for the Guardian, wherever they are.
2. A pull: a Loud hero made it angry, so it goes for that hero.
3. A hold: it is standing next to the Guardian, so it must hit the Guardian.
   A boss ignores this hold: only Taunt cards make a boss attack the Guardian.
4. Otherwise it goes for whoever its kind likes best (see `choose_target`).

"The Guardian" is always the first Guardian in the party who is up.

An enemy never picks a hero who is hidden, by any of these rules. A pull by
a hero who is hidden counts as no pull. If every hero who is up is hidden,
the enemy has nobody to go for. (A blast still hits a hidden hero who
stands in its area: it is aimed at a square, not at a hero.) A Mage in an
Ice Block is the same as hidden here: no enemy picks her, and her pull
counts for nothing. (A blast does her no harm either; see
`combat.damage_hero`.)
"""

from fastcombat.grid import adjacent, distance
from fastcombat.units import Enemy, FightState, Hero


def held(state: FightState, enemy: Enemy) -> bool:
    """True when the enemy stands next to the Guardian (the weak hold).

    Never true for a boss. A boss may walk away from the Guardian and hit
    someone else; only Taunt cards make it attack him.
    """
    if enemy.spec.tier == "boss":
        return False
    guardian = state.guardian()
    return guardian is not None and adjacent(enemy.pos, guardian.pos)


def choose_target(state: FightState, enemy: Enemy) -> Hero | None:
    """The hero `enemy` attacks this turn, or None when no hero is up and seen.

    After the rules at the top of this file pick a hero, one more rule:
    if that hero has Interceded cards, the enemy has no Taunt cards, and the
    Guardian is up, the Guardian steps in and is attacked instead. A hidden hero
    is never picked, by any rule.
    """
    up = sorted(seen_heroes(state), key=lambda hero: hero.id)
    if not up:
        return None
    guardian = state.guardian()
    if guardian is not None and guardian.hidden:
        guardian = None
    target = _first_rule_that_names_a_hero(state, enemy, guardian, up)
    if (
        "interceded" in target.stacks
        and "taunt" not in enemy.stacks
        and guardian is not None
    ):
        return guardian
    return target


def _first_rule_that_names_a_hero(
    state: FightState, enemy: Enemy, guardian: Hero | None, up: list[Hero]
) -> Hero:
    """Rules 1 to 4. `up` is every hero who is up and not hidden, in id order,
    and is never empty. `guardian` is None if the Guardian is hidden."""
    if "taunt" in enemy.stacks and guardian is not None:
        return guardian
    puller = puller_of(state, enemy)
    if puller is not None:
        return puller
    if held(state, enemy) and guardian is not None:
        return guardian
    if enemy.spec.prefers == "nearest":
        return min(up, key=lambda hero: (distance(enemy.pos, hero.pos), hero.id))
    if enemy.spec.prefers == "backline":
        # The weakest hero who is not a Guardian. A Guardian only if nobody else is up.
        others = [hero for hero in up if hero.cls != "guardian"] or up
        return min(others, key=lambda hero: (hero.max_hp, hero.id))
    # "random": a die with one side for each hero who is up.
    return up[state.dice.roll(len(up)) - 1]


def can_move(state: FightState, enemy: Enemy) -> bool:
    """False when the enemy must stay where it is this turn.

    A hold keeps it next to the Guardian, unless a pull is dragging it away
    (a pull by a hero who is down, out or hidden counts for nothing). Rooted cards
    keep it in place, and so does a stun, sap or sheep.
    """
    if held(state, enemy) and puller_of(state, enemy) is None:
        return False
    return "rooted" not in enemy.stacks and not enemy.controlled


def seen_heroes(state: FightState) -> list[Hero]:
    """Every hero an enemy can pick: up, not hidden, and not in an Ice Block."""
    return [hero for hero in state.up_heroes() if not hero.hidden and not hero.iced]


def puller_of(state: FightState, enemy: Enemy) -> Hero | None:
    """The hero who pulled `enemy`, if that hero is up, not hidden and not in
    an Ice Block. Otherwise None."""
    hero = state.heroes.get(enemy.pulled_by) if enemy.pulled_by else None
    if hero is None or not hero.up or hero.hidden or hero.iced:
        return None
    return hero


def apply_loud(state: FightState, hero_id: str, enemy: Enemy) -> None:
    """`hero_id` hit `enemy` with something Loud.

    If the enemy has Taunt cards, one comes off; a boss loses
    `boss_loud_cards` of them (from the rules in the numbers file). If it
    has fewer than that, they all come off, and the rest of the hit does not
    pull. If it has none, it is pulled: it goes for that hero on its next
    turn.
    """
    taunt = enemy.stacks.get("taunt")
    if taunt is None:
        enemy.pulled_by = hero_id
        return
    cards = state.numbers.rules["boss_loud_cards"] if enemy.spec.tier == "boss" else 1
    taunt.cards = max(0, taunt.cards - cards)
    if taunt.cards <= 0:
        del enemy.stacks["taunt"]


def loud_heal(state: FightState, hero_id: str) -> None:
    """A Loud heal by `hero_id` pulls every living enemy that nothing holds.

    An enemy with Taunt cards stays put, and so does one standing next to
    the Guardian, unless it is a boss (nothing but Taunt cards holds a boss).
    """
    for enemy in state.living_enemies():
        if "taunt" not in enemy.stacks and not held(state, enemy):
            enemy.pulled_by = hero_id


def drop_pulls(state: FightState, hero_id: str) -> None:
    """Every enemy pulled by `hero_id` lets go of them."""
    for enemy in state.enemies.values():
        if enemy.pulled_by == hero_id:
            enemy.pulled_by = None
