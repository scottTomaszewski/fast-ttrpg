"""The Warden's six abilities. The Warden is the tank: they make the enemies
attack them, and stand between the enemies and everyone else.

Each ability's numbers (what it costs, how far it reaches, how many cards it
gives and what each card is worth) are in the numbers file.

Two words used below. An ally is another hero who is not out. A free square
is one on the map where nobody stands; the one being moved does not get in
their own way, so their own square counts as free.
"""

from fastcombat.abilities import Action, check, effect
from fastcombat.combat import add_stack
from fastcombat.grid import Pos, behind, free_next_to, within
from fastcombat.numbers import AbilitySpec
from fastcombat.units import Enemy, FightState, Hero


@check("challenge")
def _challenge_needs_an_enemy(
    state: FightState, warden: Hero, spec: AbilitySpec, action: Action
) -> bool:
    return _enemy(state, action) is not None


@effect("challenge")
def challenge(
    state: FightState, warden: Hero, spec: AbilitySpec, action: Action
) -> None:
    """Taunt cards on one enemy: while they last, it must attack the Warden."""
    _taunt(state.enemies[action.target], spec.cards)


@effect("war_cry")
def war_cry(state: FightState, warden: Hero, spec: AbilitySpec, action: Action) -> None:
    """Taunt cards on every living enemy near the Warden."""
    near = within(warden.pos, spec.radius, state.fight.width, state.fight.height)
    for enemy in state.living_enemies():
        if enemy.pos in near:
            _taunt(enemy, spec.cards)


@check("intercede")
def _intercede_needs_an_ally_who_is_up(
    state: FightState, warden: Hero, spec: AbilitySpec, action: Action
) -> bool:
    ally = state.heroes.get(action.target) if action.target else None
    return ally is not None and ally is not warden and ally.up


@effect("intercede")
def intercede(
    state: FightState, warden: Hero, spec: AbilitySpec, action: Action
) -> None:
    """Leap next to an ally and guard them.

    The Warden lands on the free square next to the ally that is closest to
    where the Warden was, and stays put if there is none. The ally gets
    Guarded cards (each hit on them is smaller) and Interceded cards (an
    enemy that was going to attack them attacks the Warden instead; see
    `targeting.choose_target`).
    """
    ally = state.heroes[action.target]
    taken = state.occupied() - {warden.pos}
    landing = free_next_to(
        ally.pos, warden.pos, taken, state.fight.width, state.fight.height
    )
    if landing is not None:
        warden.pos = landing
    add_stack(ally, "guarded", spec.cards, spec.value)
    add_stack(ally, "interceded", spec.cards)


@check("chain_hook")
def _chain_hook_needs_an_enemy_it_can_pull(
    state: FightState, warden: Hero, spec: AbilitySpec, action: Action
) -> bool:
    """Not the boss, and there has to be a free square next to the Warden."""
    enemy = _enemy(state, action)
    if enemy is None or enemy.spec.tier == "boss":
        return False
    return _hook_square(state, warden, enemy) is not None


@effect("chain_hook")
def chain_hook(
    state: FightState, warden: Hero, spec: AbilitySpec, action: Action
) -> None:
    """Pull one enemy to the free square next to the Warden closest to where it was."""
    enemy = state.enemies[action.target]
    square = _hook_square(state, warden, enemy)
    if square is not None:
        enemy.pos = square


@check("bulwark")
def _bulwark_needs_a_blast_square(
    state: FightState, warden: Hero, spec: AbilitySpec, action: Action
) -> bool:
    return action.pos is not None


@effect("bulwark")
def bulwark(state: FightState, warden: Hero, spec: AbilitySpec, action: Action) -> None:
    """Plant the shield against a blast coming from the square `action.pos`.

    The Warden, and every ally in the squares behind the Warden (on the far
    side from the blast), gets a Bulwark card: the blast hits them for less.
    """
    shelter = behind(
        warden.pos, action.pos, spec.radius, state.fight.width, state.fight.height
    )
    add_stack(warden, "bulwark", spec.cards, spec.value)
    for ally in state.heroes.values():
        if ally is not warden and not ally.out and ally.pos in shelter:
            add_stack(ally, "bulwark", spec.cards, spec.value)


@effect("unbroken")
def unbroken(
    state: FightState, warden: Hero, spec: AbilitySpec, action: Action
) -> None:
    """While the card lasts, nothing can take the Warden below 1 HP."""
    add_stack(warden, "unbroken", spec.cards)


def _taunt(enemy: Enemy, cards: int) -> None:
    """Give `enemy` `cards` Taunt cards. A new taunt never shortens an old one.

    If the enemy already has as many Taunt cards as that, or more, it keeps
    the ones it has.
    """
    old = enemy.stacks.get("taunt")
    if old is None or old.cards < cards:
        add_stack(enemy, "taunt", cards)


def _enemy(state: FightState, action: Action) -> Enemy | None:
    """The enemy `action` is aimed at, or None if it is not aimed at an enemy."""
    return state.enemies.get(action.target) if action.target else None


def _hook_square(state: FightState, warden: Hero, enemy: Enemy) -> Pos | None:
    """Where Chain Hook would put `enemy`.

    None if no square next to the Warden is free.
    """
    taken = state.occupied() - {enemy.pos}
    return free_next_to(
        warden.pos, enemy.pos, taken, state.fight.width, state.fight.height
    )
