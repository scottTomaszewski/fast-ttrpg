"""One whole fight: the round loop, the party turn, and auto-attacks.

Before round 1, each Rogue makes her opening (see `opening.py`). A round
is a party turn, then a GM turn (see `enemy_ai.py`). The party wins
when no enemy is alive and no more are coming. The party loses when no hero
is up: every one of them is down or out. A fight that goes on past the last
round allowed (`rules.max_rounds`) is stopped and counts as a loss.
"""

from dataclasses import dataclass

from fastcombat.abilities import WHILE_STUNNED, Action, use_ability
from fastcombat.casting import continue_cast, drop_cast, land_casts, moving_ends
from fastcombat.combat import (
    damage_enemy,
    end_of_party_turn_cards,
    get_up,
    top_of_party_turn_cards,
)
from fastcombat.enemy_ai import gm_turn
from fastcombat.grid import Pos, adjacent, distance, on_map
from fastcombat.numbers import HAUL_UP, SHARED, FightDef, HeroSpec, Numbers
from fastcombat.opening import NONE, open_fight
from fastcombat.policies import Policy, default_policy
from fastcombat.units import CONTROL_STACKS, Enemy, FightState, Hero, Tally, new_state


@dataclass
class FightResult:
    """How one fight went."""

    won: bool
    timeout: bool  # it ran out of rounds (a timeout is never a win)
    rounds: int  # the number of the last round played
    party: list[str]  # the classes in the party, as given
    seed: int
    heroes_up: list[str]  # ids of the heroes who were up at the end
    heroes_out: list[str]  # ids of the heroes who were out at the end
    tally: Tally
    end_resource: dict[str, int]  # each hero's resource at the end, by hero id
    pool: dict[str, int]  # the most resource each hero can hold, by hero id
    # Every button the party has, and whose it is: a class, or "shared" when
    # any hero has it. In the numbers file's order, with "haul_up" last. A
    # benched ability is not a button.
    kit: dict[str, str]
    # The control cards ("stun", "sap", "sheep") on enemies still alive at
    # the end, one entry for each enemy and kind. Empty after a win.
    controlled_at_end: list[str]


def run_fight(
    numbers: Numbers,
    fight: FightDef,
    party: list[str],
    policies: dict[str, Policy] | None = None,
    seed: int = 0,
) -> FightResult:
    """Play one fight from start to end.

    `policies` says how each hero plays, by hero id. A hero who is not in
    it plays their class's default policy.
    """
    state = new_state(numbers, fight, party, seed)
    chosen = policies or {}
    plays = {
        hero.id: chosen[hero.id] if hero.id in chosen else default_policy(hero.cls)
        for hero in state.heroes.values()
    }
    openings(state, plays)
    for number in range(1, numbers.rules["max_rounds"] + 1):
        state.round = number
        party_turn(state, plays)
        # Enemies due this round have not come in yet: they come in the GM turn.
        outcome = _outcome(state, spawns_from=number)
        if outcome is None:
            gm_turn(state)
            outcome = _outcome(state, spawns_from=number + 1)
        if outcome is not None:
            return _result(state, party, seed, won=outcome, timeout=False)
    return _result(state, party, seed, won=False, timeout=True)


def openings(state: FightState, policies: dict[str, Policy]) -> None:
    """The step before round 1: each Rogue, in id order, makes the opening
    her policy picks. A policy with no `opening` picks none."""
    for hero in sorted(state.heroes.values(), key=lambda hero: hero.id):
        if hero.cls != "rogue":
            continue
        pick = getattr(policies[hero.id], "opening", None)
        open_fight(state, hero, pick(state, hero) if pick else NONE)


