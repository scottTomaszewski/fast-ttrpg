# Fast combat ("fast-ttrpg")

A tabletop combat system built for fast, MMO-style fights (about 20 cheap rounds, everyone
rolls at once), plus a Python simulator that plays the test fight thousands of times to tune
the numbers. The owner's child reads this repo too.

Read in this order: `README.md` (how to run it), `rules/` (the player rules), `docs/tuning-log.md`
(what the numbers are and why, and what needs the owner's decision), `docs/handoff.md` (where the
work stands right now), `docs/superpowers/specs/2026-11-24-fast-combat-design.md` (the design).

## How the owner likes to work
- Keep notes and memories in this repo (this file, `docs/handoff.md`, the tuning log), not in an
  assistant's private memory. They work from several devices.
- Plain words in code comments, docs and rules. Short sentences.
- Commit messages: plain, no AI attribution, no co-author trailers.
- Subagents run on the opus model.
- The owner decides game design. When something is not settled, make a call, say it, and list it
  in `docs/tuning-log.md` under "Rules the simulator had to decide" or "Needs a decision".
- Repo is private on GitHub (`origin`); work on `main`; push when a piece of work is done.

## Rules that are easy to break
- Every game number lives in `game/numbers.toml` or `game/fights/*.toml`, never in code.
- `tests/data/` is a frozen copy of the numbers for the tests. Retuning changes `game/`, never
  `tests/data/`.
- The owner's per-ability use targets are in `game/usage_targets.toml`. Only the owner changes them.
- Never loosen a check in `src/fastcombat/report.py` to make tuning pass. A check that cannot be met
  goes under "Not met" in the tuning log, and the slow test is marked xfail with that reason.
- After changing a number, run `uv run fastcombat rules` (the rules pages are made from the
  numbers; a test fails if they are stale).
- Heroes act in name order (Druid, Guardian, Mage, Rogue). Renaming a hero changes results.
- Never trade one class's use band against another's (owner): reach a class's bands with its own
  numbers and play; move fight numbers only for wins, length and danger. See the tuning log, "D4c".

## Commands
    uv run pytest -q -W error          # all quick tests
    uv run pytest -m slow -v            # the tuning-targets test (about a minute)
    uv run fastcombat run --n 1000      # play fights and print a summary
    uv run fastcombat check --n 3000 --seed 100000   # every target, pass or fail
    uv run fastcombat rules             # remake rules/ from rules/templates/
    --set abilities.meteor.cost=8       # try one number for one run without editing files
