{# How the templates work. This note is left out of rules/README.md.

Every file in rules/templates/ is a Markdown template, and the command
`uv run fastcombat rules` makes each one into the file of the same name in
rules/ (this one becomes rules/README.md). A name in braces is a
placeholder, filled in from the game files: {heroes.guardian.hp} and
{abilities.meteor.cost} from game/numbers.toml; {enemy.ogre.hp},
{boss.ground_slam.dice} and {spawns.goblin.round} from the fight file.
Dice come out like 8d6, or 2d6+4 with a bonus; yes-or-no settings come out
"yes" or "no"; {abilities.meteor.timing} says Instant, Cast or Channel;
{boss.ground_slam.rounds} lists the rounds a boss move comes up; and
{fight.map} draws the map and {fight.enemies} counts every enemy in the
fight. Names and whole numbers joined with + or -
make a sum, like {heroes.mage.hp - enemy.wolf.damage}. A name the game
files do not have stops the command with a message naming the file and
the placeholder, and nothing is written; so does a brace left over, from a
placeholder or a note that was never closed. Anything inside a pair of a brace
and a hash, like the one around this paragraph, is a note for whoever
edits the template, and is left out. The full list of names is at the top
of src/fastcombat/rules_doc.py. Never change the files in rules/ by hand:
change the template, then run the command. A test fails if they differ. #}

# Fast combat: the rules

Fast combat is a tabletop battle game. A party of heroes fights a band of
monsters played by the Game Master (the GM). Rounds are short and everyone
rolls at the same time, so a fight is about twenty quick rounds instead of
three slow ones.

## What you need

- A grid map with squares, at least {fight.width} squares wide and
  {fight.height} tall for the test fight. Squared paper works.
- A mini or a token for each hero and each enemy. The test fight has
  {fight.enemies} enemies in all.
- Dice: {dice.sides}. A roll is written like {dice.biggest}: the first
  number says how many dice to roll, and the number after the "d" says
  which die (d6 is the usual six-sided one). Roll them all and add them up.
  A "+" number after it, like the 4 in 2d6+4, is added on too.
  {dice.biggest} is the biggest roll in the game, so have at least
  {dice.most} dice of that kind.
- A stack of index cards, cut in half. Everything that lasts in this game
  is a little pile of cards.
- A pencil and paper for each player, for HP and resource, and a few
  coins or beads for combo points and Seeds.

## Who plays

One person is the GM and runs the enemies. Everyone else plays one hero.
There are four kinds of hero: the Guardian (the tank: the tough one who
makes the enemies fight him instead of the others), the Rogue, the Druid
(the healer) and the Mage. The test fight is made for one of each, but any
mix works.

## What to read, in order

1. [`core.md`](core.md): the whole game. Everyone reads this.
2. Your hero's sheet: [Guardian](classes/guardian.md),
   [Rogue](classes/rogue.md), [Druid](classes/druid.md) or
   [Mage](classes/mage.md).
3. [`cards.md`](cards.md): every kind of card, what goes on it, and who
   holds it.
4. For the GM: [`fights/ogre-warlord.md`](fights/ogre-warlord.md), the
   test fight.
