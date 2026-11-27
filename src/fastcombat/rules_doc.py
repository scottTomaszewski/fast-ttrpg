"""Making the player rules from their templates.

The rules a family plays from are in `rules/`. They are not written by
hand: each one is made from a template in `rules/templates/`, with every
number filled in from the game files. So when a number is tuned, running
`fastcombat rules` puts the new number into the rules too, and a test fails
if someone forgets.

How to write a template is at the top of `rules/templates/README.md`. In
short: `{abilities.meteor.cost}` becomes that number, `{heroes.mage.hp -
enemy.wolf.damage}` becomes the sum, and `{# a note #}` is left out.

What a placeholder can name:

- `rules.NAME`, `heroes.CLASS.FIELD`, `abilities.ID.FIELD`: the numbers file.
  An ability also has `timing` ("Instant", "Cast, 1 round", "Channel, 3 hits")
  and `loud_tag` (" · **Loud**" for a Loud ability, and nothing for others).
- `enemy.TYPE.FIELD`, `boss.MOVE.FIELD`, `spawns.TYPE.count` and
  `spawns.TYPE.round`, `fight.name`, `fight.width`, `fight.height` and
  `fight.map`: the fight. A boss move also has `rounds` (the rounds it comes
  up), and so does an enemy that casts (`cast_rounds`).
- `fights.FIGHT.` and any of the above, to name the fight. Without it, a
  template in `templates/fights/` means the fight with its name, and any
  other template means the only fight there is.
- `dice.sides` ("d4, d6 and d8") and `dice.most` (the most dice rolled at once).

Dice are written like `8d6`, or `2d6+4` with a bonus. Yes-or-no fields are
written "yes" and "no".
"""

import re
from dataclasses import dataclass, fields
from pathlib import Path

from fastcombat.numbers import FightDef, Numbers, load_fight, load_numbers

# The real rules folder, found from where this file is.
RULES = Path(__file__).resolve().parents[2] / "rules"

# A note: `{#`, anything, `#}`, and the space after it.
_NOTE = re.compile(r"\{#.*?#\}\s*", re.S)
_PLACEHOLDER = re.compile(r"\{([^{}]*)\}")
_PATH = re.compile(r"[a-z_][a-z0-9_]*(\.[a-z0-9_]+)+")
# How many rounds `rounds` lists before "and so on". Only how it is written.
_ROUNDS_SHOWN = 5
# The parts of a fight a placeholder can name.
_FIGHT_PARTS = ("enemy", "boss", "spawns", "fight")


class RulesError(ValueError):
    """A template could not be made into rules. The message says which file and why."""


class _Unknown(Exception):
    """A placeholder names nothing. The message says why."""


@dataclass(frozen=True)
class Game:
    """Everything the rules are made from: the numbers file and every fight file."""

    numbers: Numbers
    fights: dict[str, FightDef]  # by file name, without ".toml"


@dataclass(frozen=True)
class _Dice:
    count: int
    sides: int
    bonus: int = 0

    def __str__(self) -> str:
        bonus = f"+{self.bonus}" if self.bonus else ""
        return f"{self.count}d{self.sides}{bonus}"


def load_game(game_dir: Path) -> Game:
    """Read `numbers.toml` and every fight in `fights/` from `game_dir`."""
    numbers = load_numbers(game_dir / "numbers.toml")
    fights = {path.stem: load_fight(path) for path in sorted((game_dir / "fights").glob("*.toml"))}
    return Game(numbers, fights)


def render(text: str, game: Game, name: str, fight: str | None = None) -> str:
    """The template `text` with its notes left out and its placeholders filled in.

    `name` is the template's file name, for error messages. `fight` is the
    fight that `enemy.`, `boss.` and the like mean; if it is None, they
    mean the only fight there is.
    """
    if fight is None and len(game.fights) == 1:
        fight = next(iter(game.fights))

    def fill(match: re.Match) -> str:
        try:
            return _value(match.group(1), game, fight)
        except _Unknown as why:
            raise RulesError(f"{name}: unknown placeholder {match.group(0)} ({why})") from None

    return _PLACEHOLDER.sub(fill, _NOTE.sub("", text))


def render_all(rules_dir: Path, game: Game) -> dict[Path, str]:
    """Every template in `rules_dir/templates`, made into rules.

    Gives back the text of each one by where it goes, relative to
    `rules_dir`: `templates/classes/mage.md` goes to `classes/mage.md`.
    Each starts with a line saying where it came from, which a Markdown
    viewer does not show.
    """
    templates = rules_dir / "templates"
    if not templates.is_dir():
        raise RulesError(f"there are no templates: {templates} is not a folder")
    made = {}
    for path in sorted(templates.rglob("*.md")):
        where = path.relative_to(templates)
        header = (
            f"<!-- Made from templates/{where.as_posix()} by `uv run fastcombat rules`. "
            "Change the template, not this file. -->\n\n"
        )
        made[where] = header + render(
            path.read_text(), game, where.as_posix(), _fight_for(where, game)
        )
    return made


