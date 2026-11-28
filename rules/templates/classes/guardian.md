# The Guardian

The Guardian is the tank: a big shield and a bigger voice. He makes the
enemies fight him, and stands between them and everyone else.

- **HP:** {heroes.guardian.hp}
- **Auto-attack:** d{heroes.guardian.die}, on an enemy next to you.
- **Resource:** grit. At most {heroes.guardian.pool}, and you start a fight
  with {heroes.guardian.start}. You get {rules.grit_per_attack} grit each
  time an enemy attacks you (its normal attack, or a heavy hit it
  announced), even if the hit does no damage. Blasts, throws and poison
  give no grit. Grit does not come back at the top of the turn. Shield
  Slam gives grit too.
- **Crit bonus:** {heroes.guardian.crit_gain} grit.
- **The hold:** an enemy standing next to you must attack you, and cannot
  walk away. Bosses ignore the hold: only Taunt cards keep a boss on you.

## Abilities

### Taunt

- {abilities.taunt.cost} grit · {abilities.taunt.timing} · range
  {abilities.taunt.range}{abilities.taunt.loud_tag}
- Put **{abilities.taunt.cards} Taunt cards** on one enemy. While it
  has them it must attack you, wherever you are. It never makes a longer
  Taunt stack shorter.

### Challenging Shout

- {abilities.challenging_shout.cost} grit · {abilities.challenging_shout.timing} · around you{abilities.challenging_shout.loud_tag}
- Every enemy within {abilities.challenging_shout.radius} squares of you gets
  **{abilities.challenging_shout.cards} Taunt card**.

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

### Shield Slam

- {abilities.shield_slam.cost} grit · {abilities.shield_slam.timing} · range
  {abilities.shield_slam.range} (next to you) · cooldown
  {abilities.shield_slam.cooldown}{abilities.shield_slam.loud_tag}
- Slam one enemy with your shield for **{abilities.shield_slam.dice}**,
  and get **{abilities.shield_slam.alt} grit** (never more than
  {heroes.guardian.pool}). It is a hit, not an auto-attack: it never
  misses and never crits.
- Then put {abilities.shield_slam.cooldown} cooldown cards on Shield Slam.
  You turn one in at the top of each party turn with your other cards, and
  you cannot Shield Slam while any are there. So if you Shield Slam in
  round 4, you can do it again in round
  {4 + abilities.shield_slam.cooldown}.

### Disrupt (every hero has this)

- {abilities.disrupt.cost} grit · {abilities.disrupt.timing} · range
  {abilities.disrupt.range} (next to you) · cooldown
  {abilities.disrupt.cooldown}{abilities.disrupt.loud_tag}
- Break the cast an enemy has announced, so it never lands. Only on an
  enemy that has announced one. Then put {abilities.disrupt.cooldown}
  cooldown cards on Disrupt.

## How to play the Guardian

- **Keep Taunt cards on the boss, always.** The moment it has none,
  Taunt it. Without them it walks off to hit the Mage or the Druid.
- **Watch the boss's announced moves.** If a heavy hit is coming at you
  and its biggest roll could take you to 0, use Last Stand. If a blast is
  coming and allies are standing in it, stay put, plant your shield and
  let them stand behind you.
- **Disrupt** any enemy next to you that has announced a cast.
- **Intercede** for an ally at 60% HP or less who is being chased by an
  enemy with no Taunt cards. While an ally is that low, keep enough grit
  for it.
- **Loose adds** (an add is an extra enemy that fights alongside the boss):
  Challenging Shout when two or more near you are going for someone else.
  Grip one that attacks from far away (like the shaman), or one on the Mage
  or the Druid. Taunt any other loose add that is not coming for you
  (not a goblin: any hit kills one).
- **Don't spend grit on an enemy that is already next to you:** the hold
  keeps it on you anyway. Getting hit is how you earn grit.
- **Shield Slam when nothing needs you.** The boss has a Taunt card,
  every ally is above 70% HP, and no add is loose? Then Shield Slam the
  boss (or the enemy on you) instead of an auto-attack. It costs
  {abilities.shield_slam.cost} grit and gives you grit. If something needs
  you, that comes first.
- **A Stomp is coming and you hold the boss?** If someone will Disrupt it,
  stay next to the boss and keep hitting. If nobody will, you may still
  stay and take it, as long as the Druid is up: she can Cleanse your stun
  before your act step, because she acts before you. Everyone else should
  step away.
