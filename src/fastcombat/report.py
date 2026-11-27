"""Turning many fights into one summary, and checking it against the targets.

`summarize` adds up a list of fights. `check_targets` compares the summary
with what the design asks for (see "Numbers" in the design) and gives back
one pass or fail for each target. The `format_` functions print them for
people to read.

Shares are written as 0.25 for 25%.
"""

import math
import statistics
from dataclasses import dataclass, field

from fastcombat.combat import BROKEN_BY_DAMAGE
from fastcombat.fight import FightResult
from fastcombat.numbers import SHARED, UsageTarget
from fastcombat.opening import KINDS as OPENING_KINDS
from fastcombat.units import CONTROL_STACKS

# What the design asks for. These are not game numbers: they are the targets
# the game numbers are tuned to meet.
BAND = (18, 22)  # a fight should last this many rounds, ends included...
IN_BAND_AT_LEAST = 0.60  # ...in at least this share of fights
WIN_RATE = (0.70, 0.90)  # win most fights, but not all
DANGER_HP = 0.25  # a hero at this share of max HP or less is in danger...
DANGER_AT_LEAST = 0.50  # ...and that should happen in at least this share of fights
# Auto-attacks' share of all hero damage. The floor was 20%; lowered to 15%
# (owner 2026-11-27, "We can lower if needed"): with honest Arcane Volley and
# Backstab numbers it is about 16% (tuning log, "D4b"). Never below 15%.
AUTO_SHARE = (0.15, 0.50)
# No hero is starved (too little to pay for their cheapest ability) for
# this share of their up rounds or more: the owner wants every hero able to
# act in an emergency.
STARVED_UNDER = 0.20
ENDED_FULL_UNDER = 0.50  # no hero ends this share of fights or more up, with a full pool
NEEDED_AT_LEAST = 0.20  # wins should drop at least this much without any one hero
# Wins should also drop at least this much when any one hero only
# auto-attacks. Taking a hero out also takes away their HP, so a hero whose
# kit makes the party weaker can still pass the check above. This one keeps
# the hero in the fight and takes away only their kit.
KIT_AT_LEAST = 0.10
# Wins should drop at least this much when the Guardian never Taunts the
# boss. A boss with no Taunt cards goes for whoever it likes, so keeping
# Taunt cards on it should be worth real wins, as for a tank in an MMO.
TAUNT_BOSS_AT_LEAST = 0.10

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
    starved: dict[str, float]  # mean share of the rounds they were up, starved
    ended_full: dict[str, float]  # share of fights ending up, with a full pool
    lowest_hp: dict[str, float]  # mean of the lowest share of max HP they got to
    resource_curve: dict[str, list[float]]  # mean resource at each round
    # Mean uses per fight of each button the party has, by ability id, with
    # every hero's uses added together. A button never pressed is there at 0.
    uses: dict[str, float]
    kit: dict[str, str]  # whose each button in `uses` is: a class, or "shared"
    # The Rogues' openings before round 1 (see `opening.py`): mean times per
    # fight each one was picked, all Rogues together ("sneak" counts the
    # stealth checks that failed too). Empty with no Rogue in the party.
    openings: dict[str, float] = field(default_factory=dict)
    sneak_success: float | None = None  # share of stealth checks that worked; None if nobody sneaked
    # Mean GM turns per fight that enemies lost to each kind of control card
    # ("stun", "sap", "sheep"), all enemies together.
    rounds_out: dict[str, float] = field(default_factory=dict)
    # Share of fights that ended with a living enemy sapped, or a sheep:
    # by card name, "sap" and "sheep".
    asleep_at_end: dict[str, float] = field(default_factory=dict)


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
    means they fell before spending it, not that they had too much. For the
    same reason "starved" counts only the rounds the hero was up.
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
            h: sum(_part(r.tally.starved_rounds[h], r.tally.up_rounds[h]) for r in results) / n
            for h in heroes
        },
        ended_full={h: _share(results, lambda r: _ended_full(r, h)) for h in heroes},
        lowest_hp={h: sum(r.tally.lowest_hp[h] for r in results) / n for h in heroes},
        resource_curve={h: _curve([r.tally.resource_by_round[h] for r in results]) for h in heroes},
        uses={
            a: sum(used.get(a, 0) for r in results for used in r.tally.uses.values()) / n
            for a in results[0].kit
        },
        kit=dict(results[0].kit),
        openings=_openings(results),
        sneak_success=_sneak_success(results),
        rounds_out={
            name: sum(r.tally.rounds_out.get(name, 0) for r in results) / n
            for name in CONTROL_STACKS
        },
        asleep_at_end={
            name: _share(results, lambda r: name in r.controlled_at_end)
            for name in BROKEN_BY_DAMAGE
        },
    )


def _openings(results: list[FightResult]) -> dict[str, float]:
    """Mean times per fight each opening was picked. A failed Sneak is a Sneak."""
    if not results[0].tally.openings:
        return {}
    picked = {kind: 0 for kind in OPENING_KINDS}
    for r in results:
        for made in r.tally.openings.values():
            picked["sneak" if made == "spotted" else made] += 1
    return {kind: count / len(results) for kind, count in picked.items()}


