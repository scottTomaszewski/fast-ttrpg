# Fast combat: design

Date: 2026-11-24. Status: approved by the owner on 2026-11-24 (after a skim).

Things marked **(call)** were proposed by the assistant and not yet argued
over. Everything else was decided by the owner in conversation.

## Why

Tabletop combat is a slog because each turn is expensive and everyone waits.
This game makes a round cheap, so a fight is about 20 quick rounds instead of
3 slow ones. The model is MMO combat: a steady "auto-attack" that everyone
rolls at the same time, with special abilities as the spotlight moments.

Cheap rounds make MMO-style abilities possible: cast times, channels, heals
over time, stuns, interrupts, taunts. A 1-round stun is tolerable when there
are 20 rounds.

This is its own small game, not a layer on 5e.

## Goals

- A normal round takes one to two minutes at the table.
- A normal fight lasts about 20 rounds.
- Players roll often and at the same time.
- Each class has a small kit, and every button feels iconic and heroic
  (except plain shared tools like the interrupt).
- A real tank, with taunts that work, and no aggro numbers for anyone to track.
- Healing is interesting, built on heals over time.
- Anything that lasts is tracked with cards, not memory.

## Not goals (for now)

- Rules for anything outside combat.
- Levelling, gear, character creation beyond "pick one of four classes".
  (Where it is heading is in "Later: talents".)
- Balancing for a party with no healer. The rules allow it (anyone can get
  a downed hero up) but the first tuning pass assumes one of each class.
- More than one test fight.
- Publishing. The rogue uses WoW ability names, which is fine for a home
  table and would need changing before sharing widely.

## What would make it a failure

- The GM has to track threat or aggro.
- Rounds get slow because of per-round chores or arithmetic.
- Auto-attack rolls that change nothing.
- Kits so big that players read their sheet instead of playing.

## The engine

### Round

A round is a party turn, then a GM turn.

**Party turn**

1. **Top of turn.** Everyone at once: turn in one card from each stack you
   hold (a heal card heals you), regain mana or energy, and any cast that has
   finished now lands. **(call: the order is cards, then resource, then casts.)**
   Bleeding cards are the exception: they come off at the end of the party
   turn, after everyone has acted.
2. **Move.** Everyone moves at the same time.
3. **Act.** Everyone at once does one thing: roll an auto-attack, use an
   ability, or keep casting. An ability replaces the auto-attack.
   **(call: exactly one action per turn; no bonus actions.)**

**GM turn**

