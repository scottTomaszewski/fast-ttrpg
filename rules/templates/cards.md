# The cards

Everything that lasts in this game is a stack of cards. Write the name and
what it does on each card, and keep a pile of each kind. (Printable card
sheets come later; index cards cut in half are fine for now.)

When the cards come off:

- **Cards a hero holds** come off one at a time at the top of each party
  turn.
- **Bleeding cards** come off at the end of the party turn instead.
- **Cards on an enemy** come off one at a time at the end of each GM turn.
- **Wound cards** never come off during a fight.

A new stack of a kind takes the place of the old one, except Taunt, stun,
sap and sheep, which never get shorter. Going down wipes every card a hero
holds.

## Cards heroes hold

| Card | Written on it | Who holds it | Where it comes from |
|---|---|---|---|
| **Heal** (Rejuvenation) | "Heal {abilities.rejuvenation.value} at the top of your turn." | The hero healed | Druid's Rejuvenation: {abilities.rejuvenation.cards} cards |
| **Heal** (Wild Growth) | "Heal {abilities.wild_growth.value} at the top of your turn." | Each hero in the area | Druid's Wild Growth: {abilities.wild_growth.cards} cards each. A separate stack from Rejuvenation: both heal. |
| **Guarded** | "Take {abilities.intercede.value} less each time you are hurt. An enemy with no Taunt cards that goes for you attacks the Guardian instead." | The ally the Guardian leapt to | Guardian's Intercede: {abilities.intercede.cards} card |
| **Shield Plant** | "Take {abilities.shield_plant.value} less from a blast." | The Guardian, and each ally behind him | Guardian's Shield Plant: {abilities.shield_plant.cards} card each |
| **Last Stand** | "You cannot drop below 1 HP." | The Guardian | Guardian's Last Stand: {abilities.last_stand.cards} card |
| **Poison** | "Lose {enemy.shaman.poison_value} HP at the top of your turn." | The hero the shaman hit | The shaman's attack: {enemy.shaman.poison_cards} cards. The Druid's Cleanse takes them all off. |
| **Bleeding** | "You are down. When the last one goes, you are out." | A downed hero | Going down: {rules.bleeding_cards} cards, one fewer for each Wound. They come off at the end of the party turn. |
| **Wound** | "Each Wound: one Bleeding card fewer next time you go down." | A hero who got up | Getting up: 1 card, kept for the whole fight |
| **Cooldown** | "Disrupt is resting." | Put it on the Disrupt line of your sheet | Using Disrupt: {abilities.disrupt.cooldown} cards. You cannot Disrupt while any are there. |

## Cards on enemies

| Card | Written on it | Who holds it | Where it comes from |
|---|---|---|---|
| **Taunt** | "Attack the Guardian." | The enemy | Guardian's Taunt: {abilities.taunt.cards} cards. Challenging Shout: {abilities.challenging_shout.cards} card. A Loud hit takes Taunt cards off: a boss loses {rules.boss_loud_cards}, any other enemy 1. |
| **Stun** | "Do nothing this turn. Any cast you announced is broken." | The enemy (not a boss) | Rogue's Kidney Shot: {abilities.kidney_shot.cards} card, or {abilities.kidney_shot.alt} at full combo points. Cheap Shot: {abilities.cheap_shot.cards} card. |
| **Sap** | "Do nothing. Wake up the moment you are hurt." | The enemy (not a boss) | Rogue's Sap: {abilities.sap.cards} cards |
| **Sheep** | "You are a sheep: do nothing. Turn back the moment you are hurt." | The enemy (not a boss). Only one sheep at a time. | Mage's Polymorph: {abilities.polymorph.cards} cards |
| **Rooted** | "You cannot move. You can still attack." | Every enemy next to the Mage, a boss too | Mage's Frost Nova: {abilities.frost_nova.cards} cards |

## Not cards: markers

Some things last only a moment, or are just a count. Use a coin, a bead or
a token for these:

- **Pull:** a marker by an enemy, pointing at the hero who pulled it. Take
  it away after the enemy's turn.
- **Hidden:** a marker by the Rogue while she is hidden.
- **Marked area:** the squares an announced blast or a Meteor will hit.
  Coins on the corners, or a loop of string.
- **Combo points** (Rogue) and **Seeds** (Druid): coins or a die.
