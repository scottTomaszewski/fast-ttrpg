"""One whole fight: the round loop, the party turn, and auto-attacks.

A round is a party turn, then a GM turn (see `enemy_ai.py`). The party wins
when no enemy is alive and no more are coming. The party loses when no hero
is up: every one of them is down or out. A fight that goes on past the last
round allowed (`rules.max_rounds`) is stopped and counts as a loss.
"""

from dataclasses import dataclass

from fastcombat.abilities import Action, use_ability
from fastcombat.casting import continue_cast, drop_cast, land_casts
from fastcombat.combat import (
    damage_enemy,
    end_of_party_turn_cards,
    get_up,
    top_of_party_turn_cards,
)
from fastcombat.enemy_ai import gm_turn
from fastcombat.grid import Pos, adjacent, distance
from fastcombat.numbers import FightDef, HeroSpec, Numbers
from fastcombat.policies import Policy, default_policy
from fastcombat.units import Enemy, FightState, Hero, Tally, new_state


@dataclass
class FightResult:
    """How one fight went."""

    won: bool
    timeout: bool  # it ran out of rounds (a timeout is never a win)
    rounds: int  # the number of the last round played
    party: list[str]  # the classes in the party, as given
    seed: int
    heroes_out: list[str]  # ids of the heroes who were out at the end
    tally: Tally
    end_resource: dict[str, int]  # each hero's resource at the end, by hero id


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

    One die, or two added together into one hit with a Quicken card. A
    Rogue gets a combo point for each die that did not miss. Each crit also
    gives the class's crit bonus. Attacking gives a hidden hero away.
    """
    spec = state.numbers.heroes[hero.cls]
    if enemy.dead or distance(hero.pos, enemy.pos) > spec.attack_range:
        return
    rolls = [state.dice.auto_attack(spec.die)]
    if "quicken" in hero.stacks:
        rolls.append(state.dice.auto_attack(spec.die))
    damage_enemy(state, hero.id, enemy, sum(roll.damage for roll in rolls), auto=True)
    rules = state.numbers.rules
    for roll in rolls:
        if hero.cls == "rogue" and not roll.miss:
            hero.combo = min(rules["combo_max"], hero.combo + 1)
        if roll.crit:
            _crit_bonus(state, hero, spec)
    hero.hidden = False


def _crit_bonus(state: FightState, hero: Hero, spec: HeroSpec) -> None:
    """What a crit gives: `crit_gain` of something, never past its cap.

    The Warden gets grit, the Rogue extra combo points, the Druid Seeds,
    and the Mage mana.
    """
    rules = state.numbers.rules
    if hero.cls == "rogue":
        hero.combo = min(rules["combo_max"], hero.combo + spec.crit_gain)
    elif hero.cls == "druid":
        hero.seeds = min(rules["seeds_max"], hero.seeds + spec.crit_gain)
    elif hero.cls in ("warden", "mage"):
        hero.resource = min(spec.pool, hero.resource + spec.crit_gain)


def _move(state: FightState, hero: Hero, dest: Pos) -> None:
    """The move step for one hero.

    Wanting to move ends a cast (a channel is fine). The hero then moves
    only if `dest` is on the map, close enough, and nobody stands there.
    """
    if dest == hero.pos:
        return
    if hero.cast is not None and not hero.cast.is_channel:
        drop_cast(state, hero)
    on_map = 0 <= dest[0] < state.fight.width and 0 <= dest[1] < state.fight.height
    close_enough = distance(hero.pos, dest) <= state.numbers.rules["hero_move"]
    if on_map and close_enough and dest not in state.occupied():
        hero.pos = dest


def _act(state: FightState, hero: Hero, action: Action) -> None:
    """The act step for one hero.

    "continue" spends the step on the cast or channel going (nothing, if
    there is none). Anything else ends that cast or channel first. An auto
    or an ability that cannot happen is the same as doing nothing.
    """
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
    """`hero` hauls a downed ally next to them back up, on a little HP."""
    target = state.heroes.get(target_id) if target_id else None
    if target is not None and target.down and adjacent(hero.pos, target.pos):
        get_up(state, target, state.numbers.rules["haul_up_hp"])


def _write_down_resources(state: FightState, heroes: list[Hero]) -> None:
    """After the act step: each hero's resource goes in the tally.

    A hero who is up and has too little to pay for even their cheapest
    ability has had a starved round.
    """
    tally = state.tally
    for hero in heroes:
        tally.resource_by_round[hero.id].append(hero.resource)
        cheapest = _cheapest_cost(state.numbers, hero.cls)
        if hero.up and cheapest is not None and hero.resource < cheapest:
            tally.starved_rounds[hero.id] += 1


def _cheapest_cost(numbers: Numbers, cls: str) -> int | None:
    """The lowest cost above 0 among the class's own abilities, or None if none costs anything."""
    costs = [a.cost for a in numbers.abilities.values() if a.hero == cls and a.cost > 0]
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
        heroes_out=[hero.id for hero in state.heroes.values() if hero.out],
        tally=state.tally,
        end_resource={hero.id: hero.resource for hero in state.heroes.values()},
    )
