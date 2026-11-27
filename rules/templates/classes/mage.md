# The Mage

The Mage stands far back and throws the biggest spells in the game. She can
also freeze enemies in place, turn one into a sheep, and hop out of
trouble.

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
- **You are the best at Disrupt:** yours reaches
  {abilities.disrupt.alt} squares. Break the shaman's mend and the boss's
  big moves.
- **Sheep the biggest add nobody is fighting** (an add is an extra enemy
  that fights alongside the boss), when there are at least two adds. Then
  leave it, and any sapped enemy, alone until nothing else is left: a hit
  wakes it. Never aim a Meteor where it would. **Meteor** a spot with four or more
  enemies and no heroes.
- **Otherwise Firebolt.** Hit the enemy casting a mend first, then the add
  with the least HP, and the boss last.