def write_rules(rules_dir: Path, game: Game) -> list[Path]:
    """Make every template into rules and write them. Gives back the files written.

    Nothing is written if any template has a mistake.
    """
    made = render_all(rules_dir, game)
    for where, text in made.items():
        out = rules_dir / where
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
    return [rules_dir / where for where in made]


def _fight_for(where: Path, game: Game) -> str | None:
    """The fight a template in `templates/fights/` is about: the one with its name.

    `fights/ogre-warlord.md` is about `ogre_warlord.toml`. Any other template
    gets None (the only fight there is).
    """
    if where.parts[0] == "fights":
        stem = where.stem.replace("-", "_")
        if stem in game.fights:
            return stem
    return None


# --- Working out one placeholder -----------------------------------------------


def _value(expression: str, game: Game, fight: str | None) -> str:
    """What one placeholder (without its braces) is filled in with.

    One name gives its value. Names and whole numbers joined by + and -
    give the sum, which has to be 0 or more.
    """
    parts = re.split(r"\s*([+-])\s*", expression.strip())
    terms = [_term(part, game, fight) for part in parts[::2]]
    if len(terms) == 1:
        return _written(terms[0])
    for term, part in zip(terms, parts[::2]):
        if not isinstance(term, int) or isinstance(term, bool):
            raise _Unknown(f"{part} is not a number, so it cannot be added")
    total = terms[0]
    for sign, term in zip(parts[1::2], terms[1:]):
        total = total + term if sign == "+" else total - term
    if total < 0:
        raise _Unknown(f"it comes out below 0 ({total})")
    return str(total)


def _term(part: str, game: Game, fight: str | None) -> object:
    if part.isdigit():
        return int(part)
    if not _PATH.fullmatch(part):
        raise _Unknown("a placeholder is a name with dots, like abilities.meteor.cost")
    head, *rest = part.split(".")
    if head == "fights":
        name = rest[0] if rest else ""
        if name not in game.fights:
            raise _Unknown(f"no fight called {name!r} in game/fights/")
        if len(rest) < 2 or rest[1] not in _FIGHT_PARTS:
            raise _Unknown(f"after the fight, say one of: {', '.join(_FIGHT_PARTS)}")
        return _in_fight(game, game.fights[rest[0]], rest[1], rest[2:])
    if head in _FIGHT_PARTS:
        if fight is None:
            raise _Unknown(f"which fight? There are several: say fights.NAME.{part}")
        return _in_fight(game, game.fights[fight], head, rest)
    if head == "rules":
        return _one(rest, game.numbers.rules, "rule")
    if head == "heroes":
        return _field(_one(rest[:1], game.numbers.heroes, "hero class"), rest[1:])
    if head == "abilities":
        ability = _one(rest[:1], game.numbers.abilities, "ability")
        extra = {"timing": _timing(ability), "loud_tag": " · **Loud**" if ability.loud else ""}
        return _field(ability, rest[1:], extra)
    if head == "dice":
        return _one(rest, {"sides": _sides(game), "most": _most(game)}, "dice placeholder")
    raise _Unknown(f"{head!r} is not something a placeholder can name")


def _in_fight(game: Game, fight: FightDef, part: str, rest: list[str]) -> object:
    if part == "fight":
        about = {"name": fight.name, "width": fight.width, "height": fight.height}
        return _one(rest, about | {"map": _Text(_map(fight))}, "fight placeholder")
    if part == "enemy":
        enemy = _one(rest[:1], fight.enemy_types, "enemy")
        extra = {}
        if enemy.cast_every > 0:
            extra["cast_rounds"] = _Text(_rounds(enemy.cast_first, enemy.cast_every))
        return _field(enemy, rest[1:], extra)
    if part == "boss":
        moves = {step.name: step for step in fight.boss_script}
        step = _one(rest[:1], moves, "boss move")
        return _field(step, rest[1:], {"rounds": _Text(_rounds(step.first, step.every))})
    # spawns
    kinds = {spawn.type for spawn in fight.spawns}
    kind = _one(rest[:1], {k: k for k in kinds}, "enemy that comes into this fight")
    spawns = [spawn for spawn in fight.spawns if spawn.type == kind]
    rounds = {spawn.round for spawn in spawns}
    about = {"count": len(spawns)}
    if len(rounds) == 1:
        about["round"] = rounds.pop()
    elif rest[1:] == ["round"]:
        raise _Unknown(f"the {kind}s come in different rounds, so there is no one round")
    return _one(rest[1:], about, f"{kind} placeholder")