1. Announced enemy casts from the last GM turn now land.
2. Enemies move and attack.
3. The GM announces any new casts and marks their area on the grid.
4. Discard one card from each stack on each enemy (taunt, stun, sap, sheep).
   **(call: at the end, so a 1-card effect covers one whole GM turn and
   Challenge's 3 cards cover three.)**

### Auto-attack

- One damage die. No roll to hit.
- A 1 is a miss.
- The top face is a crit. Roll the die again and add it; if that is the top
  face too, keep going. **(call on the exact form; the owner wants crits to
  do more damage.)**
- A crit also triggers the class's hook **(all calls)**: Warden gains 1 Grit;
  Rogue gains 2 combo points instead of 1; Druid gains a Seed; Mage gains
  2 mana.
- Classes have different dice.
- Abilities roll dice for damage and healing but never miss and never crit.
  Talents may change that later.

### Abilities, casts and channels

- **Instant:** happens in the act step.
- **Cast (N rounds):** you spend N act steps casting and it lands at the top
  of the party turn after the last one. You may move on the turn you start,
  then must stand still until it lands. **(call on the exact timing)**
- **Channel:** takes effect each turn in the act step, for a set number of
  turns. You may move while channelling.
- A hero can cancel their own cast or channel in any act step and do
  something else that turn instead. **(call)** The cost is paid when a cast
  lands (per hit for a channel), so a cancelled or broken cast loses only
  the time.
- Enemies get the GM turns in between to stop a cast or a channel.
- **(call)** A hero's cast is broken by a stun, by forced movement, or by an
  enemy ability that says it interrupts. Plain damage does not break it.

### Resources

- **Mana:** pool of 30, +1 per round. (Mage.)
- **Energy:** pool of 10, +3 per round. (Rogue, Druid.)
- **Grit (call):** the Warden starts at 0 and gains 1 each time an enemy
  attacks them, up to 10. If the owner prefers only two resource types, the
  Warden becomes an energy class.
- **(call)** Cooldowns are kept rare, because the owner is wary of the
  tracking. Cost is the normal limit on an ability. Where a cooldown is
  truly needed (Disrupt is the only one so far) it uses the same countdown
  card stack as everything else, placed on the ability, so it is not a new
  kind of bookkeeping. If it still feels like a chore at the table, the
  fallback is to give Disrupt a resource cost instead.

### Cards

Every lasting effect is a small stack of cards on whoever has it. One card
comes off per round; when the stack is empty the effect is over. Heals over
time are the model: the healer hands an ally 4 "heal N" cards and the ally
turns one in at the top of each party turn.

Hero-side stacks tick at the top of the party turn, except Bleeding cards,
which come off at the end of the party turn. Enemy-side stacks tick at the
end of the GM turn.

### Defence

Armour is just more HP. A few abilities reduce damage by a flat amount for a
round; that is the only subtraction in the game.

### Grid

The owner wants a grid and maps.

- **(call)** Every square costs 1, diagonals included.
- **(call)** No opportunity attacks. The tank's hold does that job.
- **(call)** Areas of effect are simple shapes. An enemy cast's area is marked
  on the map when it is announced, and stays until it lands.

### Who enemies attack

No one tracks aggro.

- **Weak hold:** an enemy that starts the GM turn next to the Warden (any of
  the 8 squares around them) cannot move away and must attack the Warden.
- **Strong hold:** an enemy with Taunt cards on it must target the Warden,
  wherever it is.
- **Loud abilities (call):** some big abilities are marked Loud. Hitting an
  enemy with one removes one Taunt card from it. If it has none, it targets
  that hero on its next turn, even if it is next to the Warden.
  Auto-attacks are never Loud. A Loud heal
  pulls every enemy that has no hold on it.
- An enemy with no hold and no pull is the GM's to direct.
- Bosses obey taunts. Their answer is big announced casts aimed elsewhere and
  heavy hits on the tank.

### Going down

The owner wants "get him up now!" urgency, no yo-yo (down, up, down, up at no
cost), and a party that can cope without a healer. The mechanism below is
the assistant's proposal. **(call)**

- A hero at 0 HP is **down** and takes a stack of 3 Bleeding cards. One comes
  off at the end of each party turn, after everyone has acted. When the stack
  is empty the hero is **out** for the rest of the fight.
- **Getting someone up:** any heal does it. So does any hero standing next to
  them who spends their action to haul them up, which leaves them on a small
  amount of HP. No healer is needed.
- **Each time a hero gets up they keep a Wound card.** The next time they go
  down, their Bleeding stack is one card shorter per Wound. Third time down
  there is one round to save them; a fourth is straight out.
- A hero who is down cannot act and enemies ignore them.
- The fight is lost when every hero is down or out.

### Stuns and long control

- **(call)** Bosses cannot be stunned, sapped or sheeped, but a stun still
  breaks the cast they are in the middle of.
- Sap and Polymorph break the moment the target takes any damage.

### Enemies

- Enemies do not roll damage; an attack is a fixed number. **(call)**
- **Fodder:** any hit kills.
- **Normal and elite:** real HP. Most enemies are these.
- **Shielded** is a rare trait, not a tier: the enemy ignores any single hit
  below a number.
- **Boss:** a full stat block, rolls dice, and announces its casts one GM turn
  before they land so they can be interrupted, dodged or soaked.

## The classes

Numbers are deliberately missing here. See "Numbers".

### Warden (tank). d8. Grit.

1. **Challenge:** put 3 Taunt cards on one enemy.
2. **War Cry:** one Taunt card on every enemy near you (1 GM turn).
3. **Intercede:** leap to an ally and give them a Guarded card (they take
   less damage this round). **(call)** Any enemy with no Taunt card that was
   going to attack that ally attacks the Warden instead.
4. **Chain Hook:** pull one enemy to a square next to you.
5. **Bulwark:** plant your shield. Allies in the squares behind you take
   reduced damage from one blast.
6. **Unbroken:** you cannot drop below 1 HP this round.

### Rogue. d6. Energy and combo points.

Auto-attack hit: 1 combo point. Crit: 2. Maximum 5. **(call)**

1. **Backstab:** cheap instant. Bonus damage and a combo point. Only on an
   enemy that is attacking someone else.
2. **Eviscerate:** finisher. Spend all combo points for damage per point. Loud.
3. **Kidney Shot:** finisher. Spend combo points to stun; 2 rounds at full.
4. **Cheap Shot:** small stun. Instant, low energy, 1 round.
5. **Sap:** takes one enemy out for several rounds; breaks on damage. Only
   from hiding (start of a fight, or right after Vanish).
6. **Shadowstep:** appear next to an enemy within range.
7. **Vanish:** cancel any pull on you and go into hiding. From hiding your
   next move is a hard opener or a Sap. **(call)** The opener is not a new
   button: a Backstab from hiding works on any enemy and does double damage.
   Hiding ends when you act.

### Druid (healer). d6 ranged. Energy and Seeds (hold 2).

The kit is modelled on the SWTOR Operative healer; the owner asked for a
fantasy theme and suggested druid. Names are placeholders. **(call on names)**

1. **Rejuvenation:** instant. An ally gets 4 heal cards. One per ally, no
   stacking.
2. **Regrowth:** 1-round cast, big heal, gives a Seed. Loud.
3. **Swiftmend:** instant heal, spends a Seed. Free on an ally below half HP.
4. **Wild Growth:** allies in an area get 2 heal cards each.
5. **Cleanse:** remove one harmful card from an ally.
6. **Shadowmeld:** drop any pull on you and move a few squares.
7. **Nourish:** replaces the auto-attack. Roll your die as a heal on an ally;
   the top face gives back energy. Costs nothing.

**(call)** A Seed also comes from an auto-attack crit.

The owner chose to leave out the Operative's other utility (stealth, stun,
flash bang and so on) to keep the class simple.