def party_turn(state: FightState, policies: dict[str, Policy]) -> None:
    """Play the party turn. At each step the heroes go in id order.

    1. Top of the turn: cards, then resource comes back, then finished casts land.
    2. Move: each hero who is up moves where their policy says, if they may.
    3. Act: each hero who is up does what their policy says.
    Then each hero's resource is written down, and the Bleeding cards come
    off last, so a downed hero can be saved by anyone in this turn.
    """
    heroes = sorted(state.heroes.values(), key=lambda hero: hero.id)

    top_of_party_turn_cards(state)
    for hero in heroes:
        if hero.up:
            spec = state.numbers.heroes[hero.cls]
            hero.resource = min(spec.pool, hero.resource + spec.regen)
    land_casts(state)

    for hero in heroes:
        if hero.up:
            _move(state, hero, policies[hero.id].move(state, hero))

    for hero in heroes:
        if hero.up:
            _act(state, hero, policies[hero.id].act(state, hero))

    _write_down_resources(state, heroes)
    end_of_party_turn_cards(state)


def auto_attack(state: FightState, hero: Hero, enemy: Enemy) -> None:
    """`hero` auto-attacks `enemy`, if it is alive and in reach.

    One die. With a Quicken card, as many dice as Quicken's `value` in the
    numbers file, added together into one hit. A Rogue gets combo points
    (`combo_per_hit`) for each die that did not miss. Each crit also gives
    the class's crit bonus. A hero with an `auto_gain` (the Mage) gets that
    much of their own resource back if the attack did not miss; with
    Quicken that is once for the whole hit, not once per die. Attacking
    gives a hidden hero away.
    """
    spec = state.numbers.heroes[hero.cls]
    if enemy.dead or distance(hero.pos, enemy.pos) > spec.attack_range:
        return
    count = state.numbers.abilities["quicken"].value if "quicken" in hero.stacks else 1
    rolls = [state.dice.auto_attack(spec.die) for _ in range(count)]
    damage_enemy(state, hero.id, enemy, sum(roll.damage for roll in rolls), auto=True)
    rules = state.numbers.rules
    for roll in rolls:
        if hero.cls == "rogue" and not roll.miss:
            hero.combo = min(rules["combo_max"], hero.combo + rules["combo_per_hit"])
        if roll.crit:
            _crit_bonus(state, hero, spec)
    if not all(roll.miss for roll in rolls):
        hero.resource = min(spec.pool, hero.resource + spec.auto_gain)
    hero.hidden = False


def _crit_bonus(state: FightState, hero: Hero, spec: HeroSpec) -> None:
    """What a crit gives: `crit_gain` of something, never past its cap.

    The Guardian gets grit, the Rogue extra combo points, the Druid Seeds,
    and the Mage mana.
    """
    rules = state.numbers.rules
    if hero.cls == "rogue":
        hero.combo = min(rules["combo_max"], hero.combo + spec.crit_gain)
    elif hero.cls == "druid":
        hero.seeds = min(rules["seeds_max"], hero.seeds + spec.crit_gain)
    elif hero.cls in ("guardian", "mage"):
        hero.resource = min(spec.pool, hero.resource + spec.crit_gain)


def _move(state: FightState, hero: Hero, dest: Pos) -> None:
    """The move step for one hero.

    A stunned hero, or one in an Ice Block, does not move. Wanting to move
    ends a cast, or a channel the hero must stand still for (any other
    channel is fine). The hero then moves only if `dest` is on the map,
    close enough, and nobody stands there.
    """
    if dest == hero.pos or hero.stunned or hero.iced:
        return
    if moving_ends(state, hero):
        drop_cast(state, hero)
    on_the_map = on_map(dest, state.fight.width, state.fight.height)
    close_enough = distance(hero.pos, dest) <= state.numbers.rules["hero_move"]
    if on_the_map and close_enough and dest not in state.occupied():
        hero.pos = dest


