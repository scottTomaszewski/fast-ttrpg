"""Rolling dice.

All the luck in a fight comes through one Dice, so the same seed always
plays the same fight.
"""

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class AutoRoll:
    """What one auto-attack did."""

    damage: int
    miss: bool
    crit: bool


class Dice:
    def __init__(self, rng: random.Random):
        self.rng = rng

    def roll(self, sides: int) -> int:
        """Roll one die: a number from 1 to `sides`."""
        return self.rng.randint(1, sides)

    def roll_many(self, count: int, sides: int, bonus: int = 0) -> int:
        """Roll `count` dice, add them up, then add `bonus`.

        This is for abilities, so nothing misses and nothing rolls again.
        """
        return sum(self.roll(sides) for _ in range(count)) + bonus

    def auto_attack(self, sides: int) -> AutoRoll:
        """Roll one auto-attack die.

        A 1 is a miss. The top face is a crit: roll again and add it,
        and keep going for as long as the top face comes up.
        """
        first = self.roll(sides)
        if first == 1:
            return AutoRoll(damage=0, miss=True, crit=False)
        damage = first
        last = first
        while last == sides:
            last = self.roll(sides)
            damage += last
        return AutoRoll(damage=damage, miss=False, crit=first == sides)
