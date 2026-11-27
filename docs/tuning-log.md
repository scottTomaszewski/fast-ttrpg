# Tuning log

This is where we write down how the numbers were tuned: what we changed,
why, and what the simulator said after. The targets are in the design
(`docs/superpowers/specs/2026-11-24-fast-combat-design.md`, "Numbers").

## First pass: 2026-11-25

### Where we started

Command: `uv run fastcombat check --n 1000 --json out/baseline.json`

```
Fights played:          1000
Wins:                   0%
Ran out of rounds:      0%
Rounds:                 median 10, most between 8 and 13
Lasted 18 to 22 rounds: 1%
A hero in danger:       100% (down to 25% HP, or went down)
Auto-attack damage:     4% of all damage

hero        damage  healing  starved  up and full  went down
warden          2%       0%       0%           0%       100%
rogue          37%       0%       1%           0%       100%
druid           0%     100%       0%           0%       100%
mage           60%       0%       2%           0%       100%

FAIL  length           0.9% of fights  (wanted: at least 60.0% last 18 to 22 rounds)
FAIL  win_rate         0.0%  (wanted: 70.0% to 90.0%)
PASS  no_timeouts      0.0%  (wanted: none)
PASS  danger           100.0% of fights  (wanted: at least 50.0% have a hero at 25.0% HP or down)
FAIL  auto_share       3.9% of damage  (wanted: 20.0% to 50.0%)
PASS  resource:warden  starved 0.2% of rounds, ended up and full 0.0% of fights  (wanted: both under 50.0%)
PASS  resource:rogue   starved 0.6% of rounds, ended up and full 0.0% of fights  (wanted: both under 50.0%)
PASS  resource:druid   starved 0.0% of rounds, ended up and full 0.0% of fights  (wanted: both under 50.0%)
PASS  resource:mage    starved 1.6% of rounds, ended up and full 0.0% of fights  (wanted: both under 50.0%)
FAIL  needed:warden    wins 0.0% with, 0.0% without  (wanted: at least 20.0% fewer wins without them)
FAIL  needed:rogue     wins 0.0% with, 0.0% without  (wanted: at least 20.0% fewer wins without them)
FAIL  needed:druid     wins 0.0% with, 0.0% without  (wanted: at least 20.0% fewer wins without them)
FAIL  needed:mage      wins 0.0% with, 0.0% without  (wanted: at least 20.0% fewer wins without them)
```

### What was wrong

- The party lost every fight, in about 10 rounds. The Warden lost 37 of
  60 HP in the first two rounds and was down by round 5.
- Twelve goblins and two shamans were too much on top of the ogre, the
  brute and two wolves.
- The Warden almost never auto-attacked (about 2 damage a fight). Grit
  came in so fast that there was always an ability to use.
- Even when we made the heroes impossible to kill, a fight took 38
  rounds: the boss had too much HP for how fast the party hits.

### Kept changes, in the order they were made

Each line: what changed, from what to what, why, and the check after
(`check --n 1000`, seeds 0 to 999). "In band" means the fight lasted 18
to 22 rounds.

Changes 1 to 8 list only the main values (wins, median rounds, in band,
auto share, and danger or a resource number when it mattered). The other
checks were not written down at the time. Win rate and length failed
until change 7. Changes 9 to 11 (the second look, below) list every check.

Survival and the roster (changes 1 to 6) came before length on purpose:
while the party lost every fight in about 10 rounds, how long a fight
"should" last could not be measured yet.

1. Warden HP 60 to 90. The tank fell first in every fight.
   After: wins 0%, median 12 rounds, in band 2%, auto 3%.
   (On its own this did not win fights yet. But the final numbers with
   Warden HP 60 win only 67% of fights, with 59% in band: both fail.)
2. Goblins: two waves of six (rounds 6 and 12) to one wave of six
   (round 6). The second wave buried the party.
   After: wins 1%, median 12, in band 4%, auto 4%.
