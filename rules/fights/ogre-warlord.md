<!-- Made from templates/fights/ogre-warlord.md by `uv run fastcombat rules`. Change the template, not this file. -->

# The test fight: Ogre Warlord

This sheet is for the GM. It is one big fight that uses every rule in the
game: a boss who must be taunted, adds that run for the back line, a healer
to stop, a shielded brute, and a wave of goblins halfway through.

## The map

The map is **16 squares wide and 12 tall**, with no
walls. The heroes start on the left, the enemies on the right.

```
. . . . . . . . . . . . . . . .
. . . . . . . . . . . . . . . .
. . . . . . . . . . . . . . . .
. . . . . . . . . . w . . s . g
. . . . . . . . . . . . . . . g
. M R . . . . . . . . . . . . g
. + + W . . . . . . . o . . . g
. D + . . . . . . . b . . . . g
. + . . . . . . . . . . . . . .
. . . . . . . . . . w . . . . .
. . . . . . . . . . . . . . . .
. . . . . . . . . . . . . . . .

W Warden
R Rogue
D Druid
M Mage
+ where an extra hero starts (a second Rogue, say)
o ogre (boss)
b brute
s shaman
w wolf
g goblin (fodder, comes in round 10)
```

## The enemies

| Enemy | How many | HP | Attack | Reach | Move | Goes for |
|---|---|---|---|---|---|---|
| Ogre Warlord (boss) | 1 | 150 | 2d6+4 | 1 (next to it) | 4 | the back line |
| Brute (shielded 5) | 1 | 30 | 4 | 1 (next to it) | 4 | the nearest hero |
| Shaman | 1 | 24 | 2, and poison | 8 squares | 4 | a random hero |
| Wolf | 2 | 16 | 3 | 1 (next to it) | 7 | the back line |
| Goblin (fodder) | 5, in round 10 | 1 | 3 | 1 (next to it) | 3 | the back line |

"The back line" is the hero with the fewest max HP who is not the Warden:
the Mage (28 HP) while she is up, then the Druid or the Rogue
(36 each; the Druid first, being first in alphabetical
order). Remember the order for every enemy (core rules, section 8): Taunt
cards first, then a pull, then the Warden's hold (not the Ogre), then what
it likes.

- **Ogre Warlord.** The boss. He rolls 2d6+4 for each hit. Only
  Taunt cards keep him on the Warden: standing next to the Warden does not.
  With no Taunt cards he goes after the Mage. He cannot be stunned, sapped,
  sheeped or Chain Hooked, but a stun still breaks the move he announced,
  and Frost Ring can root him. His big moves are below.
- **Brute.** Big and slow. Shielded 5: any single hit
  under 5 does nothing to him. He walks to the nearest
  hero, so he often ends up held by the Warden.
- **Shaman.** Stands back and hits from 8 squares away.
  Each of his hits also gives the hero 3 poison
  cards worth 2 each, unless the hit took them
  down. He picks a random hero each turn: roll a die with one side for each
  hero who is up and not hidden. And he heals the Ogre (below).
- **Wolves.** Fast. They run straight past the Warden for the Mage.
- **Goblins.** Fodder: any hit kills one. **5 goblins
  come in at step 2 of the GM turn in round 10**, on
  their squares on the right edge (if one is taken, on the nearest empty
  square). They head for the back line too. The party cannot win before
  they have come in.

## The boss's moves

The Ogre announces **at most one** move each GM turn, in step 4: the first
one in this list that is due. If both are due in the same round, the
Ground Slam wins and the Skull Crusher is skipped that time. An announced
move lands in step 1 of the next GM turn.

| Move | Announced in rounds | What it does |
|---|---|---|
| **Ground Slam** | 4, 10, 16, 22, 28 and so on | A blast: every square within 2 of where the Ogre stands when he announces it. Mark them. When it lands, roll 3d6 once; every hero who is up on a marked square takes it all. |
| **Skull Crusher** | 6, 11, 16, 21, 26 and so on | A heavy hit of 6d6 on the hero he went for this turn. It lands on that hero wherever they go. If he went for nobody this turn, or that hero is no longer up, he has no Crusher to announce. |
| **Boulder** | 2, 4, 6, 8, 10 and so on | Not announced. In his turn, after his attack, he throws a boulder at a random hero who is up, not hidden and not next to him (roll a die with one side for each). It hits for 2d6. If no hero fits, he throws nothing. |

Heroes can stop an announced move with **Disrupt**, or with a stun such as
**Cheap Shot**. Taunt cards make no difference to the boulder, and neither
the Ground Slam nor the boulder gives the Warden grit. The Skull Crusher
does.

### The shaman's mend

The shaman announces a **mend** in step 4 of the GM turn in rounds
2, 6, 10, 14, 18 and so on. In step 1 of the next GM turn it heals the
Ogre 25 HP (never past his full 150). It
does not happen if the shaman is dead, or is stunned, sapped or sheeped
when it is due, or if someone Disrupts it. A shaman who is stunned, sapped
or sheeped in step 4 announces nothing.

## What to say when the boss announces a move

Say it big, then point at the map. The heroes need to know what is coming,
where, and what they can do about it.

- **Ground Slam:** "The Ogre Warlord lifts his club high over his head,
  and the ground starts to shake! Next turn he SMASHES it down." Mark every
  square within 2 of him. "Anyone still in these
  squares takes the hit. Get out, or get behind the Warden's shield!"
- **Skull Crusher:** "The Ogre glares at (say the hero's name) and winds
  up a huge swing! Next turn it lands on you, wherever you run." Then:
  "Can anyone stop him? Disrupt him or stun him now, or brace yourself!"
- **The shaman's mend:** "The shaman starts to chant, and green light
  swirls around the Ogre. Next turn the Ogre heals 25
  HP, unless someone stops the shaman!"
- **Boulder** (not announced, it just happens): "The Ogre rips a boulder
  out of the ground and hurls it at (say the hero's name)!"

When a move lands, say what it did: "CRASH! Everyone on those squares takes
11." "The shaman's chant is broken, and the green light fades."

## The GM turn, step by step

1. **Land** the announced moves: the Ground Slam, the Skull Crusher, or the
   mend. Skip any that were broken, or whose enemy is stunned, sapped or
   sheeped.
2. **In round 10:** bring in the goblins.
3. **Each enemy acts,** in alphabetical order: brute, goblins, Ogre,
   shaman, wolves. Pick its target, move it, attack. A stunned, sapped or
   sheeped enemy does nothing. After the Ogre's attack, throw the boulder
   if it is due.
4. **Announce** the Ogre's next move and the shaman's mend, if due. Mark
   the Ground Slam's squares.
5. **Take one card** off every stack on every enemy: Taunt, stun, sap,
   sheep, rooted.

The party wins when every enemy is dead, goblins too.
