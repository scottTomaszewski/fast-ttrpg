# The Druid

The Druid is the healer. She heals in a hurry when someone is about to
fall, and hands out heal cards that keep everyone going round after round.

- **HP:** {heroes.druid.hp}
- **Auto-attack:** d{heroes.druid.die}, on an enemy up to
  {heroes.druid.attack_range} squares away.
- **Resource:** energy. At most {heroes.druid.pool}, you start a fight with
  {heroes.druid.start}, and you get {heroes.druid.regen} back at the top of
  each party turn.
- **Seeds:** at most {rules.seeds_max}, and you start a fight with none.
  You get one each time a Regrowth
  lands, and one from an auto-attack crit. Swiftmend spends one.
- **Crit bonus:** {heroes.druid.crit_gain} Seed.

Your abilities can be aimed at any hero who is not out, yourself too.
Any heal gets a downed hero back up, on as much HP as the heal.

## Abilities

### Rejuvenation

- {abilities.rejuvenation.cost} energy · {abilities.rejuvenation.timing}
  · range {abilities.rejuvenation.range}{abilities.rejuvenation.loud_tag}
- Give one hero who is up **{abilities.rejuvenation.cards} heal cards**,
  each worth {abilities.rejuvenation.value}. They turn one in at the top of
  each party turn. A new Rejuvenation takes the place of the old one.

### Regrowth

- {abilities.regrowth.cost} energy · {abilities.regrowth.timing} · range
  {abilities.regrowth.range}{abilities.regrowth.loud_tag}
- When it lands, heal one hero **{abilities.regrowth.dice}** and get a
  Seed. If they went down while you were casting, it gets them up.
- **Loud:** every enemy with no Taunt cards that the Warden is not holding
  comes for you on its next turn.

### Swiftmend

- {abilities.swiftmend.cost} energy, or **free** on a hero below half their
  max HP · {abilities.swiftmend.timing} · range
  {abilities.swiftmend.range}{abilities.swiftmend.loud_tag}
- Spend a Seed (you need one) to heal one hero **{abilities.swiftmend.dice}**
  at once. A downed hero is at 0 HP, so it is free on them.

### Wild Growth

- {abilities.wild_growth.cost} energy · {abilities.wild_growth.timing} ·
  range {abilities.wild_growth.range}{abilities.wild_growth.loud_tag}
- Pick a square. Every hero who is up within
  {abilities.wild_growth.radius} squares of it, you too, gets
  **{abilities.wild_growth.cards} heal cards**, each worth
  {abilities.wild_growth.value}. These are their own stack, apart from
  Rejuvenation. A new Wild Growth takes the place of the old one.

### Cleanse

- {abilities.cleanse.cost} energy · {abilities.cleanse.timing} · range
  {abilities.cleanse.range}{abilities.cleanse.loud_tag}
- Take every poison card off one hero. Only on a hero who has poison.

### Shadowmeld

- {abilities.shadowmeld.cost} energy · {abilities.shadowmeld.timing} ·
  yourself{abilities.shadowmeld.loud_tag}
- Every pull on you is dropped, and you slip up to
  **{abilities.shadowmeld.value} squares** away from the enemies, onto an
  empty square. This is your action, on top of your normal move.

### Nourish

- {abilities.nourish.cost} energy · {abilities.nourish.timing} · range
  {abilities.nourish.range}{abilities.nourish.loud_tag}
- Roll **{abilities.nourish.dice}** and heal one hero that much. It is a
  plain roll, not an auto-attack: a 1 still heals 1, and nothing rolls
  again. On the top face you also get {abilities.nourish.alt} energy back.

### Disrupt (every hero has this)

- {abilities.disrupt.cost} energy · {abilities.disrupt.timing} · range
  {abilities.disrupt.range} (next to you) · cooldown
  {abilities.disrupt.cooldown}{abilities.disrupt.loud_tag}
- Break the cast an enemy has announced, so it never lands. Only on an
  enemy that has announced one. Then put {abilities.disrupt.cooldown}
  cooldown cards on Disrupt.

## How to play the Druid

- **Someone is down? Get them up first.** Swiftmend them (it is free on a
  downed hero, if you have a Seed), or else Nourish them.
- **Keep out of reach.** Stand within {abilities.rejuvenation.range}
  squares of the Warden and as far from the enemies as you can. If an
  enemy next to you, or one coming for you, could reach you this GM turn,
  Shadowmeld.
- **Keep Rejuvenation on the Warden all the time.** He takes the most
  hits.
- **Fix the worst first.** Swiftmend anyone at about a third of their HP.
  Wild Growth when three hurt heroes stand close together. Regrowth
  anyone at a little over half their HP or lower (but remember it is
  Loud).
- **Fill the gaps.** Cleanse poison, put Rejuvenation on anyone who is
  hurt, and Nourish when there is nothing else to do: it costs nothing.
