# The Mage

The Mage stands far back and throws the biggest spells in the game. She can
also freeze enemies in place, turn one into a sheep, hop out of trouble,
freeze herself in a block of ice, and call her mana back.

- **HP:** {heroes.mage.hp}
- **Auto-attack:** d{heroes.mage.die}, on an enemy up to
  {heroes.mage.attack_range} squares away.
- **Resource:** mana. At most {heroes.mage.pool}, you start a fight with
  {heroes.mage.start}, and you get {heroes.mage.regen} back at the top of
  each party turn.
- **Crit bonus:** {heroes.mage.crit_gain} mana.
- **Mana from a hit:** each auto-attack that does not miss gives you
  {heroes.mage.auto_gain} mana, crit or not.

## Abilities

### Arcane Volley

- {abilities.arcane_volley.cost} mana for each hit ·
  {abilities.arcane_volley.timing} · range
  {abilities.arcane_volley.range}{abilities.arcane_volley.loud_tag}
- Hit one enemy for **{abilities.arcane_volley.dice}**, now and in each of
  your next act steps, for {abilities.arcane_volley.hits} hits in all. You
  may move while you channel. Each hit is paid for, and checks its range,
  when it happens.

### Firebolt

- {abilities.firebolt.cost} mana · {abilities.firebolt.timing} · range
  {abilities.firebolt.range}{abilities.firebolt.loud_tag}
- When it lands, hit one enemy for **{abilities.firebolt.dice}**.

### Meteor

- {abilities.meteor.cost} mana · {abilities.meteor.timing} · range
  {abilities.meteor.range}{abilities.meteor.loud_tag}
- Pick a square. Every square within {abilities.meteor.radius} of it is
  marked when you start. When it lands, roll **{abilities.meteor.dice}**
  once: every enemy in the area, and **every hero who is up in the area,
  you too**, takes all of it.

### Frost Nova

- {abilities.frost_nova.cost} mana · {abilities.frost_nova.timing} ·
  around you{abilities.frost_nova.loud_tag}
- Every enemy next to you gets **{abilities.frost_nova.cards} rooted
  cards**: it cannot move, but it can still attack if someone is in reach.
  It works on a boss too.

### Blink

- {abilities.blink.cost} mana · {abilities.blink.timing} · range
  {abilities.blink.range}{abilities.blink.loud_tag}
- Jump to an empty square, without walking there.

### Polymorph

- {abilities.polymorph.cost} mana · {abilities.polymorph.timing} · range
  {abilities.polymorph.range}{abilities.polymorph.loud_tag}
- When it lands, one enemy becomes a sheep: **{abilities.polymorph.cards}
  sheep cards**. It does nothing while it has them, but turns back the
  moment it takes any damage. Not on a boss. Only one sheep at a time:
  when a new Polymorph lands, any other sheep turns back.

### Ice Block

- {abilities.ice_block.cost} mana · {abilities.ice_block.timing} · yourself · cooldown
  {abilities.ice_block.cooldown}{abilities.ice_block.loud_tag}
- Freeze yourself in a block of ice: take **{abilities.ice_block.cards}
  Ice Block card**. While you hold it, nothing can hurt you (a blast or a
  heavy hit does you no harm, and nothing can stun you), no enemy can
  pick you as its target, and you cannot move or act. It comes off at the
  top of your next party turn, so it covers the GM turn that follows.
- Going into the ice takes **every bad card** off you (stun, poison,
  rooted and the like; not Bleeding, not cooldowns), and ends your own
  cast or channel.
- **You may use it while stunned:** it is the one thing a stunned hero
  can do.
- Then put {abilities.ice_block.cooldown} cooldown cards on Ice Block.

### Evocation

- {abilities.evocation.cost} mana · Channel, {abilities.evocation.hits} rounds · yourself ·
  cooldown {abilities.evocation.cooldown}{abilities.evocation.loud_tag}
- Call your mana back: get **{abilities.evocation.value} mana** now, and
  {abilities.evocation.value} more in your next act step if you keep
  channelling ({abilities.evocation.hits} rounds in all, never more than
  {heroes.mage.pool}).
- **Stand still** while you channel it: moving ends it. Taking damage does
  not. Doing anything else, or being stunned, ends it too.
- Then put {abilities.evocation.cooldown} cooldown cards on Evocation.

### Disrupt (every hero has this)

- {abilities.disrupt.cost} mana · {abilities.disrupt.timing} · range
  **{abilities.disrupt.alt}** for you (the others need to be next to the
  enemy) · cooldown {abilities.disrupt.cooldown}{abilities.disrupt.loud_tag}
- Break the cast an enemy has announced, so it never lands. Only on an
  enemy that has announced one. Then put {abilities.disrupt.cooldown}
  cooldown cards on Disrupt.

## How to play the Mage

- **Stand back.** Stay within {abilities.firebolt.range} squares of your
  target, but well back from every enemy. Stand still while you cast.
- **Something reached you? Frost Nova,** then step away next turn.
- **Ice Block is your last way out.** A big hit is coming at you that
  could take you to 0, and you cannot Disrupt it or walk out of it? Ice
  Block. Also when you are stunned, low, and an enemy is next to you.
- **Out of mana and nobody needs you?** Evocation: stand still and get it
  back. Not while an enemy is next to you, a blast is coming down on you,
  a cast needs your Disrupt, or the boss is loose.
- **You are the best at Disrupt:** yours reaches
  {abilities.disrupt.alt} squares. Break the shaman's mend and the boss's
  big moves.
- **Sheep the biggest add nobody is fighting** (an add is an extra enemy
  that fights alongside the boss), when there are at least two adds. Then
  leave it, and any sapped enemy, alone until nothing else is left: a hit
  wakes it. Never aim a Meteor where it would. **Meteor** a spot with four or more
  enemies and no heroes.
- **Arcane Volley is your everyday spell.** A whole Volley does about as
  much damage for its mana as a Firebolt. Its edge: you can move while it
  goes, and you can stop it part-way and keep the hits that already
  landed. The owner's words: "A mage can let the spell hit twice and then
  cancel the cast to skip the third hit to kick off another, more urgent
  spell or interrupt. Firebolt is more all-or-nothing." So when a cast
  needs your Disrupt, or an enemy reaches you, stop the Volley and do it.
- **Who to hit:** the enemy casting a mend first, then the add with the
  least HP, and the boss last. **Firebolt** instead of a Volley when one
  Firebolt would finish that add.
