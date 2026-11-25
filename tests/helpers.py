"""Small tools that make tests easy to write."""

from fastcombat.dice import Dice


class _ScriptedRolls:
    """Stands in for a random number maker. Gives back set numbers, in order."""

    def __init__(self, rolls: list[int]):
        self.rolls = rolls

    def randint(self, low: int, high: int) -> int:
        if not self.rolls:
            raise AssertionError("ran out of scripted rolls")
        return self.rolls.pop(0)


def scripted(*rolls: int) -> Dice:
    """A Dice whose rolls are the given numbers, one after another."""
    return Dice(_ScriptedRolls(list(rolls)))
