# Tuning log

This is where we write down how the numbers were tuned: what we changed,
why, and what the simulator said after. The targets are in the design
(`docs/superpowers/specs/2026-11-24-fast-combat-design.md`, "Numbers").

The Warden was renamed the Guardian on 2026-11-27, and his abilities took back
their original names (Taunt, Challenging Shout, Intercede, Grip, Shield
Plant, Last Stand). Because heroes act in name order, the Guardian now acts
second (Druid, Guardian, Mage, Rogue), not last. That changed the results;
the next tuning pass accounts for it.

On 2026-11-27 Frost Ring was renamed Frost Nova and AoE Taunt was
renamed Challenging Shout.

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
guardian          2%       0%       0%           0%       100%
rogue          37%       0%       1%           0%       100%
druid           0%     100%       0%           0%       100%
mage           60%       0%       2%           0%       100%

FAIL  length           0.9% of fights  (wanted: at least 60.0% last 18 to 22 rounds)
FAIL  win_rate         0.0%  (wanted: 70.0% to 90.0%)
PASS  no_timeouts      0.0%  (wanted: none)
PASS  danger           100.0% of fights  (wanted: at least 50.0% have a hero at 25.0% HP or down)
FAIL  auto_share       3.9% of damage  (wanted: 20.0% to 50.0%)
PASS  resource:guardian  starved 0.2% of rounds, ended up and full 0.0% of fights  (wanted: both under 50.0%)
PASS  resource:rogue   starved 0.6% of rounds, ended up and full 0.0% of fights  (wanted: both under 50.0%)
PASS  resource:druid   starved 0.0% of rounds, ended up and full 0.0% of fights  (wanted: both under 50.0%)
PASS  resource:mage    starved 1.6% of rounds, ended up and full 0.0% of fights  (wanted: both under 50.0%)
FAIL  needed:guardian    wins 0.0% with, 0.0% without  (wanted: at least 20.0% fewer wins without them)
FAIL  needed:rogue     wins 0.0% with, 0.0% without  (wanted: at least 20.0% fewer wins without them)
FAIL  needed:druid     wins 0.0% with, 0.0% without  (wanted: at least 20.0% fewer wins without them)
FAIL  needed:mage      wins 0.0% with, 0.0% without  (wanted: at least 20.0% fewer wins without them)
```

### What was wrong

- The party lost every fight, in about 10 rounds. The Guardian lost 37 of
  60 HP in the first two rounds and was down by round 5.
- Twelve goblins and two shamans were too much on top of the ogre, the
  brute and two wolves.
- The Guardian almost never auto-attacked (about 2 damage a fight). Grit
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

1. Guardian HP 60 to 90. The tank fell first in every fight.
   After: wins 0%, median 12 rounds, in band 2%, auto 3%.
   (On its own this did not win fights yet. But the final numbers with
   Guardian HP 60 win only 67% of fights, with 59% in band: both fail.)
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
   Guardian ended fights full of grit 54% of the time.
6. Taunt cost 1 to 2, Grip cost 2 to 4. Now the Guardian has to
   save up, so it auto-attacks more, and ends with less grit.
   After: wins 64%, median 33, in band 10%, auto 28%, Guardian ends full
   17%.
7. Ogre HP 320 to 130. Fights were 33 rounds; this is the big one for
   length.
   After: wins 80%, median 19.5, in band 65%, danger 90%, auto 26%. Every
   check passes but one: 1 fight in 1000 ran out of rounds.
8. Boss timings: Ground Slam first round 3 to 4, every 4 rounds to every
   6; Skull Crusher first round 5 to 6. When a Ground Slam is announced,
   the Guardian and the Rogue step out of it and lose that turn. With a
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
   Guardian 31.8% / 3.7%, Rogue 1.2% / 5.4%, Druid 0.1% / 19.4%, Mage
   11.1% / 0.0%. Needed (wins without): Guardian 4.1%, Rogue 4.3%, Druid
   0.0%, Mage 0.8%. Every other check passes.
   On more seeds it is clearer: 21 of 24000 fights (seeds 40000 to
   63999) ran out of rounds, about 1 in 1100.
10. Goblins: move 1 to 3, the wave comes in round 10 instead of 6, and
   five goblins instead of six. Now they reach the back line and hurt.
   After: FAIL no_timeouts 0.2%. Length 68.4%, wins 75.2%, danger
   90.3%, auto 22.2%. Resources: Guardian 29.5% / 4.0%, Rogue 1.0% /
   16.3%, Druid 0.0% / 23.3%, Mage 11.1% / 0.0%. Needed: Guardian 3.3%,
   Rogue 6.8%, Druid 0.0%, Mage 0.2%.
11. Guardian HP 90 to 100. Most stalemates start when the Guardian is out
   (see "Needs a decision", item 3), and the goblins now hit harder.
   After: every check passes. Length 74.6%, wins 82.6%, no timeouts,
   danger 85.9%, auto 22.3%. Resources: Guardian 30.3% / 5.0%, Rogue
   1.1% / 16.4%, Druid 0.0% / 25.2%, Mage 10.9% / 0.0%. Needed: Guardian
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
| Guardian went down | 37% | 22% |
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
- Grip cost 6 (tried early, with Taunt 3): too many adds
  reached the back line (6% wins against 22% with cost 4).
- Raising every Guardian cost to 3 or more: the Guardian was "starved" 71%
  of rounds (it counts against the cheapest ability).
- Goblin move 2: wins 73% and auto share right at 20%. Move 3: wins 53%.
- Goblin wave in round 4 or round 8 instead of 6: worse length.
- Boss HP 115, 120, 140, 150. With the final boss timings, 130 gave the
  best length (120: 68% in band; 130: 73%).
- Ground Slam every 3, 5 or 7 rounds, or first in round 1, 2 or 5: all
  worse than first 4, every 6 (worse length, or too many wins).
- Putting back all three add damage cuts (brute 6, wolf 4, shaman 3):
  wins fell to 70%, the very edge. With Guardian HP 100 as well: 75%.
- Moving the brute one square closer so the Rogue can Sap it. See
  "Needs a decision", item 2.

Tried in the second look (300 fights each, seeds 0 to 299, cap 60,
Guardian HP 90 unless it says so):

- Goblin move 2, nothing else changed: auto share 19.4% (fails). With
  five goblins: every check passes at 300 fights. With five goblins and
  Guardian HP 100, Meteor is still cast 1.1 times a fight and wins are 81%
  (87% with goblin damage 0), but at 1000 fights auto share was only
  20.5%, and 8 of 24000 fights ran out of rounds. Six goblins and
  Guardian HP 100: auto 19.3% at 1000 fights (fails), 13 of 24000 ran out
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
  rounds. Five with Guardian HP 100 is what was kept.
- Goblin move 4: with six goblins in round 6, wins 41%. Four goblins in
  round 10 passes (wins 76%). With Guardian HP 100 and the ogre at move 6
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
Guardian's: he used to spend his turns on Taunts that did nothing. Enemies
also stopped picking hidden heroes, the Mage backs off further, and the
Guardian now starts with 0 grit. The first two passes were tuned to the
old, weaker Guardian, so with the fixes the fight became far too easy.

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
guardian         24%       0%      11%          76%         2%        34%
rogue          39%       0%       1%          20%         5%        38%
druid           1%     100%       0%          22%         1%        50%
mage           37%       0%      12%           0%         9%        37%

FAIL  length           58.5% of fights  (wanted: at least 60.0% last 18 to 22 rounds)
FAIL  win_rate         99.9%  (wanted: 70.0% to 90.0%)
PASS  no_timeouts      0.0%  (wanted: none)
FAIL  danger           44.7% of fights  (wanted: at least 50.0% have a hero at 25.0% HP or down)
PASS  auto_share       31.0% of damage  (wanted: 20.0% to 50.0%)
FAIL  resource:guardian  starved 11.4% of rounds, ended up and full 76.0% of fights  (wanted: both under 50.0%)
PASS  resource:rogue   starved 1.2% of rounds, ended up and full 20.1% of fights  (wanted: both under 50.0%)
PASS  resource:druid   starved 0.1% of rounds, ended up and full 21.9% of fights  (wanted: both under 50.0%)
PASS  resource:mage    starved 12.1% of rounds, ended up and full 0.0% of fights  (wanted: both under 50.0%)
PASS  needed:guardian    wins 99.9% with, 3.0% without  (wanted: at least 20.0% fewer wins without them)
PASS  needed:rogue     wins 99.9% with, 46.6% without  (wanted: at least 20.0% fewer wins without them)
PASS  needed:druid     wins 99.9% with, 0.1% without  (wanted: at least 20.0% fewer wins without them)
PASS  needed:mage      wins 99.9% with, 2.8% without  (wanted: at least 20.0% fewer wins without them)
FAIL  kit:guardian       wins 99.9% with the kit, 94.5% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
PASS  kit:rogue        wins 99.9% with the kit, 66.7% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
PASS  kit:druid        wins 99.9% with the kit, 22.5% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
PASS  kit:mage         wins 99.9% with the kit, 51.4% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
```

What was wrong:

- The party almost never lost, and fights were a little short.
- Nobody got into real danger in more than half the fights.
- The Guardian ended 76% of fights with a full pool of grit. Nothing
  near the end of a fight made him spend it.
- `kit:guardian` could not pass: with the Guardian only auto-attacking the
  party still won 94.5%, and no kit can win 10 points more than that.

Kept changes (each line: `check --n 1000`, seeds 0 to 999, every check
listed; the numbers carry on from change 11):

12. Ogre melee hit 2d6+2 to 2d6+7 (the `bonus`, 2 to 7). The boss is the
   one who should make the fight hard, and it hits the Guardian every
   round. A hurt Guardian takes more of the Druid's healing, so the others
   get low too, and the Guardian spends grit on Intercede to save them.
   After: every check passes. Length 63.6%, wins 87.1%, no timeouts,
   danger 95.3%, auto 30.1%. Resources (starved / ended full): Guardian
   12.4% / 33.2%, Rogue 3.4% / 20.9%, Druid 0.1% / 29.6%, Mage 12.3% /
   0.0%. Needed (wins without): Guardian 0.1%, Rogue 2.6%, Druid 0.0%,
   Mage 0.0%. Kit (wins on auto): Guardian 65.3%, Rogue 13.9%, Druid
   4.9%, Mage 1.5%.
13. Ogre HP 130 to 150. Wins and length were both close to the edge.
   More boss HP makes the fight longer and a little harder.
   After: every check passes. Length 74.9%, wins 82.9%, no timeouts,
   danger 97.8%, auto 29.8%. Resources: Guardian 12.3% / 27.3%, Rogue
   4.1% / 10.4%, Druid 0.1% / 30.2%, Mage 12.7% / 0.0%. Needed: Guardian
   0.1%, Rogue 0.9%, Druid 0.0%, Mage 0.0%. Kit: Guardian 57.2%, Rogue
   11.4%, Druid 1.1%, Mage 0.9%.
14. Intercede cost 2 to 4. It is the Guardian's most used button (about
   2.5 times a fight), so its cost decides how much grit he keeps. At 4
   he spends his grit faster and ends full about half as often. Wins
   did not drop.
   After: every check passes. Length 75.1%, wins 83.9%, no timeouts,
   danger 97.7%, auto 30.4%. Resources: Guardian 16.5% / 15.2%, Rogue
   3.4% / 10.7%, Druid 0.1% / 30.9%, Mage 12.6% / 0.0%. Needed: Guardian
   0.1%, Rogue 0.8%, Druid 0.0%, Mage 0.0%. Kit: Guardian 57.2%, Rogue
   12.2%, Druid 1.1%, Mage 0.7%.
15. Goblin damage 2 to 3. With the boss hitting harder, the goblins had
   become a small part of the fight (goblin damage 0 moved wins only
   from 83% to 89%). At 3 they matter again, and wins come down to
   about 4 in 5.
   After: every check passes. Length 76.0%, wins 79.6%, no timeouts,
   danger 98.8%, auto 30.5%. Resources: Guardian 16.7% / 14.0%, Rogue
   3.4% / 10.4%, Druid 0.0% / 31.3%, Mage 12.9% / 0.0%. Needed: Guardian
   0.0%, Rogue 0.5%, Druid 0.0%, Mage 0.0%. Kit: Guardian 53.2%, Rogue
   10.6%, Druid 1.0%, Mage 0.6%.

On more seeds: 0 of 24000 fights (seeds 40000 to 63999) ran out of
rounds, and the party won 78% of them.

