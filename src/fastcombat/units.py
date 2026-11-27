"""Heroes, enemies, and everything else that changes during a fight.

A fight's whole state is one FightState. Every rule reads it and changes it;
nothing else is kept anywhere. Heroes and enemies are found by their id:
heroes are named after their class ("guardian", and "guardian2" for a second
one), enemies after their type and a count ("wolf1", "wolf2").
"""

import random
from dataclasses import dataclass, field

from fastcombat.dice import Dice
from fastcombat.grid import Pos
from fastcombat.numbers import EnemySpec, FightDef, Numbers

# The cards that stop an enemy from doing anything on its turn.
CONTROL_STACKS = ("stun", "sap", "sheep")
# The bad cards: what Cleanse can take off a hero, and what Ice Block
# clears off the Mage. Today a hero can only get stun and poison; the rest
# are here so that any bad card that comes later is covered. Never
# Bleeding, and never a cooldown ("cd:" cards).
BAD_STACKS = ("stun", "poison", "rooted", "sap", "sheep")


@dataclass
class Stack:
    """One pile of cards on a unit. One card comes off each round."""

    cards: int
    value: int = 0  # heal per card, damage per card, damage taken off...
    source: str | None = None  # the hero who put it on, for the tally (heal cards)


@dataclass
class Cast:
    """A hero's cast or channel that is still going."""

    ability: str
    target: str | None  # unit id
    center: Pos | None  # for area casts
    actions_left: int  # act steps still to spend (casts)
    hits_left: int  # channel hits still to come
    is_channel: bool


@dataclass
class Announced:
    """An enemy cast waiting to land. It lands in `lands_round`."""

    name: str
    kind: str  # "blast" "heavy" "mend"
    lands_round: int
    target: str | None
    area: frozenset[Pos]
    dice: tuple[int, int]
    heal: int = 0


@dataclass
class Hero:
    id: str
    cls: str
    pos: Pos
    hp: int
    max_hp: int
    resource: int
    stacks: dict[str, Stack]
    combo: int = 0
    seeds: int = 0
    hidden: bool = False
    cast: Cast | None = None
    down: bool = False  # at 0 HP and bleeding; can still be saved
    out: bool = False  # gone for the rest of the fight
    wounds: int = 0  # one for each time they got up

    @property
    def up(self) -> bool:
        return not self.down and not self.out

    @property
    def stunned(self) -> bool:
        """Stun cards: no move and no act this party turn (Ice Block aside)."""
        return "stun" in self.stacks

    @property
    def iced(self) -> bool:
        """In an Ice Block: cannot be hurt, picked, move or act."""
        return "ice_block" in self.stacks


@dataclass
class Enemy:
    id: str
    spec: EnemySpec
    pos: Pos
    hp: int
    stacks: dict[str, Stack]
    pulled_by: str | None = None
    announced: Announced | None = None
    target: str | None = None  # who it attacked or will attack this GM turn
    dead: bool = False

    @property
    def controlled(self) -> bool:
        """Stunned, sapped or sheeped: it does nothing on its turn."""
        return any(name in self.stacks for name in CONTROL_STACKS)


@dataclass
class Tally:
    """What happened in the fight, for the report. Every table is by hero id."""

    damage: dict[str, int]  # all the HP each hero took off enemies
    auto_damage: dict[str, int]  # the part of `damage` done by auto-attacks
    healing: dict[str, int]  # HP really healed, not counting overhealing
    lowest_hp: dict[str, float]  # lowest fraction of max HP seen
    times_down: dict[str, int]
    resource_by_round: dict[str, list[int]]
    starved_rounds: dict[str, int]
    up_rounds: dict[str, int]  # rounds the hero was up after the act step
    # How many times each hero used each ability, by hero id, then ability
    # id. Hauling an ally up counts too, as "haul_up".
    uses: dict[str, dict[str, int]]
    # Each Rogue's opening before round 1, by hero id: "sneak" (it worked),
    # "spotted" (the stealth check failed), "shadowstep" or "none". Only
    # Rogues are in it. See `opening.py`.
    openings: dict[str, str] = field(default_factory=dict)
    # GM turns enemies lost to control cards, by card name ("stun", "sap",
    # "sheep"), all enemies added together. Not by hero id.
    rounds_out: dict[str, int] = field(default_factory=dict)

    @classmethod
    def for_heroes(cls, hero_ids: list[str]) -> "Tally":
        """A Tally with a starting entry for every hero."""
        return cls(
            damage={h: 0 for h in hero_ids},
            auto_damage={h: 0 for h in hero_ids},
            healing={h: 0 for h in hero_ids},
            lowest_hp={h: 1.0 for h in hero_ids},
            times_down={h: 0 for h in hero_ids},
            resource_by_round={h: [] for h in hero_ids},
            starved_rounds={h: 0 for h in hero_ids},
            up_rounds={h: 0 for h in hero_ids},
            uses={h: {} for h in hero_ids},
        )

    def count_use(self, hero_id: str, ability_id: str) -> None:
        """Write down that `hero_id` used `ability_id` once."""
        used = self.uses[hero_id]
        used[ability_id] = used.get(ability_id, 0) + 1


