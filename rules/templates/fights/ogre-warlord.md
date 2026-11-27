# The test fight: {fight.name}

This sheet is for the GM. It is one big fight that uses every rule in the
game: a boss who must be taunted, adds (extra enemies that fight
alongside the boss) that run for the back line, a healer to stop, a shielded brute, and a wave of goblins halfway through.

## The map

The map is **{fight.width} squares wide and {fight.height} tall**, with no
walls. The heroes start on the left, the enemies on the right.

```
{fight.map}
```

## The enemies

| Enemy | How many | HP | Attack | Reach | Move | Goes for |
|---|---|---|---|---|---|---|
| Ogre Warlord (boss) | {spawns.ogre.count} | {enemy.ogre.hp} | {enemy.ogre.dice} | {enemy.ogre.range} (next to it) | {enemy.ogre.move} | the back line |
| Brute (shielded {enemy.brute.shielded}) | {spawns.brute.count} | {enemy.brute.hp} | {enemy.brute.damage} | {enemy.brute.range} (next to it) | {enemy.brute.move} | the nearest hero |
| Shaman | {spawns.shaman.count} | {enemy.shaman.hp} | {enemy.shaman.damage}, and poison | {enemy.shaman.range} squares | {enemy.shaman.move} | a random hero |
| Wolf | {spawns.wolf.count} | {enemy.wolf.hp} | {enemy.wolf.damage} | {enemy.wolf.range} (next to it) | {enemy.wolf.move} | the back line |
| Goblin (fodder) | {spawns.goblin.count}, in round {spawns.goblin.round} | {enemy.goblin.hp} | {enemy.goblin.damage} | {enemy.goblin.range} (next to it) | {enemy.goblin.move} | the back line |

"The back line" is the hero with the fewest max HP who is not the Guardian:
the Mage ({heroes.mage.hp} HP) while she is up, then the Druid or the Rogue
({heroes.druid.hp} each; the Druid first, being first in alphabetical
order). If the Guardian is the only hero who is up and not hidden, they go
for him. Remember the order for every enemy (core rules, section 8): Taunt
cards first, then a pull, then the Guardian's hold (not the Ogre), then what
it likes.

- **Ogre Warlord.** The boss. He rolls {enemy.ogre.dice} for each hit. Only
  Taunt cards keep him on the Guardian: standing next to the Guardian does not.
  With no Taunt cards he goes after the Mage. He cannot be stunned, sapped,
  sheeped or Gripped, but a stun still breaks the move he announced,
  and Frost Nova can root him. His big moves are below.
- **Brute.** Big and slow. Shielded {enemy.brute.shielded}: any single hit
  under {enemy.brute.shielded} does nothing to him. He walks to the nearest
  hero, so he often ends up held by the Guardian.
- **Shaman.** Stands back and hits from {enemy.shaman.range} squares away.
  Each of his hits also gives the hero {enemy.shaman.poison_cards} poison
  cards worth {enemy.shaman.poison_value} each, unless the hit took them
  down. He picks a random hero each turn from the heroes who are up and
  not hidden: number them in alphabetical order, roll a die with at least
  that many sides, and roll again on a number with no hero (core rules,
  section 8). And he heals the Ogre (below).
- **Wolves.** Fast. They run straight past the Guardian for the Mage.
- **Goblins.** Fodder: any hit kills one. **{spawns.goblin.count} goblins
  come in at step 2 of the GM turn in round {spawns.goblin.round}**, on
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
| **Ground Slam** | {boss.ground_slam.rounds} | A blast: every square within {boss.ground_slam.radius} of where the Ogre stands when he announces it. Mark them. When it lands, roll {boss.ground_slam.dice} once; every hero who is up on a marked square takes it all. |
| **Skull Crusher** | {boss.skull_crusher.rounds} | A heavy hit of {boss.skull_crusher.dice} on the hero he went for this turn. It lands on that hero wherever they go. If he went for nobody this turn, or that hero is no longer up, he has no Crusher to announce. |
| **Boulder** | {boss.boulder.rounds} | Not announced. In his own turn, right after his attack and before the next enemy goes, he throws a boulder at a random hero who is up, not hidden and not next to him (pick one the way the shaman does). It hits for {boss.boulder.dice}. If no hero fits, he throws nothing. |

Heroes can stop an announced move with **Disrupt**, or with a stun such as
**Cheap Shot**. Taunt cards make no difference to the boulder, and neither
the Ground Slam nor the boulder gives the Guardian grit. The Skull Crusher
does.

### The shaman's mend

The shaman announces a **mend** in step 4 of the GM turn in rounds
{enemy.shaman.cast_rounds}. In step 1 of the next GM turn it heals the
Ogre {enemy.shaman.cast_heal} HP (never past his full {enemy.ogre.hp}). It
does not happen if the shaman is dead, or is stunned, sapped or sheeped
when it is due, or if someone Disrupts it. A shaman who is stunned, sapped
or sheeped in step 4 announces nothing.

## What to say when the boss announces a move

Say it big, then point at the map. The heroes need to know what is coming,
where, and what they can do about it.

- **Ground Slam:** "The Ogre Warlord lifts his club high over his head,
  and the ground starts to shake! Next turn he SMASHES it down." Mark every
  square within {boss.ground_slam.radius} of him. "Anyone still in these
  squares takes the hit. Get out, or get behind the Guardian's shield!"
- **Skull Crusher:** "The Ogre glares at (say the hero's name) and winds
  up a huge swing! Next turn it lands on you, wherever you run." Then:
  "Can anyone stop him? Disrupt him or stun him now, or brace yourself!"
- **The shaman's mend:** "The shaman starts to chant, and green light
  swirls around the Ogre. Next turn the Ogre heals {enemy.shaman.cast_heal}
  HP, unless someone stops the shaman!"
- **Boulder** (not announced, it just happens): "The Ogre rips a boulder
  out of the ground and hurls it at (say the hero's name)!"

When a move lands, say what it did: "CRASH! Everyone on those squares takes
11." "The shaman's chant is broken, and the green light fades."

## The GM turn, step by step

1. **Land** the announced moves: the Ground Slam, the Skull Crusher, or the
   mend. Skip any that were broken, or whose enemy is stunned, sapped or
   sheeped.
2. **In round {spawns.goblin.round}:** bring in the goblins.
3. **Each enemy acts,** in alphabetical order: brute, goblins, Ogre,
   shaman, wolves. Pick its target, move it, attack. A stunned, sapped or
   sheeped enemy does nothing. Right after the Ogre's attack, before the
   next enemy goes, throw the boulder if it is due.
4. **Announce** the Ogre's next move and the shaman's mend, if due. Mark
   the Ground Slam's squares.
5. **Take one card** off every stack on every enemy: Taunt, stun, sap,
   sheep, rooted.

The party wins when every enemy is dead, goblins too.