3. Shamans: two to one. Two shamans meant two poisoners and two healers.
   After: wins 5%, median 17, in band 26%, auto 14%.
4. Goblin move 5 to 1. Meteor takes two rounds to land, and its spot is
   fixed when it starts, so fast goblins had always walked out of it
   (Meteor was cast 0.1 times a fight). Slow goblins get caught, and they
   stop swarming the Mage.
   After: wins 54%, median 33, in band 11%, ran out of rounds 0.4%,
   auto 23%. All four `needed:` checks pass from here on.
   Looking back (second look, below): at move 1 the goblins did no harm
   at all. They came in at the far edge in round 6 and almost never
   reached anyone before the fight ended. With their damage set to 0 the
   results were the same (wins 81% against 83%, 300 fights). They only
   soaked up a Meteor and some Rogue auto-attacks. Changed again in 10.
5. Add damage: brute 6 to 4, wolf 4 to 3, shaman 3 to 2. The party still
   lost half its fights to the adds.
   After: wins 69%, median 34, in band 8%, auto 24%. New problem: the
   Warden ended fights full of grit 54% of the time.
6. Challenge cost 1 to 2, Chain Hook cost 2 to 4. Now the Warden has to
   save up, so it auto-attacks more, and ends with less grit.
   After: wins 64%, median 33, in band 10%, auto 28%, Warden ends full
   17%.
7. Ogre HP 320 to 130. Fights were 33 rounds; this is the big one for
   length.
   After: wins 80%, median 19.5, in band 65%, danger 90%, auto 26%. Every
   check passes but one: 1 fight in 1000 ran out of rounds.
8. Boss timings: Ground Slam first round 3 to 4, every 4 rounds to every
   6; Skull Crusher first round 5 to 6. When a Ground Slam is announced,
   the Warden and the Rogue step out of it and lose that turn. With a
   slam every 4 rounds, fights bunched up at 18-19 and 22-23 rounds and
   rarely ended on 20 or 21. Fewer, later slams make the lengths tighter.
   After: wins 81%, median 19, in band 71%, danger 83%, auto 24%.

### Second look: 2026-11-25

A review found two problems with the first pass. First, it raised
`max_rounds` (when the simulator gives up) from 60 to 200, and that is
what made `no_timeouts` pass. A fight that runs past 60 rounds is a
stalemate at the table, so a bigger cap only hid it. Second, the goblins
at move 1 were harmless (see change 4). So the cap went back to 60 and
the goblins were made a real threat again.

9. `max_rounds` back from 200 to 60 (this undoes the first pass's last
   change). It is a guard for the simulator, not a game number.
   After: FAIL no_timeouts 0.1% (1 fight in 1000). Length 70.9%, wins
   81.1%, danger 82.9%, auto 23.7%. Resources (starved / ended full):
   Warden 31.8% / 3.7%, Rogue 1.2% / 5.4%, Druid 0.1% / 19.4%, Mage
   11.1% / 0.0%. Needed (wins without): Warden 4.1%, Rogue 4.3%, Druid
   0.0%, Mage 0.8%. Every other check passes.
   On more seeds it is clearer: 21 of 24000 fights (seeds 40000 to
   63999) ran out of rounds, about 1 in 1100.
10. Goblins: move 1 to 3, the wave comes in round 10 instead of 6, and
   five goblins instead of six. Now they reach the back line and hurt.
   After: FAIL no_timeouts 0.2%. Length 68.4%, wins 75.2%, danger
   90.3%, auto 22.2%. Resources: Warden 29.5% / 4.0%, Rogue 1.0% /
   16.3%, Druid 0.0% / 23.3%, Mage 11.1% / 0.0%. Needed: Warden 3.3%,
   Rogue 6.8%, Druid 0.0%, Mage 0.2%.