def _act(state: FightState, hero: Hero, action: Action) -> None:
    """The act step for one hero.

    "continue" spends the step on the cast or channel going (nothing, if
    there is none). Anything else ends that cast or channel first. An auto
    or an ability that cannot happen is the same as doing nothing. A
    stunned hero may only use an ability in WHILE_STUNNED (Ice Block); a
    hero in an Ice Block does nothing.
    """
    if hero.iced:
        return
    if hero.stunned and not (action.kind == "ability" and action.ability in WHILE_STUNNED):
        return
    if action.kind == "continue":
        continue_cast(state, hero)
        return
    drop_cast(state, hero)
    if action.kind == "auto":
        enemy = state.enemies.get(action.target) if action.target else None
        if enemy is not None:
            auto_attack(state, hero, enemy)
    elif action.kind == "ability":
        use_ability(state, hero, action)
    elif action.kind == "haul_up":
        _haul_up(state, hero, action.target)
    elif action.kind != "none":
        raise ValueError(f"{hero.id}'s policy asked for {action.kind!r}, which is no action")


def _haul_up(state: FightState, hero: Hero, target_id: str | None) -> None:
    """`hero` hauls a downed ally next to them back up, on a little HP.

    It is counted in the tally as a use of "haul_up".
    """
    target = state.heroes.get(target_id) if target_id else None
    if target is not None and target.down and adjacent(hero.pos, target.pos):
        get_up(state, target, state.numbers.rules["haul_up_hp"])
        state.tally.count_use(hero.id, HAUL_UP)


def _write_down_resources(state: FightState, heroes: list[Hero]) -> None:
    """After the act step: each hero's resource goes in the tally.

    A hero who is up has had an up round. If they also have too little to
    pay for even their cheapest ability, it was a starved round.
    """
    tally = state.tally
    for hero in heroes:
        tally.resource_by_round[hero.id].append(hero.resource)
        if not hero.up:
            continue
        tally.up_rounds[hero.id] += 1
        cheapest = _cheapest_cost(state.numbers, hero.cls)
        if cheapest is not None and hero.resource < cheapest:
            tally.starved_rounds[hero.id] += 1


def _cheapest_cost(numbers: Numbers, cls: str) -> int | None:
    """The lowest cost above 0 among the class's own abilities (not benched
    ones), or None if none costs anything."""
    costs = [
        a.cost
        for a in numbers.abilities.values()
        if a.hero == cls and a.cost > 0 and not a.benched
    ]
    return min(costs, default=None)


def _outcome(state: FightState, spawns_from: int) -> bool | None:
    """True if the party has won, False if it has lost, None if the fight goes on.

    Won: no enemy is alive, and no spawn is due in round `spawns_from` or later.
    Lost: no hero is up.
    """
    more_coming = any(spawn.round >= spawns_from for spawn in state.fight.spawns)
    if not state.living_enemies() and not more_coming:
        return True
    if not state.up_heroes():
        return False
    return None


def _result(
    state: FightState, party: list[str], seed: int, *, won: bool, timeout: bool
) -> FightResult:
    return FightResult(
        won=won,
        timeout=timeout,
        rounds=state.round,
        party=list(party),
        seed=seed,
        heroes_up=[hero.id for hero in state.heroes.values() if hero.up],
        heroes_out=[hero.id for hero in state.heroes.values() if hero.out],
        tally=state.tally,
        end_resource={hero.id: hero.resource for hero in state.heroes.values()},
        pool={hero.id: state.numbers.heroes[hero.cls].pool for hero in state.heroes.values()},
        kit=_kit(state.numbers, party),
        controlled_at_end=[
            name for e in state.living_enemies() for name in CONTROL_STACKS if name in e.stacks
        ],
    )


def _kit(numbers: Numbers, party: list[str]) -> dict[str, str]:
    """Every ability the party has, and whose it is, with hauling up last.
    Benched abilities are left out."""
    owners = set(party) | {SHARED}
    kit = {
        a.id: a.hero for a in numbers.abilities.values() if a.hero in owners and not a.benched
    }
    kit[HAUL_UP] = SHARED
    return kit