### Mage. d4. Mana.

1. **Arcane Volley:** channel. Three hits over three turns, moving freely.
   Each hit is Loud. **(call on Loud)**
2. **Firebolt:** 1-round cast, big single-target hit.
3. **Meteor:** 2-round cast. The area is marked when you start. Biggest
   damage in the game. Hits allies still standing there.
4. **Frost Ring:** instant. Enemies next to you cannot move for 2 rounds.
5. **Blink:** short teleport.
6. **Quicken:** the whole party rolls two auto-attack dice for 2 rounds.
7. **Polymorph:** 1-round cast. Target is a sheep for up to 4 rounds; breaks
   on damage. One at a time.

### Shared

**Disrupt:** the interrupt. Instant; breaks the cast of one enemy.
**(call)** Every class has it; it is melee range except for the Mage; it
has a 3-round cooldown.

## Numbers

No numbers are settled except the dice and the resource pools above. The
builder writes a first pass for everything else (hero HP, ability damage,
healing, costs, ranges, areas, enemy HP and damage) and then tunes it with
the simulator.

Tuning targets for the test fight, with heroes played sensibly:

- The fight lasts 18 to 22 rounds most of the time.
- The party wins most of the time, but not always (aim for roughly 4 in 5).
- No hero is out of resource for most of the fight, and none ends it full.
- The healer can keep up but has to work: someone gets dangerously low at
  least once in a typical fight.
- Every class's kit matters: removing any one hero makes the fight clearly
  harder.
- Auto-attacks are a real share of total damage but less than half.

**All numbers live in one data file.** The simulator reads it, and the class
sheets and cards are made from it, so a tuning change cannot leave the
printed rules out of step. **(call)**

## Party size

The owner's test table is four players, one of each class. Real tables may
be bigger. The first tuning pass targets four, one of each. The simulator
takes the party as a setting (which classes, how many) so other parties,
including one with no healer, can be tried later.

## Later: talents

Not built now, but the owner's plan for growth, so nothing should block it.
Heroes will pick talents that change an ability: add a rider effect, extend
a duration, shorten a cast, raise the dice size or count, turn a standing
cast into a channel, let an ability crit. Plain stat increases too.

What this asks of the build now: each ability's cast time, dice, duration,
cost and tags (Loud, channel, and so on) are entries in the numbers file,
not written into code, so a talent can later be "change these entries".

## The test fight

One boss with adds, built to exercise the engine. It must include:

- a boss with an announced area blast (dodge it, or stand behind Bulwark);
- an announced heavy hit on the tank (the Unbroken moment);
- an announced cast worth interrupting (for example an add that heals);
- an attack on a non-tank hero that taunts cannot stop (work for the healer);
- loose adds that go for the back line (work for Challenge, Chain Hook,
  Intercede);
- a wave of fodder (work for Meteor);
- one Shielded enemy;
- at least two adds present at the start, so Sap and Polymorph have targets.

The builder designs the specifics.

## Approaches considered

1. **Rules write-up only.** Engine and kits in one document, numbers left
   rough. Fastest, but the first session would be spent fixing numbers.
2. **Playtest kit.** Write-up, first-pass numbers, one test fight and
   printable cards. Numbers are educated guesses.
3. **Playtest kit with numbers checked first.** As 2, but a script plays the
   test fight many times before anything is printed.

**The owner picked 3.** In a 20-round game small number errors compound, and
the arithmetic can be checked cheaply before a real session. The simulator
can say whether the numbers are sound; it cannot say whether the game is fun.

## What gets built, in this order

1. **The simulator.** Python 3.12 with `uv`, tests with `pytest`. **(call)**
   It models the grid, the round, cards, holds and Loud, the four kits and
   the test fight. Heroes follow simple written-down behaviour (for example:
   the Warden keeps Challenge on the boss and hooks loose adds; the
   Druid keeps Rejuvenation on the Warden and casts Regrowth when someone is
   low).
   It runs a fight many times and reports length, win rate, lowest HP,
   resource levels over time, and each hero's share of damage and healing.
2. **Tuning.** Change the numbers file until the targets above are met.
3. **The rules, written out.** One rules document, one sheet per class, and
   the test fight, in plain words.
4. **Printable cards.** Heal, Taunt, Guarded, stun, sap, sheep, Bleeding, Wound, cooldown and
   harmful-effect cards, as a plain page that prints on ordinary paper.
   **(call on the format)**

After that the owner intends to ask for many more simulation runs, so the
simulator should be easy to run in bulk and to point at changed numbers or a
changed hero behaviour.

## Where it lives

`~/code/fast-ttrpg`. It will be pushed to a new GitHub repo later.

## Left to the builder

- Every number not fixed above.
- The exact squares for "near", "behind", ranges and area shapes.
- The specifics of the test fight.
- How heroes behave in the simulator, as long as it is written down and
  sensible.
- The layout of the sheets and cards.
- Hero and enemy movement speeds.
