"""Using abilities: who may use what, paying for it, and cooldowns.

Every ability works the same way. `can_use` says whether a hero may use it
right now. `use_ability` uses it: an instant ability happens at once, a cast
or a channel is started (see `casting.py`). `resolve` is the moment an
ability really happens: it is paid for, does what it does, and starts its
cooldown.

What each ability does is not in this file. Each class has its own file,
which fills the tables below using these decorators:

- `@effect("id")`: what the ability does.
- `@check("id")`: an extra rule for when it may be used, if it has one.
- `@cost("id")`: a cost that is not always the same, if it has one.
- `@keeps_hiding("id")`: using it does not give a hidden hero away (Vanish
  and Shadowstep).

A cooldown is a stack of cards on the hero, called "cd:" and the ability's
name ("cd:disrupt"). One card comes off at the top of each party turn, like
any other stack. While the stack is there, the ability cannot be used.
"""

from collections.abc import Callable
from dataclasses import dataclass

from fastcombat.casting import continue_cast, start_cast, start_channel
from fastcombat.combat import add_stack
from fastcombat.grid import Pos, distance
from fastcombat.numbers import SHARED, AbilitySpec
from fastcombat.units import Enemy, FightState, Hero


@dataclass(frozen=True)
class Action:
    """What one hero does in the act step."""

    kind: str  # "auto" "ability" "continue" "haul_up" "none"
    ability: str | None = None
    target: str | None = None  # unit id
    pos: Pos | None = None  # centre of an area, or where to land


Effect = Callable[[FightState, Hero, AbilitySpec, Action], None]
Check = Callable[[FightState, Hero, AbilitySpec, Action], bool]
CostRule = Callable[[FightState, Hero, AbilitySpec, Action], int]

EFFECTS: dict[str, Effect] = {}  # what each ability does, by ability id
CHECKS: dict[str, Check] = {}  # extra rules for when it may be used
COSTS: dict[str, CostRule] = {}  # costs that are not always the same
KEEPS_HIDING: set[str] = set()  # abilities that do not give a hidden hero away


def effect(ability_id: str) -> Callable[[Effect], Effect]:
    """Decorator: the function is what ability `ability_id` does."""

    def register(fn: Effect) -> Effect:
        EFFECTS[ability_id] = fn
        return fn

    return register


def check(ability_id: str) -> Callable[[Check], Check]:
    """Decorator: the function is an extra rule for using `ability_id`.

    It gives back False when the ability may not be used.
    """

    def register(fn: Check) -> Check:
        CHECKS[ability_id] = fn
        return fn

    return register


def cost(ability_id: str) -> Callable[[CostRule], CostRule]:
    """Decorator: the function works out what `ability_id` costs this time."""

    def register(fn: CostRule) -> CostRule:
        COSTS[ability_id] = fn
        return fn

    return register


def keeps_hiding(ability_id: str) -> Callable[[Effect], Effect]:
    """Decorator: using `ability_id` does not give a hidden hero away.

    Put it on the ability's effect, above `@effect`. After that effect, the
    hero is hidden or not just as the effect left them.
    """

    def register(fn: Effect) -> Effect:
        KEEPS_HIDING.add(ability_id)
        return fn

    return register


def cost_of(state: FightState, hero: Hero, spec: AbilitySpec, action: Action) -> int:
    """What using `spec` costs now: its cost from the file, unless it has a cost rule.

    For a channel, this is the cost of one hit.
    """
    rule = COSTS.get(spec.id)
    return spec.cost if rule is None else rule(state, hero, spec, action)


def can_use(state: FightState, hero: Hero, ability_id: str, action: Action) -> bool:
    """True when `hero` may use `ability_id` right now, the way `action` says.

    No, when: the hero is not up; the ability is benched (out of the game
    for now); nothing says what the ability does; it
    belongs to another class (and is not shared); it is cooling down; the
    hero cannot pay for it now (for a channel, one hit); the target is
    missing, dead or out; the target or the square is out of reach; or the
    ability's own extra rule says no.
    """
    spec = state.numbers.abilities.get(ability_id)
    if spec is None or spec.benched or ability_id not in EFFECTS or not hero.up:
        return False
    if spec.hero not in (hero.cls, SHARED):
        return False
    if f"cd:{ability_id}" in hero.stacks:
        return False
    if hero.resource < cost_of(state, hero, spec, action):
        return False
    if not in_reach(state, hero, spec, action):
        return False
    rule = CHECKS.get(ability_id)
    return rule is None or rule(state, hero, spec, action)