11. Warden HP 90 to 100. Most stalemates start when the Warden is out
   (see "Needs a decision", item 3), and the goblins now hit harder.
   After: every check passes. Length 74.6%, wins 82.6%, no timeouts,
   danger 85.9%, auto 22.3%. Resources: Warden 30.3% / 5.0%, Rogue
   1.1% / 16.4%, Druid 0.0% / 25.2%, Mage 10.9% / 0.0%. Needed: Warden
   3.3%, Rogue 8.9%, Druid 0.0%, Mage 0.3%.

**What the goblins do now.** Five goblins come in at the far edge in
round 10 and run at the Druid and the Mage, 3 squares a turn. They do
about 15 damage a fight to the heroes (5% of all the damage the heroes
take; at move 1 it was 1.8, under 1%). Setting their damage to 0 now
changes the fight a lot (`check --n 1000`, seeds 0 to 999):

| | goblins hit for 2 | goblins hit for 0 |
|---|---|---|
| wins | 82.6% | 91.2% (fails: too easy) |
| a hero in danger | 85.9% | 77.9% |
| Warden went down | 37% | 22% |
| Rogue went down | 28% | 21% |
| Druid went down | 20% | 11% |
| Mage went down | 48% | 41% |

The cost: Meteor is not cast any more (0.0 times a fight, against 1.1
at move 1). The Mage only casts it on a spot with four or more enemies
and no hero, and with the goblins coming late and fast, such a spot
does not come up. See "Needs a decision", item 4.

How these were found: goblin move 2, 3 and 4 were each tried with small
changes to the goblin count, the wave's round, the goblins' damage,
other enemies' numbers and hero HP (300 fights each, seeds below
100000). What was tried is under "Tried and not kept".

### Tried and not kept

- Ogre melee 2d6+2 down to 1d6+2, and Boulder 2d6 down to 1d6. These
  helped while the roster was still too big, but once it was smaller the
  fight became too easy (96% to 100% wins). Put back.
- Skull Crusher 6d6 down to 4d6, and Ground Slam 3d6 down to 2d6. No
  change in any check: the Crusher almost never lands, and most heroes
  walk out of the Slam. Put back.
- Intercede cost 2 to 3: no change. Put back.
- Chain Hook cost 6 (tried early, with Challenge 3): too many adds
  reached the back line (6% wins against 22% with cost 4).
- Raising every Warden cost to 3 or more: the Warden was "starved" 71%
  of rounds (it counts against the cheapest ability).
- Goblin move 2: wins 73% and auto share right at 20%. Move 3: wins 53%.
- Goblin wave in round 4 or round 8 instead of 6: worse length.
- Boss HP 115, 120, 140, 150. With the final boss timings, 130 gave the
  best length (120: 68% in band; 130: 73%).
- Ground Slam every 3, 5 or 7 rounds, or first in round 1, 2 or 5: all
  worse than first 4, every 6 (worse length, or too many wins).
- Putting back all three add damage cuts (brute 6, wolf 4, shaman 3):
  wins fell to 70%, the very edge. With Warden HP 100 as well: 75%.
- Moving the brute one square closer so the Rogue can Sap it. See
  "Needs a decision", item 2.

Tried in the second look (300 fights each, seeds 0 to 299, cap 60,
Warden HP 90 unless it says so):

- Goblin move 2, nothing else changed: auto share 19.4% (fails). With
  five goblins: every check passes at 300 fights. With five goblins and
  Warden HP 100, Meteor is still cast 1.1 times a fight and wins are 81%
  (87% with goblin damage 0), but at 1000 fights auto share was only
  20.5%, and 8 of 24000 fights ran out of rounds. Six goblins and
  Warden HP 100: auto 19.3% at 1000 fights (fails), 13 of 24000 ran out
  of rounds. Not kept: too close to failing.
- Goblin move 2 with other fixes: four goblins (a timeout), the wave in
  round 4 (length 51%, auto 15%) or round 8 (auto 19.8%), Firebolt cost
  5 (passes, but auto 20.1%), Firebolt 3d6 (wins 63%), Backstab cost 5
  (a timeout), Meteor cost 12 (auto 18%), Arcane Volley cost 3 or
  Eviscerate cost 4 (no change).
