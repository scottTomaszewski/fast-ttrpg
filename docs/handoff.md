# Where the work stands (2026-11-27)

Delete or rewrite this file when the work below is done.

## Done
- Design, simulator, report and checks, two retunes, the player rules in `rules/` (made from the
  numbers), all pushed to GitHub.
- Bosses ignore the "next to the tank" hold; only Taunt cards keep a boss on the tank. The ogre
  goes for the back line when untaunted. A `taunt:boss` check proves taunting matters.
- The Warden was renamed the Guardian, with the owner's original ability names (Taunt,
  Challenging Shout, Intercede, Grip, Shield Plant, Last Stand). He now acts second, which moved
  the results.
- Per-ability use counts and `use:` checks against the owner's targets in
  `game/usage_targets.toml`. Resource check tightened: every hero starved in under 20% of rounds.
  The Mage's auto-attack gives 1 mana on a hit (`auto_gain`). The brute is an elite.

## In progress
**D3: heroes press every button for MMO reasons** (`src/fastcombat/policies.py`). The owner's
asks: Arcane Volley is the Mage's go-to damage spell (its Loud tag may be dropped if Loud breaks
the tank); Meteor on 3+ enemies, allies walk out of the marked area; Sap on an elite in almost
every fight; the Guardian keeps grit for emergencies (Last Stand, Intercede); Shield Plant makes
allies stand behind it instead of running from a blast; every ability lands inside its use band.
Before D3, 16 of 29 abilities missed their band, and the Guardian was starved 51% of rounds.

## Next, in order
1. **D3b: the Rogue's opening and a long Sap** (owner's idea, 2026-11-27). Proposed, not built:
   - Sap lasts much longer; try 10, 15 and 20 cards and pick by the numbers. Damage still wakes it.
   - Before round 1 the Rogue picks one enemy and either sneaks (a stealth check: roll a die, for
     example d6 on 4+, numbers in the numbers file; success starts her next to it, hidden; failure
     means spotted: normal start square, not hidden) or Shadowsteps in (always works, starts the
     fight with less energy, by Shadowstep's cost). Her priority list chooses.
   - Report how often each is chosen, the check success rate, and Sap uses per fight.
2. **D4: retune** `game/` so every check passes on `check --n 3000 --seed 100000`, including all
   `use:` checks. The tuner may also change grit regen / grit per attack and the Mage's
   `auto_gain`. Frozen: class dice, mana and energy pools and regen, cast times, card counts
   (except Sap's, set in D3b), `max_rounds`.
3. **D5:** update rule text and class tips to match, re-render `rules/`, review, push.

## Open questions for the owner (also in the tuning log)
- Grit is tight for the Guardian; D3/D4 aim to fix it.
- Meteor, Sap, Shield Plant, Last Stand, Cheap Shot, Vanish, Blink are rarely or never used (D3).
- Printable card sheets are a later step.

## Working notes
- Briefs given to subagents live in `.superpowers/sdd/round3/` (git-ignored, this machine only).
  Everything important from them is in this file.
