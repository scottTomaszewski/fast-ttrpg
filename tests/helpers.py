"""Small tools that make tests easy to write."""

from pathlib import Path

from fastcombat.dice import Dice
from fastcombat.grid import Pos
from fastcombat.numbers import load_fight, load_numbers
from fastcombat.units import Enemy, FightState, new_state

# The tests' own frozen copy of the game files. The tests check exact numbers
# (a wolf hits for 4), and the real numbers will be tuned, so the tests read
# this copy, which only changes when a test needs it to.
GAME = Path(__file__).parent / "data"
# The real game files: the numbers file and the fights.
REAL_GAME = Path(__file__).parent.parent / "game"


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


def state(
    party: tuple[str, ...] = ("guardian", "rogue", "druid", "mage"),
    rolls: list[int] | None = None,
    seed: int = 1,
) -> FightState:
    """A fight in round 1 on the tests' copy of the game files, with no enemies yet.

    Each test adds just the enemies it needs with `enemy`, so the first wolf
    a test adds is always "wolf1". The files are read fresh every time, so a
    test that changes a number cannot change another test. With `rolls`,
    the dice give exactly those numbers, in order.
    """
    numbers = load_numbers(GAME / "numbers.toml")
    fight = load_fight(GAME / "fights" / "ogre_warlord.toml")
    s = new_state(numbers, fight, list(party), seed)
    s.enemies.clear()
    if rolls is not None:
        s.dice = scripted(*rolls)
    return s


def enemy(state: FightState, type: str, pos: Pos) -> Enemy:
    """Add one enemy of `type` (from the fight file) at `pos`."""
    return state.add_enemy(type, pos)
