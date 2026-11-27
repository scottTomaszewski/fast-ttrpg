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

## Owner decisions, 2026-11-27 (not built yet)
- **Sap** lasts much longer (try 10, 15, 20 cards). Sap does not need Shadowstep.
- **Rogue's opening:** before round 1 she picks one enemy and either sneaks (stealth check, for
  example d6 on 4+; success: starts next to it, hidden; failure: spotted, normal start, not hidden)
  or Shadowsteps in (always works, starts with less energy by Shadowstep's cost).
- **Polymorph** is too short at 4 rounds; try longer.
- **Shield Slam** (new, Guardian): free, a hit bigger than his auto-attack, on a cooldown, gives
  grit. Target 2 to 3 uses a fight: "the tank should be busy and Shield Slam should only fit in
  when everything is going super well." It is last in his list.
- **Mage:** Quicken is benched (kept in code, not used, not on the sheet). Ice Block and Evocation
  join the kit (Time Warp and Mirror Image skipped for now). 8 buttons on the Mage is fine; the
  rule is no class has more than 1.5 times as many buttons as another.
- **Cleanse** removes any one bad card (a stun too), never Bleeding.
- **The ogre gets Stomp:** announced, then stuns the heroes next to it, so Cleanse has stuns.
- Usage bands I proposed for the owner to confirm: Ice Block 0.2-1.5, Evocation 0.3-2.

## Next, in order
1. **D3b:** the Rogue's opening, long Sap, longer Polymorph (pick lengths by the numbers).
2. **D3c:** Shield Slam, Ice Block, Evocation, benching Quicken, wider Cleanse, the ogre's Stomp.
3. **D4: retune** `game/` so every check passes on `check --n 3000 --seed 100000`, including all
   `use:` checks. The tuner may also change grit regen / grit per attack and the Mage's
   `auto_gain`. Frozen: class dice, mana and energy pools and regen, cast times, card counts
   (except Sap's and Polymorph's), `max_rounds`.
4. **D5:** update rule text and class tips, re-render `rules/`, review, push, refresh the copies in
   the owner's Obsidian vault (`~/Documents/obsidian/main/fast-ttrpg/`).

## Open questions for the owner (also in the tuning log)
- Last Stand fails its band by a hair (0.198) now the Guardian cannot see the boss script.
  Fixes: cheaper Last Stand, more grit, or decide players may learn the boss's rhythm.
- Meteor's value comes mostly from the shaman standing in it; enemies walk out of the area.
- Printable card sheets are a later step.

## Working notes
- Briefs given to subagents live in `.superpowers/sdd/round3/` (git-ignored, this machine only).
  Everything important from them is in this file.
