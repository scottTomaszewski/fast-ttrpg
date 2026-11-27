"""The Guardian's seven abilities. The Guardian is the tank: they make the enemies
attack them, and stand between the enemies and everyone else.

Each ability's numbers (what it costs, how far it reaches, how many cards it
gives and what each card is worth) are in the numbers file.

Two words used below. An ally is another hero who is not out. A free square
is one on the map where nobody stands; the one being moved does not get in
their own way, so their own square counts as free.
"""

from fastcombat.abilities import Action, check, effect, target_enemy
from fastcombat.combat import add_stack, damage_enemy
from fastcombat.grid import Pos, behind, free_next_to, within
from fastcombat.numbers import AbilitySpec
from fastcombat.units import Enemy, FightState, Hero


@check("taunt")
def _taunt_needs_an_enemy(
    state: FightState, guardian: Hero, spec: AbilitySpec, action: Action
) -> bool:
    return target_enemy(state, action) is not None


@effect("taunt")
def taunt(
    state: FightState, guardian: Hero, spec: AbilitySpec, action: Action
) -> None:
    """Taunt cards on one enemy: while they last, it must attack the Guardian."""
    _taunt(state.enemies[action.target], spec.cards)


@effect("challenging_shout")
def challenging_shout(state: FightState, guardian: Hero, spec: AbilitySpec, action: Action) -> None:
    """Taunt cards on every living enemy near the Guardian."""
    near = within(guardian.pos, spec.radius, state.fight.width, state.fight.height)
    for enemy in state.living_enemies():
        if enemy.pos in near:
            _taunt(enemy, spec.cards)


@check("intercede")
def _intercede_needs_an_ally_who_is_up(
    state: FightState, guardian: Hero, spec: AbilitySpec, action: Action
) -> bool:
    ally = state.heroes.get(action.target) if action.target else None
    return ally is not None and ally is not guardian and ally.up


@effect("intercede")
def intercede(
    state: FightState, guardian: Hero, spec: AbilitySpec, action: Action
) -> None:
    """Leap next to an ally and guard them.

    The Guardian lands on the free square next to the ally that is closest to
    where the Guardian was, and stays put if there is none. The ally gets
    Guarded cards (each hit on them is smaller) and Interceded cards (an
    enemy that was going to attack them attacks the Guardian instead; see
    `targeting.choose_target`).
    """
    ally = state.heroes[action.target]
    taken = state.occupied() - {guardian.pos}
    landing = free_next_to(
        ally.pos, guardian.pos, taken, state.fight.width, state.fight.height
    )
    if landing is not None:
        guardian.pos = landing
    add_stack(ally, "guarded", spec.cards, spec.value)
    add_stack(ally, "interceded", spec.cards)


@check("grip")
def _grip_needs_an_enemy_it_can_pull(
    state: FightState, guardian: Hero, spec: AbilitySpec, action: Action
) -> bool:
    """Not the boss, and there has to be a free square next to the Guardian."""
    enemy = target_enemy(state, action)
    if enemy is None or enemy.spec.tier == "boss":
        return False
    return _grip_square(state, guardian, enemy) is not None


@effect("grip")
def grip(
    state: FightState, guardian: Hero, spec: AbilitySpec, action: Action
) -> None:
    """Pull one enemy to the free square next to the Guardian closest to where it was."""
    enemy = state.enemies[action.target]
    square = _grip_square(state, guardian, enemy)
    if square is not None:
        enemy.pos = square


@check("shield_plant")
def _shield_plant_needs_a_blast_square(
    state: FightState, guardian: Hero, spec: AbilitySpec, action: Action
) -> bool:
    return action.pos is not None


@effect("shield_plant")
def shield_plant(state: FightState, guardian: Hero, spec: AbilitySpec, action: Action) -> None:
    """Plant the shield against a blast coming from the square `action.pos`.

    The Guardian, and every ally in the squares behind the Guardian (on the far
    side from the blast), gets a Shield Plant card: the blast hits them for less.
    """
    shelter = behind(
        guardian.pos, action.pos, spec.radius, state.fight.width, state.fight.height
    )
    add_stack(guardian, "shield_plant", spec.cards, spec.value)
    for ally in state.heroes.values():
        if ally is not guardian and not ally.out and ally.pos in shelter:
            add_stack(ally, "shield_plant", spec.cards, spec.value)


@effect("last_stand")
def last_stand(
    state: FightState, guardian: Hero, spec: AbilitySpec, action: Action
) -> None:
    """While the card lasts, nothing can take the Guardian below 1 HP."""
    add_stack(guardian, "last_stand", spec.cards)


@check("shield_slam")
def _shield_slam_needs_an_enemy(
    state: FightState, guardian: Hero, spec: AbilitySpec, action: Action
) -> bool:
    return target_enemy(state, action) is not None


@effect("shield_slam")
def shield_slam(
    state: FightState, guardian: Hero, spec: AbilitySpec, action: Action
) -> None:
    """Hit one enemy with the Shield Slam dice, and get `alt` grit (never past his pool).

    It is a hit, not an auto-attack: it never misses or crits, and its
    damage does not count as auto-attack damage. It has a cooldown.
    """
    amount = state.dice.roll_many(*spec.dice, spec.bonus)
    damage_enemy(state, guardian.id, state.enemies[action.target], amount, loud=spec.loud)
    pool = state.numbers.heroes[guardian.cls].pool
    guardian.resource = min(pool, guardian.resource + spec.alt)


def _taunt(enemy: Enemy, cards: int) -> None:
    """Give `enemy` `cards` Taunt cards. A new taunt never shortens an old one.

    If the enemy already has as many Taunt cards as that, or more, it keeps
    the ones it has.
    """
    old = enemy.stacks.get("taunt")
    if old is None or old.cards < cards:
        add_stack(enemy, "taunt", cards)


def _grip_square(state: FightState, guardian: Hero, enemy: Enemy) -> Pos | None:
    """Where Grip would put `enemy`.

    None if no square next to the Guardian is free.
    """
    taken = state.occupied() - {enemy.pos}
    return free_next_to(
        guardian.pos, enemy.pos, taken, state.fight.width, state.fight.height
    )