- Goblin move 3 with six goblins in round 6: wins 55%, length 55%,
  auto 15%. Three or four goblins, goblin damage 1, or weaker brute and
  wolves: auto share stays at 18% to 19%. A later wave (round 8 or 10)
  is what brings auto share back: the goblins then soak fewer
  auto-attacks. Four goblins in round 10: wins 82%, but they did less
  harm (with the ogre at move 6, goblin damage 0 moved wins only from
  79% to 83%). Five goblins in
  round 10: wins 75% at 1000 fights, with a fight that ran out of
  rounds. Five with Warden HP 100 is what was kept.
- Goblin move 4: with six goblins in round 6, wins 41%. Four goblins in
  round 10 passes (wins 76%). With Warden HP 100 and the ogre at move 6
  wins are 79% (89% with goblin damage 0), but on 6000 fights some
  still ran out of rounds, with the ogre at move 4 or 6. Not kept.
- Ogre move 4 to 6, so the boss can catch heroes who run: with the
  kept numbers, 0 of 24000 fights ran out of rounds (against 1 of 24000
  at move 4), but wins fall about 3 points. Not kept, because it changes
  how the boss plays, and the stalemate is a hero-play problem (item 3).
- Boulder 3d6 or every round, to break stalemates: wins fell to 54% and
  33%.

### Third look: after the review fixes, 2026-11-25

The final review fixed how the heroes play. The biggest fix was the
Warden's: he used to spend his turns on Taunts that did nothing. Enemies
also stopped picking hidden heroes, the Mage backs off further, and the
Warden now starts with 0 grit. The first two passes were tuned to the
old, weaker Warden, so with the fixes the fight became far too easy.

Where we started (`check --n 1000`, seeds 0 to 999, the numbers above):

```
Fights played:          1000
Wins:                   100%
Ran out of rounds:      0%
Rounds:                 median 18, most between 16 and 21
Lasted 18 to 22 rounds: 58%
A hero in danger:       45% (down to 25% HP, or went down)
Auto-attack damage:     31% of all damage

hero        damage  healing  starved  up and full  went down  lowest HP
warden         24%       0%      11%          76%         2%        34%
rogue          39%       0%       1%          20%         5%        38%
druid           1%     100%       0%          22%         1%        50%
mage           37%       0%      12%           0%         9%        37%

FAIL  length           58.5% of fights  (wanted: at least 60.0% last 18 to 22 rounds)
FAIL  win_rate         99.9%  (wanted: 70.0% to 90.0%)
PASS  no_timeouts      0.0%  (wanted: none)
FAIL  danger           44.7% of fights  (wanted: at least 50.0% have a hero at 25.0% HP or down)
PASS  auto_share       31.0% of damage  (wanted: 20.0% to 50.0%)
FAIL  resource:warden  starved 11.4% of rounds, ended up and full 76.0% of fights  (wanted: both under 50.0%)
PASS  resource:rogue   starved 1.2% of rounds, ended up and full 20.1% of fights  (wanted: both under 50.0%)
PASS  resource:druid   starved 0.1% of rounds, ended up and full 21.9% of fights  (wanted: both under 50.0%)
PASS  resource:mage    starved 12.1% of rounds, ended up and full 0.0% of fights  (wanted: both under 50.0%)
PASS  needed:warden    wins 99.9% with, 3.0% without  (wanted: at least 20.0% fewer wins without them)
PASS  needed:rogue     wins 99.9% with, 46.6% without  (wanted: at least 20.0% fewer wins without them)
PASS  needed:druid     wins 99.9% with, 0.1% without  (wanted: at least 20.0% fewer wins without them)
PASS  needed:mage      wins 99.9% with, 2.8% without  (wanted: at least 20.0% fewer wins without them)
FAIL  kit:warden       wins 99.9% with the kit, 94.5% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
PASS  kit:rogue        wins 99.9% with the kit, 66.7% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
PASS  kit:druid        wins 99.9% with the kit, 22.5% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
PASS  kit:mage         wins 99.9% with the kit, 51.4% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
```

