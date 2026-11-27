"""The `fastcombat` command: play many fights and say how they went.

    fastcombat run     plays the fights and prints a summary
    fastcombat check   also plays them with each hero left out in turn, with
                       each hero only auto-attacking in turn, and with the
                       Guardian never Taunting the boss, and checks everything
                       against the design's targets and how often each
                       ability should be used
    fastcombat rules   makes the player rules in rules/ from their templates,
                       with the numbers from the game files

`run` and `check` read the real game files (`game/numbers.toml` and
`game/fights/`) unless told to read others. `--set` changes one number for
one run, so an idea can be tried without editing the numbers file. `rules`
always reads the real game files, so the rules in the repo always match
them.
"""

import argparse
import json
import sys
import tomllib
from dataclasses import asdict
from pathlib import Path

from fastcombat.fight import FightResult, run_fight
from fastcombat.numbers import (
    FightDef,
    Numbers,
    NumbersError,
    UsageTarget,
    load_fight,
    load_numbers,
    load_usage,
)
from fastcombat.policies import POLICIES
from fastcombat.report import Summary, check_targets, format_checks, format_summary, summarize
from fastcombat.rules_doc import RULES, RulesError, load_game, write_rules
from fastcombat.units import new_state

# The real game files, found from where this file is, not from where the
# command is run.
GAME = Path(__file__).resolve().parents[2] / "game"


class _Setup:
    """Everything a batch of fights needs, read and checked from the options."""

    def __init__(self, args: argparse.Namespace):
        if args.n < 1:
            raise NumbersError(f"--n: should be 1 or more, not {args.n}")
        self.numbers = load_numbers(Path(args.numbers), _overrides(args.set))
        self.fight = load_fight(_fight_path(args.fight))
        self.party = _party(args.party, self.numbers)
        self.ids = _hero_ids(self.numbers, self.fight, self.party)
        self.policies = _policies(args.policy, self.ids)
        self.seeds = range(args.seed, args.seed + args.n)
        # How often each button should be pressed. The targets are for the
        # test party, one hero of each class, so with any other party there
        # are no `use:` checks. The file is still read, so a typo shows.
        self.usage: dict[str, UsageTarget] | None = None
        if getattr(args, "usage", None):
            usage = load_usage(Path(args.usage), self.numbers)
            if sorted(self.party) == sorted(self.numbers.heroes):
                self.usage = usage

    def play(self, keep: list[int], swap: dict[int, str] | None = None) -> list[FightResult]:
        """Play every seed with only the heroes at the places in `keep`.

        A hero's id can change when another is left out (with two Rogues,
        leaving out "rogue" makes "rogue2" the new "rogue"), so each picked
        policy follows its hero by place in the party, not by id. `swap`
        gives some places another policy by name for these fights, like
        {0: "auto"}.
        """
        swap = swap or {}
        party = [self.party[i] for i in keep]
        ids = _hero_ids(self.numbers, self.fight, party)
        names = {
            ids[k]: swap.get(i) or self.policies[self.ids[i]]
            for k, i in enumerate(keep)
            if i in swap or self.ids[i] in self.policies
        }
        results = []
        for seed in self.seeds:
            # A new policy for each fight, so no fight can change the next.
            policies = {hero: POLICIES[name]() for hero, name in names.items()}
            results.append(run_fight(self.numbers, self.fight, party, policies, seed=seed))
        return results


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "rules":
        return _rules()
    try:
        setup = _Setup(args)
    except (NumbersError, ValueError, OSError) as error:
        print(f"fastcombat: {error}", file=sys.stderr)
        return 2

    everyone = list(range(len(setup.party)))
    full = summarize(setup.play(everyone))
    print(format_summary(full))
    if args.command == "run":
        _write_json(args.json, asdict(full))
        return 0

    without: dict[str, Summary] = {}
    on_auto: dict[str, Summary] = {}
    for i, hero in enumerate(setup.ids):
        rest = [j for j in everyone if j != i]
        if rest:  # a party of one cannot be played without its only hero
            without[hero] = summarize(setup.play(rest))
    for i, hero in enumerate(setup.ids):
        on_auto[hero] = summarize(setup.play(everyone, swap={i: "auto"}))
    # Every Guardian who plays the Guardian's rules stops Taunting the boss. A
    # Guardian made to play another way (like guardian=auto) is left as he is.
    guardians = {
        i: "guardian_no_boss_taunt"
        for i, hero in enumerate(setup.ids)
        if setup.party[i] == "guardian" and setup.policies.get(hero, "guardian") == "guardian"
    }
    no_boss_taunt = summarize(setup.play(everyone, swap=guardians)) if guardians else None
    checks = check_targets(full, without, on_auto, no_boss_taunt, setup.usage)
    print()
    print(format_checks(checks))
    _write_json(
        args.json,
        {
            "full": asdict(full),
            "without": {hero: asdict(s) for hero, s in without.items()},
            "on_auto": {hero: asdict(s) for hero, s in on_auto.items()},
            "no_boss_taunt": asdict(no_boss_taunt) if no_boss_taunt else None,
            "checks": [asdict(c) for c in checks],
        },
    )
    return 0 if all(c.passed for c in checks) else 1


