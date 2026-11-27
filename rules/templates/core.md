# The core rules

{# Every rule here must match what src/fastcombat/ does. If the engine
changes, change this too. #}

## 1. The idea

A fight is lots of quick rounds, about twenty. In each round the heroes all
move at once and then all act at once, and then the GM does the same with
every enemy. On your turn you do one thing: a quick attack, or one of your
hero's special abilities. Everyone rolls at the same time, so nobody waits
long.

Some words these rules use a lot:

- **Square**: one square of the grid map.
- **Next to**: any of the 8 squares around you, corners too.
- **HP**: hit points. When a hero's HP gets to 0, they are down.
- **Up**: a hero who is still in the fight. **Down**: at 0 HP and bleeding,
  but they can still be saved. **Out**: gone for the rest of the fight.
- **Ally**: another hero who is not out.
- **Card stack**: a little pile of cards that counts down, one card a
  round (section 6).

## 2. A round

A round is a **party turn**, then a **GM turn**.

**Before round 1,** a Rogue may sneak or Shadowstep in next to one enemy
(see the Rogue's sheet). That is the only thing that happens before the
first party turn.

### The party turn

1. **Top of the turn.** Everyone at once, in this order:
   1. **Cards.** Turn in one card from each stack you hold. Heal cards
      heal you first, and then poison cards hurt you. (Bleeding cards are
      different: they wait for the end of the turn.)
   2. **Resource.** Get back your mana or energy for the round.
   3. **Casts.** A cast that has finished lands now (section 4).
2. **Move.** Everyone moves at the same time, up to {rules.hero_move}
   squares. A stunned hero does not move.
3. **Act.** Everyone does one thing at the same time:
   - roll an auto-attack,
   - use one ability (it takes the place of your auto-attack),
   - keep casting a cast or a channel you have going, or
   - haul a downed hero next to you back up (section 9).

   A stunned hero does not act (section 6, "Stunned heroes").
4. **End of the turn.** Every downed hero takes one Bleeding card off,
   and every stunned hero one stun card.

### The GM turn

1. **Casts land.** Enemy casts the GM announced last GM turn happen now.
2. **New enemies arrive,** if the fight says some come in this round.
3. **Enemies act.** One at a time, each enemy picks who to attack
   (section 8), moves, and attacks. If the fight says a throw is due, the
   boss throws in its own turn, right after its attack, before the next
   enemy takes its turn.
4. **Announce.** The GM announces any new enemy casts, and marks their
   areas on the map.
5. **Enemy cards.** One card comes off every stack on every enemy.

### Who goes first

Heroes move at the same time and act at the same time. When it matters who
goes first (two heroes want the same square, or one hero's action changes
what another can do), heroes go in this order: **Druid, Guardian, Mage,
Rogue**. Two heroes of the same kind go in the order they joined the
party. For example, the Druid acts before the Guardian, so when the
Guardian is stunned, the Druid can Cleanse him before his act step comes.
Enemies take their turns in alphabetical order of their names
(brute, goblins, ogre, shaman, wolves), and two of the same kind go by
their number.

A hero who gets up in the middle of the party turn joins in at once: if
their own move or action has not come yet, they still get it. So a hero
the Druid heals back up in the act step still acts that turn, because the
Druid goes first.

### One round, worked out

{# This example takes some things from the test fight as they are now: the
round is the one after the Ground Slam is announced, no boulder is due in
it, and no goblins come in it. If a retune changes that, change the story
too. #}

This is round {boss.ground_slam.first + 1} of a fight with all four heroes,
the Ogre Warlord (the boss) and one wolf. The heroes are told in their
order: Druid, Guardian, Mage, Rogue.

At the end of the last GM turn the Ogre **announced a Ground Slam**, so
the GM marked every square within {boss.ground_slam.radius} of him. The
Ogre has no Taunt cards. The Guardian is next to the Ogre, inside the marked
squares. The wolf went for the Mage last turn and bit her for
{enemy.wolf.damage}, so she has {heroes.mage.hp - enemy.wolf.damage} of her
{heroes.mage.hp} HP. The Mage started a Firebolt on the Ogre last turn. The
Rogue is **not hidden**: she came out of hiding when she attacked earlier
in the fight. The Guardian still has 2 Rejuvenation heal cards.

**Top of the turn.**

- Cards: the Guardian turns in a heal card and heals
  {abilities.rejuvenation.value} HP. He has 1 heal card left.
- Resource: the Druid gets back {heroes.druid.regen} energy (never more
  than {heroes.druid.pool}), the Mage {heroes.mage.regen} mana (never more
  than {heroes.mage.pool}), and the Rogue {heroes.rogue.regen} energy
  (never more than {heroes.rogue.pool}). The Guardian's grit does not come
  back this way.
- Casts: the Mage's Firebolt lands. She rolls {abilities.firebolt.dice}
  and gets 15, so the Ogre loses 15 HP. She pays the
  {abilities.firebolt.cost} mana for it now.

**Move.** Everyone at once.

- The Druid stays where she can reach everyone
  ({abilities.rejuvenation.range} squares).
- The Guardian steps {boss.ground_slam.radius + 1} squares away from the
  Ogre, out of the marked squares.
- The Mage steps back.
- The Rogue steps next to the wolf.

**Act.** Everyone at once, but told in order.

- The Druid: **Nourish** on the Mage. She rolls {abilities.nourish.dice}
  and gets the top face. That is more than the {enemy.wolf.damage} HP the
  Mage is missing, so the Mage heals {enemy.wolf.damage} HP and is back to
  her full {heroes.mage.hp} (a heal never goes past full HP). The top face
  also gives the Druid {abilities.nourish.alt} energy back.
- The Guardian: the Ogre has no Taunt cards, and standing next to a boss
  does not hold it, so nothing keeps the Ogre on him. He uses
  **Taunt** on it (it reaches {abilities.taunt.range} squares), so
  the Ogre gets {abilities.taunt.cards} Taunt cards. He pays
  {abilities.taunt.cost} grit.
- The Mage: an **auto-attack** on the wolf with her d{heroes.mage.die}.
  She rolls a {heroes.mage.die}, the top face: a crit! She rolls again and
  gets a 2, so the hit is {heroes.mage.die + 2}. The wolf had
  {enemy.wolf.hp} HP and now has {enemy.wolf.hp - heroes.mage.die - 2}. A
  Mage's auto-attack that hits gives her {heroes.mage.auto_gain} mana, and
  the crit gives her {heroes.mage.crit_gain} more.
- The Rogue: the wolf is busy with someone else (it went for the Mage), so
  she can **Backstab** it. She rolls {abilities.backstab.dice} and gets a 5
  and a 3, so {5 + 3}. She is not hidden, so it is not made bigger. The
  wolf is down to {enemy.wolf.hp - heroes.mage.die - 2 - 5 - 3} HP. She
  gets {rules.combo_per_hit} combo point.

**End of the turn.** Nobody is down, so there are no Bleeding cards to
take off.

**GM turn.**

1. The Ground Slam lands. The GM rolls {boss.ground_slam.dice} once and
   gets 11. Every hero still on a marked square takes 11. Nobody is there.
2. No new enemies come in this round.
3. The Ogre goes first (alphabetical order). It has Taunt cards, so it
   must go for the Guardian. It moves up to {enemy.ogre.move} squares to him
   and hits for {enemy.ogre.dice}: the GM rolls a 3 and a 5, and adds
   {enemy.ogre.bonus}, so {3 + 5 + enemy.ogre.bonus}. The Guardian loses
   {3 + 5 + enemy.ogre.bonus} HP, and gains {rules.grit_per_attack} grit
   for being attacked. Then the wolf: no Taunt cards, it is not next to
   the Guardian, and nobody pulled it, so it goes where wolves like to go,
   the back line. It runs at the Mage and bites her for
   {enemy.wolf.damage}.
4. Nothing new is announced this round.
5. One Taunt card comes off the Ogre. It has
   {abilities.taunt.cards - 1} left.

Next round the wolf, with {enemy.wolf.hp - heroes.mage.die - 2 - 5 - 3} HP
left, will not last long.

## 3. Auto-attacks and abilities

### Auto-attacks

An auto-attack is your quick, steady attack. Roll your hero's die against
one enemy in reach:

| Hero | Die | Reach |
|---|---|---|
| Guardian | d{heroes.guardian.die} | {heroes.guardian.attack_range} (next to you) |
| Rogue | d{heroes.rogue.die} | {heroes.rogue.attack_range} (next to you) |
| Druid | d{heroes.druid.die} | {heroes.druid.attack_range} squares |
| Mage | d{heroes.mage.die} | {heroes.mage.attack_range} squares |

- A **1 misses.** No damage.
- The **top face is a crit.** Roll the die again and add it. If that is
  the top face too, keep going. A Guardian who rolls {heroes.guardian.die},
  then {heroes.guardian.die}, then 3 hits for
  {heroes.guardian.die + heroes.guardian.die + 3}.
- Anything else hits for what it shows. There is no roll to hit and no
  roll to dodge.
- A crit also gives your hero a **crit bonus**: the Guardian gets
  {heroes.guardian.crit_gain} grit, the Rogue {heroes.rogue.crit_gain} extra
  combo point, the Druid {heroes.druid.crit_gain} Seed, and the Mage
  {heroes.mage.crit_gain} mana.
- The Mage also gets {heroes.mage.auto_gain} mana back from each auto-attack
  that does not miss, crit or not. Her auto-attack is weak, but it keeps
  her mana coming.

### Abilities

Abilities are your hero's special moves, listed on your sheet.

- An ability **never misses and never crits**. Roll the dice it says and
  add any bonus.
- Using one is your whole action for the turn.
- You can only use an ability if you can pay for it, the target is in
  range, and the ability's own rule allows it (for example, Sap only works
  while you are hidden).
- **Range** is counted in squares, the same way as moving. Range 1 means
  next to you. An ability with no range is used on yourself or around you.
- **You pay when it happens.** An instant ability is paid for at once, a
  cast when it lands, and a channel one hit at a time.

### Enemy attacks

Enemies do not roll for their attacks: each kind hits for a set number. A
boss is the exception: it rolls dice. There is no armour. A tough hero just
has more HP. A few cards take a set number off a hit (Guarded and
Shield Plant); that is the only taking away in the game.

## 4. Casts and channels

Your sheet says how long each ability takes:

- **Instant:** it happens in your act step, right away.
- **Cast, N rounds:** it takes N act steps, and then it lands.
- **Channel:** it hits once in each act step, for a few turns.

### Casts

- You start a cast in your act step. That is the first of its act steps.
  On each later turn your action is "keep casting", until you have spent
  all its act steps.
- It **lands at the top of the next party turn**, after cards and
  resource, before anyone moves.
- So a 1-round cast (like Firebolt) is started this turn and lands at the
  top of the next one, and you are free to act again in that turn. A
  2-round cast (like Meteor) is started this turn, you keep casting next
  turn, and it lands at the top of the turn after that.
- **Stand still** while a cast is going. You may move on the turn you
  start it, because you move before you act.
- A cast lands on its target wherever the target is by then, even if it
  has moved out of range. A cast that hits an area has its squares marked
  on the map when you start it, and they do not move.
- If the target is dead or out by then, or you cannot pay, the cast
  fizzles. It costs nothing.

### Channels

- A channel hits for the first time in the act step you start it, and
  once more in each act step after that while you keep channelling, until
  it has made all its hits.
- Pay for each hit as it happens.
- You **may move** while channelling, unless your sheet says to stand
  still (the Mage's Evocation): then moving ends it.
- Each hit needs its target in range at that moment. If it is not, or you
  cannot pay, the channel ends.

### Stopping a cast or a channel

- **Cancelling:** in any turn you may stop. Moving ends a cast (not a
  channel). Doing anything else in your act step ends either one. A
  cancelled cast costs nothing: you only lose the time.
- **What breaks a cast:** going down, or being stunned. Plain damage
  never breaks a cast or a channel.

Enemies cast too: see section 10.

## 5. Resources

Every hero has a resource that pays for their abilities.

| Hero | Resource | Most you can hold | At the start | Gets back |
|---|---|---|---|---|
| Guardian | grit | {heroes.guardian.pool} | {heroes.guardian.start} | {rules.grit_per_attack} each time an enemy attacks him |
| Rogue | energy | {heroes.rogue.pool} | {heroes.rogue.start} | {heroes.rogue.regen} at the top of each party turn |
| Druid | energy | {heroes.druid.pool} | {heroes.druid.start} | {heroes.druid.regen} at the top of each party turn |
| Mage | mana | {heroes.mage.pool} | {heroes.mage.start} | {heroes.mage.regen} at the top of each party turn, and {heroes.mage.auto_gain} for each auto-attack that does not miss |

- You never go above the most you can hold.
- A downed hero gets nothing back.
- Crits give a little extra (section 3).
- **Grit** comes when an enemy attacks the Guardian: its normal attack, or a
  heavy hit it announced. He gets the grit even if the hit is made smaller
  or does no damage at all. A blast, a boss's throw and poison are not
  attacks on him and give no grit. Grit does not come back at the top of
  the turn.

Two heroes also keep a count of something:

- **Combo points** (Rogue), at most {rules.combo_max}. She gets
  {rules.combo_per_hit} for each auto-attack die that hits, and
  {heroes.rogue.crit_gain} more for a crit. A Backstab gives
  {rules.combo_per_hit} too. Eviscerate and Kidney Shot spend them all.
- **Seeds** (Druid), at most {rules.seeds_max}. She gets one each time a
  Regrowth lands and one from an auto-attack crit. Swiftmend spends one.

Keep these with coins, beads or a die.

## 6. Cards

Everything that lasts is a **stack of cards** on whoever has it. Put the
stack by the mini, or in front of the player. One card comes off each
round. When the last card is gone, the effect is over. Heals over time
work this way: the Druid hands an ally {abilities.rejuvenation.cards} heal
cards, and the ally turns in one at the top of each party turn.

### When cards come off

- **Hero cards:** one from each stack at the **top of the party turn**. A
  heal card heals and a poison card hurts as it is turned in.
- **Bleeding cards and stun cards:** at the **end of the party turn**
  instead, after everyone has acted. So everyone gets a whole turn to
  save a downed hero, and a stun from the GM turn costs the party turn
  after it.
- **Enemy cards:** one from each stack at the **end of the GM turn**.

This means a card handed out in the party turn always covers the whole GM
turn that follows:

- On a hero, it comes off at the top of the next party turn. A 1-card
  stack, like Guarded or Last Stand, covers exactly one GM turn.
- On an enemy, it comes off at the end of the GM turn. So
  {abilities.taunt.cards} Taunt cards cover {abilities.taunt.cards}
  GM turns.
- Heal cards handed out in the act step heal for the first time at the top
  of the next party turn.

### Rules for stacks

- A new stack of the same kind **takes the place of the old one**. A new
  Rejuvenation on an ally replaces the one they had; it does not add to
  it.
- **Taunt, stun, sap and sheep** never get shorter: if the enemy already
  has as many of those cards or more, it keeps the ones it has.
- Different kinds are different stacks. An ally can hold Rejuvenation heal
  cards and Wild Growth heal cards at the same time, and both heal.
- **Going down wipes every card you hold**: heal cards, Guarded,
  poison, cooldowns, all of them. Then you take Bleeding cards (section
  9).
- **Cooldowns** use cards too. Disrupt has one, and so do Shield Slam, Ice
  Block and Evocation. When you use one, put its cooldown cards on it
  (Disrupt: {abilities.disrupt.cooldown}). You cannot use it while any are
  there. They come off like your other cards, so a hero who Disrupts in
  round 1 can Disrupt again in round {1 + abilities.disrupt.cooldown}. A
  channel (Evocation) puts its cooldown cards on when it starts, not again
  on later rounds.

### Stunned heroes

The ogre's Stomp stuns heroes. A **stunned** hero holds stun cards:

- You **do not move and do not act** in the party turn. The only thing a
  stunned hero may do is the Mage's Ice Block.
- Being stunned ends your cast or channel.
- Stun cards come off at the **end of the party turn**, like Bleeding. So
  a 1-card stun handed out in the GM turn costs you exactly the next
  party turn.
- The Druid's **Cleanse** takes a stun off. She acts before the others,
  so if she Cleanses you in the act step, you still act that turn (your
  move step has gone by). A stunned Druid cannot Cleanse herself.

[`cards.md`](cards.md) lists every card.

## 7. Moving and the grid

- **Every step costs 1, corners too.** The distance between two squares is
  the bigger of the gap across and the gap up and down. Three across and
  five down is five squares.
- **Heroes move** up to {rules.hero_move} squares in the move step. You
  may go past anyone, but you must stop on an empty square on the map.
- **Enemies walk around** everyone: no enemy can pass through a hero or
  another enemy. An enemy walks toward the hero it is after, up to its
  move, and stops once that hero is in reach of its attack. If the way is
  blocked, it gets as close as it can.
- A downed hero still takes up their square. A hero who is out is taken off
  the map.
- **No opportunity attacks.** You can walk right past an enemy. The
  Guardian's hold (section 8) does that job.
- **Areas** are square blocks. An area "within 2" of a square is every
  square 2 or fewer steps from it: a block 5 squares across. "Within 1" is
  the 3 by 3 block around it.
- Some abilities put someone on a square without walking (Intercede,
  Shadowstep, Blink, Grip). They happen in the act step, go past
  anyone, and land on an empty square.

## 8. Who enemies attack

Nobody keeps track of anger or threat. Each enemy picks who to attack at
its own turn, with this list. Read from the top: the first rule that names
a hero who is up and not hidden wins.

1. **Taunt cards.** An enemy with Taunt cards must go for the Guardian,
   wherever he is.
2. **A pull.** An enemy pulled by a hero goes for that hero.
3. **The hold.** An enemy standing next to the Guardian must attack the
   Guardian, and cannot move away. **Bosses ignore the hold.**
4. **What it likes.** Otherwise each kind of enemy goes for whoever it
   likes best: the **nearest** hero, the **back line** (the hero with the
   fewest max HP who is not the Guardian; if the Guardian is the only hero who
   is up and not hidden, it goes for him), or a **random** hero (see
   below). The fight sheet says which. Ties go to the hero first in
   alphabetical order.

**Picking a random hero.** Number the heroes who can be picked, 1, 2, 3
and so on, in alphabetical order. Roll a die with at least that many
sides, and roll again if it shows a number with no hero. With three
heroes, roll a d4 and roll again on a 4. With only one, there is nothing
to roll.

Then one last check: if the hero it picked holds a **Guarded card from
Intercede**, and the enemy has no Taunt cards, the Guardian steps in and is
attacked instead.

"The Guardian" means a Guardian who is up. With two Guardians, it is the first
one on the party list who is up. If no Guardian is up, Taunt cards and the
hold do nothing.

### Taunt cards

The Guardian's Taunt and Challenging Shout put Taunt cards on enemies. Taunt cards
are the only thing that keeps a boss on the Guardian.

### Loud

Some big abilities are **Loud**. Your sheet says which.

- A Loud hit on an enemy **with Taunt cards** takes Taunt cards off it:
  a boss loses {rules.boss_loud_cards}, and any other enemy loses 1.
- A Loud hit on an enemy **with no Taunt cards** pulls it: on its next
  turn it goes for you, even if it is next to the Guardian.
- It still counts as Loud if a shield turned the whole hit aside. It does
  nothing if the hit killed the enemy.
- A **Loud heal** (Regrowth) pulls every enemy that has no Taunt cards and
  is not held by the Guardian. A boss is pulled if it has no Taunt cards.
- Auto-attacks are never Loud.

### Pulls

- A pull lasts for the enemy's next turn only. Put a small marker by the
  enemy pointing at the hero, and take it away after the enemy's turn.
- A pull beats the hold: a pulled enemy walks away from the Guardian.
- A pull by a hero who is down, out or hidden counts for nothing.
- The Rogue's Vanish and the Druid's Shadowmeld drop every pull on you.
- A stunned, sapped or sheeped enemy loses its pull.

### Hiding

- The Rogue starts every fight hidden, and Vanish hides her again.
- No enemy can pick a hidden hero, by any rule.
- Blasts still hit a hidden hero standing in the area: they are aimed at
  squares, not at heroes.
- If every hero who is up is hidden, the enemies have nobody to go for:
  they do not move or attack.
- A Mage in an **Ice Block** counts as hidden for all of this, and more:
  nothing can hurt her, a blast neither.

### Bosses

- Only Taunt cards make a boss attack the Guardian. Standing next to it does
  not.
- A boss with no Taunt cards goes where its kind likes. The Ogre Warlord
  goes for the back line.
- A boss can be pulled by a Loud hit, like anyone.
- A boss's answer to the Guardian is big announced moves, aimed where it
  hurts (section 10).

## 9. Going down

- At 0 HP a hero is **down**. Lay the mini on its side. You lose your
  cast, your hiding and every card you hold, and you take a stack of
  {rules.bleeding_cards} **Bleeding cards**, one fewer for each Wound you
  have.
- While down you cannot act, enemies ignore you, and nothing can hurt you.
  You still take up your square.
- At the **end of each party turn**, after everyone has acted, a downed
  hero takes one Bleeding card off. When the last one is gone, you are
  **out** for the rest of the fight. Take the mini off the map.
- Most heroes go down in the GM turn, and then they have
  {rules.bleeding_cards} party turns to be saved. A hero who goes down in
  the party turn (to poison, say) loses the first Bleeding card at the end
  of that same turn.

### Getting up

- **Any heal** gets a downed hero up, on as much HP as the heal. Swiftmend,
  Regrowth and Nourish can do it. (Rejuvenation and Wild Growth only go on
  a hero who is up.)
- **Haul up:** any hero next to a downed hero can spend their action to
  haul them up, on {rules.haul_up_hp} HP. No healer needed.
- A hero who is out cannot be healed or hauled up.

### Wounds

Each time you get up, take a **Wound card** and keep it for the rest of the
fight. Each Wound makes your Bleeding stack one card shorter the next time
you go down:

| Wounds you have | Bleeding cards when you go down |
|---|---|
| 0 | {rules.bleeding_cards} |
| 1 | {rules.bleeding_cards - 1} |
| 2 | {rules.bleeding_cards - 2} |

With {rules.bleeding_cards} Wounds, going down puts you straight out.

### Winning and losing

- The party **wins** when every enemy is dead and no more are coming.
- The party **loses** when no hero is up: every hero is down or out at the
  same moment.
- A fight that drags on past round {rules.max_rounds} counts as lost. (A
  normal fight is over long before that.)

## 10. Enemies

### Kinds of enemy

- **Fodder:** any hit of 1 or more kills it. The goblins are fodder.
- **Normal:** real HP, like heroes. Most enemies are these.
- **Shielded** is a rare extra, not a kind. A shielded enemy ignores any
  single hit smaller than its shield number; a hit that big or bigger does
  all its damage.
- **Boss:** a full set of numbers, rolls dice for its attacks, and
  announces its big moves (below).

### Stuns, saps, sheep and roots

- A **stunned, sapped or sheeped** enemy does nothing on its turn: no
  move, no attack. It forgets any pull, and a cast it announced never
  lands.
- Sap and sheep end the moment the enemy takes any damage. A hit a shield
  turned aside does no damage, so it does not wake them. A sap lasts
  {abilities.sap.cards} rounds and a sheep {abilities.polymorph.cards}
  rounds, so it pays not to hit them while anything else is left.
- A **rooted** enemy cannot move, but still attacks if a hero is in reach.
- **Bosses cannot be stunned, sapped or sheeped**, but a stun still breaks
  the cast a boss has announced. A boss can be rooted.

### Announced casts

The boss, and some other enemies, have big moves that they **announce one
GM turn early**. The GM says what is coming in step 4 of the GM turn, and
marks any area on the map. It lands in step 1 of the next GM turn. That
gives the heroes one party turn to get out of the way, get ready (Shield Plant,
Last Stand), or break it (Disrupt, or a stun such as Cheap Shot).
Every hero has Disrupt. It reaches an enemy next to you, and the Mage's
reaches {abilities.disrupt.alt} squares.

- A **blast** hits the marked squares. The GM rolls once, and every hero
  who is up and still on a marked square takes all of it, hidden heroes
  too. Walk out and you are safe.
- A **stomp** is a blast on the squares next to the boss that also hands
  every hero it hits stun cards. A stomp counts as a blast: it gives the
  Guardian no grit.
- A **heavy hit** is aimed at one hero, and lands on that hero wherever
  they go, if they are still up. Hiding does not stop it. It counts as an
  attack, so the Guardian gets grit for it.
- A **mend** heals the boss.
- An enemy with a cast already waiting does not announce another.
- A cast never lands if the enemy is stunned, sapped or sheeped when it
  is due, or if it was broken.

### Throws

A boss may also **throw** something in its own turn, right after its
attack and before the next enemy takes its turn. A throw is not
announced. It goes at a random hero who is up, not hidden and not
next to the boss. Taunt cards make no difference, and it is not an attack
on the Guardian, so it gives him no grit.

## 11. Quick reference

| | |
|---|---|
| **Party turn** | 1. Top: cards (heals, then poison), then resource, then casts land. 2. Move (up to {rules.hero_move}). 3. Act (one thing). Stunned heroes do neither. 4. End: downed heroes take one Bleeding card off, stunned heroes one stun card. |
| **GM turn** | 1. Announced casts land. 2. New enemies arrive. 3. Each enemy picks, moves, attacks; the boss throws in its own turn, right after its attack. 4. Announce new casts. 5. One card off each enemy stack. |
| **Order** | Heroes: Druid, Guardian, Mage, Rogue. Enemies: alphabetical. |
| **Auto-attack** | One die. 1 misses. Top face rolls again and adds, and gives the crit bonus. |
| **Abilities** | Never miss, never crit. Pay when it happens. |
| **Casts** | Land at the top of a party turn. Stand still. Cancelled or broken costs nothing. |
| **Channels** | One hit each act step. May move. Pay each hit. |
| **Cards** | Hero cards: top of party turn. Bleeding and hero stuns: end of party turn. Enemy cards: end of GM turn. A new stack replaces the old (Taunt, stun, sap and sheep never get shorter). |
| **Who enemies attack** | Taunt cards, then a pull, then the hold (not bosses), then what it likes. Guarded from Intercede sends it to the Guardian. Hidden heroes are never picked. |
| **Loud** | Takes Taunt cards off (a boss loses {rules.boss_loud_cards}, any other enemy 1), or pulls an enemy with none. |
| **Moving** | Corners cost 1. No opportunity attacks. Enemies walk around bodies. |
| **Going down** | {rules.bleeding_cards} Bleeding cards, one fewer per Wound. Any heal or a haul up ({rules.haul_up_hp} HP) gets you up, and gives you a Wound. |
| **Losing** | No hero is up. |

| Hero | HP | Die | Resource | Most | Start | Back each round |
|---|---|---|---|---|---|---|
| Guardian | {heroes.guardian.hp} | d{heroes.guardian.die} | grit | {heroes.guardian.pool} | {heroes.guardian.start} | {rules.grit_per_attack} each time attacked |
| Rogue | {heroes.rogue.hp} | d{heroes.rogue.die} | energy | {heroes.rogue.pool} | {heroes.rogue.start} | {heroes.rogue.regen} |
| Druid | {heroes.druid.hp} | d{heroes.druid.die} | energy | {heroes.druid.pool} | {heroes.druid.start} | {heroes.druid.regen} |
| Mage | {heroes.mage.hp} | d{heroes.mage.die} | mana | {heroes.mage.pool} | {heroes.mage.start} | {heroes.mage.regen}, and {heroes.mage.auto_gain} for each auto-attack that hits |