What was wrong:

- The party almost never lost, and fights were a little short.
- Nobody got into real danger in more than half the fights.
- The Warden ended 76% of fights with a full pool of grit. Nothing
  near the end of a fight made him spend it.
- `kit:warden` could not pass: with the Warden only auto-attacking the
  party still won 94.5%, and no kit can win 10 points more than that.

Kept changes (each line: `check --n 1000`, seeds 0 to 999, every check
listed; the numbers carry on from change 11):

12. Ogre melee hit 2d6+2 to 2d6+7 (the `bonus`, 2 to 7). The boss is the
   one who should make the fight hard, and it hits the Warden every
   round. A hurt Warden takes more of the Druid's healing, so the others
   get low too, and the Warden spends grit on Intercede to save them.
   After: every check passes. Length 63.6%, wins 87.1%, no timeouts,
   danger 95.3%, auto 30.1%. Resources (starved / ended full): Warden
   12.4% / 33.2%, Rogue 3.4% / 20.9%, Druid 0.1% / 29.6%, Mage 12.3% /
   0.0%. Needed (wins without): Warden 0.1%, Rogue 2.6%, Druid 0.0%,
   Mage 0.0%. Kit (wins on auto): Warden 65.3%, Rogue 13.9%, Druid
   4.9%, Mage 1.5%.
13. Ogre HP 130 to 150. Wins and length were both close to the edge.
   More boss HP makes the fight longer and a little harder.
   After: every check passes. Length 74.9%, wins 82.9%, no timeouts,
   danger 97.8%, auto 29.8%. Resources: Warden 12.3% / 27.3%, Rogue
   4.1% / 10.4%, Druid 0.1% / 30.2%, Mage 12.7% / 0.0%. Needed: Warden
   0.1%, Rogue 0.9%, Druid 0.0%, Mage 0.0%. Kit: Warden 57.2%, Rogue
   11.4%, Druid 1.1%, Mage 0.9%.
14. Intercede cost 2 to 4. It is the Warden's most used button (about
   2.5 times a fight), so its cost decides how much grit he keeps. At 4
   he spends his grit faster and ends full about half as often. Wins
   did not drop.
   After: every check passes. Length 75.1%, wins 83.9%, no timeouts,
   danger 97.7%, auto 30.4%. Resources: Warden 16.5% / 15.2%, Rogue
   3.4% / 10.7%, Druid 0.1% / 30.9%, Mage 12.6% / 0.0%. Needed: Warden
   0.1%, Rogue 0.8%, Druid 0.0%, Mage 0.0%. Kit: Warden 57.2%, Rogue
   12.2%, Druid 1.1%, Mage 0.7%.
15. Goblin damage 2 to 3. With the boss hitting harder, the goblins had
   become a small part of the fight (goblin damage 0 moved wins only
   from 83% to 89%). At 3 they matter again, and wins come down to
   about 4 in 5.
   After: every check passes. Length 76.0%, wins 79.6%, no timeouts,
   danger 98.8%, auto 30.5%. Resources: Warden 16.7% / 14.0%, Rogue
   3.4% / 10.4%, Druid 0.0% / 31.3%, Mage 12.9% / 0.0%. Needed: Warden
   0.0%, Rogue 0.5%, Druid 0.0%, Mage 0.0%. Kit: Warden 53.2%, Rogue
   10.6%, Druid 1.0%, Mage 0.6%.

On more seeds: 0 of 24000 fights (seeds 40000 to 63999) ran out of
rounds, and the party won 78% of them.

**The goblins after the third look.** Setting their damage to 0 still changes
the fight a lot (`check --n 1000`, seeds 0 to 999):

