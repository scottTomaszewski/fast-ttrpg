"""Casts and channels: abilities that take more than one turn.

A cast of N rounds is started in the act step of one turn, takes the act
steps of the next N - 1 turns as well, and lands at the top of the turn
after that. So a 1-round cast started this turn lands at the top of the
next one. The hero must stand still until it lands. Nothing is paid until
it lands, so a cast that is cancelled, broken, or has nobody left to hit
costs nothing but the time.

A channel makes one hit in each act step, for a set number of hits, and
the hero may move while channelling, unless the ability says `still`
(Evocation): then moving ends it. Each hit is paid for when it happens.
If the target (or the square) is out of reach by then, the channel ends.

A hero's cast or channel is kept in `hero.cast`. A cast that hits an area
also marks that area in `state.marked`, so everyone can see where it will
land.
"""

from typing import TYPE_CHECKING

from fastcombat.grid import within
from fastcombat.numbers import AbilitySpec
from fastcombat.units import Cast, FightState, Hero

if TYPE_CHECKING:
    # Only for the type names below. The ability rules import this file,
    # so this file cannot import them while the program runs (see
    # `_resolve_cast`).
    from fastcombat.abilities import Action


def start_cast(
    state: FightState, hero: Hero, spec: AbilitySpec, action: "Action"
) -> None:
    """`hero` starts casting `spec`. This act step is the first one spent on it.

    An area cast marks its squares now. Nothing is paid yet.
    """
    drop_cast(state, hero)  # a new cast takes the place of any old one
    hero.cast = Cast(
        ability=spec.id,
        target=action.target,
        center=action.pos,
        actions_left=spec.cast - 1,
        hits_left=0,
        is_channel=False,
    )
    if action.pos is not None and spec.radius > 0:
        area = within(action.pos, spec.radius, state.fight.width, state.fight.height)
        state.marked[hero.id] = frozenset(area)


def start_channel(
    state: FightState, hero: Hero, spec: AbilitySpec, action: "Action"
) -> None:
    """`hero` starts channelling `spec`, with all its hits still to come.

    The first hit is made by whoever calls this (see `use_ability`).
    """
    drop_cast(state, hero)  # a new channel takes the place of any old cast
    hero.cast = Cast(
        ability=spec.id,
        target=action.target,
        center=action.pos,
        actions_left=0,
        hits_left=spec.hits,
        is_channel=True,
    )


def continue_cast(state: FightState, hero: Hero) -> None:
    """`hero` spends this act step on the cast or channel they have going.

    A cast has one act step fewer left to spend. A channel makes its next
    hit, and pays for it. The channel ends after its last hit, or as soon
    as a hit cannot happen (the hero cannot pay, or the target is gone or
    out of reach). A hit that cannot happen costs nothing.
    """
    cast = hero.cast
    if cast is None:
        return
    if not cast.is_channel:
        cast.actions_left = max(0, cast.actions_left - 1)
        return
    landed = _resolve_cast(state, hero, cast)
    cast.hits_left -= 1
    if not landed or cast.hits_left <= 0:
        drop_cast(state, hero)


def land_casts(state: FightState) -> None:
    """Top of the party turn: every cast with no act steps left lands now.

    Each one is paid for as it lands. One that cannot land (the hero cannot
    pay, or the target is gone) fizzles and costs nothing. Either way the
    cast is over, and its marked area is gone. Channels never land here;
    their hits happen in the act step.
    """
    for hero in sorted(state.heroes.values(), key=lambda hero: hero.id):
        cast = hero.cast
        if cast is None or cast.is_channel or cast.actions_left > 0:
            continue
        drop_cast(state, hero)
        _resolve_cast(state, hero, cast)


def drop_cast(state: FightState, hero: Hero) -> None:
    """`hero`'s cast or channel ends without landing: cancelled or broken.

    Its marked area is gone too. It costs nothing.
    """
    hero.cast = None
    state.marked.pop(hero.id, None)


def moving_ends(state: FightState, hero: Hero) -> bool:
    """True when moving would end what the hero has going: a cast, or a
    channel they must stand still for. Any other channel is fine."""
    cast = hero.cast
    if cast is None:
        return False
    return not cast.is_channel or state.numbers.abilities[cast.ability].still


def _resolve_cast(state: FightState, hero: Hero, cast: Cast) -> bool:
    """Make `cast` happen once, through the ability rules. True if it did.

    A channel hit happens only if its target, or its square, is still in
    reach: the hero or the target may have moved since the last hit.
    """
    # Imported here and not at the top, because the ability rules import
    # this file to start casts. Importing it at the top would go round in
    # a circle.
    from fastcombat.abilities import Action, in_reach, resolve

    spec = state.numbers.abilities[cast.ability]
    action = Action("ability", cast.ability, cast.target, cast.center)
    if cast.is_channel and not in_reach(state, hero, spec, action):
        return False
    return resolve(state, hero, spec, action)