**The goblins after the third look.** Setting their damage to 0 still changes
the fight a lot (`check --n 1000`, seeds 0 to 999):

| | goblins hit for 3 | goblins hit for 0 |
|---|---|---|
| wins | 79.6% | 89.6% (right at the top edge) |
| a hero in danger | 98.8% | 95.7% |
| Guardian went down | 58% | 44% |
| Rogue went down | 54% | 46% |
| Druid went down | 24% | 14% |
| Mage went down | 38% | 25% |

Tried in the third look, and not kept (300 to 1000 fights each, seeds
below 100000):

- Each of these alone left wins at 97% or more: Guardian HP 80; ogre HP
  150; adds back to brute 6, wolf 4, shaman 3; goblin damage 4; Rogue
  and Druid HP 30 with Mage HP 24.
- Ogre melee 3d6+3: wins 91%. 2d6+5: wins 95%.
- Ogre melee 2d6+8 (with HP 145 or 150): wins 74% to 75%, and the
  Guardian went down in two fights of three.
- Ogre melee 2d6+6 with goblin damage 3: wins 86%, too close to 90%.
  With a sixth goblin as well, wins were 80% and it looked fine (the
  `needed:` checks were not run), but it is one more change than what
  was kept, for the same result.
- Taunt cost 2 to 3, or Challenging Shout cost 3 to 5, instead of Intercede:
  the Guardian ended full less often (27% of fights) but not as much as
  with Intercede at 4 (18%). Intercede 3: 24%.
- Intercede 3, Taunt 3 and Challenging Shout 4 together: the Guardian was
  starved 23% of rounds, with no gain over Intercede alone.

### Fourth look: a boss that must be taunted, 2026-11-26

The owner wants the Guardian to need to taunt the boss, like a tank in an
MMO. So bosses now ignore the hold: standing next to the Guardian does not
keep a boss on him, only Taunt cards do. And the Guardian Taunts the
boss whenever it has no Taunt cards.

That alone made taunting the boss worse than useless. The ogre went for
the nearest hero, and the Guardian stands next to it, so an untaunted ogre
hit him anyway. The taunt only cost him grit and turns. A new check,
`taunt:boss`, plays the same fights with the Guardian never Taunting
the boss (Challenging Shout can still taunt it), and wants at least 10 points fewer
wins.

Where we started (`check --n 1000`, seeds 0 to 999, the numbers after
the third look, with bosses ignoring the hold):

```
Fights played:          1000
Wins:                   43%
Ran out of rounds:      0%
Rounds:                 median 20, most between 16 and 24
Lasted 18 to 22 rounds: 59%
A hero in danger:       100% (down to 25% HP, or went down)
Auto-attack damage:     28% of all damage

hero        damage  healing  starved  up and full  went down  lowest HP
guardian         19%       0%      26%           2%        92%         1%
rogue          41%       0%       1%          12%        76%        12%
druid           0%     100%       0%          19%        62%        12%
mage           40%       0%      12%           0%        73%         6%

FAIL  length           58.7% of fights  (wanted: at least 60.0% last 18 to 22 rounds)
FAIL  win_rate         42.8%  (wanted: 70.0% to 90.0%)
PASS  no_timeouts      0.0%  (wanted: none)
PASS  danger           99.9% of fights  (wanted: at least 50.0% have a hero at 25.0% HP or down)
PASS  auto_share       27.9% of damage  (wanted: 20.0% to 50.0%)
PASS  resource:guardian  starved 26.3% of rounds, ended up and full 1.8% of fights  (wanted: both under 50.0%)
PASS  resource:rogue   starved 1.1% of rounds, ended up and full 11.7% of fights  (wanted: both under 50.0%)
PASS  resource:druid   starved 0.0% of rounds, ended up and full 18.8% of fights  (wanted: both under 50.0%)
PASS  resource:mage    starved 12.4% of rounds, ended up and full 0.0% of fights  (wanted: both under 50.0%)
PASS  needed:guardian    wins 42.8% with, 0.0% without  (wanted: at least 20.0% fewer wins without them)
PASS  needed:rogue     wins 42.8% with, 0.2% without  (wanted: at least 20.0% fewer wins without them)
PASS  needed:druid     wins 42.8% with, 0.0% without  (wanted: at least 20.0% fewer wins without them)
PASS  needed:mage      wins 42.8% with, 0.0% without  (wanted: at least 20.0% fewer wins without them)
FAIL  kit:guardian       wins 42.8% with the kit, 43.6% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
PASS  kit:rogue        wins 42.8% with the kit, 7.9% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
PASS  kit:druid        wins 42.8% with the kit, 0.3% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
PASS  kit:mage         wins 42.8% with the kit, 0.6% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
FAIL  taunt:boss       wins 42.8% with, 68.7% when the Guardian never Taunts the boss  (wanted: at least 10.0% fewer wins without Taunting the boss)
```

What was wrong:

- Taunting the boss cost wins: 69% without it, 43% with it. The Guardian's
  kit as a whole was worth nothing (`kit:guardian`: 44% on auto).
- The party won less than half its fights. With the boss free to move,
  the Guardian spent his grit on Taunt (about 5 a fight) and had little
  left for Intercede.

Kept changes (each line: `check --n 1000`, seeds 0 to 999, every check
listed, `taunt:boss` too; the numbers carry on from change 15):

16. Ogre `prefers` "nearest" to "backline". The controller's ruling: a
   boss with no Taunt cards should go for the soft heroes, as in an MMO.
   Now the taunt is what keeps it off the Mage and the Druid.
   After: FAIL length 53.3%, FAIL wins 43.7%. No timeouts, danger 99.5%,
   auto 24.2%. Resources (starved / ended full): Guardian 44.9% / 2.2%,
   Rogue 1.2% / 15.5%, Druid 0.0% / 17.2%, Mage 11.5% / 0.0%. Needed
   (wins without): Guardian 0.2%, Rogue 0.0%, Druid 0.0%, Mage 0.0%. Kit
   (wins on auto): Guardian 20.1%, Rogue 6.4%, Druid 0.9%, Mage 0.6%.
   Taunt:boss (wins without Taunting the boss): 10.9%. So the taunt now
   matters a lot, but the fight is far too hard.
17. Ogre melee hit 2d6+7 to 2d6+4 (the `bonus`, 7 to 4). The +7 was
   tuned for a boss that only ever hit the Guardian (change 12). Now every
   lapse in the taunt sends it at a hero with 28 to 36 HP, and a 2d6+7
   hit is a third of that or more.
   After: every check passes. Length 65.6%, wins 73.6%, no timeouts,
   danger 94.8%, auto 25.8%. Resources: Guardian 39.4% / 8.4%, Rogue 0.6%
   / 17.6%, Druid 0.1% / 24.0%, Mage 10.6% / 0.0%. Needed: Guardian 1.0%,
   Rogue 0.5%, Druid 0.0%, Mage 0.1%. Kit: Guardian 44.5%, Rogue 22.4%,
   Druid 2.5%, Mage 3.5%. Taunt:boss: 34.8%.
18. Guardian HP 100 to 110. Wins were close to the bottom edge, and the
   Guardian still went down in about half the fights. More Guardian HP keeps
   the taunt going longer.
   After: every check passes. Length 69.2%, wins 80.4%, no timeouts,
   danger 91.3%, auto 26.2%. Resources: Guardian 37.2% / 10.9%, Rogue
   0.6% / 17.2%, Druid 0.1% / 27.2%, Mage 10.3% / 0.0%. Needed: Guardian
   1.0%, Rogue 1.3%, Druid 0.0%, Mage 0.2%. Kit: Guardian 45.5%, Rogue
   26.9%, Druid 4.0%, Mage 6.6%. Taunt:boss: 36.7%.

On more seeds: 0 of 24000 fights (seeds 40000 to 63999) ran out of
rounds, and the party won 79% of them.

`boss_loud_cards` stays at 1: taunting the boss is already worth about
40 points of wins, so a Loud hit taking two cards off a boss was not
needed.

**The goblins after the fourth look.** Setting their damage to 0 still
changes the fight a lot (`check --n 3000 --seed 100000`, the confirm
seeds):

| | goblins hit for 3 | goblins hit for 0 |
|---|---|---|
| wins | 77.9% | 92.9% (fails: too easy) |
| a hero in danger | 92.4% | 84.6% |
| Guardian went down | 50% | 30% |
| Rogue went down | 23% | 9% |
| Druid went down | 27% | 11% |
| Mage went down | 56% | 41% |

Tried in the fourth look, and not kept (300 fights, seeds 0 to 299,
with the ogre on "backline", unless it says so):

- Taunt cost 2 to 1: wins fell to 43% and auto share to 18%
  (fails). With cheap taunts the Guardian spends more turns on abilities
  and fewer on auto-attacks.
- Each of these alone, with the ogre at +7: Guardian HP 120 (wins 56%),
  ogre HP 130 (wins 57%, length 53%), Intercede cost 3 (wins 43%),
  goblin damage 2 (wins 55%).
- Ogre +6: wins 52%. With Guardian HP 120: 65%. With Guardian HP 130:
  passes (74% at 500 fights), but more HP on the tank for the same
  result as a smaller hit.
- Ogre +5: wins 63%. With ogre HP 140: 67%. With Guardian HP 110: 70%,
  the very edge. With Guardian HP 115 or 120: passes (73% and 76% at 1000
  fights, seeds 2000 to 2999), but lower wins than +4 with HP 110.
- Ogre +3: wins 85%, and one fight ran out of rounds.
- Ogre +4 with ogre HP 160: wins 71%, length 63%. With Guardian HP 105 or
  115: wins 77% and 81% (1000 fights, seeds 2000 to 2999); 110 is in the
  middle.

## D3b: the Rogue's opening, a long Sap and a longer Polymorph, 2026-11-27

The owner asked for three things: a Sap that puts an enemy out of most of
the fight (try 10, 15 or 20 cards), an opening before round 1 (sneak with
a stealth check, or Shadowstep in for less energy), and a Polymorph longer
than 4. Every run here is `--n 500 --seed 100000` unless it says 2000
(seeds 100000 to 101999), and plays the full party, which is the first
part of `check`.

### What woke a Sap before this step

Almost nothing. With the D3 rules nobody aims at a stunned, sapped or
sheeped enemy, the Mage never puts a Meteor over one, Frost Nova only
roots (no damage), and enemy blasts hit only heroes, so no enemy can wake
one. In 500 fights with Sap at 4 cards, one Sap of about 575 was woken: an
Arcane Volley already under way on the enemy the Rogue then sapped. The
real trouble with a long Sap was the other way round: nobody ever hit a
sapped enemy, so once it was the last one left the party stood and
waited. With the old rules and Sap at 20, only 17% of fights lasted 18 to
22 rounds and 1.6% ran out of rounds.

So this step changed how heroes play (`policies.py`):

- Nobody hits a sapped or sheeped enemy while anything else is left. Once
  every enemy left is controlled, they hit a stunned one first, then a
  sapped or sheeped one, instead of waiting for its cards to run out.
- The Rogue does not Sap, and the Mage does not sheep, an enemy a
  Firebolt or a Volley is aimed at or a Meteor is coming down on (it
  would wake at once). The Mage ends a Volley whose enemy was sapped
  after it began, unless nothing else is left to hit (then she keeps
  channelling).