| | goblins hit for 3 | goblins hit for 0 |
|---|---|---|
| wins | 79.6% | 89.6% (right at the top edge) |
| a hero in danger | 98.8% | 95.7% |
| Warden went down | 58% | 44% |
| Rogue went down | 54% | 46% |
| Druid went down | 24% | 14% |
| Mage went down | 38% | 25% |

Tried in the third look, and not kept (300 to 1000 fights each, seeds
below 100000):

- Each of these alone left wins at 97% or more: Warden HP 80; ogre HP
  150; adds back to brute 6, wolf 4, shaman 3; goblin damage 4; Rogue
  and Druid HP 30 with Mage HP 24.
- Ogre melee 3d6+3: wins 91%. 2d6+5: wins 95%.
- Ogre melee 2d6+8 (with HP 145 or 150): wins 74% to 75%, and the
  Warden went down in two fights of three.
- Ogre melee 2d6+6 with goblin damage 3: wins 86%, too close to 90%.
  With a sixth goblin as well, wins were 80% and it looked fine (the
  `needed:` checks were not run), but it is one more change than what
  was kept, for the same result.
- Challenge cost 2 to 3, or War Cry cost 3 to 5, instead of Intercede:
  the Warden ended full less often (27% of fights) but not as much as
  with Intercede at 4 (18%). Intercede 3: 24%.
- Intercede 3, Challenge 3 and War Cry 4 together: the Warden was
  starved 23% of rounds, with no gain over Intercede alone.

## Needs a decision

These are things numbers alone could not fix well. Each needs a change
to a rule or to how a hero plays, so it is for the owner to decide.

1. **Skull Crusher almost never lands, so Unbroken is never used.** The
   boss announces it about 2 times a fight, but it lands only 0.08 times
   a fight: Disrupt breaks it almost every time (the Mage's Disrupt
   reaches 10 squares, so she can always get it). Unbroken was used 0.0
   times a fight. The "Unbroken moment" in the design does not happen.
   Choices: make the boss's heavy hit something Disrupt cannot break, or
   have the Mage keep Disrupt for the shaman.
   After the third look (the 3000 confirm fights): still true. The
   Crusher is announced 2.0 times a fight and lands 0.03 times (80
   times in 3000 fights). Unbroken was used 23 times in 3000 fights.
2. **Sap never happens.** The Rogue only Saps in round 1, and her rule
   looks 7 squares away (move 6 plus 1). The brute starts 8 squares
   from her. Moving the brute from [10, 7] to [9, 7] makes Sap happen in
   every fight, but it also lets the Mage Meteor the whole group at the
   start. Then the party wins 99-100% and auto-attacks fall to about
   15% of damage. A few tries at making it harder again (stronger adds,
   a second shaman, more boss HP) did not bring auto share back above
   20%. Choices: change where heroes or the brute start and retune
   around it, or change the Rogue's Sap rule.
   After the third look: still true. Sap was used 0 times in the 3000
   confirm fights.
3. **Stalemates once the Warden is out.** With the first pass's
   numbers, about 1 fight in 1100 was still going after 60 rounds (21 of
   24000; 2 of the 3000 confirm fights). In all 5 we looked at, the
   Warden was out and the ogre was left, with the Druid alone or with
   the Rogue. Why: only the Warden gives Taunt cards, and Eviscerate on
   the boss needs them; Backstab needs the boss to be attacking someone
   else, and it is attacking her; so the Rogue mostly does nothing. The
   Druid heals faster than the ogre hurts, and heroes move 6 while the
   ogre moves 4, so it cannot catch them. The slow goblins made it worse
   (the Rogue's auto-attack goes to the enemy with the least HP, which
   was a slow goblin far away), but they were not the main cause.
   Numbers now make it rare: Warden HP 100 alone cuts it to 1 in 24000;
   the new goblins alone to 5 in 24000; both together to 1 in 24000. The
   confirm run had none. It can still happen. Ogre move 6 removes it
   (0 in 24000) but makes the boss play differently. Choices: let the
   Rogue hit the boss when nobody can Taunt it, or let the ogre catch
   heroes who run.
   After the third look: 0 of 24000 fights (seeds 40000 to 63999) ran
   out of rounds. Best guess why: the boss now hits much harder, so
   once the Warden is out the others go down too, instead of running
   from it for 40 rounds. The cause is still there, so it could come
   back if the boss gets weaker.
