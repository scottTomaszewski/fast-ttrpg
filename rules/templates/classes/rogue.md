# The Rogue

The Rogue strikes from the shadows. She builds up combo points with quick
hits, then spends them all on one huge blow or a long stun.

- **HP:** {heroes.rogue.hp}
- **Auto-attack:** d{heroes.rogue.die}, on an enemy next to you.
- **Resource:** energy. At most {heroes.rogue.pool}, you start a fight with
  {heroes.rogue.start}, and you get {heroes.rogue.regen} back at the top of
  each party turn.
- **Combo points:** at most {rules.combo_max}, and you start a fight with
  none. You get
  {rules.combo_per_hit} for each auto-attack die that hits, and for each
  Backstab. Eviscerate and Kidney Shot spend them all. Keep them with
  coins or a die.
- **Crit bonus:** {heroes.rogue.crit_gain} extra combo point, so a crit
  gives {rules.combo_per_hit + heroes.rogue.crit_gain} in all.

## Hiding

- You **start every fight hidden**, and Vanish hides you again.
- While you are hidden, no enemy can pick you as its target, and a pull
  by you counts for nothing. A blast still hits you if you stand in it.
- Hiding ends once you auto-attack or use any ability except Vanish and
  Shadowstep, and when you go down. Moving and hauling an ally up do not
  end it.
- An ability "from hiding" is checked before your hiding ends, so a
  Backstab from hiding still counts as from hiding.

## Abilities

### Backstab

- {abilities.backstab.cost} energy · {abilities.backstab.timing} · range
  {abilities.backstab.range} (next to you){abilities.backstab.loud_tag}
- Roll **{abilities.backstab.dice}** and get {rules.combo_per_hit} combo
  point.
- Only on an enemy that is **busy with someone else**: it has Taunt cards,
  or it went for another hero on its last turn, or it is standing next to
  the Guardian (and is not a boss). Not on an enemy you pulled, unless it has
  Taunt cards.
- **From hiding**, it works on any enemy, and the damage is multiplied by
  {rules.backstab_hidden_multiplier}.

### Eviscerate

- {abilities.eviscerate.cost} energy · {abilities.eviscerate.timing} ·
  range {abilities.eviscerate.range} (next to you){abilities.eviscerate.loud_tag}
- Spend all your combo points (you need at least 1). Roll
  **{abilities.eviscerate.dice} for each point**: with {rules.combo_max}
  points, that is {rules.combo_max} rolls added together.

### Kidney Shot

- {abilities.kidney_shot.cost} energy · {abilities.kidney_shot.timing} ·
  range {abilities.kidney_shot.range} (next to you){abilities.kidney_shot.loud_tag}
- Spend all your combo points (you need at least 1) to stun one enemy:
  **{abilities.kidney_shot.cards} stun card**, or
  **{abilities.kidney_shot.alt}** if you had the full {rules.combo_max}.
  Not on a boss.

### Cheap Shot

- {abilities.cheap_shot.cost} energy · {abilities.cheap_shot.timing} ·
  range {abilities.cheap_shot.range} (next to you){abilities.cheap_shot.loud_tag}
- A quick stun: **{abilities.cheap_shot.cards} stun card** on one enemy. No
  combo points needed. It works on a boss too: a boss cannot be stunned,
  but the stun still breaks the cast it has announced.

### Sap

- {abilities.sap.cost} energy · {abilities.sap.timing} · range
  {abilities.sap.range} (next to you){abilities.sap.loud_tag}
- **Only while hidden.** Knock one enemy out: **{abilities.sap.cards} sap
  cards**. It does nothing while it has them, but wakes the moment it
  takes any damage. Not on a boss. Using it ends your hiding.

### Shadowstep

- {abilities.shadowstep.cost} energy · {abilities.shadowstep.timing} ·
  range {abilities.shadowstep.range}{abilities.shadowstep.loud_tag}
- Pick an enemy in range. You appear next to it, on the empty square
  nearest to you (there has to be one). It **does not end your hiding**.

### Vanish

- {abilities.vanish.cost} energy · {abilities.vanish.timing} ·
  yourself{abilities.vanish.loud_tag}
- Every pull on you is dropped, and you **hide**. It works even if you are
  already hidden.

### Disrupt (every hero has this)

- {abilities.disrupt.cost} energy · {abilities.disrupt.timing} · range
  {abilities.disrupt.range} (next to you) · cooldown
  {abilities.disrupt.cooldown}{abilities.disrupt.loud_tag}
- Break the cast an enemy has announced, so it never lands. Only on an
  enemy that has announced one. Then put {abilities.disrupt.cooldown}
  cooldown cards on Disrupt.

## How to play the Rogue

- **Open from hiding.** Your first hit should be a Backstab from hiding,
  for {rules.backstab_hidden_multiplier} times the damage. In round 1 you can Sap an enemy instead, if you can
  get next to it.
- **Stop casts next to you.** If an enemy next to you has announced a
  cast, Disrupt it, or Cheap Shot it if Disrupt is cooling down.
- **If something is coming for you because of your Loud hit, Vanish.**
- **At {rules.combo_max} combo points, Eviscerate.** On the boss, only while
  it has Taunt cards: Eviscerate is Loud, so then the boss loses
  {rules.boss_loud_cards} of its Taunt cards instead of being pulled onto
  you. If an add (an extra enemy that fights alongside the boss) next to you is chasing the Druid or the Mage, Kidney Shot it instead.
- **Otherwise Backstab** whatever is busy with someone else. If your target
  is too far to walk to, Shadowstep to it. Hit the enemy casting a mend
  first, then the add with the least HP, and the boss last.