- Meteor still never covers a sapped or sheeped enemy. I looked for an
  exception ("unless the fight is nearly won, or it is the only way to hit
  three or more"): in 500 fights a sleeper stopped a Meteor 9 times, and
  in 8 of them every enemy it would have hit was a goblin, which any hit
  kills anyway. Not worth a rule.

After: in 2000 fights at the picked numbers (Sap 20, Polymorph 12) every
Sap or sheep woken by a hit was woken on purpose, when nothing else was
left. (With Polymorph at 20 there was one exception in 2000 fights: a
Firebolt started at a sheep when nothing else was left, which landed
after the goblins had come in.)

### The Sap length (Shadowstep in, Polymorph at 4)

| Sap cards | wins | median rounds | 18 to 22 rounds | rounds sapped a fight | still sapped at the end | Saps woken |
|---|---|---|---|---|---|---|
| 4 (old) | 63.8% | 23 | 43.2% | 4.7 | 4.6% | 0% |
| 10 | 68.8% | 23 | 38.4% | 12.0 | 13.4% | 6% |
| 15 | 74.6% | 23 | 42.4% | 16.4 | 16.4% | 10% |
| 20 | 75.8% | 23 | 44.4% | 19.4 | 14.6% | 33% |

"Rounds sapped" is GM turns that enemies lost to Sap cards, all of them
together, per fight. A win needs every enemy dead, so "still sapped at the
end" only happens in fights the party lost. "Saps woken" is the share of
Saps that a hit ended; every one of them was hit because nothing else was
left, so the rest ran their cards out or outlasted the fight. With 2000
fights: 15 cards 74.8% wins, 44.8% in 18 to 22; 20 cards 77.2%, 46.9%.

**Picked: 20 cards.** It wins the most, has the best length, and keeps
the sapped elite out for 19 rounds a fight on the mean: the whole fight,
as the owner wanted. A third of the time the Sap is still on when every
other enemy is dead, and then the party wakes it and kills it. The owner
accepts 20 cards until it has been tried at the table (2026-11-27).

### The Polymorph length (Sap at 20, 2000 fights)

| Polymorph cards | wins | median rounds | 18 to 22 rounds | rounds a sheep a fight | still a sheep at the end |
|---|---|---|---|---|---|
| 4 (old) | 77.2% | 22 | 46.9% | 3.7 | 0.0% |
| 8 | 73.8% | 22 | 47.4% | 7.4 | 0.0% |
| 12 | 81.7% | 22 | 59.5% | 11.1 | 0.05% |
| 20 | 87.5% | 22 | 49.9% | 14.4 | 2.75% |

With 500 fights: 4: 75.8% and 44.4%; 8: 71.8% and 47.8%; 12: 81.8% and
58.6%; 20: 87.4% and 48.8%.

**Picked: 12 cards.** By far the best length (59.5% of fights in 18 to 22
rounds, the closest any setting has come to the 60% target in this round
of work), with wins well inside 70% to 90%. 20 cards wins more but pushes
wins near the top of the band and makes fights less even in length. It
also leaves Sap as the longer of the two, which is how it is in the game
the kit comes from.

Why 8 is worse than 4 (measured in the review of this step): the Mage
sheeps a wolf in round 4 or 5. At 8 cards it wakes in round 12, in the
middle of the goblin wave (which comes in round 10), and runs at the back
line with the goblins. At 4 cards it wakes in round 8, alone, and dies
first; at 12 it wakes in round 16, after the wave is dealt with. So the
Polymorph pick is tied to this fight's goblin timing: if the wave moves,
check the Polymorph length again.

### The opening

The rule is in the engine (`opening.py`): before round 1 each Rogue picks
one enemy that is there from the start and is not a boss, and Sneaks
(d6, 4 or more, `rules.sneak_die` and `rules.sneak_target`) or Shadowsteps
in, or neither. The Rogue's policy picks the elite that hits hardest
(the brute) and then Saps it in round 1.

Three ways to choose, measured at the picked numbers (Sap 20, Polymorph
12):

| rule | wins | median rounds | 18 to 22 rounds | Sap uses a fight | stealth checks that worked |
|---|---|---|---|---|---|
| always Sneak | 82.8% | 22 | 54.8% | 0.61 | 50.2% |
| always Shadowstep in | 81.8% | 22 | 58.6% | 1.11 | (none made) |
| judgement (kept) | 81.8% | 22 | 58.6% | 1.11 | (none made) |
| for comparison: no opening | 86.4% | 22 | 63.4% | 1.08 | (none made) |

And at the old numbers (Sap 4, Polymorph 4): always Sneak 72.8% wins,
48.4% in 18 to 22, 0.66 Saps; always Shadowstep in 63.8%, 43.2%, 1.21
Saps; no opening 75.2%, 41.4%, 1.15 Saps.

The judgement rule: Shadowstep in, if after paying for it and getting
round 1's energy back she can still pay for the Sap; else Sneak. With
today's numbers it is the same as always Shadowstepping in, so the two
rows are the same fights.

**Kept: the judgement rule (so, today, always Shadowstep in).** Always
Sneak won 82.8% against 81.8%; at 500 fights that one point is noise. It
comes through the half of the fights where the stealth check fails and
there is no round-1 Sap: always Sneak Saps 0.61 times a fight, under the
owner's `use:sap` band (0.7 to 2). Shadowstep in was kept for that band,
so the owner can see this is a call about the band, not about wins. The
cost of the round-1 Sap is the Guardian grit problem below, which is for
the retune, not for the opening.

**The choice is not a real choice yet.** Shadowstep in always works and
costs nothing in the end: the Rogue starts with 10 energy, pays 2, and
gets 3 back at the top of round 1, so she has her full 10 on her first
turn. Sneak can only lose. Any of these would make it a real choice (the
owner's call, not changed here): a Shadowstep cost over 3 (her energy back
per round), so that some energy is really lost; a pre-fight Shadowstep
that also skips round 1's energy; or an easier stealth check (d6 on 2 or
more is 5 in 6), so that a Sneak is a fair gamble against a real cost.

### The Sap opener and the Guardian

The D3 step found that a Sap in round 1 costs wins, because the Guardian
only gets grit when he is hit, and the brute is what hits him early. A
long Sap makes this stronger, and the Guardian's checks now fail:

| Sap / Polymorph | wins | the Guardian on auto | the Guardian never Taunts the boss |
|---|---|---|---|
| before D3b (no opening, 4 / 4) | 75.2% | 37.0% | 54.2% |
| 4 / 4 | 64% | 34% | 56% |
| 10 / 12 | 71% | 65% | 63% |
| 15 / 12 | 79% | 74% | 71% |
| 20 / 12 (picked) | 82% | 79% | 76% |

With the brute out of the fight the Guardian has little to do: he is
starved 61% of rounds, Taunts the boss 3.2 times a fight (5.6 with no
opening), and a Guardian who only auto-attacks wins nearly as often.
`kit:guardian`, `taunt:boss` and `length` fail (see "Not met").

**Correction (review of D3b).** These notes first blamed the long Sap
("it takes the brute out all fight"). The review measured that the
round-1 opening Sap is the bigger cause: the brute is asleep before it
ever hits the Guardian, so he has almost no grit early. At the top of
round 2 he has 0.39 grit on the mean with the opening, against 1.45
without it. With Sap 20 and Polymorph 12 and no opening, all three checks
pass: wins 86.4%, length 63.4%, the Guardian on auto 75.2% (a drop of 11.2
points), never Taunting the boss 69.2% (a drop of 17.2). So the long Sap
alone is fine; it is the Sap before the brute's first swing that starves
him. This is the retune's (D4) to fix, with grit (the tuner may change
grit regen or grit per attack) or with the elite. Not tuned around here.

## D3c: Shield Slam, Ice Block, Evocation, Quicken benched, a wider Cleanse, the Stomp, 2026-11-27

The owner's kit decisions of 2026-11-27 (see the design, "The classes").
No old number was changed; the new ones are start values for the retune.
Every run here is `--n 500 --seed 100000`, the full party.

### Start values

| What | Numbers (in `game/`) |
|---|---|
| Shield Slam (Guardian) | cost 0 grit, range 1, 2d8, gives 1 grit (`alt`, never past his pool), cooldown 2, not Loud |
| Ice Block (Mage) | cost 0, 1 card, cooldown 8 |
| Evocation (Mage) | cost 0, a channel of 2 rounds (`hits = 2`), 6 mana a round (`value`), `still = true`, cooldown 8 |
| Quicken | `benched = true` (in `game/` only) |
| Stomp (the ogre) | `kind = "stomp"`, rounds 8, 14, 20 (`first = 8`, `every = 6`), radius 1, 1d6, 1 stun card |
| Usage targets | Shield Slam 2 to 3 (owner's); Ice Block 0.2 to 1.5 and Evocation 0.3 to 2 (proposed, owner to confirm); Quicken commented out |

**Where the Stomp sits.** Rounds 8, 14 and 20 in a 20-round fight: three
times, and never on a round with the Ground Slam (4, 10, 16, 22) or the
Skull Crusher (6, 11, 16, 21). It is last in the script, so the first
clash (round 26, with the Crusher) goes to the Crusher. 9/15/21 would
meet the Crusher in round 21. Other timings measured below.

**A design rule (owner, 2026-11-27):** no class has more than 1.5 times as
many buttons as another. The Mage has 8 (Arcane Volley, Firebolt, Meteor,
Frost Nova, Blink, Polymorph, Ice Block, Evocation), the others 7. Disrupt,
which everyone has, is not counted; a benched ability is not a button.

### What came out (`check --n 500 --seed 100000`)

| | D3b | D3c |
|---|---|---|
| wins | 81.8% | 69.4% |
| 18 to 22 rounds | 58.6% | 39.8% |
| median rounds | 22 | 23 |
| the Guardian on auto (`kit:guardian`) | 79.2% (drop 2.6) | 67.4% (drop 2.0) |
| never Taunting the boss (`taunt:boss`) | 75.8% (drop 6.0) | 59.6% (drop 9.8) |
| the Guardian starved | 61.4% | 60.6% |
| the Mage went down | 74% of fights | 83% |

Uses per fight of the new buttons: Shield Slam 0.48, Ice Block 0.00 (1 in
500 fights), Evocation 0.46, Cleanse 1.23 (0.59 on poison, 0.64 on a
stunned Guardian). The Stomp is announced 2.34 times a fight and lands
2.05 times; it stuns the Guardian 0.85 times a fight, the Mage 0.04, the
Rogue and the Druid almost never.

**The Stomp is what costs the wins, and not by its hit or its stun.**

| Stomp | wins | 18 to 22 rounds |
|---|---|---|
| none | 80.6% | 52.6% |
| as built (8/14/20, 1d6, 1 stun) | 69.4% | 39.8% |
| no damage and no stun, same squares | 72.8% | 38.0% |
| radius 0 (no squares around him) | 79.2% | 52.6% |
| 9/15/21 | 71.4% | 46.0% |
| 13/19 | 71.2% | 43.4% |
| 7/14/21 | 67.8% | 34.2% |

A Stomp that does nothing at all costs almost as much as the real one:
the cost is the melee heroes stepping out of the squares next to the boss
for a turn, and the Disrupts spent on it. It is the Ground Slam's old
problem ("Needs a decision", item 6) again. Not tuned around here: the
retune (D4) has to take it in, or the owner changes the Stomp.

The Stomp with no change to how heroes play cost the same, and stunned
nobody (0.05 stuns a fight): everyone stepped out, and the Mage Disrupted
the rest. So the Guardian now stays to take it when a Druid is up to
Cleanse him, and nobody spends an interrupt on a Stomp only he is taking.
That is what gives Cleanse its stuns.

**Shield Slam is pressed far less than the owner's 2 to 3, not more.** The
Guardian is rarely free: the boss has fewer than 2 Taunt cards, an add is
loose, or an ally is hurt. How much the rule's lines matter:

| Shield Slam when | uses a fight | wins |
|---|---|---|
| boss 2+ Taunt cards, every ally above 75%, no add loose (kept) | 0.48 | 69.4% |
| ... allies above 60% | 0.74 | 69.4% |
| ... any ally HP | 1.19 | 69.8% |
| boss 1+ Taunt card, allies above 75% | 0.69 | 69.0% |
| boss 1+ Taunt card, any ally HP | 1.56 | 69.2% |

Even with no HP line at all it stays under 2: "no add loose" and "the
boss held" are what keep him busy. That is a fight finding (the Guardian
is busy in this fight), not a policy to loosen. It also does little for
his grit: with Shield Slam benched the Guardian on auto drops wins by 1.4
points (2.0 with it) and never Taunting the boss by 9.8 (the same), and
he is still starved 61% of rounds. It does not mend the D3b grit problem
by itself; the retune has to.

**Ice Block almost never happens** (1 in 500 fights). Its trigger is the
owner's: a hit or a blast that would down her and that she cannot get
out of. The heavy hits on her (0.6 a fight) she Disrupts from 10 squares,
and she is almost never stunned. What downs her is the ogre's plain
melee hit when it walks to the back line untaunted (1.37 times a fight),
which is not announced. A wider rule (Ice Block at 35% HP or less with an
enemy next to her) gives 1.44 uses a fight but 66.2% wins (3 points
fewer). Left as the owner said; see "Needs a decision".