@dataclass
class FightState:
    numbers: Numbers
    fight: FightDef
    dice: Dice
    heroes: dict[str, Hero]
    enemies: dict[str, Enemy]
    round: int
    tally: Tally
    marked: dict[str, frozenset[Pos]]  # hero blasts waiting to land, by hero id

    def guardian(self) -> Hero | None:
        """The first Guardian in the party who is up, or None."""
        return next((h for h in self.up_heroes() if h.cls == "guardian"), None)

    def living_enemies(self) -> list[Enemy]:
        return [e for e in self.enemies.values() if not e.dead]

    def up_heroes(self) -> list[Hero]:
        return [h for h in self.heroes.values() if h.up]

    def occupied(self) -> set[Pos]:
        """Squares nobody else may step on. A downed hero still lies there."""
        heroes = {h.pos for h in self.heroes.values() if not h.out}
        return heroes | {e.pos for e in self.living_enemies()}

    def danger_squares(self) -> set[Pos]:
        """Squares where a blast is going to land: enemy casts and hero casts."""
        squares: set[Pos] = set()
        for e in self.living_enemies():
            if e.announced is not None:
                squares |= e.announced.area
        for area in self.marked.values():
            squares |= area
        return squares

    def add_enemy(self, type: str, pos: Pos) -> Enemy:
        """Bring one enemy of `type` into the fight at `pos`, at full HP.

        Its id is the type and the next number for that type: "wolf1",
        then "wolf2". Dead enemies stay in `enemies`, so an id is never reused.
        """
        spec = self.fight.enemy_types[type]
        n = 1
        while f"{type}{n}" in self.enemies:
            n += 1
        enemy = Enemy(id=f"{type}{n}", spec=spec, pos=pos, hp=spec.hp, stacks={})
        self.enemies[enemy.id] = enemy
        return enemy


def new_state(
    numbers: Numbers, fight: FightDef, party: list[str], seed: int
) -> FightState:
    """Set up a fight at the start of round 1.

    The first hero of each class stands on that class's start square. A second
    hero of a class, or a class the map has no square for, takes the next of
    the extra start squares. The enemies that are there from the start (round
    0 in the fight file) are placed too.
    """
    heroes: dict[str, Hero] = {}
    extra = iter(fight.extra_starts)
    for cls in party:
        if cls not in numbers.heroes:
            raise ValueError(f"{cls!r} is not a hero class in the numbers file")
        spec = numbers.heroes[cls]
        count = sum(1 for h in heroes.values() if h.cls == cls) + 1
        hero_id = cls if count == 1 else f"{cls}{count}"
        if count == 1 and cls in fight.hero_starts:
            pos = fight.hero_starts[cls]
        else:
            pos = next(extra, None)
            if pos is None:
                raise ValueError(
                    f"the fight {fight.name!r} has too few start squares for this party"
                )
        heroes[hero_id] = Hero(
            id=hero_id,
            cls=cls,
            pos=pos,
            hp=spec.hp,
            max_hp=spec.hp,
            resource=spec.start,
            stacks={},
            hidden=cls == "rogue",
        )

    state = FightState(
        numbers=numbers,
        fight=fight,
        dice=Dice(random.Random(seed)),
        heroes=heroes,
        enemies={},
        round=1,
        tally=Tally.for_heroes(list(heroes)),
        marked={},
    )
    for spawn in fight.spawns:
        if spawn.round == 0:
            state.add_enemy(spawn.type, spawn.pos)
    return state