4. **Meteor only hits enemies that stand still.** Its spot is fixed when
   the 2-round cast starts. With goblins at move 5 it was cast 0.1 times
   a fight; with move 1, about 1.1 times; with move 3 (now), 0.0. The
   design wants the goblin wave to be "work for Meteor". Goblins slow
   enough for Meteor (move 1) did no harm; goblins at move 2 still get
   Meteored but left the checks too close to failing (see "Tried and not
   kept"). If goblins should be a threat and Meteor food, the Mage needs
   a way to aim where they will be, or Meteor needs a shorter cast.
   After the third look: Meteor is cast 0.11 times a fight (344 times
   in 3000 fights). That is more than 0.0, but most fights still have
   no Meteor.
5. **Some buttons are almost never pressed in this fight** (per fight,
   first pass's numbers): War Cry 0.0, Kidney Shot 0.0, Cheap Shot 0.0,
   Unbroken 0.0, Sap 0, Frost Ring 0.1, Bulwark 0.3, Wild Growth 0.4.
   After the second look: Meteor 0.0 too, Kidney Shot 0.2, Frost Ring
   0.3.
   After the third look (per fight, the 3000 confirm fights, with the
   count in brackets): Sap 0 (0), Bulwark 0.002 (6), Cheap Shot 0.005
   (14), Unbroken 0.008 (23), Meteor 0.11 (344), Frost Ring 0.15
   (437), Chain Hook 0.15 (451), Kidney Shot 0.28 (842), Wild Growth
   0.33 (1000), War Cry 0.60 (1787).
   Why Chain Hook is rare now: Challenge (2 grit) does its old job of
   turning an add around for half the grit, so the Warden keeps Chain
   Hook for an enemy that hits from far away (the shaman).
   Why Bulwark is rare: every hero moves before anyone acts, so by the
   time the Warden could plant his shield, everyone has already
   stepped out of the Ground Slam.
   Every hero is still needed (without any one hero the party wins 9% or
   less), but "every button feels iconic" is not something the checks
   measure.
6. **Fight length is touchy about the boss's timings.** Changing when
   the Ground Slam comes moved "in band" anywhere from 47% to 75%,
   because the Warden and Rogue lose a whole turn stepping out of it.
   If the slam timing changes later, length needs checking again.

## Rules the simulator had to decide

The design left these open, or said something the simulator could not
do as written. Each was decided while building it. The owner may want
to change any of them.

- Bleeding cards come off at the end of the party turn, after everyone
  has acted, not at the top like other cards.
- Shadowstep keeps the Rogue hidden.
- Enemies cannot pick a hidden hero as their target. Blasts still hit a
  hidden hero standing in the area.
- A new Taunt, stun, sap or sheep never shortens one already there.
- Going down wipes every card the hero holds: heal cards, Quicken,
  cooldowns, all of them.
- Kidney Shot cannot be used on a boss, but Cheap Shot can, to break the
  boss's cast.
- A channel (Arcane Volley) checks its reach again on every hit.
- Vanish while already hidden keeps the Rogue hidden.
- A cast that is cancelled or broken costs nothing.
- Heroes move, and act, one after another in id order (druid, mage,
  rogue, warden), not truly all at once. So a hero who acts before the
  Mage in that order gets one quickened turn fewer than one who acts
  after her: Quicken lands after they have already attacked that turn.
- The Warden starts a fight with 0 grit.
- Bosses ignore the hold: only Taunt cards make a boss attack the Warden
  (owner's decision).

## Final

These are the numbers after the third look, tuned with the fixes from
the final review in place (the kit check, the Warden's new rules,
hidden heroes, the Mage and Rogue fixes, the Warden starting on 0 grit).

Command: `uv run fastcombat check --n 3000 --seed 100000` (seeds never
used while tuning; every tuning run used seeds below 100000). The
simulator gives up after 60 rounds (`max_rounds = 60`).

```
Fights played:          3000
Wins:                   78%
Ran out of rounds:      0%
Rounds:                 median 20, most between 17 and 24
Lasted 18 to 22 rounds: 73%
A hero in danger:       98% (down to 25% HP, or went down)
Auto-attack damage:     31% of all damage

hero        damage  healing  starved  up and full  went down  lowest HP
warden         23%       0%      16%          13%        58%         6%
rogue          39%       0%       3%          11%        54%        10%
druid           0%     100%       0%          29%        26%        27%
mage           38%       0%      13%           0%        40%        17%

PASS  length           73.4% of fights  (wanted: at least 60.0% last 18 to 22 rounds)
PASS  win_rate         78.4%  (wanted: 70.0% to 90.0%)
PASS  no_timeouts      0.0%  (wanted: none)
PASS  danger           97.9% of fights  (wanted: at least 50.0% have a hero at 25.0% HP or down)
PASS  auto_share       30.6% of damage  (wanted: 20.0% to 50.0%)
PASS  resource:warden  starved 16.3% of rounds, ended up and full 13.1% of fights  (wanted: both under 50.0%)
PASS  resource:rogue   starved 3.2% of rounds, ended up and full 11.4% of fights  (wanted: both under 50.0%)
PASS  resource:druid   starved 0.1% of rounds, ended up and full 28.8% of fights  (wanted: both under 50.0%)
PASS  resource:mage    starved 12.7% of rounds, ended up and full 0.0% of fights  (wanted: both under 50.0%)
PASS  needed:warden    wins 78.4% with, 0.0% without  (wanted: at least 20.0% fewer wins without them)
PASS  needed:rogue     wins 78.4% with, 0.8% without  (wanted: at least 20.0% fewer wins without them)
PASS  needed:druid     wins 78.4% with, 0.0% without  (wanted: at least 20.0% fewer wins without them)
PASS  needed:mage      wins 78.4% with, 0.0% without  (wanted: at least 20.0% fewer wins without them)
PASS  kit:warden       wins 78.4% with the kit, 54.2% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
PASS  kit:rogue        wins 78.4% with the kit, 10.3% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
PASS  kit:druid        wins 78.4% with the kit, 0.9% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
PASS  kit:mage         wins 78.4% with the kit, 0.7% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
```

Every check passes with the round cap at 60. The pinned test seeds
(`check --n 600 --seed 500000`) pass too.

Things to keep an eye on:

- The fight is now won or lost on the tank. The Warden goes down in
  58% of fights and gets down to 6% of his HP on average; the Rogue
  goes down in 54%. Wins are still about 4 in 5 because the Druid
  brings them back up. At the table this may feel like a lot of close
  calls.
- A hero is in danger in 98% of fights. The target is "at least 50%",
  so this passes easily, but nearly every fight is a scare.
- The Warden still ends 13% of fights full of grit (it was 76%). Most
  of his spending is Intercede (about 2.5 a fight). See "Needs a
  decision", item 5, for the buttons he almost never presses.
- With goblin damage 0 wins go up to about 90%, the top of the target.
  So the goblins matter, and the fight depends on them being there.
- No fight ran out of rounds, here or in 24000 tuning fights. See
  "Needs a decision", item 3.
- Without any one hero the party almost never wins (1% or less). The
  design asks for "clearly harder", and this is much more than that: a
  party of three cannot beat this fight.
- `kit:rogue` passes with a lot of room (a Rogue on auto: 10% wins),
  and so does every other `kit:` check. The Warden's kit is worth
  about 24 points of wins.

## Not met

Nothing: every check passed on the confirm run, with the round cap at
60. The items under "Needs a decision" are design goals the checks do
not measure.
