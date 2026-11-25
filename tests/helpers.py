"""Small tools that make tests easy to write."""

from fastcombat.dice import Dice


class _ScriptedRolls:
    """Stands in for a random number maker. Gives back set numbers, in order."""

    def __init__(self, rolls: list[int]):
        self.rolls = rolls

    def randint(self, low: int, high: int) -> int:
        if not self.rolls:
            raise AssertionError("ran out of scripted rolls")
        value = self.rolls.pop(0)
        assert low <= value <= high, f"scripted roll {value} cannot come up on a {low}-{high} die"
        return value


def scripted(*rolls: int) -> Dice:
    """A Dice whose rolls are the given numbers, one after another."""
    return Dice(_ScriptedRolls(list(rolls)))
