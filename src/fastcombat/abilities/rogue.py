"""The Rogue's seven abilities. The Rogue strikes from the shadows, builds up
combo points, and spends them on one big hit or a long stun.

Each ability's numbers (what it costs, how far it reaches, its dice and how
many cards it gives) are in the numbers file. Three more are in the rules
there: the most combo points a Rogue can hold (`combo_max`), how many one
hit gives (`combo_per_hit`), and how many times bigger a Backstab from
hiding is (`backstab_hidden_multiplier`).

Three words used below. Hidden: the Rogue starts a fight hidden (unless she
was spotted sneaking in before round 1, see `opening.py`), and Vanish
hides them again. Shadowstep does not give them away. Using any other
ability does, once it has happened (see `resolve`), so a rule that asks "is
the Rogue hidden?" still sees the answer from before. While hidden, no
enemy can pick the Rogue as its target, and a pull by her counts for
nothing; a blast still hits her (see `targeting.py`). Combo points: the
Rogue gets them from auto-attacks that hit and from Backstab, and Eviscerate
and Kidney Shot spend them all. A free square is one on the map where nobody stands; the Rogue's
own square counts as free.
"""

from fastcombat.abilities import Action, check, effect, keeps_hiding, target_enemy
from fastcombat.combat import control, damage_enemy
from fastcombat.grid import Pos, free_next_to
from fastcombat.numbers import AbilitySpec
from fastcombat.targeting import drop_pulls, held
from fastcombat.units import Enemy, FightState, Hero


@check("backstab")
def _backstab_needs_an_enemy_busy_with_someone_else(
    state: FightState, rogue: Hero, spec: AbilitySpec, action: Action
) -> bool:
    """From hiding, any enemy will do. Otherwise it must be busy with someone else.

    Busy means: it has Taunt cards; or the Rogue did not pull it, and it is
    going for another hero or the Guardian is holding it. An enemy the Rogue
    pulled is coming for her (a pull beats the Guardian's hold), so it is not
    busy with someone else; only Taunt cards beat her pull.
    """
    enemy = target_enemy(state, action)
    if enemy is None:
        return False
    if rogue.hidden or "taunt" in enemy.stacks:
        return True
    if enemy.pulled_by == rogue.id:
        return False
    going_for_someone_else = enemy.target is not None and enemy.target != rogue.id
    return going_for_someone_else or held(state, enemy)


@effect("backstab")
def backstab(state: FightState, rogue: Hero, spec: AbilitySpec, action: Action) -> None:
    """Hit the enemy with the Backstab dice, and get `combo_per_hit` combo points.

    From hiding the hit is `backstab_hidden_multiplier` times as big.
    """
    rules = state.numbers.rules
    amount = state.dice.roll_many(*spec.dice, spec.bonus)
    if rogue.hidden:
        amount *= rules["backstab_hidden_multiplier"]
    damage_enemy(state, rogue.id, state.enemies[action.target], amount, loud=spec.loud)
    rogue.combo = min(rules["combo_max"], rogue.combo + rules["combo_per_hit"])


@check("eviscerate")
def _eviscerate_needs_a_combo_point(
    state: FightState, rogue: Hero, spec: AbilitySpec, action: Action
) -> bool:
    return target_enemy(state, action) is not None and rogue.combo >= 1


@effect("eviscerate")
def eviscerate(
    state: FightState, rogue: Hero, spec: AbilitySpec, action: Action
) -> None:
    """Spend every combo point on one hit.

    The Eviscerate dice are rolled once for each point, and the bonus is
    added once to the total.
    """
    count, sides = spec.dice
    amount = state.dice.roll_many(count * rogue.combo, sides, spec.bonus)
    damage_enemy(state, rogue.id, state.enemies[action.target], amount, loud=spec.loud)
    rogue.combo = 0


@check("kidney_shot")
def _kidney_shot_needs_a_combo_point_and_no_boss(
    state: FightState, rogue: Hero, spec: AbilitySpec, action: Action
) -> bool:
    enemy = target_enemy(state, action)
    return enemy is not None and enemy.spec.tier != "boss" and rogue.combo >= 1


@effect("kidney_shot")
def kidney_shot(
    state: FightState, rogue: Hero, spec: AbilitySpec, action: Action
) -> None:
    """Spend every combo point on a stun.

    With the most combo points a Rogue can hold, the stun lasts `alt` cards;
    with fewer, `cards`.
    """
    full = rogue.combo == state.numbers.rules["combo_max"]
    cards = spec.alt if full else spec.cards
    control(state, state.enemies[action.target], "stun", cards)
    rogue.combo = 0


@check("cheap_shot")
def _cheap_shot_needs_an_enemy(
    state: FightState, rogue: Hero, spec: AbilitySpec, action: Action
) -> bool:
    """Any enemy, a boss too: the stun does not stop a boss, but breaks its cast."""
    return target_enemy(state, action) is not None


@effect("cheap_shot")
def cheap_shot(
    state: FightState, rogue: Hero, spec: AbilitySpec, action: Action
) -> None:
    """A short stun on one enemy."""
    control(state, state.enemies[action.target], "stun", spec.cards)


@check("sap")
def _sap_only_from_hiding_and_not_on_a_boss(
    state: FightState, rogue: Hero, spec: AbilitySpec, action: Action
) -> bool:
    enemy = target_enemy(state, action)
    return rogue.hidden and enemy is not None and enemy.spec.tier != "boss"


@effect("sap")
def sap(state: FightState, rogue: Hero, spec: AbilitySpec, action: Action) -> None:
    """Knock one enemy out for a long time. It wakes the moment it takes any damage."""
    control(state, state.enemies[action.target], "sap", spec.cards)


@check("shadowstep")
def _shadowstep_needs_a_free_square_by_the_enemy(
    state: FightState, rogue: Hero, spec: AbilitySpec, action: Action
) -> bool:
    enemy = target_enemy(state, action)
    return enemy is not None and landing(state, rogue, enemy) is not None


@keeps_hiding("shadowstep")
@effect("shadowstep")
def shadowstep(
    state: FightState, rogue: Hero, spec: AbilitySpec, action: Action
) -> None:
    """Appear on the free square next to the enemy that is closest to the Rogue.

    It does not give the Rogue away: if she was hidden, she still is, so she
    can open with a Backstab from hiding or a Sap, and no enemy can pick her
    as its target. If she was not, she is not.
    """
    square = landing(state, rogue, state.enemies[action.target])
    if square is not None:
        rogue.pos = square


@keeps_hiding("vanish")
@effect("vanish")
def vanish(state: FightState, rogue: Hero, spec: AbilitySpec, action: Action) -> None:
    """Every enemy pulled by the Rogue lets go of them, and the Rogue hides.

    While she is hidden, no enemy can pick her as its target (a blast still
    hits her). Vanish while already hidden keeps her hidden.
    """
    drop_pulls(state, rogue.id)
    rogue.hidden = True


def landing(state: FightState, rogue: Hero, enemy: Enemy) -> Pos | None:
    """Where Shadowstep would put the Rogue: the free square next to the
    enemy that is closest to her. The opening before round 1 uses it too
    (see `opening.py`).

    None if no square next to the enemy is free.
    """
    taken = state.occupied() - {rogue.pos}
    return free_next_to(
        enemy.pos, rogue.pos, taken, state.fight.width, state.fight.height
    )
