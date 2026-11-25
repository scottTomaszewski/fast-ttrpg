"""Reading the numbers file and the fight files.

Every number in the game lives in `game/numbers.toml` (the rules, the heroes
and their abilities) or in a fight file under `game/fights/` (the map, the
enemies and the boss's script). This file reads them into simple records and
checks them closely. A typo stops the simulator with a message that says
where it is, so it never quietly plays the wrong game.

A place in a file is written as a dotted path, like `abilities.meteor.cost`.
Lists use a number in brackets, counting from 0: `spawns[3].type` is the
`type` of the fourth spawn.
"""

import tomllib
from collections.abc import Iterable
from dataclasses import MISSING, dataclass, fields
from pathlib import Path

from fastcombat.grid import Pos


class NumbersError(ValueError):
    """Something in a numbers file or a fight file is wrong. The message says where."""


# The words a few settings may be. Anything else is a mistake.
RESOURCES = ("grit", "energy", "mana")
TIERS = ("normal", "elite", "boss", "fodder")
PREFERS = ("nearest", "backline", "random")
KINDS = ("blast", "heavy", "throw")
SHARED = "shared"  # an ability's `hero` when any hero may use it


@dataclass(frozen=True)
class HeroSpec:
    """One class of hero: its HP, its auto-attack, and its resource."""

    hp: int
    die: int  # sides on the auto-attack die
    attack_range: int
    resource: str  # one of RESOURCES
    pool: int  # the most resource it can hold
    start: int  # resource at the start of a fight
    regen: int  # resource back at the top of each party turn
    crit_gain: int  # what a crit gives; each class uses it its own way


@dataclass(frozen=True)
class AbilitySpec:
    """One ability. The numbers file explains each field above the abilities."""

    id: str  # the ability's name, from its table in the file
    hero: str  # the class that has it, or SHARED
    cost: int = 0
    cast: int = 0  # rounds to cast; 0 means it happens at once
    hits: int = 0  # how many hits a channel makes; 0 means not a channel
    range: int = 0  # 0 means it needs no reach: used on yourself, or around you
    radius: int = 0
    dice: tuple[int, int] = (0, 0)  # (how many dice, sides on each)
    bonus: int = 0
    cards: int = 0  # how many rounds it lasts
    value: int = 0  # what each card is worth
    alt: int = 0  # a second number, explained per ability
    loud: bool = False
    cooldown: int = 0


@dataclass(frozen=True)
class Numbers:
    """Everything in the numbers file."""

    rules: dict[str, int]
    heroes: dict[str, HeroSpec]
    abilities: dict[str, AbilitySpec]


@dataclass(frozen=True)
class EnemySpec:
    """One kind of enemy in a fight.

    `hp`, `move` and `range` have no default: the fight file has to say them.
    """

    type: str  # its name, from its table in the fight file
    hp: int
    move: int  # squares it walks in a turn
    range: int  # how far its attack reaches; 1 means next to it
    tier: str = "normal"  # one of TIERS
    damage: int = 0  # a plain hit; most enemies do not roll
    dice: tuple[int, int] = (0, 0)  # for enemies that do roll, like the boss
    bonus: int = 0
    prefers: str = "nearest"  # who it goes for, one of PREFERS
    shielded: int = 0  # ignores any single hit below this
    poison_cards: int = 0
    poison_value: int = 0
    cast_every: int = 0  # rounds between its heals of the boss
    cast_first: int = 0  # the round of its first heal
    cast_heal: int = 0


@dataclass(frozen=True)
class Spawn:
    """One enemy coming into the fight: what it is, where, and in which round.

    Round 0 means it is there from the start.
    """

    type: str
    pos: Pos
    round: int = 0


@dataclass(frozen=True)
class ScriptStep:
    """One move in the boss's script.

    It first comes up in round `first`, then again every `every` rounds.
    """

    name: str
    kind: str  # one of KINDS
    first: int
    every: int
    dice: tuple[int, int]
    radius: int = 0


@dataclass(frozen=True)
class FightDef:
    """Everything in a fight file."""

    name: str
    width: int
    height: int
    hero_starts: dict[str, Pos]  # where each class stands at the start
    extra_starts: list[Pos]  # for a second hero of a class, or one with no start
    enemy_types: dict[str, EnemySpec]
    spawns: list[Spawn]
    boss_script: list[ScriptStep]


def load_numbers(path: Path, overrides: dict[str, object] | None = None) -> Numbers:
    """Read and check the numbers file.

    `overrides` changes some numbers first, to try an idea without editing
    the file. Each key is a dotted path to one number, such as
    "abilities.meteor.cost". The changed numbers are checked like the rest.
    """
    raw = _read(path)
    for key, value in (overrides or {}).items():
        _override(raw, key, value)
    _check_keys(raw, Numbers, "")

    rules = {
        name: _check(value, int, f"rules.{name}")
        for name, value in _check(raw["rules"], dict, "rules").items()
    }

    heroes = {}
    for name, table in _check(raw["heroes"], dict, "heroes").items():
        where = f"heroes.{name}"
        hero = _build(HeroSpec, table, where)
        _check_word(hero.resource, RESOURCES, f"{where}.resource")
        heroes[name] = hero

    abilities = {}
    for name, table in _check(raw["abilities"], dict, "abilities").items():
        where = f"abilities.{name}"
        ability = _build(AbilitySpec, table, where, id=name)
        if ability.hero != SHARED and ability.hero not in heroes:
            raise NumbersError(
                f"{where}.hero: {ability.hero!r} is not a hero in this file, "
                f"and not {SHARED!r}"
            )
        abilities[name] = ability

    return Numbers(rules, heroes, abilities)


