"""Turning many fights into one summary, and checking it against the targets.

`summarize` adds up a list of fights. `check_targets` compares the summary
with what the design asks for (see "Numbers" in the design) and gives back
one pass or fail for each target. The `format_` functions print them for
people to read.

Shares are written as 0.25 for 25%.
"""

import statistics
from dataclasses import dataclass

from fastcombat.fight import FightResult

# What the design asks for. These are not game numbers: they are the targets
# the game numbers are tuned to meet.
BAND = (18, 22)  # a fight should last this many rounds, ends included...
IN_BAND_AT_LEAST = 0.60  # ...in at least this share of fights
WIN_RATE = (0.70, 0.90)  # win most fights, but not all
DANGER_HP = 0.25  # a hero at this share of max HP or less is in danger...
DANGER_AT_LEAST = 0.50  # ...and that should happen in at least this share of fights
AUTO_SHARE = (0.20, 0.50)  # auto-attacks' share of all hero damage
STARVED_UNDER = 0.50  # no hero starved for this share of rounds or more
ENDED_FULL_UNDER = 0.50  # no hero ends this share of fights or more up, with a full pool
NEEDED_AT_LEAST = 0.20  # wins should drop at least this much without any one hero

# Win rates are counts divided by the number of fights, so one taken from
# another can come out a hair under what it should be (0.7 - 0.5 is
# 0.19999999999999996 to a computer). A difference this small is not real.
_TINY = 1e-9


@dataclass
class Summary:
    """How a batch of fights went. Every table is by hero id."""

    fights: int
    win_rate: float
    timeout_rate: float
    rounds_median: float
    rounds_p10: float  # a tenth of the fights were this short or shorter
    rounds_p90: float  # a tenth of the fights were this long or longer
    in_band: float  # share of fights lasting 18 to 22 rounds
    danger_rate: float  # share of fights where some hero dropped to 25% HP or went down
    down_rate: dict[str, float]  # share of fights each hero went down at least once
    auto_share: float  # auto-attack damage / all hero damage
    damage_share: dict[str, float]  # each hero's part of all hero damage
    healing_share: dict[str, float]  # each hero's part of all healing
    starved: dict[str, float]  # mean share of rounds starved
    ended_full: dict[str, float]  # share of fights ending up, with a full pool
    resource_curve: dict[str, list[float]]  # mean resource at each round


@dataclass
class Check:
    """One target: its name, whether it was met, what it came to, and what was wanted."""

    name: str
    passed: bool
    value: str
    wanted: str


def summarize(results: list[FightResult]) -> Summary:
    """Add up a batch of fights, all with the same party.

    Damage, healing and auto share are counted over all the fights put
    together, so a long fight counts for more than a short one. The
    resource curve at round 15 is the mean over the fights that got that far.

    A hero "ended full" only if they were up at the end with a full pool. A
    hero who is down or out gets no resource back, so a full pool then only
    means they fell before spending it, not that they had too much.
    """
    if not results:
        raise ValueError("there are no fights to sum up")
    n = len(results)
    heroes = list(results[0].tally.damage)
    rounds = sorted(r.rounds for r in results)
    if n == 1:
        p10 = p90 = float(rounds[0])
    else:
        tenths = statistics.quantiles(rounds, n=10, method="inclusive")
        p10, p90 = tenths[0], tenths[-1]

    damage = {h: sum(r.tally.damage[h] for r in results) for h in heroes}
    auto = sum(sum(r.tally.auto_damage.values()) for r in results)
    healing = {h: sum(r.tally.healing[h] for r in results) for h in heroes}

    return Summary(
        fights=n,
        win_rate=_share(results, lambda r: r.won),
        timeout_rate=_share(results, lambda r: r.timeout),
        rounds_median=float(statistics.median(rounds)),
        rounds_p10=float(p10),
        rounds_p90=float(p90),
        in_band=_share(results, lambda r: BAND[0] <= r.rounds <= BAND[1]),
        danger_rate=_share(results, _in_danger),
        down_rate={h: _share(results, lambda r: r.tally.times_down[h] > 0) for h in heroes},
        auto_share=_part(auto, sum(damage.values())),
        damage_share={h: _part(damage[h], sum(damage.values())) for h in heroes},
        healing_share={h: _part(healing[h], sum(healing.values())) for h in heroes},
        starved={
            h: sum(r.tally.starved_rounds[h] / r.rounds for r in results) / n for h in heroes
        },
        ended_full={h: _share(results, lambda r: _ended_full(r, h)) for h in heroes},
        resource_curve={h: _curve([r.tally.resource_by_round[h] for r in results]) for h in heroes},
    )


