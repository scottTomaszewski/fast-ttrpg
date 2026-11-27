# Where the work stands (2026-11-27)

Delete or rewrite this file when the work below is done.

## Done
- Design, simulator, report and checks, two retunes, the player rules in `rules/` (made from the
  numbers), all pushed to GitHub.
- Bosses ignore the "next to the tank" hold; only Taunt cards keep a boss on the tank. The ogre
  goes for the back line when untaunted. A `taunt:boss` check proves taunting matters.
- The Warden was renamed the Guardian, with the owner's original ability names. Frost Ring is now
  Frost Nova and AoE Taunt is now Challenging Shout.
- Per-ability use counts and `use:` checks against the owner's targets in
  `game/usage_targets.toml`. Every hero must be starved in under 20% of rounds.
- D3: heroes press every button for MMO reasons (`policies.py`), reviewed and fixed. Heroes use
  only what the table can see. Arcane Volley is no longer Loud. 7 use bands still fail (Guardian
  grit, Rogue combo points, Mage mana); fights run long (42% in 18-22 rounds). For the retune.
- D3b: the Rogue's opening before round 1 (`opening.py`: Sneak with `sneak_die`/`sneak_target`,
  or Shadowstep in), Sap 20 cards, Polymorph 12, picked by the numbers (tuning log, "D3b").
  The Rogue Shadowsteps in next to the brute and Saps it in round 1. Nobody hits a sapped or
  sheeped enemy while anything else is left. Summary has a "Rogue opening" block. Always
  Sneak won 82.8% against 81.8% for Shadowstep in (noise at 500 fights); Shadowstep in was
  kept for the `use:sap` band, a call the owner can see. The Polymorph pick (12) is tied to
  this fight's goblin timing (a sheep that wakes during the wave is bad).
- D3c (built, not pushed): the owner's 2026-11-27 kit decisions. **Shield Slam** (Guardian,
  free, 2d8, 1 grit, cooldown 2, last in his list). **Ice Block** and **Evocation** (Mage);
  **Quicken benched** (`benched = true` in `game/`: in the code, not usable, off the sheet and
  the checks). **Cleanse** takes any one bad card (`units.BAD_STACKS`), never Bleeding.
  **Hero stuns** (no move, no act; the card comes off at the end of the party turn). The
  ogre's **Stomp** (rounds 8, 14, 20; 1d6 and 1 stun next to him). The Guardian stays to take a
  Stomp when a Druid is up to Cleanse him. Proposed bands for the owner: Ice Block 0.2-1.5,
  Evocation 0.3-2. Design rule: no class has more than 1.5 times another's buttons.
  Results and every rule call: tuning log, "D3c".

## Next, in order
1. **D4: retune** `game/` so every check passes on `check --n 3000 --seed 100000`, including all
   `use:` checks. The tuner may also change grit regen / grit per attack and the Mage's
   `auto_gain`. Frozen: class dice, mana and energy pools and regen, cast times, card counts
   (except Sap's and Polymorph's), `max_rounds`. Watch: since D3b the round-1 opening Sap puts the
   brute to sleep before it ever hits the Guardian, so he has almost no grit early (0.39 at
   the top of round 2, against 1.45 without the opening), and `kit:guardian`, `taunt:boss` and
   `length` fail. With no opening, Sap 20 and Polymorph 12 pass all three (tuning log, D3b,
   "Correction"). Also since D3c: the Stomp costs about 11 points of wins and 13 of length by
   making the melee heroes step around it (not by its hit); Shield Slam is pressed 0.48 a fight
   (band 2-3) and barely helps grit; Ice Block almost never (tuning log, D3c).
2. **D5:** update rule text and class tips, re-render `rules/`, review, push, refresh the copies in
   the owner's Obsidian vault (`~/Documents/obsidian/main/fast-ttrpg/`).

## Open questions for the owner (also in the tuning log)
- Last Stand fails its band by a hair (0.198) now the Guardian cannot see the boss script.
  Fixes: cheaper Last Stand, more grit, or decide players may learn the boss's rhythm.
- Meteor's value comes mostly from the shaman standing in it; enemies walk out of the area.
- Printable card sheets are a later step.
- Is 20 Sap cards too many to handle at the table? One "until hurt or N rounds" card may be better.
- The Rogue's opening is not a real choice yet: Shadowstep in costs 2, and round 1 gives 3 back.
- (D3c) The Stomp's cost is in the stepping, not the stun: change it, or let the retune absorb it?
- (D3c) Shield Slam 0.48 a fight against 2-3: the Guardian is rarely free in this fight.
- (D3c) Ice Block's trigger leaves it almost unused; a wider one costs about 3 points of wins.
- (D3c) Should nobody Disrupt a Ground Slam that everyone has walked out of (as for the Stomp)?
- (D3c) Confirm the proposed bands for Ice Block and Evocation.

## Working notes
- Briefs given to subagents live in `.superpowers/sdd/round3/` (git-ignored, this machine only).
  Everything important from them is in this file.