def in_reach(state: FightState, hero: Hero, spec: AbilitySpec, action: Action) -> bool:
    """True when the target and the square that `action` names are close enough.

    A target that is missing, dead or out is never in reach. An action with
    no target, or no square, is fine. A channel asks this again before each
    hit, because the hero or the target may have moved (see `casting.py`).
    """
    if action.target is not None:
        target = _target(state, action.target)
        if target is None or not _close_enough(hero, spec, target.pos):
            return False
    return action.pos is None or _close_enough(hero, spec, action.pos)


def use_ability(state: FightState, hero: Hero, action: Action) -> bool:
    """`hero` uses the ability `action` names. True if they could.

    If they may not, nothing happens and it gives back False. A cast is
    started, and paid for when it lands. A channel is started and makes its
    first hit now. Anything else happens now.

    Using an ability gives a hidden hero away: starting a cast does it at
    once, and anything else does it once it has happened (see `resolve`).

    Each use is counted in the tally when it starts: a cast once, even if it
    is stopped before it lands, and a channel once, not once for each hit.
    """
    if action.ability is None or not can_use(state, hero, action.ability, action):
        return False
    spec = state.numbers.abilities[action.ability]
    state.tally.count_use(hero.id, spec.id)
    if spec.cast > 0:
        start_cast(state, hero, spec, action)
        hero.hidden = False
    elif spec.hits > 0:
        start_channel(state, hero, spec, action)
        continue_cast(state, hero)  # the first hit
    else:
        resolve(state, hero, spec, action)
    return True


def resolve(state: FightState, hero: Hero, spec: AbilitySpec, action: Action) -> bool:
    """The ability really happens now: pay, do what it does, start the cooldown.

    False, and nothing happens, if the hero cannot pay or the target is
    missing, dead or out by now.

    Once it has happened, the hero is not hidden any more, unless the
    ability is marked with `@keeps_hiding` (Vanish and Shadowstep): after
    one of those, the hero is hidden or not just as its effect left them.
    """
    price = cost_of(state, hero, spec, action)
    if hero.resource < price:
        return False
    if action.target is not None and _target(state, action.target) is None:
        return False
    hero.resource -= price
    EFFECTS[spec.id](state, hero, spec, action)
    if spec.id not in KEEPS_HIDING:
        hero.hidden = False
    if spec.cooldown > 0:
        add_stack(hero, f"cd:{spec.id}", spec.cooldown)
    return True


def target_enemy(state: FightState, action: Action) -> Enemy | None:
    """The living enemy `action` is aimed at.

    None if it is aimed at a hero, at nobody, or at an enemy that is dead.
    The class files use it in their extra rules.
    """
    enemy = state.enemies.get(action.target) if action.target else None
    return None if enemy is None or enemy.dead else enemy


def _target(state: FightState, unit_id: str) -> Hero | Enemy | None:
    """The unit called `unit_id`, or None if there is none, or it is dead or out.

    A downed hero still counts: they can be healed or helped up.
    """
    hero = state.heroes.get(unit_id)
    if hero is not None:
        return None if hero.out else hero
    enemy = state.enemies.get(unit_id)
    if enemy is not None:
        return None if enemy.dead else enemy
    return None


def _close_enough(hero: Hero, spec: AbilitySpec, square: Pos) -> bool:
    """True when `square` is close enough for `hero` to use `spec` on it.

    A reach of 0 means the ability needs none. Disrupt reaches farther for
    a Mage: its `alt` is the Mage's reach.
    """
    reach = spec.alt if spec.id == "disrupt" and hero.cls == "mage" else spec.range
    return reach == 0 or distance(hero.pos, square) <= reach


# --- The class files ---------------------------------------------------------
# Each class file fills the tables at the top when it is imported. They are
# imported here, at the very bottom, so that everything above is ready for
# them. Later tasks add one line per class file below this comment.
from . import guardian  # noqa: F401
from . import rogue  # noqa: F401
from . import druid  # noqa: F401
from . import mage, shared  # noqa: F401
