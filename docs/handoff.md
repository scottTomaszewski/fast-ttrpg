# Where the work stands (2026-11-27)

Delete or rewrite this file when the work below is done.

## Done
- The design, the simulator, the report and checks, and the player rules in
  `rules/` (made from the numbers). The full kit for four classes and the
  Ogre Warlord fight, retuned in D4, D4b and D4c. Details: `docs/tuning-log.md`.
- D4c (2026-11-27), the owner's decisions:
  - **Firebolt is a 2-round cast**, all or nothing. It is now 6d6 for 9
    mana: a whole Volley's damage in two of her act steps instead of three, for
    more mana. The
    Mage starts one only with a whole Volley's mana to spare and no enemy
    able to walk up to her, and lets it go to Disrupt or get away.
  - **Evocation's band 0.3 to 2** is the owner's.
  - **One of each is not the game:** a class's bands are reached with its
    own numbers and play, never by trading against another class. Written
    into the design, the tuning log and `CLAUDE.md`. The Guardian now
    Shield Slams with every ally above 70% HP; the Rogue Kidney Shots an add
    attacking anyone. No fight number changed.
  - **20 Sap cards** accepted until a table test.
  - **Reactions** written down as an idea, not planned.
- On the official run (`check --n 3000 --seed 100000`) every check passes:
  wins 86.4%, 66.4% of fights in 18 to 22 rounds. On the other two confirm
  ranges only Kidney Shot fails (0.48, 0.49), under "Not met". The slow
  targets test passes on its seeds, so it is no longer xfail.
- The rules pages: every class's "How to play" tips rewritten from how the
  heroes play now; the Mage's Firebolt and the core cast rules updated.
  Ready for the owner to read.

## Open for the owner (the tuning log, "Needs a decision")
- **Kidney Shot** sits on its line (0.48 to 0.54): it and Eviscerate share
  the Rogue's full combo points, about 2.5 a fight here. "Not met" says why.
- **The `needed:` check is a man down** (item 18). Without any one hero the
  party wins under 1%. With one class swapped for a second copy of another,
  a party with no Druid or no Guardian but a second Mage wins about 85%;
  every party without a Mage wins 5% or less. The owner may want a
  different check.
- **Reactions** (item 19): an idea for Ice Block, Disrupt, maybe Last Stand
  and Intercede.
- Older items still open: the Rogue's opening is not a real choice (item 8),
  the Rogue Kidney Shots the last enemy instead of killing it (item 14),
  and only the Guardian gives Taunt cards, the old cause of stalemates
  (item 3).
- Printable card sheets are a later step.
- Small known thing: `_firebolt_finishes` (`policies.py`) ignores a
  controlled enemy at any distance; one already next to her whose stun ends
  first can make her drop the Firebolt for Frost Nova. Very rare (about
  0.001 a fight). Fix: ignore a controlled enemy only when it is more than
  one square away.

## Next
1. The owner reads `rules/`. Refresh the copies in the owner's Obsidian
   vault (`~/Documents/obsidian/main/fast-ttrpg/`) once it is pushed.

## Working notes
- Briefs given to subagents live in `.superpowers/sdd/round3/` (git-ignored, this machine only).
  Everything important from them is in this file and the tuning log.