def load_fight(path: Path) -> FightDef:
    """Read and check one fight file."""
    raw = _read(path)
    _check_keys(raw, FightDef, "")

    hero_starts = {
        name: _check(pos, Pos, f"hero_starts.{name}")
        for name, pos in _check(raw["hero_starts"], dict, "hero_starts").items()
    }
    extra_starts = [
        _check(pos, Pos, f"extra_starts[{i}]")
        for i, pos in enumerate(_check(raw["extra_starts"], list, "extra_starts"))
    ]

    enemy_types = {}
    for name, table in _check(raw["enemy_types"], dict, "enemy_types").items():
        where = f"enemy_types.{name}"
        enemy = _build(EnemySpec, table, where, type=name)
        _check_word(enemy.tier, TIERS, f"{where}.tier")
        _check_word(enemy.prefers, PREFERS, f"{where}.prefers")
        enemy_types[name] = enemy

    spawns = []
    for i, table in enumerate(_check(raw["spawns"], list, "spawns")):
        spawn = _build(Spawn, table, f"spawns[{i}]")
        if spawn.type not in enemy_types:
            raise NumbersError(
                f"spawns[{i}].type: there is no {spawn.type!r} in enemy_types"
            )
        spawns.append(spawn)

    boss_script = []
    for i, table in enumerate(_check(raw["boss_script"], list, "boss_script")):
        step = _build(ScriptStep, table, f"boss_script[{i}]")
        _check_word(step.kind, KINDS, f"boss_script[{i}].kind")
        boss_script.append(step)

    return FightDef(
        name=_check(raw["name"], str, "name"),
        width=_check(raw["width"], int, "width"),
        height=_check(raw["height"], int, "height"),
        hero_starts=hero_starts,
        extra_starts=extra_starts,
        enemy_types=enemy_types,
        spawns=spawns,
        boss_script=boss_script,
    )


def _read(path: Path) -> dict:
    with open(path, "rb") as file:
        try:
            return tomllib.load(file)
        except tomllib.TOMLDecodeError as error:
            raise NumbersError(f"{path}: this is not a TOML file ({error})") from error


def _override(raw: dict, key: str, value: object) -> None:
    """Put `value` at the dotted path `key`, before anything is checked.

    Every part of the path but the last has to be a table already in the
    file. A rule has to be in the file too: any name is allowed for a rule,
    so a misspelled one would otherwise be quietly added and never used.
    """
    *parents, last = key.split(".")
    table = raw
    for depth, part in enumerate(parents):
        table = table.get(part)
        if not isinstance(table, dict):
            where = ".".join(parents[: depth + 1])
            raise NumbersError(f"{key}: there is no table called {where} to change")
    if parents == ["rules"] and last not in table:
        raise NumbersError(f"{key}: there is no such rule to change")
    table[last] = value


def _build(record: type, table: object, where: str, **given: str):
    """Make one record (such as a HeroSpec) from a table in the file.

    `given` holds fields that come from outside the table, such as an
    ability's `id`, which is the name of its table.
    """
    table = _check(table, dict, where)
    _check_keys(table, record, where, given)
    values = {
        field.name: _check(table[field.name], field.type, f"{where}.{field.name}")
        for field in fields(record)
        if field.name in table
    }
    return record(**given, **values)


def _check_keys(
    table: dict, record: type, where: str, given: Iterable[str] = ()
) -> None:
    """Every key in `table` must be a field of `record`, and none may be missing.

    A field with a default may be left out. A field in `given` is filled in
    from outside, so it may not be in the table.
    """
    allowed = {field.name for field in fields(record)} - set(given)
    for key in table:
        if key not in allowed:
            raise NumbersError(
                f"{_join(where, key)}: no such setting (is it spelled right?)"
            )
    for field in fields(record):
        has_default = (
            field.default is not MISSING or field.default_factory is not MISSING
        )
        if field.name in allowed and field.name not in table and not has_default:
            raise NumbersError(
                f"{_join(where, field.name)}: missing, and it has to be there"
            )


# How to say what each kind of value should look like.
_SHOULD_BE = {
    int: "a whole number",
    str: "a word in quotes",
    bool: "true or false",
    Pos: "a pair of whole numbers, like [2, 6]",
    dict: "a table",
    list: "a list",
}


def _check(value: object, kind: object, where: str):
    """Give back `value` if it is the right kind. A pair becomes a tuple."""
    if kind is int and _whole(value):
        return value
    # `==`, not `is`: each `tuple[int, int]` written out is its own object.
    if kind == Pos and isinstance(value, (list, tuple)):
        if len(value) == 2 and all(map(_whole, value)):
            return tuple(value)
    if kind in (str, bool, dict, list) and type(value) is kind:
        return value
    raise NumbersError(f"{where}: should be {_SHOULD_BE[kind]}, not {value!r}")


def _whole(value: object) -> bool:
    # In Python, true and false count as numbers. Here they do not.
    return isinstance(value, int) and not isinstance(value, bool)


def _check_word(value: str, allowed: tuple[str, ...], where: str) -> None:
    if value not in allowed:
        raise NumbersError(f"{where}: {value!r} should be one of {', '.join(allowed)}")


def _join(where: str, key: str) -> str:
    return f"{where}.{key}" if where else key
