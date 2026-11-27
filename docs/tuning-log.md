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
other enemy is dead, and then the party wakes it and kills it.

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
6. **Fight length is touchy about the boss's timings.** Changing when
   the Ground Slam comes moved "in band" anywhere from 47% to 75%,
   because the Guardian and Rogue lose a whole turn stepping out of it.
   If the slam timing changes later, length needs checking again.
7. **Twenty Sap cards (and twelve sheep cards) at the table.** A pile of
   20 cards on one enemy, one coming off each round, is a lot to handle.
   A single card that says "until hurt, or for N rounds" with a die or a
   tally for the rounds left may be better. That is the owner's call.
8. **The opening is not a real choice yet.** Shadowstep in costs 2
   energy, but the Rogue gets 3 back at the top of round 1, so it is free
   and always works; a Sneak can only lose. See "The opening" in D3b for
   numbers that would make it a choice.
9. **The round-1 Sap makes the Guardian matter less.** With the brute
   sapped in round 1, before it ever hits him, `kit:guardian`,
   `taunt:boss` and `length` fail (see D3b, and its correction: it is the
   opening Sap, more than the long one). Grit only comes from being hit,
   and the brute was what hit him early. For the retune, or a rule change
   (grit from something else).

10. **The Stomp costs about 11 points of wins and 13 of length, by
    making the melee heroes step around it,** not by its hit or its stun
    (D3c). The retune can take it in, or the Stomp can change (a smaller
    or no area, with the stun on the boss's target only, say).
11. **Shield Slam is pressed 0.48 times a fight, not 2 to 3.** The
    Guardian is rarely free in this fight. Loosening the rule does not get
    there (1.56 at the loosest). Either the fight leaves the tank more
    quiet turns, or the band moves.
12. **Ice Block is almost never pressed** (1 in 500 fights) under the
    owner's trigger. A wider trigger (low, with an enemy next to her)
    would press it about 1.4 times a fight and cost about 3 points of
    wins.
13. **Disrupting a blast nobody stands in.** The Mage Disrupts Ground
    Slams everyone has walked out of. Treating those as answered (as
    the Stomp is) is worth about 2 points of wins and 11 of length today
    (D3c). It changes how an old button is played, so it was left.

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
- The Guardian starts a fight with 0 grit.
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
  they stand and their list will get to it), the Guardian and the Rogue
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
  she can). Since D4 also, as a mage in an MMO does: at 35% HP or less
  (`ICE_BLOCK_AT`) with the boss or an elite next to her and on her (it
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

## Final (before the rename; being retuned)

These are the numbers after the fourth look: bosses ignore the hold, the
Guardian Taunts the boss whenever it has no Taunt cards, and the ogre
goes for the back line when nobody taunts it. `boss_loud_cards` is 1.

Command: `uv run fastcombat check --n 3000 --seed 100000` (seeds never
used while tuning; every tuning run used seeds below 100000). The
simulator gives up after 60 rounds (`max_rounds = 60`).

```
Fights played:          3000
Wins:                   78%
Ran out of rounds:      0%
Rounds:                 median 21, most between 18 and 26
Lasted 18 to 22 rounds: 67%
A hero in danger:       92% (down to 25% HP, or went down)
Auto-attack damage:     26% of all damage

hero        damage  healing  starved  up and full  went down  lowest HP
guardian         19%       0%      39%           9%        50%        10%
rogue          48%       0%       1%          18%        23%        44%
druid           1%     100%       0%          25%        27%        26%
mage           32%       0%      11%           0%        56%        11%

PASS  length           67.2% of fights  (wanted: at least 60.0% last 18 to 22 rounds)
PASS  win_rate         77.9%  (wanted: 70.0% to 90.0%)
PASS  no_timeouts      0.0%  (wanted: none)
PASS  danger           92.4% of fights  (wanted: at least 50.0% have a hero at 25.0% HP or down)
PASS  auto_share       26.2% of damage  (wanted: 20.0% to 50.0%)
PASS  resource:guardian  starved 39.0% of rounds, ended up and full 8.8% of fights  (wanted: both under 50.0%)
PASS  resource:rogue   starved 0.6% of rounds, ended up and full 17.7% of fights  (wanted: both under 50.0%)
PASS  resource:druid   starved 0.2% of rounds, ended up and full 24.9% of fights  (wanted: both under 50.0%)
PASS  resource:mage    starved 10.5% of rounds, ended up and full 0.0% of fights  (wanted: both under 50.0%)
PASS  needed:guardian    wins 77.9% with, 0.7% without  (wanted: at least 20.0% fewer wins without them)
PASS  needed:rogue     wins 77.9% with, 1.8% without  (wanted: at least 20.0% fewer wins without them)
PASS  needed:druid     wins 77.9% with, 0.0% without  (wanted: at least 20.0% fewer wins without them)
PASS  needed:mage      wins 77.9% with, 0.1% without  (wanted: at least 20.0% fewer wins without them)
PASS  kit:guardian       wins 77.9% with the kit, 44.4% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
PASS  kit:rogue        wins 77.9% with the kit, 25.7% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
PASS  kit:druid        wins 77.9% with the kit, 3.2% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
PASS  kit:mage         wins 77.9% with the kit, 6.0% on auto  (wanted: at least 10.0% fewer wins when they only auto-attack)
PASS  taunt:boss       wins 77.9% with, 35.2% when the Guardian never Taunts the boss  (wanted: at least 10.0% fewer wins without Taunting the boss)
```

Every check passes with the round cap at 60, `taunt:boss` too. The
pinned test seeds (`check --n 600 --seed 500000`) pass too.

Things to keep an eye on:

- Taunting the boss now matters: without it the party wins 35% instead
  of 78%. The Guardian Taunts the boss about 5.7 times a fight.
- The Guardian is starved 39% of rounds (the line is 50%). Keeping the
  boss taunted costs him 2 grit about every three rounds, and he only
  gets grit by auto-attacking. A more costly Taunt, or one more
  grit-hungry button, would push him over.
- The Guardian goes down in 50% of fights and the Mage in 56%. The Rogue
  went down in 54% after the third look and in 23% now. Best guess why:
  the boss used to hit whoever stood nearest, often her, and now it is
  either on the Guardian or going for the back line.
- A hero is in danger in 92% of fights, so nearly every fight is still
  a scare.
- With goblin damage 0 wins go up from 78% to 93%, over the top of the
  target. So the goblins matter.
- No fight ran out of rounds, here or in 24000 tuning fights. See
  "Needs a decision", item 3.
- Without any one hero the party almost never wins (2% or less).
- Meteor and Arcane Volley are almost never or never cast. See "Needs a
  decision", items 4 and 5.

## Not met

Nothing: every check passed on the confirm run after the fourth look,
`taunt:boss` included, with the round cap at 60. The items under "Needs
a decision" are design goals the checks do not measure.

Since then (D3 and D3b, 2026-11-27) checks fail again, waiting for the
retune (D4). After D3b, `check --n 500 --seed 100000` fails `length`
(58.6%), `resource:guardian` (starved 61.4%), `kit:guardian` (81.8% with
the kit, 79.2% on auto), `taunt:boss` (81.8% with, 75.8% without), and
these use bands: Challenging Shout, Intercede, Grip, Shield Plant, Last
Stand, Eviscerate, Kidney Shot, Arcane Volley, Firebolt and Quicken. The
slow test fails with them; it is left failing (not marked xfail) because
D4 is the step that has to make them pass.

After D3c, `check --n 500 --seed 100000` fails `length` (39.8%),
`win_rate` (69.4%, a hair under 70%), `resource:guardian` (starved
60.6%), `kit:guardian` (69.4% with the kit, 67.4% on auto), `taunt:boss`
(69.4% with, 59.6% without), and these use bands: Challenging Shout,
Intercede, Grip, Shield Plant, Last Stand, Shield Slam (0.48, wanted 2 to
3), Eviscerate, Kidney Shot, Arcane Volley, Firebolt and Ice Block (0.00,
wanted 0.2 to 1.5). Quicken has no check now (benched). Still for D4.