def _sneak_success(results: list[FightResult]) -> float | None:
    """The share of stealth checks that worked, or None if there were none."""
    made = [m for r in results for m in r.tally.openings.values() if m in ("sneak", "spotted")]
    return made.count("sneak") / len(made) if made else None


def check_targets(
    full: Summary,
    without: dict[str, Summary],
    on_auto: dict[str, Summary] | None = None,
    no_boss_taunt: Summary | None = None,
    usage: dict[str, UsageTarget] | None = None,
) -> list[Check]:
    """Check the full party's summary against each target, in a fixed order.

    `without` holds, for each hero id, the summary of the party with that
    hero taken out. It gives one `needed:` check each. `on_auto` holds, for
    each hero id, the summary of the same party with only that hero playing
    the `auto` policy (it never uses an ability). It gives one `kit:` check
    each. `no_boss_taunt` is the summary of the same party with the Guardian
    playing `guardian_no_boss_taunt` (he never Taunts the boss). It gives
    the `taunt:boss` check; with no Guardian there is none, and no check.
    `usage` holds how often each button should be pressed. It gives one
    `use:` check for each button in the summary; with no `usage`, there are
    none (the targets are for a party of one of each class).
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
                f"starved under {_pct(STARVED_UNDER)}, "
                f"ended up and full under {_pct(ENDED_FULL_UNDER)}",
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
    for hero, other in (on_auto or {}).items():
        drop = full.win_rate - other.win_rate
        checks.append(
            Check(
                f"kit:{hero}",
                drop >= KIT_AT_LEAST - _TINY,
                f"wins {_pct(full.win_rate)} with the kit, {_pct(other.win_rate)} on auto",
                f"at least {_pct(KIT_AT_LEAST)} fewer wins when they only auto-attack",
            )
        )
    if no_boss_taunt is not None:
        drop = full.win_rate - no_boss_taunt.win_rate
        checks.append(
            Check(
                "taunt:boss",
                drop >= TAUNT_BOSS_AT_LEAST - _TINY,
                f"wins {_pct(full.win_rate)} with, "
                f"{_pct(no_boss_taunt.win_rate)} when the Guardian never Taunts the boss",
                f"at least {_pct(TAUNT_BOSS_AT_LEAST)} fewer wins without Taunting the boss",
            )
        )
    if usage is not None:
        checks += [_use_check(button, uses, usage[button]) for button, uses in full.uses.items()]
    return checks


def _use_check(button: str, uses: float, target: UsageTarget) -> Check:
    """The `use:` check for one button: pressed `uses` times per fight, on the mean."""
    if target.max == math.inf:
        wanted = f"at least {target.min:g} per fight"
    else:
        wanted = f"{target.min:g} to {target.max:g} per fight"
    return Check(f"use:{button}", target.min <= uses <= target.max, f"{uses:.2f} per fight", wanted)


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
        f"{'hero':<10}{'damage':>8}{'healing':>9}{'starved':>9}{'up and full':>13}"
        f"{'went down':>11}{'lowest HP':>11}",
    ]
    for h in s.damage_share:
        lines.append(
            f"{h:<10}{_whole_pct(s.damage_share[h]):>8}{_whole_pct(s.healing_share[h]):>9}"
            f"{_whole_pct(s.starved[h]):>9}{_whole_pct(s.ended_full[h]):>13}"
            f"{_whole_pct(s.down_rate[h]):>11}{_whole_pct(s.lowest_hp[h]):>11}"
        )
    lines += ["", "Uses per fight (all heroes of a class together):"]
    width = max((len(a) for a in s.uses), default=0)
    owners = list(dict.fromkeys(s.kit.values()))
    # Each class's own buttons under its name, then the ones anyone has.
    for owner in sorted(owners, key=lambda o: o == SHARED):
        lines.append("anyone" if owner == SHARED else owner)
        lines += [f"  {a:<{width}}  {s.uses[a]:5.1f}" for a in s.uses if s.kit[a] == owner]
    if s.openings:
        lines += ["", *_format_openings(s)]
    return "\n".join(lines)


def _format_openings(s: Summary) -> list[str]:
    """The "Rogue opening" block: what the Rogues did before round 1, and how
    long their Saps kept enemies out."""
    success = "-" if s.sneak_success is None else _whole_pct(s.sneak_success)
    return [
        "Rogue opening (per fight, all Rogues together):",
        f"  sneak {s.openings['sneak']:.2f}, shadowstep in {s.openings['shadowstep']:.2f}, "
        f"none {s.openings['none']:.2f}",
        f"  stealth checks that worked: {success}",
        f"  rounds an enemy spent sapped: {s.rounds_out['sap']:.1f} "
        f"(still sapped at the end of {_whole_pct(s.asleep_at_end['sap'])} of fights)",
        f"  rounds an enemy spent as a sheep: {s.rounds_out['sheep']:.1f} "
        f"(still a sheep at the end of {_whole_pct(s.asleep_at_end['sheep'])} of fights)",
    ]


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