def _one(rest: list[str], table: dict, what: str) -> object:
    """The one entry `rest` names in `table`."""
    if len(rest) != 1 or rest[0] not in table:
        name = ".".join(rest)
        raise _Unknown(f"no {what} called {name!r}")
    return table[rest[0]]


def _field(record: object, rest: list[str], extra: dict | None = None) -> object:
    """The field `rest` names in a record from the game files, or in `extra`.

    `dice` comes back as dice, with the record's bonus if it has one.
    """
    names = {field.name for field in fields(record)}
    if len(rest) != 1 or (rest[0] not in names and rest[0] not in (extra or {})):
        raise _Unknown(f"no field called {'.'.join(rest)!r}")
    if rest[0] in (extra or {}):
        return extra[rest[0]]
    if rest[0] == "dice":
        count, sides = record.dice
        if count == 0:
            raise _Unknown("it rolls no dice")
        return _Dice(count, sides, getattr(record, "bonus", 0))
    value = getattr(record, rest[0])
    if isinstance(value, (tuple, list, dict)):
        raise _Unknown(f"{rest[0]} is not one number or word")
    return value


class _Text(str):
    """Text worked out from the game files, like the map. It is not a number."""


def _written(value: object) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def _timing(ability) -> str:
    if ability.cast > 0:
        return f"Cast, {ability.cast} round{'s' if ability.cast > 1 else ''}"
    if ability.hits > 0:
        return f"Channel, {ability.hits} hits"
    return "Instant"


def _rounds(first: int, every: int) -> str:
    shown = [str(first + every * i) for i in range(_ROUNDS_SHOWN)]
    return ", ".join(shown) + " and so on"


def _all_dice(game: Game) -> list[tuple[int, int]]:
    """Every (count, sides) the game rolls, the heroes' auto-attack dice too."""
    dice = [(1, hero.die) for hero in game.numbers.heroes.values()]
    dice += [a.dice for a in game.numbers.abilities.values()]
    for fight in game.fights.values():
        dice += [enemy.dice for enemy in fight.enemy_types.values()]
        dice += [step.dice for step in fight.boss_script]
    return [d for d in dice if d[0] > 0]


def _sides(game: Game) -> _Text:
    names = [f"d{sides}" for sides in sorted({sides for _, sides in _all_dice(game)})]
    if len(names) == 1:
        return _Text(names[0])
    return _Text(", ".join(names[:-1]) + " and " + names[-1])


def _most(game: Game) -> int:
    return max(count for count, _ in _all_dice(game))


def _map(fight: FightDef) -> str:
    """The fight's map as text: where every hero starts, and every enemy comes in.

    Heroes are capital letters, enemies small ones, and `+` is a start
    square for a hero past the first of each class. A legend follows.
    """
    grid = [["."] * fight.width for _ in range(fight.height)]
    legend = []
    used: set[str] = set()
    for cls, (x, y) in fight.hero_starts.items():
        letter = _letter(cls, used, upper=True)
        grid[y][x] = letter
        legend.append(f"{letter} {cls.capitalize()}")
    for x, y in fight.extra_starts:
        grid[y][x] = "+"
    legend.append("+ where an extra hero starts (a second Rogue, say)")
    letters: dict[str, str] = {}
    for spawn in fight.spawns:
        if spawn.type not in letters:
            letters[spawn.type] = _letter(spawn.type, used, upper=False)
        x, y = spawn.pos
        grid[y][x] = letters[spawn.type]
    for kind, letter in letters.items():
        spec = fight.enemy_types[kind]
        notes = [spec.tier] if spec.tier in ("boss", "fodder") else []
        late = sorted({s.round for s in fight.spawns if s.type == kind and s.round > 0})
        if late:
            notes.append("comes in round " + " and ".join(map(str, late)))
        legend.append(f"{letter} {kind}" + (f" ({', '.join(notes)})" if notes else ""))
    rows = [" ".join(row) for row in grid]
    return "\n".join(rows + [""] + legend)


def _letter(name: str, used: set[str], upper: bool) -> str:
    """The first letter of `name` not used yet on the map, as a capital or not."""
    for char in name:
        letter = char.upper() if upper else char.lower()
        if letter.isalpha() and letter not in used:
            used.add(letter)
            return letter
    raise RulesError(f"no letter is left to show {name!r} on the map")
