# Fast combat simulator

This program plays the fast combat rules for a tabletop game over and over,
with each hero following written-down rules for how to play. It counts how
the fights went, so we can tell if the numbers are fair and fun before
anyone sits down at the table.

## The two commands

Play 1000 fights and print how they went:

    uv run fastcombat run --n 1000

Play them, then play again with each hero left out in turn, and check
everything against the targets in the design (a fight lasts 18 to 22
rounds, the party wins about 4 times in 5, and so on). It prints PASS or
FAIL for each target:

    uv run fastcombat check --n 1000

The checks about the whole fight:

- `length`: at least 60% of fights last 18 to 22 rounds.
- `win_rate`: the party wins 70% to 90% of fights.
- `no_timeouts`: no fight runs out of rounds (the simulator stops at
  round 60 and counts it as a loss).
- `danger`: in at least half the fights some hero drops to 25% HP or goes
  down.
- `auto_share`: auto-attacks do 15% to 50% of all the heroes' damage.

The tuning is confirmed on seeds never used while tuning:

    uv run fastcombat check --n 3000 --seed 100000
    uv run fastcombat check --n 1000 --seed 400000
    uv run fastcombat check --n 1000 --seed 700000

Two checks are there for each hero. `needed:` plays the fight without
that hero, and wants at least 20 points fewer wins. That is a man down
(three heroes in a fight made for four), not a party without that class;
the tuning log, "Needs a decision", has both. `kit:` keeps the hero
in the fight but has them only auto-attack (the `auto` policy), and wants
at least 10 points fewer wins. Taking a hero out also takes away their HP,
so a hero whose abilities make the party weaker could still pass
`needed:`; `kit:` catches that. The same fights (the same seeds) are
played each time, so the numbers can be compared.

`taunt:boss` plays the fight with the Guardian never using Taunt on the
boss (the `guardian_no_boss_taunt` policy; Challenging Shout can still taunt it) and
wants at least 10 points fewer wins; it is only there when the party has a
Guardian.

`resource:` is there for each hero: they should be starved (too little
left to pay for their cheapest ability) in under 20% of the rounds they
are up, because every hero should be able to act in an emergency, and
end under half of the fights up with a full pool.

## How often each ability is used

Both commands print a uses table: for each hero, each ability and how many
times it was used in a fight, on the mean (all heroes of a class added
together). An ability never used shows 0.0, so a button nobody presses
stands out. Starting a cast counts as one use, even if it is stopped; a
channel counts once, not once per hit. Hauling a downed ally up is listed
too, as `haul_up`.

`check` also has a `use:` check for each ability. `game/usage_targets.toml`
says how many times a fight each one should be used (`min`, and `max` if
there is an upper limit), with a comment saying what kind of button it is
in an MMO (a main builder, a big emergency, an interrupt...). The check
passes when the mean is in that band. The bands are for the test party,
one hero of each class, so with any other party the `use:` checks are left
out. These are the owner's targets: tuning changes the game numbers to
meet them, never this file. To try other targets, point `check` at
another file:

    uv run fastcombat check --usage my_targets.toml

A benched ability (`benched = true` in `game/numbers.toml`, like Quicken
for now) is out of the game: nobody uses it, it is not in the uses table,
and it has no `use:` check, so it needs no target. Try one back for a run
with `--set abilities.quicken.benched=false` (it then needs a target in the
usage file again).

`uv run fastcombat run --help` lists every option: which fight, which
party (`--party guardian,rogue,rogue`), the first seed, and `--json PATH` to
save the results to a file.

## Tests

    uv run pytest -q -W error     # the quick tests, a few seconds
    uv run pytest -m slow -v      # plays `check --n 600 --seed 500000`, about a minute

The tests read a frozen copy of the numbers in `tests/data/`, so retuning
`game/` does not change them. The slow test reads the real numbers.

## The rules

The rules a family plays from are in [`rules/README.md`](rules/README.md):
the core rules, a sheet for each hero, the cards, and the test fight for
the GM. They are made from templates in `rules/templates/`, with every
number filled in from the game files. After changing a number, or a
template, run:

    uv run fastcombat rules

A test fails if the rules in `rules/` are not what the templates make, so
a retuned number cannot leave the rules out of step.

## Where the numbers live

Every number in the game is in one of two places:

- `game/numbers.toml`: the rules, the heroes, and their abilities.
- `game/fights/`: one file for each fight, with the map, the enemies and
  what the boss does.

`game/usage_targets.toml` is not game numbers: it is how often each ability
should be used, which the game numbers are tuned to meet.

## Trying a change

`--set` changes one number for one run, without editing the file. Give it
as many times as you like:

    uv run fastcombat check --set abilities.meteor.cost=12 --set heroes.guardian.hp=70

The name is the place in `game/numbers.toml`, with dots between the parts.
If the change helps, write it into the file. A misspelled name stops the
run with a message saying what is wrong, so a typo never quietly plays the
old numbers. `--set` only changes the numbers file, not the fight file.
