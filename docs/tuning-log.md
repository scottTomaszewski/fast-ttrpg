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
9. `max_rounds` 60 to 200. About 1 fight in 750 drags on past 60 rounds
   (see "Needs a decision", item 3). It does end, so the simulator now
   waits for it. Longest seen: 78 rounds with these numbers, 118 with a
   near version of them.
   After: every check passes. Wins 81%, median 19, in band 71%,
   danger 83%, auto 24%, no fight ran out of rounds.

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

## Needs a decision

These are things numbers alone could not fix well. Each needs a change
to a rule or to how a hero plays, so it is for the owner to decide.

1. **Skull Crusher almost never lands, so Unbroken is never used.** The
   boss announces it about 2 times a fight, but it lands only 0.08 times
   a fight: Disrupt breaks it almost every time (the Mage's Disrupt
   reaches 10 squares, so she can always get it). Unbroken was used 0.0 times a fight. The "Unbroken
   moment" in the design does not happen. Choices: make the boss's heavy
   hit something Disrupt cannot break, or have the Mage keep Disrupt for
   the shaman.
2. **Sap never happens.** The Rogue only Saps in round 1, and her rule
   looks 7 squares away (move 6 plus 1). The brute starts 8 squares
   from her. Moving the brute from [10, 7] to [9, 7] makes Sap happen in
   every fight, but it also lets the Mage Meteor the whole group at the
   start. Then the party wins 99-100% and auto-attacks fall to about
   15% of damage. A few tries at making it harder again (stronger adds,
   a second shaman, more boss HP) did not bring auto share back above
   20%. Choices: change where heroes or the brute start and retune
   around it, or change the Rogue's Sap rule.
3. **Very long fights when only the Rogue and the Druid are left.** About
   1 fight in 750 lasts more than 60 rounds (8 of 6000; the longest 78,
   and 118 in a near version of these numbers). Why: the Rogue's
   auto-attack goes to the enemy with the least HP, which is a slow
   goblin far away, so she does nothing. Backstab needs the boss to be
   attacking someone else (it is attacking her), and Eviscerate on the
   boss needs Taunt cards, which only the Warden gives. The fights do
   end, so `max_rounds` is now 200. Choice: let the Rogue hit the enemy
   next to her when her focus is far away.
4. **Meteor only hits enemies that stand still.** Its spot is fixed when
   the 2-round cast starts. With goblins at move 5 it was cast 0.1 times
   a fight; with move 1 it is cast about 1.1 times a fight. If goblins
   should be fast, the Mage needs a way to aim where they will be.
5. **Some buttons are almost never pressed in this fight** (per fight,
   final numbers): War Cry 0.0, Kidney Shot 0.0, Cheap Shot 0.0,
   Unbroken 0.0, Sap 0, Frost Ring 0.1, Bulwark 0.3, Wild Growth 0.4.
   Every hero is still needed (without any one hero the party wins 5% or
   less), but "every button feels iconic" is not something the checks
   measure.
6. **Fight length is touchy about the boss's timings.** Changing when
   the Ground Slam comes moved "in band" anywhere from 47% to 75%,
   because the Warden and Rogue lose a whole turn stepping out of it.
   If the slam timing changes later, length needs checking again.

## Final

Command: `uv run fastcombat check --n 3000 --seed 100000` (seeds never
used while tuning; every tuning run used seeds below 100000).

```
Fights played:          3000
Wins:                   82%
Ran out of rounds:      0%
Rounds:                 median 19, most between 17 and 23
Lasted 18 to 22 rounds: 73%
A hero in danger:       84% (down to 25% HP, or went down)
Auto-attack damage:     24% of all damage

hero        damage  healing  starved  up and full  went down
warden         16%       0%      32%           3%        40%
rogue          44%       0%       1%           4%        32%
druid           1%     100%       0%          20%        21%
mage           39%       0%      11%           0%        47%

PASS  length           73.5% of fights  (wanted: at least 60.0% last 18 to 22 rounds)
PASS  win_rate         81.7%  (wanted: 70.0% to 90.0%)
PASS  no_timeouts      0.0%  (wanted: none)
PASS  danger           84.4% of fights  (wanted: at least 50.0% have a hero at 25.0% HP or down)
PASS  auto_share       23.7% of damage  (wanted: 20.0% to 50.0%)
PASS  resource:warden  starved 31.9% of rounds, ended up and full 3.3% of fights  (wanted: both under 50.0%)
PASS  resource:rogue   starved 1.1% of rounds, ended up and full 3.9% of fights  (wanted: both under 50.0%)
PASS  resource:druid   starved 0.1% of rounds, ended up and full 20.3% of fights  (wanted: both under 50.0%)
PASS  resource:mage    starved 10.8% of rounds, ended up and full 0.0% of fights  (wanted: both under 50.0%)
PASS  needed:warden    wins 81.7% with, 3.1% without  (wanted: at least 20.0% fewer wins without them)
PASS  needed:rogue     wins 81.7% with, 4.8% without  (wanted: at least 20.0% fewer wins without them)
PASS  needed:druid     wins 81.7% with, 0.0% without  (wanted: at least 20.0% fewer wins without them)
PASS  needed:mage      wins 81.7% with, 0.4% without  (wanted: at least 20.0% fewer wins without them)
```

Things to keep an eye on:

- Auto-attacks are 24% of damage. That passes, but it is close to the
  20% floor.
- Without any one hero the party almost never wins (5% or less). The
  design asks for "clearly harder", and this is much more than that: a
  party of three cannot beat this fight.

## Not met

Nothing: every check passed on the confirm run. The items under "Needs
a decision" are design goals the checks do not measure.
