"""The Rogue's opening: a step before round 1.

Before the first round, each Rogue may pick one enemy that is there from
the start and is not a boss, and get next to it in one of two ways:

- Sneak: roll a stealth check, one die of `rules.sneak_die` sides. On
  `rules.sneak_target` or more she starts on the free square next to the
  enemy that is closest to her (the same square Shadowstep would land her
  on), still hidden. Below it she is spotted: she stays on her start
  square, and is not hidden.
- Shadowstep in: it always works. She starts on that same square, hidden,
  with Shadowstep's cost taken off her starting energy. It is not a use of
  Shadowstep.

Or she does neither, and starts where she is, hidden, as always.

The policy picks (see `Policy.opening` in `policies.py`). A policy with no
`opening` picks neither. A choice that is not allowed (see `can_open`)
does nothing, the same as an ability that `can_use` refuses. Each Rogue's
opening goes in the tally (`Tally.openings`): "sneak" (it worked),
"spotted" (the stealth check failed), "shadowstep", or "none".
"""

from dataclasses import dataclass

from fastcombat.abilities.rogue import landing
from fastcombat.units import FightState, Hero

KINDS = ("sneak", "shadowstep", "none")


@dataclass(frozen=True)
class Opening:
    """What one Rogue does before round 1: `kind` is one of KINDS."""

    kind: str
    target: str | None = None  # the enemy's id; None for "none"


NONE = Opening("none")


def can_open(state: FightState, hero: Hero, opening: Opening) -> bool:
    """True when `hero` may make this opening.

    "none" is always allowed. Sneak and Shadowstep in need: a Rogue who is
    hidden; an enemy that is alive and not a boss; and a free square next
    to it. (Before round 1 every enemy there is one that is there from the
    start.) Shadowstep in also needs her energy to pay for Shadowstep.
    """
    if opening.kind not in KINDS:
        raise ValueError(f"{hero.id}'s policy asked for the opening {opening.kind!r}, which is none")
    if opening.kind == "none":
        return True
    if hero.cls != "rogue" or not hero.hidden:
        return False
    enemy = state.enemies.get(opening.target) if opening.target else None
    if enemy is None or enemy.dead or enemy.spec.tier == "boss":
        return False
    if landing(state, hero, enemy) is None:
        return False
    if opening.kind == "shadowstep":
        return hero.resource >= state.numbers.abilities["shadowstep"].cost
    return True


def open_fight(state: FightState, hero: Hero, opening: Opening) -> bool:
    """`hero` makes `opening`. True if it was allowed (a failed Sneak counts).

    If it is not allowed, nothing happens and it counts as "none". The
    stealth die is rolled through `state.dice`, so the same seed always
    gives the same result. "none" rolls nothing.
    """
    allowed = can_open(state, hero, opening)
    kind = opening.kind if allowed else "none"
    if kind == "none":
        state.tally.openings[hero.id] = "none"
        return allowed
    enemy = state.enemies[opening.target]
    square = landing(state, hero, enemy)
    if kind == "shadowstep":
        hero.resource -= state.numbers.abilities["shadowstep"].cost
        hero.pos = square
        state.tally.openings[hero.id] = "shadowstep"
        return True
    rules = state.numbers.rules
    if state.dice.roll(rules["sneak_die"]) >= rules["sneak_target"]:
        hero.pos = square
        state.tally.openings[hero.id] = "sneak"
    else:
        hero.hidden = False
        state.tally.openings[hero.id] = "spotted"
    return True
