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
- D3c (built): the owner's 2026-11-27 kit decisions. **Shield Slam** (Guardian,
  free, 2d8, 1 grit, cooldown 2, last in his list). **Ice Block** and **Evocation** (Mage);
  **Quicken benched** (`benched = true` in `game/`: in the code, not usable, off the sheet and
  the checks). **Cleanse** takes any one bad card (`units.BAD_STACKS`), never Bleeding.
  **Hero stuns** (no move, no act; the card comes off at the end of the party turn). The
  ogre's **Stomp** (rounds 8, 14, 20; 1d6 and 1 stun next to him). The Guardian stays to take a
  Stomp when a Druid is up to Cleanse him. Proposed bands for the owner: Ice Block 0.2-1.5,
  Evocation 0.3-2. Design rule: no class has more than 1.5 times another's buttons.
  Results and every rule call: tuning log, "D3c".

- D4: the retune for the full kit (tuning log, "D4").
- D4b (done, not pushed): the owner's calls on D4, and honest buttons.
  Start grit 4 and combo points 3 accepted; Shield Slam band 0.5 to 1.5
  and Ice Block 0.1 to 1.5 (the owner's); the auto-attack floor is 15%
  (owner's "if needed": it was). Arcane Volley 2d6 (a whole Volley does
  as much for its mana as a Firebolt), Backstab 5, Blink back to 6,
  Challenging Shout radius 4, ogre HP 130. The Mage Ice Blocks at half HP;
  the Stomp's Disrupter is whoever's Disrupt rule really goes for it. The
  Mage already breaks a Volley to Disrupt and keeps the hits (0.4 a
  fight). On the three confirm ranges everything passes but Shield Slam
  (0.47 to 0.53) and Kidney Shot (0.49 to 0.53), which pull against each
  other ("Not met"); the slow test stays xfail. All in the tuning log,
  "D4b" and "Final".

## Next, in order
1. **D5:** update rule text and class tips, re-render `rules/`, review, push, refresh the copies in
   the owner's Obsidian vault (`~/Documents/obsidian/main/fast-ttrpg/`). (The Mage's Volley tip is
   already written, D4b.)

## Open questions for the owner (also in the tuning log, "Needs a decision")
- (D4b) Shield Slam and Kidney Shot cannot both clear 0.5 a fight: lower
  one band a little, or change Shield Slam's "every ally above 75%" rule
  (item 16).
- (D4b) Firebolt has no turn in the middle in the simulator, so per act
  step it does twice what a Volley does; the Mage Volleys only because her
  rules say so (item 17).
- (D4b) Evocation's band 0.3 to 2 is still only proposed.
- (D4) The Rogue's opening: even at Shadowstep 5 the judgement rule always
  Shadowsteps in; the round-1 Sap is worth about 22 points of wins.
- (D4) The Rogue Kidney Shots the last enemy instead of Eviscerating it
  (it caused a rare stalemate, ended with numbers).
- Meteor's value comes mostly from the shaman standing in it; enemies walk out of the area.
- Printable card sheets are a later step.
- (Settled) 20 Sap cards: accepted for now, to be tried at the table.

## Working notes
- Briefs given to subagents live in `.superpowers/sdd/round3/` (git-ignored, this machine only).
  Everything important from them is in this file.
