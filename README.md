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

Two checks are there for each hero. `needed:` plays the fight without
that hero, and wants at least 20 points fewer wins. `kit:` keeps the hero
in the fight but has them only auto-attack (the `auto` policy), and wants
at least 10 points fewer wins. Taking a hero out also takes away their HP,
so a hero whose abilities make the party weaker could still pass
`needed:`; `kit:` catches that. The same fights (the same seeds) are
played each time, so the numbers can be compared.

`taunt:boss` plays the fight with the Warden never using Taunt on the
boss (the `warden_no_boss_taunt` policy; AoE Taunt can still taunt it) and
wants at least 10 points fewer wins; it is only there when the party has a
Warden.

`uv run fastcombat run --help` lists every option: which fight, which
party (`--party warden,rogue,rogue`), the first seed, and `--json PATH` to
save the results to a file.

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

## Trying a change

`--set` changes one number for one run, without editing the file. Give it
as many times as you like:

    uv run fastcombat check --set abilities.meteor.cost=12 --set heroes.warden.hp=70

The name is the place in `game/numbers.toml`, with dots between the parts.
If the change helps, write it into the file. A misspelled name stops the
run with a message saying what is wrong, so a typo never quietly plays the
old numbers. `--set` only changes the numbers file, not the fight file.