**Disrupt on a blast nobody stands in.** Found while measuring the
Stomp: the Mage also Disrupts Ground Slams after everyone has stepped
out. Counting a blast with nobody in it as answered (as the Stomp now is)
gives 71.4% wins and 51.0% in 18 to 22 rounds (83.0% and 63.4% with no
Stomp). Not changed here (it changes an old button's play); for the
retune or the owner.

## D4: the retune for the full kit, 2026-11-27

The kit is complete (D3c), so this step tunes `game/` to the checks. It
had two parts: five fixes to how the heroes play (the only policy changes
allowed), then numbers. Tuning runs used seeds below 100000 (`--seed 0`,
1000 or 2000 fights, full party unless it says so); the confirm run is at
the end, under "Final".

### The five play fixes (`policies.py`)

Each fix was measured by taking it back out of the five, one at a time
(1000 fights, seeds 0 to 999). With all five: wins 77.0%, 56.6% of fights
in 18 to 22 rounds. With none (D3c's play): 69.0% and 36.3%.

| Fix | Without it | What it moved |
|---|---|---|
| 1. The Stomp: whoever can Disrupt it does (the Guardian next to the boss first), and the Guardian and the Rogue stay next to the boss when someone will; they step out only when nobody will | wins 68.7%, length 48.8%, Disrupt 2.27 a fight | +8 points of wins, +8 of length. Disrupt 3.69 a fight. Cleanse drops from 1.63 to 0.68 (fewer stunned Guardians) |
| 2. The Guardian walks next to the boss to take a Stomp, not only when he is already in it | 76.5%, 55.6% | about 1 point each: noise at 1000 fights, but it is the right play (on half the Stomp turns he used to stop outside and not hit the boss) |
| 3. Shield Slam needs 1 Taunt card on the boss, not 2 (a boss loses its card at the end of the GM turn, after it attacks, so 1 card means it still attacks him in the coming GM turn) | Shield Slam 0.62 a fight | Shield Slam 0.83 a fight. Wins the same |
| 4. Ice Block: low (35%), the boss or an elite next to her and on her, and no Blink out (or she would Frost Nova first); the dead "rooted" line is gone | Ice Block 0.00 | Ice Block 0.31 a fight. Wins the same (it does not take Blink's place) |
| 5. Nobody Disrupts a blast or a Stomp with nobody in it | 75.0%, 51.3%, Disrupt 4.84 | +2 points of wins, +5 of length |

The D3c rule "a Stomp only the Guardian is in, with a Druid up, is
answered" is gone with fix 1: a hero who can Disrupt it now does.

After the fixes the checks that still failed were `length`,
`resource:guardian` (starved 61%), `kit:guardian` and 11 use bands.

### The Guardian's grit was the root problem

Probed round by round (500 fights, the fixed play, the D3c numbers): the
Guardian had under 2 grit (Taunt's cost) in 90% or more of rounds 1 to 5,
and the boss had Taunt cards after only 3% to 27% of party turns in rounds
2 to 8. The opening Sap takes the brute out before it hits him, the boss
goes for the back line, and the wolves run past him: nothing hits him, so
he gets no grit, so he cannot Taunt, so nothing hits him. Grit per attack
alone does not break this (2 grit: starved 41%; 3 grit: 37%), nor does a
cheaper Taunt (cost 1 with 2 grit per attack: starved 24%, it counts round
1 too). Only grit at the start breaks it: with 2 grit at the start the boss
is held from round 1 and the party won 98% of fights. So the start grit
went up, and then the fight had to be made harder again.

### Kept changes

Each row: the change, why, and what taking just that one change back out
of the final numbers does (2000 fights, seeds 0 to 1999, full party). The
final numbers there: wins 81.5%, 69.5% in 18 to 22 rounds, auto-attacks
21% of damage, the Guardian starved 3% of rounds, every check of the full
party passing except Shield Slam (0.65).

| Change | Old → new | Why | With the old number instead |
|---|---|---|---|
| Guardian start grit (`heroes.guardian.start`) | 0 → 4 | breaks the no-grit spiral (above): two Taunts' worth. **Owner to decide** | wins 52.0%, length 54.9%, Guardian starved 42%; Grip 0.05, Arcane Volley 3.32 fail. With 2: everything passes, but the Guardian is starved 18% of rounds (the line is 20%) |
| Grit per attack (`rules.grit_per_attack`) | 1 → 2 | with the boss held he is hit every round; at 1 grit he still cannot pay for his emergency buttons | Guardian starved 36%; Challenging Shout 0.32, Last Stand 0.18, Kidney Shot 0.40 fail; wins 87.1% |
| Ogre melee bonus | 4 → 9 (2d6+9) | a held boss only hits the Guardian, and +4 was tuned for a boss that ran to the back line (fourth look) | wins 97.2% and auto share 20% (both fail), the Guardian ends up and full too often; Intercede 0.86, Kidney Shot 0.29, Vanish 0.08, Frost Nova 0.13, Blink 0.04, Ice Block 0.03 |
| Ogre HP | 150 → 115 | with +9 the fight ran long and was lost too often | wins 38.9%, length 51.2%, auto share 20% (fails), Rejuvenation 3.83 |
| Grip cost | 4 → 2 | Grip was 0.02 to 0.25 a fight: the Guardian kept his grit for Intercede and Taunt | Guardian starved 12%, Kidney Shot just under 0.5. (Before the other Rogue changes, Grip was 0.25 a fight at cost 4 and 1.01 at 2) |
| Intercede cost | 4 → 2 | Intercede was 0.57 to 0.86 a fight | Guardian starved 7%; Kidney Shot 0.48. With Grip at 4 too, Intercede falls to 0.90 to 0.92 |
| Challenging Shout radius | 3 → 5 | Shout was 0.31 to 0.5: two loose adds within 3 squares of the tank are rare | Challenging Shout 0.48 |
| Combo points at most (`rules.combo_max`) | 5 → 3 | Eviscerate 1.28 to 1.5 and Kidney Shot 0.21 to 0.4: full combo points came too seldom | Eviscerate 1.44, Kidney Shot 0.32, Intercede 0.88, Ice Block 0.16 |
| Backstab cost | 4 → 7 | auto-attacks were 12% to 18% of all damage: with the boss held, the Guardian auto-attacks much less, so the Rogue has to | auto share 16%, wins 89.8%, the Guardian ends up and full too often; Kidney Shot 0.49, Vanish 0.16, Ice Block 0.16 |
| Cheap Shot cost | 3 → 2 | with Shadowstep at 5 and Backstab at 7, the Rogue's cheapest button was 3, and she was starved 21% to 26% of rounds | Rogue starved 21% |
| Arcane Volley dice | 2d6 → 2d4 | at 2d6 the Mage's spells were more than half of all damage and auto share fell under 20%; at a higher cost instead, Volley fell under 4 a fight | auto share 19%, wins 88.8%, the Guardian ends up and full too often; Eviscerate 1.96, Kidney Shot 0.42, Vanish 0.16, Ice Block 0.15 |
| Blink range | 6 → 5 | the ogre reaches 5 squares (move 4, reach 1), so Blink 6 nearly always got her out and Ice Block almost never fired | Ice Block 0.19 |
| Wolf HP | 16 → 20 | wolves died before they hurt anyone; this puts Intercede and the wins in band | wins 89.6%, the Guardian ends up and full too often; Kidney Shot 0.41, Vanish 0.16, Ice Block 0.14 |
| Brute shield (`shielded`) | 5 → 3 | a stalemate, about 1 fight in 3000: the Guardian and the Mage out, the brute (sapped early, awake late) left alone on the Rogue and the Druid. Their d6 auto-attacks mostly bounced off it, and the Rogue spent each full combo on Kidney Shot | 1 or 2 fights in 6000 to 9000 ran out of rounds (0 in 24000 at 3) |
| Shadowstep cost | 2 → 5 | **the owner's number** (2026-11-27), not tuned | see "The opening" below |

Tried and put back (each one made no difference at the final numbers, so
the old number stays): Guardian grit pool 15 (he ends up and full in
about 35% of fights against about 43% at 10, both under the 50% line), goblin damage 2, Evocation 4 mana, Meteor cost 14. Tried and not
kept: Backstab cost 6 or 8 (6: auto share 19%; 8: the Rogue starved),
Arcane Volley cost 3 (Volley 3.55 a fight), Meteor 6d6 or 7d6 (wins fell to
57% and 64%: Meteor kills the adds), a boulder of 1d6 (fights ran out of
rounds) or every 3 or 4 rounds (length under 60%), 1 grit a round
(`regen`) instead of start grit (starved 27% to 28%, and it is a design
change too), Guardian HP 120 or 130 (wins 87% to 95%, and still a
stalemate), Mage HP 24 or 26 (fewer wins, shorter band), ogre move 5
(wins 74%, and still a stalemate).

### The opening, with Shadowstep at 5

The owner set Shadowstep's cost to 5. The judgement rule (Shadowstep in if
she can still pay for the Sap after round 1's energy comes back: 10 - 5 + 3
= 8, and Sap costs 3) still always picks Shadowstep in: it would only pick
Sneak at a cost over 10, which she could not pay anyway. So the choice is
still not a real choice in this fight, but now for a different reason: the
Sap is worth too much to gamble. 2000 fights, seeds 0 to 1999, final
numbers:

| Opening | wins | 18 to 22 rounds | Sap a fight | Shadowstep | Vanish | Rogue starved |
|---|---|---|---|---|---|---|
| Shadowstep in (judgement, kept) | 81.5% | 69.5% | 1.05 | 1.05 | 0.24 | 12% |
| always Sneak (works 49%) | 53.8% | 59.5% | 0.53 | 1.41 | 0.58 | 14% |
| no opening | 59.4% | 56.8% | 1.08 | 1.54 | 0.38 | 12% |
| Shadowstep at 2 (before) | 82.5% | 69.0% | 1.05 | 1.22 | 0.27 | 4% |

With the Guardian able to hold the boss, the round-1 Sap on the brute is
now worth about 22 points of wins. A failed Sneak is worse than no opening
(she ends up next to the brute and seen). At 5 the Rogue is starved more
(12% against 4%) and Shadowsteps a little less in the fight; her bands all
pass (Backstab 4.73, Eviscerate 2.16, Kidney Shot 0.52, Cheap Shot 0.60,
Sap 1.05, Shadowstep 1.05, Vanish 0.24).

### Shield Slam cannot reach 2 to 3 a fight

Probed at the final numbers: the Guardian gets to rule 10 (Shield Slam or
auto-attack) only about 5.7 turns a fight; he is busy with Taunt, Shield
Plant, Disrupt, Grip, Intercede and Last Stand the rest. On 4.4 of those
turns an ally is at 75% HP or less, on 1.8 an add is loose (wolves, then
goblins). How much the ally line matters (2000 fights, seeds 0 to 1999):

| Shield Slam when every ally is above | Shield Slam a fight | auto share | wins |
|---|---|---|---|
| 75% (kept) | 0.65 | 21% | 81.5% |
| 60% | 1.57 | 18% (fails) | 82.4% |
| 50% | 1.91 | 17% (fails) | 82.8% |
| any HP | in band | 16% (fails) | 83.2% |
| 75%, but 2 Taunt cards (D3c) | 0.54 | 21% | 81.4% |

So it only gets into its band when the HP line is gone, which is not the
owner's "only when everything is going super well", and then every Slam
takes an auto-attack's place and the auto share check fails. Left as "Not
met".

## D4b: the owner's calls, and honest buttons, 2026-11-27

The owner looked at D4 and decided six things. A review of D4 also found
numbers that were tuned to pass a check rather than to play well. This
step applies the decisions and undoes those numbers. Tuning runs used
seeds below 100000 (2000 fights from `--seed 0` unless it says so). (The
"Final" section now shows D4c. D4b's confirm runs: everything passed but
Shield Slam, 0.49, 0.53 and 0.49, and Kidney Shot, 0.53, 0.52 and 0.49.)

### The owner's decisions (2026-11-27)

1. **The Guardian starts with 4 grit: accepted.** The numbers file and the
   design say so now.
2. **Shield Slam's band is now 0.5 to 1.5** (it was 2 to 3; the owner's
   change in `game/usage_targets.toml`). It stays the rare "everything is
   going very well" filler. Why 2 to 3 could not work: every Slam takes an
   auto-attack's place. No reading of the rule reached 2 to 3 without
   pushing auto-attacks under 20% of all damage (D4, "Shield Slam cannot
   reach 2 to 3 a fight": with no HP line at all it was in band, with
   auto-attacks at 16%).
3. **Ice Block's band is now 0.1 to 1.5** (the owner's). Evocation's 0.3 to 2
   is still only proposed.
4. **Combo points at most 3: accepted** (it was 5).
5. **Arcane Volley must be a good button in its own right**, not only
   because the Mage's rules say so. The owner: "The advantage of Arcane
   Volley is channelling ... and it can be partially used. A mage can let
   the spell hit twice and then cancel the cast to skip the third hit to
   kick off another, more urgent spell or interrupt. Firebolt is more
   all-or-nothing. If the mage needs to interrupt in the middle of a
   Firebolt cast, they lose the entire cast with no damage dealt." So a
   whole Volley should do about what a Firebolt does for its mana. This is
   in the design and in the Mage's tips now.
6. **The auto-attack floor may go down to 15%, only if needed** ("We can
   lower if needed"). It was needed; see below.

### Arcane Volley: as good for its mana as Firebolt

| | dice | damage on the mean | mana | damage for each mana | act steps | damage for each act step |
|---|---|---|---|---|---|---|
| Arcane Volley, D4 | 2d4 a hit, 3 hits | 15 | 6 | 2.5 | 3 | 5 |
| **Arcane Volley, now** | **2d6 a hit, 3 hits** | **21** | **6** | **3.5** | **3** | **7** |
| Firebolt | 4d6 | 14 | 4 | 3.5 | 1 | 14 |

Does the Mage really use Volley's edge? Measured at the final numbers
(2000 fights, seeds 0 to 1999), per fight:

- She starts 4.37 Volleys. 2.56 run all three hits. 0.80 end early
  because the enemy died or got out of reach.
- **0.40 she stops herself, and keeps the hits that landed:** 0.39 to
  Disrupt (0.24 after one hit, 0.16 after two), and about 0.01 to Frost
  Nova, Blink or haul someone up. That is about one Volley in eleven.
- 0.23 are ended by a stun, going down or her own Ice Block, again keeping
  the hits that landed.
- Firebolt, for comparison: 0.67 started, 0.65 landed. The 0.025 that did
  not (a stun or going down in the GM turn between) did no damage at all.
  (A Firebolt whose target died before it landed did nothing either; those
  were counted as landed here. With a 2-round cast, D4c, they are about
  0.06 a fight.)

So no policy change was needed. Her rules 1, 2, 4 and 5 (Ice Block, haul
up, Frost Nova or Blink, Disrupt) come before rule 6 (keep channelling),
and doing anything else ends a channel (`fight._act`). A test already
checks it (`test_mage_breaks_her_channel_to_disrupt_a_mend_before_a_boss_cast`).

One thing the owner should know: in the simulator a Firebolt has no turn
"in the middle". Its cast is 1 round: she starts it in the act step and it
lands at the top of her next party turn, before she moves. So she never
has to choose between a Firebolt and a Disrupt mid-cast; only a stun or
going down in between can lose it (or its target dying first, which
wastes it too). Per act step a Firebolt does twice what
a Volley does (14 against 7). The Mage still Volleys by default because
her rules say so. See "Needs a decision", item 17.

### Kept changes

Each row: what changed, why, and what putting just that number back does
(2000 fights, seeds 0 to 1999, everything else at the final numbers). The
final numbers there: wins 84.7%, 67.1% of fights in 18 to 22 rounds,
auto-attacks 16.2% of damage, every check passes (Shield Slam 0.50, Kidney
Shot 0.52, right on their lines).

| Change | Old → new | Why | With the old number instead |
|---|---|---|---|
| Arcane Volley dice | 2d4 → 2d6 | the owner: a whole Volley does as much for its mana as a Firebolt (table above). 2d4 was there to hold auto share at 20% | wins 73.5%, length 59.3% (fails), Challenging Shout 0.47 and Shield Slam 0.36 (fail), auto share 17.2% |
| Backstab cost | 7 → 5 | it gives one combo point, like an auto-attack that hits; at 7 it was barely better than an auto-attack. 5 is the cheapest that keeps auto-attacks over 15% | at 4: auto share 13.8% (fails even at 15%), wins 88.3%, Kidney Shot 0.46, Vanish 0.18. At 6: auto 17.6%, Kidney Shot 0.47. At 7: auto 19.1%, wins 79.3%, Kidney Shot 0.49 |
| Auto-share floor (`report.py`, `AUTO_SHARE`) | 20% → 15% | the owner's "we can lower if needed". With Volley at 2d6, auto-attacks are under 20% whatever Backstab costs (19.1% even at 7), so honest buttons cannot hold 20% | (at 20% the `auto_share` check fails at every Backstab cost) |
| Ogre HP | 115 → 130 | with Volley at 2d6 and Backstab at 5 the party won 94% of fights | wins 93.6% (fails), the Guardian ends up and full 53%, Intercede 0.98, Eviscerate 1.93, Kidney Shot 0.46, Vanish 0.16, Ice Block 0.09 |
| Challenging Shout radius | 5 → 4 | 5 covers 121 of the 192 squares, close to the whole map. 4 covers 81 (9 by 9). 3 is too small for its band | at 5: Shout 0.68, Kidney Shot 0.47 (fails), length 70.8%, taunting the boss worth 24 points of wins instead of 40. At 3: Shout 0.45 (fails), length 65.2% |
| Blink range | 5 → 6 | 5 was only there to feed Ice Block's old band (0.2); its band is 0.1 now. 5 is not better play: the same wins | at 5: wins 85.0%, Ice Block 0.20, Blink 0.18 |
| `ICE_BLOCK_AT` (Mage policy) | 0.35 → 0.5 | it was not rethought for the ogre's 2d6+9 (16 on the mean, 21 at most). At half HP she has 14, so one plain hit downs her | at 0.35: Ice Block 0.14 (0.16 at 0.5), the same wins. 0.45 and 0.6 are the same as 0.5 |

Looked at again and kept from D4:

- **Cheap Shot cost 2.** Its reason was Backstab at 7. At 3 (with Backstab
  at 5) the Rogue is starved 21.0% of rounds, over the 20% line.
- No other D4 number gave "to keep auto share up" as its reason. (The ogre
  +9 row lists auto share among what the old number did, but its reason is
  the held boss.) Grip 2, Intercede 2, wolf HP 20, brute shield 3 and the
  rest stay.

### A play fix: who Disrupts the Stomp

`_stomp_disrupter` (who will Disrupt the Stomp, so the melee heroes stay
in) counted the Guardian next to the boss, but his rule 4 Disrupts the
first caster next to him by id, which can be another enemy. Now both ask
one helper, `_disrupt_pick`: the cast that hero's Disrupt rule goes for
(the Guardian and the Rogue: the first caster next to them by id; the
Mage: a mend first, then by id, the first she can reach). A hero counts
only if that is the boss. A test with a casting brute ("brute1" comes
before "ogre1") checks it. In this fight the ogre comes first by id, so
for the Guardian nothing changes; for the Mage it is a little looser than
before (she was left out whenever any other enemy had a cast, even one her
list would get to after the ogre's). At the D4 numbers: wins 81.6% → 81.3%,
Disrupt 2.20 → 2.14 a fight. Noise.

### Shield Slam and Kidney Shot pull against each other

After the changes above, these two were the thin ones, and no number
tried got both over the line without breaking another check (a 2d4
boulder with the ogre at +10 got both over, but then Intercede or Vanish
failed). Shield Slam needs every ally
above 75% HP and no add loose. Kidney Shot needs full combo points and an
add next to the Rogue going for someone who is not the Guardian: about half
are on the brute when it wakes late in a long fight, half on a wolf (0.27
and 0.25 a fight). So a harder fight or adds on the back line give more
Kidney Shots and fewer Slams, and an easier one the other way.

On 4000 fights (seeds 40000 to 43999), everything else at the final
numbers:

| Ogre HP | wins | Shield Slam | Kidney Shot |
|---|---|---|---|
| 125 | 87.6% | 0.51 | 0.49 |
| 127 | 86.2% | 0.49 | 0.50 |
| 130 (kept) | 84.1% | 0.47 | 0.51 |

130 was kept: wins in the middle of the band, and Kidney Shot (the check
the review found failing) holds on two of the three confirm ranges. Shield
Slam goes under "Not met".

Tried and not kept (2000 fights, seeds 0 to 1999, all with Volley 2d6,
Backstab 5 and Blink 6; most also with Shout 4 and Ice Block at half HP):

- Ogre melee +10 or +11 at HP 115: wins 91.1% and 90.0%, Shield Slam 0.49
  and 0.39. Ogre HP 135: Shield Slam 0.46. HP 135 with +8: Kidney Shot 0.48.
- Wolf HP 24: wins 49% to 56%. A whole Volley (21 on the mean) no longer
  kills a wolf, so the wolves live much longer.
- Wolf damage 4: Kidney Shot up, Shield Slam and Vanish down (with a
  softer boulder too: Slam 0.49, Vanish 0.18).
- Goblin damage 2 with ogre +10 or +11: Shield Slam 0.42 and 0.34,
  Challenging Shout 0.50 and 0.42. Goblin move 2 with +10: Kidney Shot
  0.41, Frost Nova 0.18.
- Boulder 1d6 or 2d4: Shield Slam 0.81 and 0.62, but wins 93% and 90%,
  Kidney Shot 0.41 and 0.46, Vanish 0.11 and 0.14. With ogre +10 as well:
  Slam 0.65 and 0.50, Kidney Shot 0.50 and 0.53, Intercede or Vanish fail.
- Rejuvenation 5 a card: Shield Slam 0.60, Kidney Shot 0.43.
- Kidney Shot cost 2: no change (0.52). She is not short of energy for it;
  she waits for the moment.
- Rogue HP 32 (with a 2d4 boulder): Vanish 0.38, Kidney Shot 0.41.
- Shield Slam cooldown 1, only to see if the cooldown holds it back: 0.57
  (from 0.50). Not a candidate: a free button needs some limit.

## D4c: a 2-round Firebolt, 2026-11-27

The owner made Firebolt a 2-round cast and set a principle for tuning
classes. This step applies both, retunes, and brings the rules pages up to
date. Tuning runs used seeds below 100000 (2000 fights from `--seed 0`
unless it says so); the confirm runs are under "Final".

### The owner's decisions (2026-11-27)

1. **Firebolt is a 2-round cast** (`cast = 2`). The owner: "The advantage
   of Arcane Volley is channelling ... it can be partially used. A mage can
   let the spell hit twice and then cancel the cast ... to kick off
   another, more urgent spell or interrupt. Firebolt is more
   all-or-nothing. If the mage needs to interrupt in the middle of a
   Firebolt cast, they lose the entire cast with no damage dealt." With a
   1-round cast there was no middle. Now the cast takes her next act step
   too, and anything else she does then throws it away.
2. **Evocation's band, 0.3 to 2, is the owner's** (it was only proposed).
3. **One of each is not the game.** The owner, asked about Shield Slam
   (Guardian) and Kidney Shot (Rogue) pulling against each other: "Having
   one of each of these classes is not required. I plan on making many
   more classes. I don't think we can really weigh one class ability
   against another class ability." So, from now on:
   - A class's use bands are reached with that class's own numbers and
     play (its costs, dice, and the thresholds in its own rules).
   - Fight numbers (the boss's HP, the adds, the boulder...) move only for
     targets about the whole fight: wins, length, danger. Never to trade
     one class's band against another's.
   - Where a class's band still cannot be met in this one fight with that
     class's own levers, it goes under "Not met", as a property of this
     test fight and party, not of the class. The bands are not changed.
4. **20 Sap cards are accepted** until a table test.
5. **Reactions** are an idea, not planned ("Needs a decision", item 19).

### What the 2-round cast did on its own

Firebolt per fight, at the D4b numbers and play (the Mage's old rule 11:
Firebolt an add one Firebolt would finish):

| | wins | 18 to 22 rounds | started | landed | target died first | stepped out of a blast | she went down | Volley |
|---|---|---|---|---|---|---|---|---|
| 1-round (D4b) | 84.7% | 67.2% | 0.67 | 0.60 | 0.05 | 0 | 0.02 | 4.37 |
| 2-round, same play | 75.4% | 58.5% | 0.67 | 0.39 | 0.13 | 0.08 | 0.04 | 3.96 |
| no Firebolt at all | 77.4% | 59.6% | 0 | 0 | 0 | 0 | 0 | 4.45 |

So the 1-round Firebolt was worth about 7 points of wins: 14 damage in
one act step, twice what a Volley does in one. The 2-round one on the old
rule was worse than none: the adds it went for were low, so another hero
often killed them first, and 0.30 times a fight she kept casting with an
enemy next to her (her rule 3 came before Frost Nova and Blink).

### Firebolt's numbers: a whole Volley, one act step sooner, for more mana

| | dice | damage on the mean | mana | damage for each mana | act steps | damage for each act step |
|---|---|---|---|---|---|---|
| Arcane Volley | 2d6 a hit, 3 hits | 21 | 6 | 3.5 | 3 | 7 |
| Firebolt, D4b | 4d6 | 14 | 4 | 3.5 | 1 | 14 |
| **Firebolt, now** | **6d6** | **21** | **9** | **2.3** | **2** | **10.5** |

Now the trade is real both ways. Firebolt is the quicker damage, for more
mana, and all or nothing. Volley is cheaper, slower, lets her move, and
can be stopped part-way with the hits kept.

| Firebolt (everything else at the final numbers) | wins | 18 to 22 rounds | Firebolt | Volley |
|---|---|---|---|---|
| **6d6, 9 mana (kept)** | **87.1%** | **68.3%** | **1.26** | **4.22** |
| 6d6, 8 mana | 87.5% | 66.7% | 1.51 | 4.01 (just on the line; 3.99 on seeds 20000 to 21999) |
| 6d6, 4 mana | 80.0% | 65.8% | 3.14 | 2.02 (fails) |
| 4d6, 9 mana | 82.8% | 63.5% | 1.23 | 4.29 |
| 7d6, 9 mana | 88.8% | 67.3% | 1.27 | 4.15 |

### How the Mage plays it (`policies.py`, her rules 3, 6 and 11)

- **Rule 11, the new Firebolt rule.** She starts a Firebolt only when she
  can expect to finish it: she can pay for it and still have a whole
  Volley's mana after it (9 + 6 = 15 today), and no enemy could walk up
  next to her before her next act step (one that is not stunned, sapped
  or sheeped, not held by the Guardian, has no Taunt cards, attacks next
  to it, and stands within its move plus 1 of her). Then she Firebolts
  her focus, the boss too. No new threshold: "a whole Volley" and "move
  plus 1" come from the game files. Her rule 5 (Disrupt) comes first, so
  no cast that needs her Disrupt is waiting when she starts one.
- **Rules 3 and 6.** In the middle of a Firebolt her rules 4 (an enemy
  next to her: Frost Nova or Blink) and 5 (Disrupt) come before keeping
  it going, so she throws it away when she has to, as the owner
  describes. A Meteor she still keeps going (rule 3, unchanged).

What a Firebolt does now, per fight (final numbers): started 1.26, landed
1.11. Thrown away: its target died first 0.06, she Disrupted instead 0.03,
she went down 0.03, she stepped out of a blast 0.01, she Frost Novaed
0.001. None of those cost her any mana.

Each part taken back out, alone (final numbers):

| Taken out | wins | 18 to 22 rounds | Firebolt | Volley | Notes |
|---|---|---|---|---|---|
| nothing (kept) | 87.1% | 68.3% | 1.26 | 4.22 | |
| all of it: the old rule 11, and rule 3 keeps a Firebolt going | 70.7% | 56.9% | 1.23 | 3.20 | 0.57 times a fight she kept casting with an enemy next to her |
| the "could an enemy walk up" check | 73.4% | 55.0% | 1.97 | 3.30 | 0.42 a fight thrown away for a Frost Nova, 0.29 lost to the target dying |
| "a whole Volley's mana after it" (only its cost) | 79.2% | 62.2% | 3.05 | 1.99 | Volley fails |
| letting a Firebolt go for rules 4 and 5 | 87.5% | 69.0% | 1.23 | 4.26 | noise; kept, because it is how the owner says a Firebolt plays |

Tried and not kept:

- No Firebolt at half HP or less: at 8 mana it cost about 3 points of
  wins. The walk-up check already covers what would make her Ice Block or
  Blink.
- No Firebolt while a casting enemy is in her Disrupt range and nobody
  else is next to it: no difference at all, to the last fight.
- The old target rule (an add one Firebolt finishes) with the new checks:
  at the D4b dice and cost, 0.11 Firebolts a fight, about half of them
  wasted on an add that died first.
- A Firebolt only on the boss: at 4 mana, Volley 3.2 to 3.3 a fight.
- Letting a Meteor go for rules 4 and 5 too: no difference, and Meteor's
  play was not part of this step.

### Shield Slam and Kidney Shot, each with its own class's levers

Under the owner's principle, Shield Slam is reached with the Guardian's own
play and Kidney Shot with the Rogue's.

**Shield Slam: every ally above 70% HP, not 75%** (`SLAM_ALLIES_ABOVE`, the
Guardian's rule 10). It is still the "everything is going very well"
filler: 70% is the Druid's own line for "hurt" (her Wild Growth counts
allies at 70% or less, and she Regrowths at 60%), so an ally above it is
one the Druid is not busy with.

| Shield Slam when every ally is above | Shield Slam a fight | auto-attacks | wins |
|---|---|---|---|
| 75% (D4b) | 0.50 | 16.1% | 86.5% |
| 72% | 0.74 | 15.6% | 87.0% |
| **70% (kept)** | **0.82** | **15.4%** | **87.0%** |
| 65% | 1.03 | 14.9% (fails) | 87.2% |
| 60% | 1.33 | 14.2% (fails) | 87.6% |

Each Slam takes an auto-attack's place, so the line cannot go much lower
without the auto-attack share falling under 15%.

**Kidney Shot: on an add attacking anyone** (the Rogue's rule 6). Before,
only on an add going for someone who is not the Guardian. A stunned add
hits nobody for two GM turns, the Guardian included, and the boss cannot be
stunned, so the boss gets her Eviscerates.

| Rogue rule 6, with full combo points | Kidney Shot | Eviscerate |
|---|---|---|
| an add going for someone who is not the Guardian (D4b) | 0.43 | 2.11 |
| **an add attacking anyone (kept)** | **0.53** | **2.01** |
| ... or an elite on anyone | 0.47 to 0.50 | |
| ... an add on anyone at 80% HP or less | 0.50 to 0.52 | 2.0 |
| ... an add on anyone at 60% HP or less | 0.48 to 0.50 | 2.1 |
| ... but not one an Eviscerate would kill | 0.26 | 2.3 |

(Some rows measured at a Firebolt of 8 mana, or on 2000 fights from seeds
0, 20000 and 40000; the Rogue's numbers barely move with the Mage's.)

Her own numbers did not help: Eviscerate at 2 energy (Eviscerate 1.98,
auto-attacks 14.6%), Kidney Shot at 2 as well (the same), Backstab at 4
(Eviscerate 1.96, auto-attacks 12.8%). The Rogue gets full combo points
about 2.5 times a fight, and Kidney Shot and Eviscerate share them: their
floors (0.5 and 2) add up to 2.5. So in this fight both sit on their lines
whatever her rule says. That is a property of this test fight (how often
she gets to 3 combo points), not of the Rogue.

**No fight numbers changed.** With the new Firebolt, wins and length are in
band at the D4b fight (ogre HP 130). Ogre HP 135 was tried for a lower win
rate: 84.3% wins, but 63.5% in 18 to 22 rounds and auto-attacks at 15.1%.

### The rules pages

Every class's "How to play" tips were rewritten from the priority lists in
`policies.py`, as advice for players. The Firebolt on the Mage's sheet says
it is all or nothing. The core rules' example round and the cast timing use
a 2-round Firebolt. See the handoff for the list.

## Needs a decision

These are things numbers alone could not fix well. Each needs a change
to a rule or to how a hero plays, so it is for the owner to decide.

1. **Skull Crusher almost never lands, so Last Stand is never used.** The
   boss announces it about 2 times a fight, but it lands only 0.08 times
   a fight: Disrupt breaks it almost every time (the Mage's Disrupt
   reaches 10 squares, so she can always get it). Last Stand was used 0.0
   times a fight. The "Last Stand moment" in the design does not happen.
   Choices: make the boss's heavy hit something Disrupt cannot break, or
   have the Mage keep Disrupt for the shaman.
   After the third look (the 3000 confirm fights): still true. The
   Crusher is announced 2.0 times a fight and lands 0.03 times (80
   times in 3000 fights). Last Stand was used 23 times in 3000 fights.
   After the fourth look (the 3000 confirm fights): still true. The
   Crusher is announced 2.2 times a fight and lands 0.02 times (56
   times). Last Stand was used 45 times in 3000 fights.
   After D4: Last Stand 0.77 a fight, in band. He now has the grit, and
   comes first on his list once a heavy hit that could drop him is
   announced.
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
   After the fourth look: still true, 0 times in the 3000 confirm fights.
   After D3 and D3b: fixed by how the Rogue plays. She opens next to the
   brute before round 1 and Saps it in round 1: 1.1 Saps a fight.
3. **Stalemates once the Guardian is out.** With the first pass's
   numbers, about 1 fight in 1100 was still going after 60 rounds (21 of
   24000; 2 of the 3000 confirm fights). In all 5 we looked at, the
   Guardian was out and the ogre was left, with the Druid alone or with
   the Rogue. Why: only the Guardian gives Taunt cards, and Eviscerate on
   the boss needs them; Backstab needs the boss to be attacking someone
   else, and it is attacking her; so the Rogue mostly does nothing. The
   Druid heals faster than the ogre hurts, and heroes move 6 while the
   ogre moves 4, so it cannot catch them. The slow goblins made it worse
   (the Rogue's auto-attack goes to the enemy with the least HP, which
   was a slow goblin far away), but they were not the main cause.
   Numbers now make it rare: Guardian HP 100 alone cuts it to 1 in 24000;
   the new goblins alone to 5 in 24000; both together to 1 in 24000. The
   confirm run had none. It can still happen. Ogre move 6 removes it
   (0 in 24000) but makes the boss play differently. Choices: let the
   Rogue hit the boss when nobody can Taunt it, or let the ogre catch
   heroes who run.
   After the third look: 0 of 24000 fights (seeds 40000 to 63999) ran
   out of rounds. Best guess why: the boss now hits much harder, so
   once the Guardian is out the others go down too, instead of running
   from it for 40 rounds. The cause is still there, so it could come
   back if the boss gets weaker.
   After the fourth look: 0 of 24000 fights ran out of rounds, even
   with the boss hitting for +4 instead of +7. Best guess why: once
   nobody taunts it, the boss now goes for the back line instead of
   standing by the Guardian, so the fight keeps moving. The cause (only
   the Guardian gives Taunt cards) is still there.
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
   After the fourth look: 0.005 times a fight (14 times in 3000
   fights), so almost never again. Best guess why: with the boss
   walking to the back line, the enemies end up close to the heroes,
   and the Mage never drops a Meteor where a hero stands.
   After D4: 1.61 a fight, in band (not looked into why it came back).
5. **Some buttons are almost never pressed in this fight** (per fight,
   first pass's numbers): Challenging Shout 0.0, Kidney Shot 0.0, Cheap Shot 0.0,
   Last Stand 0.0, Sap 0, Frost Nova 0.1, Shield Plant 0.3, Wild Growth 0.4.
   After the second look: Meteor 0.0 too, Kidney Shot 0.2, Frost Nova
   0.3.
   After the third look (per fight, the 3000 confirm fights, with the
   count in brackets): Sap 0 (0), Shield Plant 0.002 (6), Cheap Shot 0.005
   (14), Last Stand 0.008 (23), Meteor 0.11 (344), Frost Nova 0.15
   (437), Grip 0.15 (451), Kidney Shot 0.28 (842), Wild Growth
   0.33 (1000), Challenging Shout 0.60 (1787).
   Why Grip is rare now: Taunt (2 grit) does its old job of
   turning an add around for half the grit, so the Guardian keeps Grip
   for an enemy that hits from far away (the shaman).
   Why Shield Plant is rare: every hero moves before anyone acts, so by the
   time the Guardian could plant his shield, everyone has already
   stepped out of the Ground Slam.
   Every hero is still needed (without any one hero the party wins 9% or
   less), but "every button feels iconic" is not something the checks
   measure.
   After the fourth look (per fight, the 3000 confirm fights, with the
   count in brackets): Taunt on the boss 5.68 (17039), Shield Plant
   0.014 (43), Last Stand 0.015 (45), Sap 0 (0), Meteor 0.005 (14),
   Arcane Volley 0 (0), Grip 0.20 (603), Cheap Shot 0 (0), Kidney
   Shot 0.19 (575). Also Challenging Shout 0.18 (529), Frost Nova 0.39 (1178),
   Wild Growth 0.32 (953). Taunt on the boss went from about 0.01 a
   fight to 5.7: the Guardian now keeps the boss taunted most of the
   fight, which is what the owner asked for.
   Why Arcane Volley is never used (and was not before the fourth look
   either: 0 in 600 fights with the third look's numbers): the Mage only
   Volleys a focus with 3 Taunt cards on it (`VOLLEY_TAUNT_CARDS`). A
   Taunt gives 3, but back then the Guardian acted after the Mage (heroes
   act in id order, and his old id came last), and a card comes off at
   the end of the GM turn. So on the
   Mage's turn her focus has 2 cards at most. In 200 fights it had 3
   cards 0 times. With the rule at 2 cards, she Volleys about 1.8 times
   a fight, but the party won 155 of 200 instead of 170: Volley is Loud,
   so it takes Taunt cards off and lets the boss loose sooner. Choices:
   change the Mage's rule (how she plays, not a game number), or leave
   Volley for fights where it fits better.
   After D4: every button is pressed inside its band but Shield Slam
   (see "Not met"). Arcane Volley is 4.44 a fight (it is quiet since D3).
6. **Fight length is touchy about the boss's timings.** Changing when
   the Ground Slam comes moved "in band" anywhere from 47% to 75%,
   because the Guardian and Rogue lose a whole turn stepping out of it.
   If the slam timing changes later, length needs checking again.
7. (Settled 2026-11-27: the owner accepts 20 Sap cards for now, to be
   tried at the table. Twelve sheep cards likewise.)
8. **The opening is still not a real choice.** Shadowstep in now costs 5
   (the owner's number), so it is no longer free: she starts round 1 on 8
   energy, not 10. But the judgement rule still always Shadowsteps in, and
   it should: in this fight the round-1 Sap is worth about 22 points of
   wins, and a failed Sneak is worse than no opening (D4, "The opening").
   Sneak would only be worth it with an easier stealth check or a fight
   where the Sap matters less.
9. (Settled 2026-11-27: the owner accepted 4 grit at the start.)

10. (Done in D4: whoever can Disrupt the Stomp does, and the melee heroes
    stay in. It was worth about 8 points of wins and 8 of length.)
11. (Settled 2026-11-27: the owner lowered Shield Slam's band to 0.5 to 1.5.
    It is still just under it; see item 16 and "Not met".)
12. (Settled 2026-11-27: the owner set Ice Block's band to 0.1 to 1.5.
    Evocation's 0.3 to 2 is still only proposed.)
13. (Done in D4: nobody Disrupts a blast or a Stomp with nobody in it.)
14. **The Rogue spends full combo points on Kidney Shot when an add is on
    her** (rule 6), even when it is the last enemy and an Eviscerate would
    kill it. That made a rare stalemate with the brute (D4, the brute's
    shield). The numbers end it today (the shield stops hits below 3,
    not 5); the rule could also skip Kidney Shot on the last enemy.
    Since D4c she Kidney Shots an add attacking anyone, the Guardian too,
    so this comes up a little more often; no fight ran out of rounds on
    the confirm runs.
15. (Settled 2026-11-27: the owner let the auto-attack floor go down to 15%.
    It is about 16% now, with honest Volley and Backstab numbers; D4b.)
16. (Settled 2026-11-27 by the owner's principle, D4c: one class's band is
    never traded against another's. Shield Slam and Kidney Shot each got
    there with their own class's play: the Guardian Shield Slams with every
    ally above 70% HP, and the Rogue Kidney Shots an add attacking anyone.
    See D4c.)
17. (Settled 2026-11-27: the owner made Firebolt a 2-round cast, so it has
    a turn in the middle, and the Mage throws it away if she has to do
    something else then. See D4c.)
18. **What the `needed:` check really asks.** Today's check is a man
    down: it plays the fight with one hero left out, three heroes against
    a fight built for four. That says little about whether a class is
    required. The swapped parties below (four heroes, one class replaced by
    a second copy of another) are what answer "is a healer (or a tank)
    required". The owner said early on "I also don't want a healer to be 100% required",
    and with more classes and parties coming, the owner may want a
    different check (for example: a party missing any one role can still
    win some fights). Nothing is changed; the check stays as it is.

    A man down (the check, `check --n 3000 --seed 100000`, D4c numbers):

    | Hero left out | wins without them |
    |---|---|
    | Guardian | 0.2% |
    | Rogue | 0.1% |
    | Druid | 0.4% |
    | Mage | 0.0% |

    Four heroes, with one class swapped for a second copy of another
    (`run --n 1000 --seed 0 --party ...`, D4c numbers):

    | Class taken out | Second Guardian | Second Rogue | Second Druid | Second Mage |
    |---|---|---|---|---|
    | Guardian | - | 15.9% (30.2%) | 74.5% (6.9%) | 84.9% (54.7%) |
    | Rogue | 23.0% (54.5%) | - | 65.2% (3.5%) | 56.9% (52.9%) |
    | Druid | 58.3% (24.1%) | 54.1% (22.1%) | - | 85.0% (47.1%) |
    | Mage | 2.4% (54.6%) | 3.0% (35.3%) | 4.5% (53.4%) | - |

    Wins, with the share of fights lasting 18 to 22 rounds in brackets. The
    full party wins 87.9% on these seeds (68.0% in 18 to 22 rounds). So in
    this fight no healer and no tank are needed: with a second Mage in
    their place the party wins nearly as often as the full party (85%),
    and fights run a little short (median 18 or 19 rounds). Two Druids win
    too, but slowly (median 31 to 34 rounds). What this fight cannot do without is
    the Mage: every party without one wins 5% or less. That is a property
    of this one test fight (about half of all damage is hers, and Meteor is
    the answer to the goblin wave), not of the Mage.
19. **Reactions** (owner, 2026-11-27, an idea, not planned): "I don't think
    we have reactions and I'm a bit concerned about how slow they make the
    game, but if we add them, Ice Block may fit in better. Generally,
    abilities that happen outside of Global Cooldown in MMOs are likely
    reactions." Today every button takes the hero's one action. If
    reactions came in, the candidates are Ice Block, interrupts like
    Disrupt, and maybe Last Stand and Intercede. Nothing is built.

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
- Heroes move, and act, one after another in id order (druid, guardian,
  mage, rogue), not truly all at once. So a hero who acts before the
  Mage in that order gets one quickened turn fewer than one who acts
  after her: Quicken lands after they have already attacked that turn.
- The Guardian starts a fight with 4 grit (D4; it was 0. The owner
  accepted it on 2026-11-27).
- Bosses ignore the hold: only Taunt cards make a boss attack the Guardian
  (owner's decision).

New buttons and the Stomp (D3c, 2026-11-27):

- **Hero stuns.** A stunned hero does not move or act in the party turn;
  the Mage's Ice Block is the one thing they may do. Stun cards on a hero
  come off at the end of the party turn (like Bleeding), not the top, so a
  1-card stun handed out in the GM turn costs exactly the next party turn.
  A new stun never shortens one already there. A stun ends the hero's cast
  or channel. A downed hero, or a Mage in an Ice Block, gets none.
- The Druid acts before the Guardian, the Mage and the Rogue (id order),
  so her Cleanse in the act step gives a stunned one of them back their
  act step that turn. Their move step has already gone by.
- **Bad cards** (one list, `units.BAD_STACKS`): stun, poison, rooted, sap,
  sheep. Heroes can only get stun and poison today; the rest are there for
  later. Never Bleeding, never a cooldown. Cleanse takes one stack of the
  Druid's choice; told no card, it takes the first in that list.
- **Ice Block timing.** One card, put on in the act step. It comes off at
  the top of her next party turn, so it covers the GM turn after it, and
  she is free on her next turn. While she holds it: no damage of any kind
  (a blast too), no stun, no enemy picks her, her pulls count for
  nothing, and she cannot move or act. It takes off her bad cards and ends
  her own cast or channel; heal cards and cooldowns stay.
- **Evocation** is a channel of 2 rounds: 6 mana when she starts it, 6
  more on the next act step if she keeps channelling. A new field,
  `still`: moving ends it (Arcane Volley does not have it). Damage does
  not end it; a stun does, like any cast.
- **Cooldowns on channels** start on the first round and are not started
  again by later rounds. (Before, a cooldown was put on at each hit; no
  channel had one.)
- **Shield Slam** is a hit, not an auto-attack: it never misses or crits,
  and its damage is not auto damage. It is not Loud. The grit it gives is
  its `alt`. Cooldown 2: used in round 4, again in round 6.
- **The Stomp** is a new script kind. It is announced like a blast, on the
  squares within its radius of the boss when it is announced, and lands
  next GM turn: one roll, every hero who is up there takes it all, then
  each of them who is still up gets its stun cards. It counts as a blast:
  Shield Plant takes its value off, and it gives the Guardian no grit.
  Disrupt, or a stun on the boss, breaks it.
- **Benched** is a new ability field. A benched ability cannot be used, is
  not a button in the summary or the `use:` checks, does not count for
  starving, and is left off the rules pages (a test checks). A usage
  target for one is allowed and ignored. Only Quicken, in `game/`. The
  Mage's Quicken rule is kept in her list and never fires.
- The tests pair the frozen numbers with a frozen copy of the usage
  targets (`tests/data/usage_targets.toml`), since the real targets now
  name abilities the old copy did not have, and leave out Quicken.

How the heroes play (the priority lists in `src/fastcombat/policies.py`,
2026-11-27). These are calls about play, not game numbers:

- Heroes play only on what a player at the table can see: announced
  casts, cards, HP, positions and the round number. The boss's script is
  the GM's secret. So the Guardian keeps no grit back for Last Stand
  before a heavy hit is announced; once it is announced, Last Stand comes
  first on his list.
- Nobody Disrupts a heavy hit aimed at a Guardian who holds a Last Stand
  card: he has answered it. The same goes for a blast once he has planted
  his shield.
- Arcane Volley is no longer Loud. Measured with 500 fights: Loud gave 78%
  wins and passed the length check, but then Firebolt became the Mage's
  go-to spell and 11 checks failed. Quiet gave 73% wins and 7 failed. The
  owner asked for Volley as the go-to spell, so it is quiet.
- The shield plan: when the boss's blast is about to land on a Guardian
  who will plant his shield, he stays put, and allies stand behind him
  (out of the blast's reach behind the shield) instead of running out.
- The Guardian Intercedes for an ally at 60% HP or less, and keeps enough
  grit for Intercede while one is that low.
- Cheap Shot (outside stopping a cast) goes only on an add hitting a
  squishy hero (Druid or Mage) at half HP or less.
- Kidney Shot stops a cast only with full combo points, when Disrupt is
  cooling down. With fewer it gives the same one-card stun as Cheap Shot
  and wastes the combo points, so Cheap Shot does it instead.
- The Rogue Saps an elite only while it has more than half its HP. A
  nearly dead elite gets a Backstab from hiding instead.
- The Rogue waits hidden for an elite she cannot reach for 2 rounds at
  most, then plays the rest of her list.
- The Rogue Vanishes from a pull only when the boss or an elite is pulled
  onto her. A goblin or a wolf she just fights (unless she is low on HP).
- Meteor never goes where its area would cover a sapped or sheeped enemy:
  the hit would wake it, and keeping a dangerous add out of the fight is
  worth more than Meteor's damage on it.
- (D3b) Nobody hits a sapped or sheeped enemy while anything else is left,
  and once nothing else is, they hit it (a stunned one first). Nobody Saps
  or sheeps an enemy a Firebolt, a Volley or a Meteor is on its way to,
  and the Mage ends a Volley whose enemy was sapped after it began, unless
  nothing else is left to hit.
- (D3b) The Rogue's opening: the elite that hits hardest and that nobody
  stands next to yet. Shadowstep in, unless she could not then pay for the
  Sap in round 1 (then Sneak). With no elite, no opening.
- (D3c, D4) The Guardian Shield Slams only when he can spare the turn: the
  boss has a Taunt card (`SLAM_TAUNT_CARDS`, 1 since D4: a boss loses its
  card at the end of the GM turn, after it attacks, so one card means it
  still attacks him in the coming GM turn; D3c asked for 2, which only held
  the turn right after a Taunt), every ally is above 75% HP
  (`SLAM_ALLIES_ABOVE`), and no add is loose (fodder too). It is last
  before his auto-attack: the boss if it is next to him, else the lowest-HP
  add next to him that is not fodder and not controlled. Never on a boss
  with no Taunt cards.
- (D4) The Stomp and Disrupt. When the Stomp lands this round and someone
  will Disrupt it (`_stomp_disrupter`: the Guardian next to the boss first,
  then the others by id, each only if they can Disrupt the boss from where
  they stand and their list will get to it, and since D4b only if their
  Disrupt rule goes for the boss's cast, not another enemy's:
  `_disrupt_pick`), the Guardian and the Rogue
  stay next to the boss and keep hitting, and that hero Disrupts it. Only
  when nobody will do they step out. The Guardian also takes it when a
  Druid is up to Cleanse him (D3c), and now walks next to the boss to take
  it even when he starts the turn away from it (before, he stopped outside
  its squares and could not hit the boss), or when he is in it holding an
  add. The D3c rule "a Stomp only a Guardian is in, with a Druid up, is
  answered" is gone: someone who can Disrupt it does.
- (D4) A blast or a Stomp with no hero who is up in its area is answered:
  nobody Disrupts it. (Before, the Mage Disrupted Ground Slams everyone had
  walked out of.)
- (D3c) The Druid Cleanses a stun right after her emergencies (her rule
  4), the Guardian first, but only a stun that still costs something: the
  ally acts after her this turn, or it has more than one card. Other bad
  cards (poison) come where poison did.
- (D3c, D4) The Mage Ice Blocks (her rule 1) an announced hit or blast that
  lands this GM turn, could take her to 0 at its biggest roll, that she is
  still in after moving, and that she cannot Disrupt (she Disrupts first if
  she can). Since D4 also, as a mage in an MMO does: at half HP or less
  (`ICE_BLOCK_AT`; 35% in D4, half since D4b, under the ogre's average hit) with the boss or an elite next to her and on her (it
  went for her last turn and has no Taunt cards), when her rule 4 will not
  get her out of its reach: she cannot Blink to a square it cannot reach
  (stunned, in the middle of a cast, no mana, no square), or she would
  Frost Nova first. A rooted enemy next to her still hits her, so Frost Nova
  is never enough against one already next to her. The old "stunned or
  rooted" line is gone (heroes cannot be rooted).
- (D3c) The Mage Evokes below 6 mana (`EVOCATION_BELOW`, a whole Volley)
  when no awake enemy is next to her, no blast or stomp is coming down on
  her square, no cast in her Disrupt range is waiting, and the boss has
  Taunt cards. It comes after Meteor, before Firebolt.
- (D3c) The Mage keeps channelling Arcane Volley on a sapped or sheeped
  enemy when nothing else is left to hit (the D3b rule ended it).

The Rogue's opening (D3b), rules the owner left open:

- She lands on the free square next to the enemy that is nearest to her
  start square, the same square Shadowstep would put her on. Sneak and
  Shadowstep in land on the same square.
- Shadowstep in reaches any enemy on the map, not only one in
  Shadowstep's range: before the fight she can get into place first.
- Shadowstep in takes the cost off her starting energy, and she still gets
  her energy back at the top of round 1 like everyone. (That is what makes
  it free today; see "Needs a decision", item 8.)
- Spotted means only that she is not hidden, on her own square. The
  enemies do not come for her because of it; they pick targets as always.
- A second Rogue opens after the first (id order). Her policy leaves an
  elite that someone already stands next to, so she picks another elite or
  none.
- A refused opening (a boss, a dead enemy, no free square, too little
  energy, a Rogue who is not hidden) does nothing, the same as an ability
  that is refused, and counts as no opening.
- The enemies' tally: a sapped, sheeped or stunned enemy "loses" each GM
  turn it spends with those cards (`rounds_out` in the summary).

## Final (D4c, 2026-11-27)

These are the numbers after D4c: the D4b numbers and play, with Firebolt a
2-round cast of 6d6 for 9 mana, the Mage's new Firebolt rule, the
Guardian's Shield Slam at every ally above 70% HP, and the Rogue's Kidney
Shot on an add attacking anyone. No fight number changed.

Command: `uv run fastcombat check --n 3000 --seed 100000` (seeds never
used while tuning). The simulator gives up after 60 rounds.

```
Fights played:          3000
Wins:                   86%
Ran out of rounds:      0%
Rounds:                 median 20, most between 17 and 25
Lasted 18 to 22 rounds: 66%
A hero in danger:       90% (down to 25% HP, or went down)
Auto-attack damage:     16% of all damage

hero        damage  healing  starved  up and full  went down  lowest HP
guardian       11%       0%       2%          39%        54%         8%
rogue          33%       0%      14%          38%        14%        52%
druid           1%     100%       1%          38%        14%        48%
mage           55%       0%       1%           0%        38%        19%

Uses per fight (all heroes of a class together):
guardian
  taunt                4.3
  challenging_shout    0.6
  intercede            1.1
  grip                 1.0
  shield_plant         1.5
  last_stand           0.8
  shield_slam          0.8
rogue
  backstab             6.1
  eviscerate           2.0
  kidney_shot          0.5
  cheap_shot           0.4
  sap                  1.0
  shadowstep           1.2
  vanish               0.2
druid
  rejuvenation         4.4
  regrowth             4.2
  swiftmend            2.1
  wild_growth          2.0
  cleanse              0.5
  shadowmeld           1.0
  nourish              3.5
mage
  arcane_volley        4.2
  firebolt             1.3
  meteor               1.4
  frost_nova           0.3
  blink                0.2
  polymorph            0.8
  ice_block            0.1
  evocation            0.3
anyone
  disrupt              2.0
  haul_up              0.1

Rogue opening (per fight, all Rogues together):
  sneak 0.00, shadowstep in 1.00, none 0.00
  stealth checks that worked: -
  rounds an enemy spent sapped: 17.8 (still sapped at the end of 11% of fights)
  rounds an enemy spent as a sheep: 9.7 (still a sheep at the end of 0% of fights)

PASS  length                 66.4% of fights  (wanted: at least 60.0% last 18 to 22 rounds)
PASS  win_rate               86.4%  (wanted: 70.0% to 90.0%)
PASS  no_timeouts            0.0%  (wanted: none)
PASS  danger                 89.7% of fights  (wanted: at least 50.0% have a hero at 25.0% HP or down)
PASS  auto_share             15.5% of damage  (wanted: 15.0% to 50.0%)
PASS  resource:guardian      starved 1.9% of rounds, ended up and full 39.1% of fights  (wanted: starved under 20.0%, ended up and full under 50.0%)
PASS  resource:rogue         starved 14.1% of rounds, ended up and full 37.8% of fights  (wanted: starved under 20.0%, ended up and full under 50.0%)
PASS  resource:druid         starved 1.2% of rounds, ended up and full 37.7% of fights  (wanted: starved under 20.0%, ended up and full under 50.0%)
PASS  resource:mage          starved 0.6% of rounds, ended up and full 0.0% of fights  (wanted: starved under 20.0%, ended up and full under 50.0%)
PASS  needed:guardian        wins 86.4% with, 0.2% without  (wanted: at least 20.0% fewer wins without them)
PASS  needed:rogue           wins 86.4% with, 0.1% without  (wanted: at least 20.0% fewer wins without them)
PASS  needed:druid           wins 86.4% with, 0.4% without  (wanted: at least 20.0% fewer wins without them)
PASS  needed:mage            wins 86.4% with, 0.0% without  (wanted: at least 20.0% fewer wins without them)
PASS  kit:guardian           wins 86.4% with the kit, 43.6% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
PASS  kit:rogue              wins 86.4% with the kit, 0.0% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
PASS  kit:druid              wins 86.4% with the kit, 20.0% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
PASS  kit:mage               wins 86.4% with the kit, 0.0% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
PASS  taunt:boss             wins 86.4% with, 43.6% when the Guardian never Taunts the boss  (wanted: at least 10.0% fewer wins without Taunting the boss)
PASS  use:taunt              4.29 per fight  (wanted: 3 to 10 per fight)
PASS  use:challenging_shout  0.60 per fight  (wanted: 0.5 to 3 per fight)
PASS  use:intercede          1.05 per fight  (wanted: 1 to 4 per fight)
PASS  use:grip               1.01 per fight  (wanted: 0.5 to 4 per fight)
PASS  use:shield_plant       1.51 per fight  (wanted: 0.5 to 3 per fight)
PASS  use:last_stand         0.79 per fight  (wanted: 0.2 to 2 per fight)
PASS  use:shield_slam        0.79 per fight  (wanted: 0.5 to 1.5 per fight)
PASS  use:backstab           6.08 per fight  (wanted: at least 4 per fight)
PASS  use:eviscerate         2.02 per fight  (wanted: at least 2 per fight)
PASS  use:kidney_shot        0.54 per fight  (wanted: 0.5 to 3 per fight)
PASS  use:cheap_shot         0.43 per fight  (wanted: 0.3 to 3 per fight)
PASS  use:sap                1.04 per fight  (wanted: 0.7 to 2 per fight)
PASS  use:shadowstep         1.23 per fight  (wanted: 0.5 to 4 per fight)
PASS  use:vanish             0.24 per fight  (wanted: 0.2 to 2 per fight)
PASS  use:rejuvenation       4.43 per fight  (wanted: at least 4 per fight)
PASS  use:regrowth           4.20 per fight  (wanted: 1 to 6 per fight)
PASS  use:swiftmend          2.10 per fight  (wanted: 0.5 to 4 per fight)
PASS  use:wild_growth        2.03 per fight  (wanted: 0.5 to 4 per fight)
PASS  use:cleanse            0.50 per fight  (wanted: 0.3 to 4 per fight)
PASS  use:shadowmeld         0.96 per fight  (wanted: 0.1 to 2 per fight)
PASS  use:nourish            3.53 per fight  (wanted: at least 2 per fight)
PASS  use:arcane_volley      4.22 per fight  (wanted: at least 4 per fight)
PASS  use:firebolt           1.27 per fight  (wanted: 0.5 to 4 per fight)
PASS  use:meteor             1.42 per fight  (wanted: 0.5 to 3 per fight)
PASS  use:frost_nova         0.27 per fight  (wanted: 0.2 to 3 per fight)
PASS  use:blink              0.17 per fight  (wanted: 0.1 to 3 per fight)
PASS  use:polymorph          0.85 per fight  (wanted: 0.5 to 3 per fight)
PASS  use:ice_block          0.15 per fight  (wanted: 0.1 to 1.5 per fight)
PASS  use:evocation          0.34 per fight  (wanted: 0.3 to 2 per fight)
PASS  use:disrupt            2.03 per fight  (wanted: at least 1 per fight)
PASS  use:haul_up            0.06 per fight  (wanted: at least 0 per fight)
```

Every check passes. The other two confirm ranges (`check --n 1000`):

- `--seed 400000`: one fails, `use:kidney_shot` 0.48 (wins 86.4%, length
  66.6%, auto share 15.5%, Shield Slam 0.81, Eviscerate 2.03).
- `--seed 700000`: one fails, `use:kidney_shot` 0.49 (wins 85.4%, length
  66.6%, auto share 15.3%, Shield Slam 0.80, Eviscerate 2.04).

No fight ran out of rounds on any of the three.

The pinned test seeds (`check --n 600 --seed 500000`): every check passes
(Kidney Shot passes there; auto share is 15.0%, right on its line). So the
slow targets test is no longer xfail.

Things to keep an eye on (thin margins on the confirm runs):

- Kidney Shot 0.48 to 0.54 (line 0.5) and Eviscerate 2.02 to 2.04 (line 2):
  they share the Rogue's full combo points; see "Not met".
- Auto share 15.0% to 15.5% (line 15%): every Shield Slam takes an
  auto-attack's place.
- Evocation 0.34 (0.3), Ice Block 0.15 (0.1), Blink 0.17 (0.1), Frost Nova
  0.27 (0.2), Vanish 0.24 to 0.26 (0.2), Challenging Shout 0.60 to 0.63
  (0.5), Intercede 1.05 (1), Arcane Volley 4.19 to 4.25 (4).
- The Mage does more than half of all damage (55%), and the Guardian goes
  down in about half the fights.
- Taunting the boss is worth about 43 points of wins (86.4% against 43.6%).

## Not met

After D4c, on the three confirm ranges (`check --n 3000 --seed 100000`,
`--n 1000 --seed 400000`, `--n 1000 --seed 700000`):

- **`use:kidney_shot`: 0.54, 0.48 and 0.49 a fight, wanted 0.5 to 3.** It
  fails on two of the three.

Under the owner's principle (D4c) only the Rogue's own numbers and play
were used for it. The Rogue reaches full combo points about 2.5 times a
fight in this fight, and Kidney Shot and Eviscerate share those moments;
their floors (0.5 and 2) add up to 2.5. A wider Kidney Shot rule takes its
uses from Eviscerate (D4c, "Shield Slam and Kidney Shot, each with its own class's levers"). So this is a
property of this one test fight and party (how often the Rogue gets to 3
combo points here), not of the Rogue. The band is not changed and the
check is not loosened. The slow targets test passes on its own seeds, so
it is not marked xfail; this entry is the record.

Shield Slam, Not met after D4b, now passes on all three (0.79 to 0.81).
