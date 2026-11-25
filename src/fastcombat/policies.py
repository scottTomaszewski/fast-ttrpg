"""How a hero plays: where to move, and what to do.

A policy answers two questions for one hero each party turn: in the move
step, which square to go to (`move`), and in the act step, what to do
(`act`). The round loop in `fight.py` asks, and checks the answers: a move
that is too far or onto someone does not happen, and an action that is not
allowed is the same as doing nothing.
"""

from typing import Protocol

from fastcombat.abilities import Action
from fastcombat.grid import Pos, approach, distance
from fastcombat.units import Enemy, FightState, Hero


class Policy(Protocol):
    def move(self, state: FightState, hero: Hero) -> Pos: ...
    def act(self, state: FightState, hero: Hero) -> Action: ...


class AutoOnly:
    """Walk to the nearest living enemy that is not controlled, and auto-attack it.

    It never uses an ability. Nearest is counted in steps; if two enemies
    are just as near, the one whose id comes first. A stunned, sapped or
    sheeped enemy is left alone. With no enemy to go for, it stays put and
    does nothing.
    """

    def move(self, state: FightState, hero: Hero) -> Pos:
        enemy = _nearest_enemy(state, hero)
        if enemy is None:
            return hero.pos
        return approach(
            hero.pos,
            enemy.pos,
            state.numbers.rules["hero_move"],
            state.occupied(),
            state.fight.width,
            state.fight.height,
            reach=state.numbers.heroes[hero.cls].attack_range,
        )

    def act(self, state: FightState, hero: Hero) -> Action:
        enemy = _nearest_enemy(state, hero)
        reach = state.numbers.heroes[hero.cls].attack_range
        if enemy is None or distance(hero.pos, enemy.pos) > reach:
            return Action("none")
        return Action("auto", target=enemy.id)


# Every policy by name, so one can be picked by its name.
POLICIES: dict[str, type] = {"auto": AutoOnly}


def default_policy(cls: str) -> Policy:
    """The policy a hero of class `cls` plays by when nobody picks one.

    For now every class only auto-attacks. Each class gets its own policy later.
    """
    return AutoOnly()


def _nearest_enemy(state: FightState, hero: Hero) -> Enemy | None:
    """The nearest living enemy that is not controlled (ties: by id), or None."""
    free = [enemy for enemy in state.living_enemies() if not enemy.controlled]
    return min(free, key=lambda enemy: (distance(hero.pos, enemy.pos), enemy.id), default=None)
