"""The Druid's seven abilities. The Druid is the healer: they heal now, put
heal cards on allies that heal a little every round, and save up Seeds for
a heal in a hurry.

Each ability's numbers (what it costs, how far it reaches, its dice, how
many cards it gives and what each card is worth) are in the numbers file.
The most Seeds a Druid can hold is `seeds_max`, in the rules.

Four words used below. An ally is any hero who is not out, and the Druid
counts too: every Druid ability aimed at someone is aimed at a hero, never
at an enemy. Down: a hero at 0 HP who is bleeding. Any heal gets them up
(see `combat.heal_hero`). Heal cards: Rejuvenation and Wild Growth cards
heal their value at the top of each party turn (see
`combat.top_of_party_turn_cards`). Seeds: the Druid gets one from Regrowth
and from an auto-attack crit, and Swiftmend spends one.
"""

from fastcombat.abilities import Action, check, cost, effect
from fastcombat.combat import add_stack, heal_hero
from fastcombat.grid import walk_away, within
from fastcombat.numbers import AbilitySpec
from fastcombat.targeting import drop_pulls, loud_heal
from fastcombat.units import FightState, Hero


@check("rejuvenation")
def _rejuvenation_needs_an_ally_who_is_up(
    state: FightState, druid: Hero, spec: AbilitySpec, action: Action
) -> bool:
    """Only for an ally who is up, not one who is down."""
    ally = _ally(state, action)
    return ally is not None and ally.up


@effect("rejuvenation")
def rejuvenation(
    state: FightState, druid: Hero, spec: AbilitySpec, action: Action
) -> None:
    """Heal cards on one ally. A new Rejuvenation takes the place of the old one."""
    add_stack(state.heroes[action.target], "rejuvenation", spec.cards, spec.value)


@check("regrowth")
def _regrowth_needs_an_ally(
    state: FightState, druid: Hero, spec: AbilitySpec, action: Action
) -> bool:
    return _ally(state, action) is not None


@effect("regrowth")
def regrowth(state: FightState, druid: Hero, spec: AbilitySpec, action: Action) -> None:
    """A big heal on one ally, and a Seed for the Druid. It is Loud.

    It is a cast, so this happens when it lands. An ally who went down in
    between is healed too, and gets up. Loud: every enemy that nothing holds
    goes for the Druid (see `targeting.loud_heal`).
    """
    amount = state.dice.roll_many(*spec.dice, spec.bonus)
    heal_hero(state, druid.id, state.heroes[action.target], amount)
    druid.seeds = min(state.numbers.rules["seeds_max"], druid.seeds + 1)
    if spec.loud:
        loud_heal(state, druid.id)


@cost("swiftmend")
def _swiftmend_is_free_on_a_badly_hurt_ally(
    state: FightState, druid: Hero, spec: AbilitySpec, action: Action
) -> int:
    """Free on an ally below half their max HP. A downed ally, at 0 HP, is too."""
    ally = _ally(state, action)
    if ally is not None and ally.hp * 2 < ally.max_hp:
        return 0
    return spec.cost


@check("swiftmend")
def _swiftmend_needs_an_ally_and_a_seed(
    state: FightState, druid: Hero, spec: AbilitySpec, action: Action
) -> bool:
    return _ally(state, action) is not None and druid.seeds >= 1


@effect("swiftmend")
def swiftmend(
    state: FightState, druid: Hero, spec: AbilitySpec, action: Action
) -> None:
    """Spend a Seed on a heal for one ally, at once."""
    druid.seeds -= 1
    amount = state.dice.roll_many(*spec.dice, spec.bonus)
    heal_hero(state, druid.id, state.heroes[action.target], amount)


@check("wild_growth")
def _wild_growth_needs_a_centre(
    state: FightState, druid: Hero, spec: AbilitySpec, action: Action
) -> bool:
    return action.pos is not None


@effect("wild_growth")
def wild_growth(
    state: FightState, druid: Hero, spec: AbilitySpec, action: Action
) -> None:
    """Heal cards on every ally who is up in the area around the square `action.pos`.

    A new Wild Growth takes the place of an old one on a hero; it never adds to it.
    """
    area = within(action.pos, spec.radius, state.fight.width, state.fight.height)
    for ally in state.up_heroes():
        if ally.pos in area:
            add_stack(ally, "wild_growth", spec.cards, spec.value)


@check("cleanse")
def _cleanse_needs_a_poisoned_ally(
    state: FightState, druid: Hero, spec: AbilitySpec, action: Action
) -> bool:
    ally = _ally(state, action)
    return ally is not None and "poison" in ally.stacks


@effect("cleanse")
def cleanse(state: FightState, druid: Hero, spec: AbilitySpec, action: Action) -> None:
    """Take the poison cards off one ally. Their other cards stay."""
    state.heroes[action.target].stacks.pop("poison", None)


@effect("shadowmeld")
def shadowmeld(
    state: FightState, druid: Hero, spec: AbilitySpec, action: Action
) -> None:
    """Every enemy pulled by the Druid lets go of them, and the Druid slips away.

    The Druid moves up to `value` squares, to get as far as they can from
    the nearest living enemy (see `grid.walk_away`). They never walk through
    or stop on a square where someone stands.
    """
    drop_pulls(state, druid.id)
    threats = [enemy.pos for enemy in state.living_enemies()]
    blocked = state.occupied() - {druid.pos}
    druid.pos = walk_away(
        druid.pos, threats, spec.value, blocked, state.fight.width, state.fight.height
    )


@check("nourish")
def _nourish_needs_an_ally(
    state: FightState, druid: Hero, spec: AbilitySpec, action: Action
) -> bool:
    return _ally(state, action) is not None


@effect("nourish")
def nourish(state: FightState, druid: Hero, spec: AbilitySpec, action: Action) -> None:
    """Roll one die and heal one ally by what it shows.

    It is a plain roll: a 1 still heals 1, and nothing rolls again. The top
    face also gives the Druid `alt` energy back, never more than their pool.
    """
    sides = spec.dice[1]
    roll = state.dice.roll(sides)
    heal_hero(state, druid.id, state.heroes[action.target], roll)
    if roll == sides:
        pool = state.numbers.heroes[druid.cls].pool
        druid.resource = min(pool, druid.resource + spec.alt)


def _ally(state: FightState, action: Action) -> Hero | None:
    """The hero `action` is aimed at, or None if it is not aimed at a hero."""
    return state.heroes.get(action.target) if action.target else None
