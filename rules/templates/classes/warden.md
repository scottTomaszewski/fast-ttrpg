# The Warden

The Warden is the tank: a big shield and a bigger voice. He makes the
enemies fight him, and stands between them and everyone else.

- **HP:** {heroes.warden.hp}
- **Auto-attack:** d{heroes.warden.die}, on an enemy next to you.
- **Resource:** grit. At most {heroes.warden.pool}, and you start a fight
  with {heroes.warden.start}. You get {rules.grit_per_attack} grit each
  time an enemy attacks you (its normal attack, or a heavy hit it
  announced), even if the hit does no damage. Blasts, throws and poison
  give no grit. Grit does not come back at the top of the turn.
- **Crit bonus:** {heroes.warden.crit_gain} grit.
- **The hold:** an enemy standing next to you must attack you, and cannot
  walk away. Bosses ignore the hold: only Taunt cards keep a boss on you.

## Abilities

### Taunt

- {abilities.taunt.cost} grit · {abilities.taunt.timing} · range
  {abilities.taunt.range}{abilities.taunt.loud_tag}
- Put **{abilities.taunt.cards} Taunt cards** on one enemy. While it
  has them it must attack you, wherever you are. It never makes a longer
  Taunt stack shorter.

### AoE Taunt

- {abilities.aoe_taunt.cost} grit · {abilities.aoe_taunt.timing} · around you{abilities.aoe_taunt.loud_tag}
- Every enemy within {abilities.aoe_taunt.radius} squares of you gets
  **{abilities.aoe_taunt.cards} Taunt card**.

### Intercede

- {abilities.intercede.cost} grit · {abilities.intercede.timing} · range
  {abilities.intercede.range}{abilities.intercede.loud_tag}
- Leap to an ally who is up: you land on the empty square next to them
  that is closest to where you were (if there is none, you stay put). They
  get **{abilities.intercede.cards} Guarded card**: they take
  {abilities.intercede.value} less each time they are hurt. While they hold it, any
  enemy with no Taunt cards that goes for them attacks you instead.

### Grip

- {abilities.grip.cost} grit · {abilities.grip.timing} · range
  {abilities.grip.range}{abilities.grip.loud_tag}
- Pull one enemy to the empty square next to you that is closest to where
  it was. Now it is next to you, so the hold keeps it on you. Not on a
  boss. You need an empty square next to you.

### Shield Plant

- {abilities.shield_plant.cost} grit · {abilities.shield_plant.timing} · around you{abilities.shield_plant.loud_tag}
- Plant your shield against a blast that is coming from one square (the
  boss's square, for a Ground Slam). You, and every ally in the squares
  behind you, get **{abilities.shield_plant.cards} Shield Plant card**: take
  {abilities.shield_plant.value} less from a blast. "Behind you" means within
  {abilities.shield_plant.radius} squares of you, and farther from the blast's
  square than you are.

### Last Stand

- {abilities.last_stand.cost} grit · {abilities.last_stand.timing} · yourself{abilities.last_stand.loud_tag}
- Take **{abilities.last_stand.cards} Last Stand card**: while you hold it,
  nothing can take you below 1 HP. Use it when a heavy hit is coming.

### Disrupt (every hero has this)

- {abilities.disrupt.cost} grit · {abilities.disrupt.timing} · range
  {abilities.disrupt.range} (next to you) · cooldown
  {abilities.disrupt.cooldown}{abilities.disrupt.loud_tag}
- Break the cast an enemy has announced, so it never lands. Only on an
  enemy that has announced one. Then put {abilities.disrupt.cooldown}
  cooldown cards on Disrupt.

## How to play the Warden

- **Keep Taunt cards on the boss, always.** The moment it has none,
  Taunt it. Without them it walks off to hit the Mage or the Druid.
- **Watch the boss's announced moves.** If a heavy hit is coming at you
  and its biggest roll could take you to 0, use Last Stand. If a blast is
  coming and allies are standing in it, use Shield Plant.
- **Disrupt** any enemy next to you that has announced a cast.
- **Intercede** for an ally at half HP or less who is being chased by an
  enemy with no Taunt cards.
- **Don't spend grit on an enemy that is already next to you:** the hold
  keeps it on you anyway. Taunt a loose enemy that is going for
  someone else, Grip one that attacks from far away (like the
  shaman), and otherwise auto-attack. Getting hit is how you earn grit.