def check_targets(full: Summary, without: dict[str, Summary]) -> list[Check]:
    """Check the full party's summary against each target, in a fixed order.

    `without` holds, for each hero id, the summary of the party with that
    hero taken out. It gives one `needed:` check each.
    """
    low, high = WIN_RATE
    auto_low, auto_high = AUTO_SHARE
    checks = [
        Check(
            "length",
            full.in_band >= IN_BAND_AT_LEAST,
            f"{_pct(full.in_band)} of fights",
            f"at least {_pct(IN_BAND_AT_LEAST)} last {BAND[0]} to {BAND[1]} rounds",
        ),
        Check(
            "win_rate",
            low <= full.win_rate <= high,
            _pct(full.win_rate),
            f"{_pct(low)} to {_pct(high)}",
        ),
        Check("no_timeouts", full.timeout_rate == 0, _pct(full.timeout_rate), "none"),
        Check(
            "danger",
            full.danger_rate >= DANGER_AT_LEAST,
            f"{_pct(full.danger_rate)} of fights",
            f"at least {_pct(DANGER_AT_LEAST)} have a hero at {_pct(DANGER_HP)} HP or down",
        ),
        Check(
            "auto_share",
            auto_low <= full.auto_share <= auto_high,
            f"{_pct(full.auto_share)} of damage",
            f"{_pct(auto_low)} to {_pct(auto_high)}",
        ),
    ]
    for hero in full.starved:
        starved, ended_full = full.starved[hero], full.ended_full[hero]
        checks.append(
            Check(
                f"resource:{hero}",
                starved < STARVED_UNDER and ended_full < ENDED_FULL_UNDER,
                f"starved {_pct(starved)} of rounds, "
                f"ended up and full {_pct(ended_full)} of fights",
                f"both under {_pct(STARVED_UNDER)}",
            )
        )
    for hero, other in without.items():
        drop = full.win_rate - other.win_rate
        checks.append(
            Check(
                f"needed:{hero}",
                drop >= NEEDED_AT_LEAST - _TINY,
                f"wins {_pct(full.win_rate)} with, {_pct(other.win_rate)} without",
                f"at least {_pct(NEEDED_AT_LEAST)} fewer wins without them",
            )
        )
    return checks


def format_summary(s: Summary) -> str:
    """The summary as a short table for people."""
    lines = [
        f"Fights played:          {s.fights}",
        f"Wins:                   {_whole_pct(s.win_rate)}",
        f"Ran out of rounds:      {_whole_pct(s.timeout_rate)}",
        f"Rounds:                 median {s.rounds_median:g}, "
        f"most between {s.rounds_p10:g} and {s.rounds_p90:g}",
        f"Lasted {BAND[0]} to {BAND[1]} rounds: {_whole_pct(s.in_band)}",
        f"A hero in danger:       {_whole_pct(s.danger_rate)} "
        f"(down to {_whole_pct(DANGER_HP)} HP, or went down)",
        f"Auto-attack damage:     {_whole_pct(s.auto_share)} of all damage",
        "",
        f"{'hero':<10}{'damage':>8}{'healing':>9}{'starved':>9}{'up and full':>13}{'went down':>11}",
    ]
    for h in s.damage_share:
        lines.append(
            f"{h:<10}{_whole_pct(s.damage_share[h]):>8}{_whole_pct(s.healing_share[h]):>9}"
            f"{_whole_pct(s.starved[h]):>9}{_whole_pct(s.ended_full[h]):>13}"
            f"{_whole_pct(s.down_rate[h]):>11}"
        )
    return "\n".join(lines)


def format_checks(checks: list[Check]) -> str:
    """One line for each check: PASS or FAIL, its name, what it came to, what was wanted."""
    width = max((len(c.name) for c in checks), default=0)
    return "\n".join(
        f"{'PASS' if c.passed else 'FAIL'}  {c.name:<{width}}  {c.value}  (wanted: {c.wanted})"
        for c in checks
    )


def _share(results: list[FightResult], happened) -> float:
    """The share of fights in which `happened(fight)` is true."""
    return sum(1 for r in results if happened(r)) / len(results)


def _part(amount: float, total: float) -> float:
    """`amount` as a share of `total`, or 0 when there is no total."""
    return amount / total if total else 0.0


def _ended_full(r: FightResult, hero: str) -> bool:
    """Was `hero` up at the end of this fight, with a full pool?"""
    return hero in r.heroes_up and r.end_resource[hero] == r.pool[hero]


def _in_danger(r: FightResult) -> bool:
    """Did some hero drop to the danger line, or go down, in this fight?"""
    tally = r.tally
    return any(
        tally.lowest_hp[h] <= DANGER_HP or tally.times_down[h] > 0 for h in tally.lowest_hp
    )


def _curve(per_fight: list[list[int]]) -> list[float]:
    """The mean at each round, over the fights that lasted that long."""
    longest = max(len(values) for values in per_fight)
    curve = []
    for i in range(longest):
        values = [v[i] for v in per_fight if i < len(v)]
        curve.append(sum(values) / len(values))
    return curve


def _pct(share: float) -> str:
    """A share as a percent with one decimal, like 62.5%."""
    return f"{share:.1%}"


def _whole_pct(share: float) -> str:
    """A share as a whole percent, like 62%."""
    return f"{share:.0%}"