def _parser() -> argparse.ArgumentParser:
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument(
        "--fight",
        default="ogre_warlord",
        help="a fight's name under game/fights/, or the path to a .toml file (default: ogre_warlord)",
    )
    shared.add_argument("--n", type=int, default=1000, help="how many fights to play (default: 1000)")
    shared.add_argument(
        "--seed", type=int, default=0, help="the first seed; fight i uses seed+i (default: 0)"
    )
    shared.add_argument(
        "--party",
        default="guardian,rogue,druid,mage",
        help="the classes in the party, with commas; repeats are fine (default: guardian,rogue,druid,mage)",
    )
    shared.add_argument(
        "--numbers",
        default=str(GAME / "numbers.toml"),
        help="the numbers file to read (default: game/numbers.toml)",
    )
    shared.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="change one number in the numbers file for this run only, like "
        "abilities.meteor.cost=12 or abilities.meteor.dice=[3,6]. Can be given "
        "many times. It changes the numbers file only, not the fight file.",
    )
    shared.add_argument(
        "--policy",
        action="append",
        default=[],
        metavar="HERO=NAME",
        help=f"make one hero play another way, like mage=auto. HERO is a hero id "
        f"(guardian, rogue2, ...); NAME is one of: {', '.join(POLICIES)}",
    )
    shared.add_argument("--json", metavar="PATH", help="also write the results to this file as JSON")

    parser = argparse.ArgumentParser(
        prog="fastcombat", description="Play many fights and say how they went."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "run", parents=[shared], help="play the fights and print a summary"
    )
    check = commands.add_parser(
        "check",
        parents=[shared],
        help="also play with each hero left out, with each hero only "
        "auto-attacking, and with the Guardian never Taunting the boss, and check "
        "the design's targets (exits 0 only if every check passes)",
    )
    check.add_argument(
        "--usage",
        default=str(GAME / "usage_targets.toml"),
        help="how often each ability should be used, for the use: checks "
        "(default: game/usage_targets.toml). The use: checks are only there "
        "when the party is one hero of each class.",
    )
    commands.add_parser(
        "rules",
        help="make the player rules in rules/ from rules/templates/, with the "
        "numbers from game/ (run it after changing a number)",
    )
    return parser


def _rules() -> int:
    """Make the player rules from their templates, and say which files were written."""
    try:
        written = write_rules(RULES, load_game(GAME))
    except (RulesError, NumbersError, OSError) as error:
        print(f"fastcombat: {error}", file=sys.stderr)
        return 2
    for path in written:
        print(f"wrote {path.relative_to(RULES.parent)}")
    return 0


def _overrides(pairs: list[str]) -> dict[str, object]:
    """Turn each KEY=VALUE into one override. VALUE is read as TOML: 12, true, [2, 6], "nearest"."""
    overrides: dict[str, object] = {}
    for pair in pairs:
        key, equals, value = pair.partition("=")
        key = key.strip()
        if not equals or not key:
            raise NumbersError(f"--set {pair}: should look like KEY=VALUE, such as abilities.meteor.cost=12")
        try:
            overrides[key] = tomllib.loads(f"v = {value}")["v"]
        except tomllib.TOMLDecodeError:
            raise NumbersError(
                f"{key}: {value!r} is not a value (words go in quotes, like \"nearest\")"
            ) from None
    return overrides


def _fight_path(fight: str) -> Path:
    """A fight's name means the file of that name under game/fights/."""
    if fight.endswith(".toml") or "/" in fight:
        path = Path(fight)
    else:
        path = GAME / "fights" / f"{fight}.toml"
    if not path.is_file():
        raise NumbersError(f"--fight: there is no fight {fight!r} (looked for {path})")
    return path


def _party(text: str, numbers: Numbers) -> list[str]:
    party = [cls.strip() for cls in text.split(",")]
    for cls in party:
        if cls not in numbers.heroes:
            raise NumbersError(
                f"--party: {cls!r} is not a hero class in the numbers file "
                f"(there are: {', '.join(numbers.heroes)})"
            )
    return party


def _hero_ids(numbers: Numbers, fight: FightDef, party: list[str]) -> list[str]:
    """The heroes' ids, in party order, named the way a fight names them."""
    return list(new_state(numbers, fight, party, seed=0).heroes)


def _policies(pairs: list[str], ids: list[str]) -> dict[str, str]:
    """Turn each HERO=NAME into a policy name for that hero id."""
    chosen: dict[str, str] = {}
    for pair in pairs:
        hero, equals, name = (part.strip() for part in pair.partition("="))
        if not equals:
            raise NumbersError(f"--policy {pair}: should look like HERO=NAME, such as mage=auto")
        if hero not in ids:
            raise NumbersError(
                f"--policy: there is no hero {hero!r} in the party (there are: {', '.join(ids)})"
            )
        if name not in POLICIES:
            raise NumbersError(
                f"--policy: there is no policy {name!r} (there are: {', '.join(POLICIES)})"
            )
        chosen[hero] = name
    return chosen


def _write_json(path: str | None, data: object) -> None:
    if path:
        Path(path).write_text(json.dumps(data, indent=2) + "\n")
