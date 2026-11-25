# Combat Simulator and First Tuning Pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A script that plays the test fight thousands of times from one numbers file and reports whether the numbers meet the design's targets, plus a first set of numbers that does.

**Architecture:** A small Python package, `fastcombat`, with one job per file. All game numbers live in `game/numbers.toml` and the test fight in `game/fights/ogre_warlord.toml`; code holds rules, never numbers. Heroes are driven by written-down priority lists ("policies"); enemies by a `prefers` setting and a boss script. One fight is a pure function of (numbers, fight, party, policies, seed).

**Tech Stack:** Python 3.12, `uv`, `pytest`. Standard library only (`tomllib`, `random`, `dataclasses`, `argparse`, `statistics`, `json`).

**Spec:** `docs/superpowers/specs/2026-11-24-fast-combat-design.md`. Read it first. This plan covers "What gets built" items 1 and 2 (simulator, tuning). Items 3 and 4 (written rules, printable cards) get their own plan after tuning.

## Global Constraints

- Every number lives in `game/numbers.toml` or the fight file. No game number is written in code.
- Each ability's cost, cast time, dice, duration, and tags are entries in the numbers file, so a later talent can be "change these entries".
- The party is a setting: any list of classes, any length, repeats allowed, any class missing.
- Same inputs and same seed give the same result.
- Auto-attack: one die, a 1 misses, top face rolls again and adds (and keeps going). Abilities never miss and never crit.
- Hero-side card stacks tick at the top of the party turn. Enemy-side stacks tick at the end of the GM turn.
- Squares: every step costs 1, diagonals included. Distance is the larger of the x and y gaps. No opportunity attacks.
- One action per hero per turn.
- Comments and docs in plain words.
- Commit messages: plain, no AI attribution, no co-author trailers.

## Review Focus

1. **A party with a class missing** (no Warden, no Druid, or two Rogues): the fight runs to an end without an error; enemies with Taunt cards or next to nobody fall back to their `prefers`. Test in Task 5 and Task 13.
2. **A fight that never ends:** it stops at `rules.max_rounds`, and is reported as a timeout and a loss, never a win. Test in Task 7.
3. **A typo in the numbers file** (unknown key, unknown ability, missing hero field): loading fails with a message that names the file section and the key. Test in Task 3.
4. **A cast whose target is gone when it lands** (enemy dead, hero out): it fizzles, costs nothing, and nothing crashes. Test in Task 6.
5. **Two units wanting the same square, or no path:** nobody ever shares a square; a unit with no path stays where it is. Test in Task 2 and Task 7.

## File Structure

```
pyproject.toml
README.md
game/numbers.toml                 every hero and ability number
game/fights/ogre_warlord.toml     map, enemies, boss script
src/fastcombat/
  dice.py        rolling: plain rolls and the auto-attack roll
  grid.py        squares: distance, areas, "behind", walking
  numbers.py     load and check the two TOML files
  units.py       Hero, Enemy, Stack, Cast, Announced, FightState
  combat.py      damage, healing, going down, getting up
  targeting.py   who an enemy must attack (taunt, pull, hold, intercede)
  casting.py     hero casts and channels
  abilities/__init__.py   use_ability: cost, range, cooldown, cast start, Loud
  abilities/warden.py  rogue.py  druid.py  mage.py  shared.py   one effect per ability
  enemy_ai.py    enemy turn, boss script, announced casts
  policies.py    how each hero class plays
  fight.py       the round loop; run_fight
  report.py      turn many FightResults into numbers and target checks
  cli.py         `fastcombat run` and `fastcombat check`
tests/helpers.py and tests/test_<file>.py
docs/tuning-log.md
```

## Shared names (used across tasks)

```python
Pos = tuple[int, int]

@dataclass
class Stack:            # one pile of cards on a unit
    cards: int
    value: int = 0      # heal per card, damage per card, damage reduced...

# Stack names, used as keys of unit.stacks: dict[str, Stack]
# heroes:  "rejuvenation" "wild_growth" "poison" "guarded" "interceded"
#          "bulwark" "unbroken" "quicken" "bleeding" "cd:<ability id>"
# enemies: "taunt" "stun" "sap" "sheep" "rooted"
```

Unit ids are strings: heroes `"warden"`, `"rogue"`, `"druid"`, `"mage"` (a repeat gets `"rogue2"`); enemies `"<type><n>"`, for example `"wolf1"`.

---

### Task 1: Project and dice

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `src/fastcombat/__init__.py`, `src/fastcombat/dice.py`
- Test: `tests/test_dice.py`, `tests/helpers.py`

**Interfaces:**
- Produces:
  - `Dice(rng: random.Random)` with `roll(sides: int) -> int`, `roll_many(count: int, sides: int, bonus: int = 0) -> int`, `auto_attack(sides: int) -> AutoRoll`
  - `AutoRoll(damage: int, miss: bool, crit: bool)` (frozen dataclass)
  - `tests/helpers.py`: `scripted(*rolls: int) -> Dice`, a Dice whose rolls come from the list in order (raise `AssertionError("ran out of scripted rolls")` when empty)

- [ ] **Step 1: Scaffold.** `uv init --package --name fastcombat --python 3.12`, `uv add --dev pytest`. In `pyproject.toml` set `[project.scripts] fastcombat = "fastcombat.cli:main"` and `[tool.pytest.ini_options] testpaths = ["tests"]`, `markers = ["slow: plays hundreds of fights"]`, `addopts = "-m 'not slow'"`. `.gitignore`: `.venv/`, `__pycache__/`, `.pytest_cache/`, `out/`.

- [ ] **Step 2: Write the failing tests**

```python
from tests.helpers import scripted

def test_one_is_a_miss():
    r = scripted(1).auto_attack(6)
    assert (r.damage, r.miss, r.crit) == (0, True, False)

def test_plain_hit():
    r = scripted(4).auto_attack(6)
    assert (r.damage, r.miss, r.crit) == (4, False, False)

def test_top_face_rolls_again_and_keeps_going():
    r = scripted(6, 6, 2).auto_attack(6)
    assert (r.damage, r.miss, r.crit) == (14, False, True)

def test_a_one_after_a_crit_still_counts():
    assert scripted(4, 1).auto_attack(4).damage == 5

def test_roll_many_adds_bonus_and_never_explodes():
    assert scripted(6, 6, 1).roll_many(3, 6, bonus=4) == 17
```

- [ ] **Step 3:** Run `uv run pytest tests/test_dice.py -v`. Expected: FAIL, `fastcombat.dice` not found.
- [ ] **Step 4:** Implement `dice.py` and `tests/helpers.py::scripted` (a tiny object with `randint(a, b)` that pops from the list, passed as the rng).
- [ ] **Step 5:** Run again. Expected: 5 passed.
- [ ] **Step 6: Commit** everything, including the existing `docs/`. Message: `Start the simulator: project setup and dice`.

---

### Task 2: Grid

**Files:**
- Create: `src/fastcombat/grid.py`
- Test: `tests/test_grid.py`

**Interfaces:**
- Produces:
  - `distance(a: Pos, b: Pos) -> int`
  - `adjacent(a: Pos, b: Pos) -> bool` (distance exactly 1)
  - `within(center: Pos, radius: int, width: int, height: int) -> set[Pos]` (on-map squares with distance <= radius)
  - `behind(shield: Pos, source: Pos, depth: int, width: int, height: int) -> set[Pos]`: on-map squares within `depth` of `shield` that are farther from `source` than `shield` is
  - `walk(start: Pos, goal: Pos, steps: int, blocked: set[Pos], width: int, height: int, reach: int = 0) -> Pos`: the square you end on after at most `steps` steps along a shortest path (breadth-first, 8 directions, never through or onto a blocked square) toward the nearest free square within `reach` of `goal`. Returns `start` if there is no path. With `reach=0` and a blocked goal, returns `start`.
  - `walk_away(start: Pos, threats: list[Pos], steps: int, blocked: set[Pos], width: int, height: int) -> Pos`: the reachable square (within `steps`) whose nearest threat is farthest; ties go to the fewest steps.

- [ ] **Step 1: Write the failing tests**

```python
from fastcombat.grid import distance, adjacent, within, behind, walk, walk_away

def test_diagonals_cost_one():
    assert distance((0, 0), (3, 2)) == 3

def test_adjacent_is_the_eight_squares_not_your_own():
    assert adjacent((2, 2), (3, 3)) and not adjacent((2, 2), (2, 2))

def test_within_is_clipped_to_the_map():
    assert within((0, 0), 1, 5, 5) == {(0, 0), (1, 0), (0, 1), (1, 1)}

def test_behind_is_the_far_side_from_the_blast():
    b = behind((5, 5), (8, 5), 2, 20, 20)
    assert (4, 5) in b and (3, 4) in b
    assert (6, 5) not in b and (5, 5) not in b

def test_walk_stops_next_to_the_goal_with_reach_one():
    assert walk((0, 0), (5, 0), 10, {(5, 0)}, 10, 10, reach=1) == (4, 0)

def test_walk_goes_only_as_far_as_its_steps():
    assert walk((0, 0), (9, 0), 3, set(), 10, 10) == (3, 0)

def test_walk_goes_round_a_blocker_and_never_ends_on_one():
    end = walk((0, 0), (2, 0), 5, {(1, 0), (1, 1)}, 3, 2)
    assert end == (0, 0)          # walled off: no path, stay put

def test_walk_away_gets_farther_from_the_threat():
    end = walk_away((5, 5), [(4, 5)], 3, set(), 20, 20)
    assert distance(end, (4, 5)) == 4
```

- [ ] **Step 2:** Run `uv run pytest tests/test_grid.py -v`. Expected: FAIL, module not found.
- [ ] **Step 3:** Implement `grid.py`.
- [ ] **Step 4:** Run again. Expected: 8 passed.
- [ ] **Step 5: Commit.** Message: `Add the grid: distance, areas and walking`.

---

### Task 3: The numbers files and their loader

**Files:**
- Create: `game/numbers.toml`, `game/fights/ogre_warlord.toml`, `src/fastcombat/numbers.py`
- Test: `tests/test_numbers.py`

**Interfaces:**
- Produces (all frozen dataclasses):
  - `HeroSpec(hp: int, die: int, attack_range: int, resource: str, pool: int, start: int, regen: int, crit_gain: int)`
  - `AbilitySpec(id: str, hero: str, cost: int = 0, cast: int = 0, hits: int = 0, range: int = 1, radius: int = 0, dice: tuple[int, int] = (0, 0), bonus: int = 0, cards: int = 0, value: int = 0, alt: int = 0, loud: bool = False, cooldown: int = 0)`
  - `Numbers(rules: dict[str, int], heroes: dict[str, HeroSpec], abilities: dict[str, AbilitySpec])`
  - `EnemySpec(type: str, tier: str = "normal", hp: int = 1, damage: int = 0, dice: tuple[int, int] = (0, 0), bonus: int = 0, move: int = 4, range: int = 1, prefers: str = "nearest", shielded: int = 0, poison_cards: int = 0, poison_value: int = 0, cast_every: int = 0, cast_first: int = 0, cast_heal: int = 0)`
  - `Spawn(type: str, pos: Pos, round: int = 0)`
  - `ScriptStep(name: str, kind: str, first: int, every: int, dice: tuple[int, int], radius: int = 0)`; `kind` is `"blast"`, `"heavy"` or `"throw"`
  - `FightDef(name: str, width: int, height: int, hero_starts: dict[str, Pos], extra_starts: list[Pos], enemy_types: dict[str, EnemySpec], spawns: list[Spawn], boss_script: list[ScriptStep])`
  - `load_numbers(path: Path, overrides: dict[str, object] | None = None) -> Numbers`. An override key is a dotted path such as `"abilities.meteor.cost"`, applied before checking.
  - `load_fight(path: Path) -> FightDef`
  - `NumbersError(ValueError)`: raised for any unknown key, missing required key, unknown `tier`/`prefers`/`kind`/`resource`, or an ability whose `hero` is not a hero or `"shared"`. The message contains the dotted path of the problem, for example `abilities.meteor.cots`.

- [ ] **Step 1: Write `game/numbers.toml`** exactly as below. These are first guesses; Task 15 changes them.

```toml
# Every number in the game. The simulator reads this file, and the class
# sheets and cards will be made from it. Change a number here, nowhere else.

[rules]
hero_move = 6
bleeding_cards = 3     # rounds to save a downed hero
haul_up_hp = 5         # HP after an ally hauls you up
combo_max = 5
seeds_max = 2
grit_per_attack = 1
max_rounds = 60        # the simulator gives up after this many

[heroes.warden]
hp = 60
die = 8
attack_range = 1
resource = "grit"
pool = 10
start = 2
regen = 0
crit_gain = 1          # grit

[heroes.rogue]
hp = 36
die = 6
attack_range = 1
resource = "energy"
pool = 10
start = 10
regen = 3
crit_gain = 1          # one extra combo point

[heroes.druid]
hp = 36
die = 6
attack_range = 8
resource = "energy"
pool = 10
start = 10
regen = 3
crit_gain = 1          # a Seed

[heroes.mage]
hp = 28
die = 4
attack_range = 10
resource = "mana"
pool = 30
start = 30
regen = 1
crit_gain = 2          # mana

# Ability fields: cost, cast (rounds), hits (channel), range, radius,
# dice = [count, sides], bonus, cards (how long it lasts), value (what each
# card is worth), alt (a second number, explained per ability), loud, cooldown.

[abilities.challenge]
hero = "warden"
cost = 1
range = 6
cards = 3

[abilities.war_cry]
hero = "warden"
cost = 3
radius = 3
cards = 1

[abilities.intercede]
hero = "warden"
cost = 2
range = 6
cards = 1
value = 4              # damage taken off each hit on the guarded ally

[abilities.chain_hook]
hero = "warden"
cost = 2
range = 6

[abilities.bulwark]
hero = "warden"
cost = 4
radius = 2             # how deep "behind you" goes
cards = 1
value = 8              # damage taken off the blast

[abilities.unbroken]
hero = "warden"
cost = 5
cards = 1

[abilities.backstab]
hero = "rogue"
cost = 4
dice = [2, 6]

[abilities.eviscerate]
hero = "rogue"
cost = 3
dice = [1, 6]          # per combo point
loud = true

[abilities.kidney_shot]
hero = "rogue"
cost = 3
cards = 1
alt = 2                # cards at full combo points

[abilities.cheap_shot]
hero = "rogue"
cost = 3
cards = 1

[abilities.sap]
hero = "rogue"
cost = 3
cards = 4

[abilities.shadowstep]
hero = "rogue"
cost = 2
range = 8

[abilities.vanish]
hero = "rogue"
cost = 4

[abilities.rejuvenation]
hero = "druid"
cost = 2
range = 8
cards = 4
value = 4

[abilities.regrowth]
hero = "druid"
cost = 4
cast = 1
range = 8
dice = [3, 6]
bonus = 4
loud = true

[abilities.swiftmend]
hero = "druid"
cost = 2               # free on an ally below half HP
range = 8
dice = [2, 6]
bonus = 2

[abilities.wild_growth]
hero = "druid"
cost = 5
range = 8
radius = 2
cards = 2
value = 4

[abilities.cleanse]
hero = "druid"
cost = 1
range = 8

[abilities.shadowmeld]
hero = "druid"
cost = 2
value = 3              # squares moved

[abilities.nourish]
hero = "druid"
range = 8
dice = [1, 6]
alt = 2                # energy back on the top face

[abilities.arcane_volley]
hero = "mage"
cost = 2               # per hit
hits = 3
range = 10
dice = [2, 6]
loud = true

[abilities.firebolt]
hero = "mage"
cost = 4
cast = 1
range = 10
dice = [4, 6]

[abilities.meteor]
hero = "mage"
cost = 10
cast = 2
range = 10
radius = 2
dice = [8, 6]

[abilities.frost_ring]
hero = "mage"
cost = 3
cards = 2

[abilities.blink]
hero = "mage"
cost = 2
range = 6

[abilities.quicken]
hero = "mage"
cost = 8
cards = 2

[abilities.polymorph]
hero = "mage"
cost = 4
cast = 1
range = 10
cards = 4

[abilities.disrupt]
hero = "shared"
range = 1
alt = 10               # the Mage's range
cooldown = 3
```

- [ ] **Step 2: Write `game/fights/ogre_warlord.toml`** exactly as below.

```toml
name = "Ogre Warlord"
width = 16
height = 12
extra_starts = [[2, 7], [1, 6], [2, 6], [1, 8]]

[hero_starts]
warden = [3, 6]
rogue = [2, 5]
druid = [1, 7]
mage = [1, 5]

[enemy_types.ogre]
tier = "boss"
hp = 320
dice = [2, 6]          # the boss rolls its melee hit
bonus = 2
move = 4
prefers = "nearest"

[enemy_types.shaman]   # stands back, poisons, and heals the boss unless stopped
hp = 24
damage = 3
range = 8
prefers = "random"
poison_cards = 3
poison_value = 2
cast_first = 2
cast_every = 4
cast_heal = 25

[enemy_types.wolf]     # runs past the tank
hp = 16
damage = 4
move = 7
prefers = "backline"

[enemy_types.brute]    # Shielded: ignores hits below 5
hp = 30
damage = 6
prefers = "nearest"
shielded = 5

[enemy_types.goblin]
tier = "fodder"
damage = 2
move = 5
prefers = "backline"

[[spawns]]
type = "ogre"
pos = [11, 6]
[[spawns]]
type = "brute"
pos = [10, 7]
[[spawns]]
type = "shaman"
pos = [13, 3]
[[spawns]]
type = "shaman"
pos = [13, 9]
[[spawns]]
type = "wolf"
pos = [10, 3]
[[spawns]]
type = "wolf"
pos = [10, 9]

# two waves of six goblins on the far edge
[[spawns]]
type = "goblin"
pos = [15, 3]
round = 6
[[spawns]]
type = "goblin"
pos = [15, 4]
round = 6
[[spawns]]
type = "goblin"
pos = [15, 5]
round = 6
[[spawns]]
type = "goblin"
pos = [15, 6]
round = 6
[[spawns]]
type = "goblin"
pos = [15, 7]
round = 6
[[spawns]]
type = "goblin"
pos = [15, 8]
round = 6
[[spawns]]
type = "goblin"
pos = [15, 3]
round = 12
[[spawns]]
type = "goblin"
pos = [15, 4]
round = 12
[[spawns]]
type = "goblin"
pos = [15, 5]
round = 12
[[spawns]]
type = "goblin"
pos = [15, 6]
round = 12
[[spawns]]
type = "goblin"
pos = [15, 7]
round = 12
[[spawns]]
type = "goblin"
pos = [15, 8]
round = 12

# The boss announces at most one of these per turn; the first that is due wins.
[[boss_script]]
name = "ground_slam"   # announced blast around the boss
kind = "blast"
first = 3
every = 4
radius = 2
dice = [3, 6]

[[boss_script]]
name = "skull_crusher" # announced heavy hit on whoever the boss is attacking
kind = "heavy"
first = 5
every = 5
dice = [6, 6]

[[boss_script]]
name = "boulder"       # not announced; thrown at a random hero not next to the boss
kind = "throw"
first = 2
every = 2
dice = [2, 6]
```

- [ ] **Step 3: Write the failing tests**

```python
import pytest
from pathlib import Path
from fastcombat.numbers import load_numbers, load_fight, NumbersError

GAME = Path(__file__).parent.parent / "game"

def test_the_real_files_load():
    n = load_numbers(GAME / "numbers.toml")
    f = load_fight(GAME / "fights" / "ogre_warlord.toml")
    assert n.heroes["mage"].pool == 30 and n.heroes["rogue"].regen == 3
    assert n.abilities["meteor"].cast == 2 and n.abilities["meteor"].dice == (8, 6)
    assert n.abilities["eviscerate"].loud is True
    assert len(n.abilities) == 28
    assert f.enemy_types["brute"].shielded == 5
    assert sum(1 for s in f.spawns if s.round == 6) == 6
    assert f.hero_starts["warden"] == (3, 6)

def test_an_override_changes_one_number():
    n = load_numbers(GAME / "numbers.toml", {"abilities.meteor.cost": 12})
    assert n.abilities["meteor"].cost == 12

def test_a_typo_names_the_place(tmp_path):
    text = (GAME / "numbers.toml").read_text().replace("cost = 10", "cots = 10")
    p = tmp_path / "n.toml"; p.write_text(text)
    with pytest.raises(NumbersError, match=r"abilities\.meteor\.cots"):
        load_numbers(p)

def test_a_missing_hero_number_names_the_place(tmp_path):
    text = (GAME / "numbers.toml").read_text().replace("hp = 28\n", "")
    p = tmp_path / "n.toml"; p.write_text(text)
    with pytest.raises(NumbersError, match=r"heroes\.mage\.hp"):
        load_numbers(p)

def test_an_override_for_something_that_is_not_there_fails():
    with pytest.raises(NumbersError, match=r"abilities\.meteor\.nope"):
        load_numbers(GAME / "numbers.toml", {"abilities.meteor.nope": 1})
```

- [ ] **Step 4:** Run `uv run pytest tests/test_numbers.py -v`. Expected: FAIL, module not found.
- [ ] **Step 5:** Implement `numbers.py`. TOML arrays for `dice` and positions become tuples.
- [ ] **Step 6:** Run again. Expected: 5 passed.
- [ ] **Step 7: Commit.** Message: `Add the numbers file, the test fight and their loader`.

---

### Task 4: Units, damage, healing and going down

**Files:**
- Create: `src/fastcombat/units.py`, `src/fastcombat/combat.py`
- Modify: `tests/helpers.py`
- Test: `tests/test_combat.py`

**Interfaces:**
- Consumes: `Numbers`, `FightDef`, `EnemySpec`, `Dice`.
- Produces in `units.py`:

```python
@dataclass
class Cast:
    ability: str
    target: str | None        # unit id
    center: Pos | None        # for area casts
    actions_left: int         # act steps still to spend (casts)
    hits_left: int            # channel hits still to come
    is_channel: bool

@dataclass
class Announced:              # an enemy cast waiting to land
    name: str
    kind: str                 # "blast" "heavy" "mend"
    lands_round: int
    target: str | None
    area: frozenset[Pos]
    dice: tuple[int, int]
    heal: int = 0

@dataclass
class Hero:
    id: str; cls: str; pos: Pos; hp: int; max_hp: int; resource: int
    stacks: dict[str, Stack]
    combo: int = 0; seeds: int = 0; hidden: bool = False
    cast: Cast | None = None
    down: bool = False; out: bool = False; wounds: int = 0
    # property: up -> not down and not out

@dataclass
class Enemy:
    id: str; spec: EnemySpec; pos: Pos; hp: int
    stacks: dict[str, Stack]
    pulled_by: str | None = None
    announced: Announced | None = None
    target: str | None = None     # who it attacked or will attack this GM turn
    dead: bool = False
    # property: controlled -> has a "stun", "sap" or "sheep" stack

@dataclass
class Tally:                  # what happened, for the report
    damage: dict[str, int]; auto_damage: dict[str, int]; healing: dict[str, int]
    lowest_hp: dict[str, float]            # lowest fraction of max HP seen
    times_down: dict[str, int]
    resource_by_round: dict[str, list[int]]
    starved_rounds: dict[str, int]

@dataclass
class FightState:
    numbers: Numbers; fight: FightDef; dice: Dice
    heroes: dict[str, Hero]; enemies: dict[str, Enemy]
    round: int; tally: Tally
    marked: dict[str, frozenset[Pos]]      # hero blasts waiting to land, by hero id
    # helpers: warden() -> Hero | None (first up Warden), living_enemies(),
    #          up_heroes(), occupied() -> set[Pos] (heroes not out + living enemies),
    #          danger_squares() -> set[Pos] (all announced enemy blast areas + marked)
```

- `new_state(numbers: Numbers, fight: FightDef, party: list[str], seed: int) -> FightState`: heroes placed at `hero_starts[cls]`, repeats and unknown-to-the-map classes at `extra_starts` in order; resource at `start`; every Rogue starts `hidden`; enemies from spawns with `round == 0`; `round = 1`.
- Produces in `combat.py`:
  - `add_stack(unit, name: str, cards: int, value: int = 0) -> None` (replaces any stack of that name)
  - `tick_stacks(unit) -> None`: one card off every stack, empty stacks removed
  - `damage_enemy(state, hero_id: str, enemy: Enemy, amount: int, *, auto: bool = False, loud: bool = False) -> int`: returns damage done. Order: a hit below `shielded` does 0 and stops; fodder dies to any hit of 1 or more; any damage removes `sap` and `sheep`; record in tally; then Loud (see Task 5's `apply_loud`, called from here once it exists).
  - `damage_hero(state, hero: Hero, amount: int, *, attacker: Enemy | None, blast: bool = False) -> int`: takes off `guarded.value`, and `bulwark.value` when `blast`; never below 0; with an `unbroken` stack HP stops at 1; breaks nothing; a Warden hit by an enemy attack (`attacker` set, not `blast`) gains `rules.grit_per_attack` up to the pool, even if the damage was reduced to 0; at 0 HP calls `go_down`.
  - `go_down(state, hero) -> None`: `down = True`, cast dropped, `hidden = False`, all stacks cleared, then a `bleeding` stack of `rules.bleeding_cards - hero.wounds`; if that is 0 or less the hero is `out` instead.
  - `get_up(state, hero, hp: int) -> None`: `down = False`, bleeding removed, `wounds += 1`, HP set to `min(hp, max_hp)`.
  - `heal_hero(state, healer_id: str, target: Hero, amount: int) -> int`: nothing for a hero who is `out`; gets a downed hero up at `amount` HP; otherwise adds up to max; records real healing only.
  - `top_of_party_turn_cards(state) -> None`: for each hero not out: heal stacks (`rejuvenation`, `wild_growth`) heal their value (credited to the first Druid in the party, or the hero if none); `poison` deals its value through `damage_hero(attacker=None)`; then every stack the hero had at the start of this call loses one card, once; a `bleeding` stack that reaches 0 means the hero is `out`.
- `tests/helpers.py` adds `state(party=("warden","rogue","druid","mage"), rolls=None, seed=1) -> FightState` (real game files; `scripted(*rolls)` when `rolls` is given) and `enemy(state, type: str, pos: Pos) -> Enemy` (adds one of that type from the fight file).

- [ ] **Step 1: Write the failing tests**

```python
from tests.helpers import state, enemy
from fastcombat.combat import *

def test_shielded_ignores_small_hits():
    s = state(); b = enemy(s, "brute", (8, 8))
    assert damage_enemy(s, "rogue", b, 4) == 0 and b.hp == 30
    assert damage_enemy(s, "rogue", b, 5) == 5 and b.hp == 25

def test_fodder_dies_to_any_hit():
    s = state(); g = enemy(s, "goblin", (8, 8))
    damage_enemy(s, "mage", g, 1); assert g.dead

def test_damage_wakes_a_sapped_enemy():
    s = state(); w = enemy(s, "wolf", (8, 8)); add_stack(w, "sap", 4)
    damage_enemy(s, "mage", w, 1); assert "sap" not in w.stacks

def test_guarded_takes_damage_off():
    s = state(); m = s.heroes["mage"]; add_stack(m, "guarded", 1, 4)
    assert damage_hero(s, m, 6, attacker=None) == 2

def test_unbroken_stops_at_one():
    s = state(); w = s.heroes["warden"]; add_stack(w, "unbroken", 1)
    damage_hero(s, w, 999, attacker=None); assert w.hp == 1 and not w.down

def test_warden_gains_grit_when_attacked():
    s = state(); w = s.heroes["warden"]; o = enemy(s, "wolf", (4, 6))
    damage_hero(s, w, 4, attacker=o); assert w.resource == 3

def test_going_down_and_bleeding_out():
    s = state(); m = s.heroes["mage"]
    damage_hero(s, m, 99, attacker=None)
    assert m.down and m.stacks["bleeding"].cards == 3
    for _ in range(3): top_of_party_turn_cards(s)
    assert m.out

def test_any_heal_gets_you_up_with_a_wound():
    s = state(); m = s.heroes["mage"]; damage_hero(s, m, 99, attacker=None)
    heal_hero(s, "druid", m, 7)
    assert not m.down and m.hp == 7 and m.wounds == 1

def test_each_wound_shortens_the_next_bleed():
    s = state(); m = s.heroes["mage"]; m.wounds = 2
    damage_hero(s, m, 99, attacker=None); assert m.stacks["bleeding"].cards == 1
    s2 = state(); m2 = s2.heroes["mage"]; m2.wounds = 3
    damage_hero(s2, m2, 99, attacker=None); assert m2.out

def test_heal_cards_heal_one_card_a_turn():
    s = state(); w = s.heroes["warden"]; w.hp = 40; add_stack(w, "rejuvenation", 4, 4)
    top_of_party_turn_cards(s)
    assert w.hp == 44 and w.stacks["rejuvenation"].cards == 3

def test_a_second_rogue_gets_its_own_id_and_square():
    s = state(party=("rogue", "rogue"))
    assert set(s.heroes) == {"rogue", "rogue2"}
    assert s.heroes["rogue"].pos != s.heroes["rogue2"].pos and s.warden() is None
```

- [ ] **Step 2:** Run `uv run pytest tests/test_combat.py -v`. Expected: FAIL, module not found.
- [ ] **Step 3:** Implement `units.py`, `combat.py` and the helpers.
- [ ] **Step 4:** Run again. Expected: 11 passed.
- [ ] **Step 5: Commit.** Message: `Add heroes, enemies, damage, healing and going down`.

---

### Task 5: Who an enemy attacks

**Files:**
- Create: `src/fastcombat/targeting.py`
- Modify: `src/fastcombat/combat.py` (call `apply_loud` from `damage_enemy` when `loud=True`)
- Test: `tests/test_targeting.py`

**Interfaces:**
- Produces:
  - `held(state, enemy) -> bool`: an up Warden exists and the enemy is adjacent to them
  - `choose_target(state, enemy) -> Hero | None`: the first rule that gives an up hero wins:
    1. `taunt` stack: the Warden
    2. `pulled_by`: that hero
    3. `held`: the Warden
    4. `spec.prefers`: `"nearest"` (closest up hero, ties by id), `"backline"` (the up non-Warden hero with the lowest max HP, ties by id; the Warden only if no one else), `"random"` (`state.dice.roll` over up heroes sorted by id)
    Then, if the chosen hero has an `interceded` stack, the enemy has no `taunt` stack, and a Warden is up: the Warden instead. Returns `None` when no hero is up.
  - `can_move(state, enemy) -> bool`: false when `held` with no `pulled_by`, or `rooted`, or `controlled`
  - `apply_loud(state, hero_id: str, enemy: Enemy) -> None`: one `taunt` card off if it has any; otherwise `pulled_by = hero_id`
  - `loud_heal(state, hero_id: str) -> None`: every living enemy with no `taunt` stack that is not `held` gets `pulled_by = hero_id`
  - `drop_pulls(state, hero_id: str) -> None`: clears `pulled_by` on every enemy pulled by that hero

- [ ] **Step 1: Write the failing tests**

```python
from tests.helpers import state, enemy
from fastcombat.combat import add_stack, damage_enemy, damage_hero
from fastcombat.targeting import *

def test_an_enemy_next_to_the_warden_must_attack_the_warden():
    s = state(); w = enemy(s, "wolf", (4, 6))          # warden is at (3, 6)
    assert choose_target(s, w).id == "warden" and not can_move(s, w)

def test_a_loose_wolf_goes_for_the_back_line():
    s = state(); w = enemy(s, "wolf", (10, 3))
    assert choose_target(s, w).id == "mage" and can_move(s, w)

def test_taunt_cards_work_at_any_distance():
    s = state(); w = enemy(s, "wolf", (10, 3)); add_stack(w, "taunt", 3)
    assert choose_target(s, w).id == "warden"

def test_loud_strips_a_taunt_card_before_it_pulls():
    s = state(); w = enemy(s, "wolf", (4, 6)); add_stack(w, "taunt", 1)
    damage_enemy(s, "rogue", w, 1, loud=True)
    assert "taunt" not in w.stacks and w.pulled_by is None
    damage_enemy(s, "rogue", w, 1, loud=True)
    assert w.pulled_by == "rogue"
    assert choose_target(s, w).id == "rogue" and can_move(s, w)   # beats the weak hold

def test_intercede_sends_untaunted_attackers_to_the_warden():
    s = state(); w = enemy(s, "wolf", (10, 3)); add_stack(s.heroes["mage"], "interceded", 1)
    assert choose_target(s, w).id == "warden"

def test_a_loud_heal_pulls_everything_with_no_hold():
    s = state(); near = enemy(s, "wolf", (4, 6)); far = enemy(s, "wolf", (10, 3))
    loud_heal(s, "druid")
    assert far.pulled_by == "druid" and near.pulled_by is None

def test_downed_heroes_are_ignored():
    s = state(); w = enemy(s, "wolf", (10, 3))
    damage_hero(s, s.heroes["mage"], 99, attacker=None)
    assert choose_target(s, w).id != "mage"

def test_with_no_warden_taunted_enemies_fall_back_to_what_they_prefer():
    s = state(party=("rogue", "mage")); w = enemy(s, "wolf", (10, 3)); add_stack(w, "taunt", 3)
    assert choose_target(s, w).id == "mage"

def test_with_nobody_up_there_is_no_target():
    s = state(party=("mage",)); w = enemy(s, "wolf", (10, 3))
    damage_hero(s, s.heroes["mage"], 99, attacker=None)
    assert choose_target(s, w) is None
```

- [ ] **Step 2:** Run `uv run pytest tests/test_targeting.py -v`. Expected: FAIL, module not found.
- [ ] **Step 3:** Implement `targeting.py`; wire `apply_loud` into `damage_enemy`.
- [ ] **Step 4:** Run `uv run pytest -v`. Expected: all pass.
- [ ] **Step 5: Commit.** Message: `Add taunts, holds and Loud: who an enemy attacks`.

---

### Task 6: Abilities core, casts and channels

**Files:**
- Create: `src/fastcombat/casting.py`, `src/fastcombat/abilities/__init__.py`
- Test: `tests/test_casting.py`

**Interfaces:**
- Produces in `abilities/__init__.py`:

```python
@dataclass(frozen=True)
class Action:
    kind: str                  # "auto" "ability" "continue" "haul_up" "none"
    ability: str | None = None
    target: str | None = None  # unit id
    pos: Pos | None = None     # centre of an area, or where to land

Effect = Callable[[FightState, Hero, AbilitySpec, Action], None]
EFFECTS: dict[str, Effect]     # filled by the class files with @effect("id")
CHECKS: dict[str, Callable[[FightState, Hero, AbilitySpec, Action], bool]]  # extra rules, @check("id")

def cost_of(state, hero, spec, action) -> int      # spec.cost unless a @cost("id") rule says otherwise
def can_use(state, hero, ability_id: str, action: Action) -> bool
def use_ability(state, hero, action: Action) -> bool
def resolve(state, hero, spec, action) -> bool     # pay, run the effect, start cooldown
```

  - `can_use` is false when: the hero is not up; the ability belongs to another class (and is not `"shared"`); a `cd:<id>` stack exists; the hero cannot pay `cost_of` now (for a channel: one hit's cost); the target unit is missing, dead or out; the target or `pos` is farther than `range` (Disrupt uses `alt` as the range for a Mage); or its `CHECKS` entry says no.
  - `use_ability` returns false and does nothing when `can_use` is false. Otherwise: `cast > 0` starts a cast and pays nothing; `hits > 0` starts a channel and resolves the first hit now; anything else resolves now. Using any ability ends `hidden` after the effect has run.
  - `resolve` pays `cost_of` (it returns false and does nothing if the hero cannot pay or the target is now missing, dead or out), runs `EFFECTS[id]`, and adds a `cd:<id>` stack of `cooldown` cards when `cooldown > 0`.
- Produces in `casting.py`:
  - `start_cast(state, hero, spec, action) -> None`: `Cast(actions_left = spec.cast - 1, ...)`; an area cast records `state.marked[hero.id] = within(action.pos, spec.radius, ...)`
  - `start_channel(state, hero, spec, action) -> None`: `Cast(hits_left = spec.hits, is_channel=True)`
  - `continue_cast(state, hero) -> None`: for a cast, `actions_left -= 1`; for a channel, resolve one hit, `hits_left -= 1`, and drop the cast at 0 or if the hit could not resolve
  - `land_casts(state) -> None`: top of the party turn. Every non-channel cast with `actions_left == 0` resolves through `resolve` and is dropped, along with its `marked` entry
  - `drop_cast(state, hero) -> None`: cancel or break; clears `marked`; costs nothing
  - `may_move(hero) -> bool`: false while a non-channel cast is active

  A hero who starts a cast in the act step of turn T with `cast = N` continues in the act steps of turns T+1 to T+N-1, and it lands at the top of turn T+N.

- [ ] **Step 1: Write the failing tests.** They register two throwaway abilities so they do not depend on the class files.

```python
import pytest
from dataclasses import replace
from tests.helpers import state, enemy
from fastcombat import abilities as ab
from fastcombat.abilities import Action, use_ability, can_use, effect
from fastcombat.casting import land_casts, continue_cast, drop_cast, may_move
from fastcombat.combat import top_of_party_turn_cards

@pytest.fixture
def s():
    st = state(party=("mage",))
    hits = []
    spec = st.numbers.abilities["firebolt"]
    st.numbers.abilities["t_bolt"] = replace(spec, id="t_bolt", cast=2, cost=4)
    st.numbers.abilities["t_beam"] = replace(spec, id="t_beam", cast=0, hits=3, cost=2)
    st.numbers.abilities["t_kick"] = replace(spec, id="t_kick", cast=0, cost=0, cooldown=3)
    for name in ("t_bolt", "t_beam", "t_kick"):
        effect(name)(lambda state, hero, spec, action: hits.append(action.target))
    st.hits = hits
    yield st
    for name in ("t_bolt", "t_beam", "t_kick"):
        ab.EFFECTS.pop(name, None)

def test_a_two_round_cast_takes_two_actions_and_lands_the_turn_after(s):
    m = s.heroes["mage"]; w = enemy(s, "wolf", (6, 5))
    assert use_ability(s, m, Action("ability", "t_bolt", "wolf1"))
    assert m.resource == 30 and not may_move(m)
    land_casts(s); assert s.hits == []          # top of turn T+1: not yet
    continue_cast(s, m)                         # act step T+1
    land_casts(s)                               # top of turn T+2
    assert s.hits == ["wolf1"] and m.resource == 26 and m.cast is None

def test_a_cancelled_cast_costs_nothing(s):
    m = s.heroes["mage"]; enemy(s, "wolf", (6, 5))
    use_ability(s, m, Action("ability", "t_bolt", "wolf1")); drop_cast(s, m)
    land_casts(s); assert s.hits == [] and m.resource == 30 and may_move(m)

def test_a_cast_fizzles_free_if_the_target_died(s):
    m = s.heroes["mage"]; w = enemy(s, "wolf", (6, 5))
    use_ability(s, m, Action("ability", "t_bolt", "wolf1")); continue_cast(s, m)
    w.dead = True; land_casts(s)
    assert s.hits == [] and m.resource == 30 and m.cast is None

def test_a_channel_hits_now_pays_per_hit_and_allows_moving(s):
    m = s.heroes["mage"]; enemy(s, "wolf", (6, 5))
    use_ability(s, m, Action("ability", "t_beam", "wolf1"))
    assert s.hits == ["wolf1"] and m.resource == 28 and may_move(m)
    continue_cast(s, m); continue_cast(s, m)
    assert len(s.hits) == 3 and m.resource == 24 and m.cast is None

def test_out_of_range_or_too_poor_is_refused(s):
    m = s.heroes["mage"]; enemy(s, "wolf", (15, 11))
    assert not can_use(s, m, "t_bolt", Action("ability", "t_bolt", "wolf1"))
    enemy(s, "wolf", (6, 5)); m.resource = 3
    assert not can_use(s, m, "t_bolt", Action("ability", "t_bolt", "wolf2"))

def test_a_cooldown_is_a_card_stack_on_the_hero(s):
    m = s.heroes["mage"]; enemy(s, "wolf", (6, 5)); a = Action("ability", "t_kick", "wolf1")
    assert use_ability(s, m, a) and not can_use(s, m, "t_kick", a)
    for _ in range(3): top_of_party_turn_cards(s)
    assert can_use(s, m, "t_kick", a)
```

- [ ] **Step 2:** Run `uv run pytest tests/test_casting.py -v`. Expected: FAIL, module not found.
- [ ] **Step 3:** Implement both files. `effect`, `check` and `cost` are decorators that fill the three dicts.
- [ ] **Step 4:** Run again. Expected: 6 passed.
- [ ] **Step 5: Commit.** Message: `Add the ability core: costs, casts, channels and cooldowns`.

---

### Task 7: The round loop, auto-attacks and plain enemies

**Files:**
- Create: `src/fastcombat/fight.py`, `src/fastcombat/enemy_ai.py`, `src/fastcombat/policies.py` (base only)
- Test: `tests/test_fight.py`

**Interfaces:**
- Produces in `policies.py`:

```python
class Policy(Protocol):
    def move(self, state: FightState, hero: Hero) -> Pos: ...
    def act(self, state: FightState, hero: Hero) -> Action: ...

class AutoOnly:    # walk to the nearest living enemy that is not controlled, auto-attack it
```

- Produces in `enemy_ai.py`:
  - `gm_turn(state) -> None`: (1) land announced casts whose `lands_round == state.round` (Task 12 fills this in; a no-op for now); (2) spawn `fight.spawns` with `round == state.round` on their square, or the nearest free one; (3) each living enemy in id order, skipped if `controlled`: `target = choose_target`; if `can_move`, `walk` toward the target with `reach = spec.range`, `blocked = state.occupied()`; if the target is within `spec.range`, hit it for `spec.damage`, or `dice.roll_many(*spec.dice, spec.bonus)` when `spec.dice[0] > 0`, through `damage_hero(attacker=enemy)`; a `poison_cards` enemy also adds a `poison` stack; then `pulled_by = None`; (4) boss announcements (Task 12); (5) `tick_stacks` on every living enemy.
- Produces in `fight.py`:

```python
@dataclass
class FightResult:
    won: bool; timeout: bool; rounds: int
    party: list[str]; seed: int
    heroes_out: list[str]
    tally: Tally
    end_resource: dict[str, int]

def party_turn(state, policies: dict[str, Policy]) -> None
def auto_attack(state, hero, enemy) -> None
def run_fight(numbers, fight, party: list[str], policies: dict[str, Policy] | None = None, seed: int = 0) -> FightResult
```

  - `party_turn`, heroes in id order at each step: (1) `top_of_party_turn_cards`, then each up hero gains `regen` up to `pool`, then `land_casts`; (2) each up hero: `dest = policy.move(...)`; if `dest != hero.pos` and the hero has a non-channel cast, `drop_cast`; the hero moves to `dest` only if it is within `rules.hero_move` and not occupied, otherwise stays; (3) each up hero: `action = policy.act(...)`; `"continue"` calls `continue_cast` (treated as `"none"` when there is no cast); anything else first drops any active cast; `"auto"` calls `auto_attack`; `"ability"` calls `use_ability` and falls back to `"none"` when refused; `"haul_up"` needs an adjacent downed target and calls `get_up(hp = rules.haul_up_hp)`. After step 3, record each hero's resource in `tally.resource_by_round`, and count a starved round for an up hero whose resource is below the cheapest non-zero cost among their own abilities.
  - `auto_attack`: needs the enemy within `HeroSpec.attack_range`; roll `dice.auto_attack(die)`, and a second time added on when the hero has a `quicken` stack; `damage_enemy(..., auto=True)`; a crit gives the class hook: Warden `crit_gain` grit, Rogue `crit_gain` extra combo points, Druid `crit_gain` Seeds (up to `rules.seeds_max`), Mage `crit_gain` mana. A Rogue gains 1 combo point per roll that did not miss (up to `rules.combo_max`). Ends `hidden`.
  - `run_fight`: policies default to `policies.default_policy(cls)` (Task 13; until then `AutoOnly`), keyed by hero id. Loop: `party_turn`; won if no enemy is alive and no spawn is still to come; `gm_turn`; lost if no hero is up; `round += 1`; at `round > rules.max_rounds` stop with `timeout=True, won=False`.

- [ ] **Step 1: Write the failing tests**

```python
from tests.helpers import state, enemy, GAME
from fastcombat.numbers import load_numbers, load_fight
from fastcombat.fight import run_fight, party_turn, auto_attack
from fastcombat.enemy_ai import gm_turn
from fastcombat.policies import AutoOnly
from fastcombat.combat import add_stack
from dataclasses import replace

N = load_numbers(GAME / "numbers.toml")
F = load_fight(GAME / "fights" / "ogre_warlord.toml")
WOLF_ONLY = replace(F, spawns=[s for s in F.spawns if s.type == "wolf"], boss_script=[])
NO_ENEMY_DAMAGE = replace(F, spawns=[s for s in F.spawns if s.type == "brute"], boss_script=[],
    enemy_types={**F.enemy_types, "brute": replace(F.enemy_types["brute"], hp=10**6, damage=0)})

def test_rogue_builds_combo_points_and_a_crit_gives_two():
    s = state(rolls=[3, 6, 2]); r = s.heroes["rogue"]; w = enemy(s, "wolf", (3, 5))
    auto_attack(s, r, w); assert r.combo == 1 and w.hp == 13
    auto_attack(s, r, w); assert r.combo == 3 and w.hp == 5

def test_quicken_rolls_two_dice():
    s = state(rolls=[3, 4]); r = s.heroes["rogue"]; w = enemy(s, "wolf", (3, 5))
    add_stack(r, "quicken", 2); auto_attack(s, r, w); assert w.hp == 9

def test_a_held_enemy_stays_and_hits_the_warden():
    s = state(); w = enemy(s, "wolf", (4, 6)); gm_turn(s)
    assert w.pos == (4, 6) and s.heroes["warden"].hp == 56 and s.heroes["warden"].resource == 3

def test_a_stunned_enemy_does_nothing_and_the_card_comes_off_after():
    s = state(); w = enemy(s, "wolf", (4, 6)); add_stack(w, "stun", 1); gm_turn(s)
    assert s.heroes["warden"].hp == 60 and "stun" not in w.stacks

def test_nobody_ever_shares_a_square():
    s = state()
    for i in range(8): enemy(s, "wolf", (10 + i % 4, 2 + i // 4))
    for _ in range(6):
        party_turn(s, {h: AutoOnly() for h in s.heroes}); gm_turn(s); s.round += 1
        spots = [h.pos for h in s.heroes.values() if not h.out] + [e.pos for e in s.living_enemies()]
        assert len(spots) == len(set(spots))

def test_same_seed_same_fight():
    a = run_fight(N, WOLF_ONLY, ["warden", "rogue", "druid", "mage"], seed=7)
    b = run_fight(N, WOLF_ONLY, ["warden", "rogue", "druid", "mage"], seed=7)
    assert (a.won, a.rounds, a.tally.damage) == (b.won, b.rounds, b.tally.damage)

def test_four_heroes_beat_two_wolves():
    r = run_fight(N, WOLF_ONLY, ["warden", "rogue", "druid", "mage"], seed=1)
    assert r.won and not r.timeout and r.rounds < 20

def test_a_fight_nobody_can_finish_stops_as_a_timeout_and_a_loss():
    r = run_fight(N, NO_ENEMY_DAMAGE, ["warden"], seed=1)
    assert r.timeout and not r.won and r.rounds == N.rules["max_rounds"]
```

- [ ] **Step 2:** Run `uv run pytest tests/test_fight.py -v`. Expected: FAIL, module not found.
- [ ] **Step 3:** Implement the three files. `tests/helpers.py` exports `GAME`.
- [ ] **Step 4:** Run `uv run pytest -v`. Expected: all pass.
- [ ] **Step 5: Commit.** Message: `Add the round loop, auto-attacks and the enemy turn`.

---

### Task 8: Warden abilities

**Files:**
- Create: `src/fastcombat/abilities/warden.py`; import it from `abilities/__init__.py`
- Test: `tests/test_warden.py`

**Interfaces:**
- Consumes: `effect`, `check`, `add_stack`, `walk`, `within`, `behind`.
- Produces effects (the action's `target` is an enemy id unless noted):
  - `challenge`: `taunt` stack of `cards` on the enemy
  - `war_cry`: `taunt` stack of `cards` on every living enemy within `radius`
  - `intercede` (target: ally id): the Warden moves to the free square adjacent to the ally that is nearest to the Warden (stays put if none); ally gets `guarded` (`cards`, `value`) and `interceded` (`cards`)
  - `chain_hook`: the enemy moves to the free square adjacent to the Warden that is nearest to the enemy's old square; refused by its check for a boss or when no adjacent square is free
  - `bulwark` (`pos`: the blast's source square): every ally in `behind(warden.pos, pos, radius)` and the Warden get a `bulwark` stack (`cards`, `value`)
  - `unbroken`: `unbroken` stack of `cards` on the Warden

- [ ] **Step 1: Write the failing tests**

```python
from tests.helpers import state, enemy
from fastcombat.abilities import Action, use_ability
from fastcombat.targeting import choose_target
from fastcombat.combat import damage_hero
from fastcombat.grid import adjacent

def use(s, hero, ability, target=None, pos=None):
    return use_ability(s, s.heroes[hero], Action("ability", ability, target, pos))

def test_challenge_puts_three_taunt_cards_on_and_costs_grit():
    s = state(); w = enemy(s, "wolf", (8, 6))
    assert use(s, "warden", "challenge", "wolf1")
    assert w.stacks["taunt"].cards == 3 and s.heroes["warden"].resource == 1

def test_war_cry_taunts_everything_near_for_one_turn():
    s = state(); s.heroes["warden"].resource = 10
    a = enemy(s, "wolf", (5, 6)); b = enemy(s, "wolf", (6, 8)); far = enemy(s, "wolf", (12, 6))
    use(s, "warden", "war_cry")
    assert a.stacks["taunt"].cards == 1 and b.stacks["taunt"].cards == 1 and "taunt" not in far.stacks

def test_chain_hook_drags_a_loose_enemy_into_the_ring():
    s = state(); w = enemy(s, "wolf", (8, 6))
    assert use(s, "warden", "chain_hook", "wolf1")
    assert adjacent(w.pos, s.heroes["warden"].pos) and choose_target(s, w).id == "warden"

def test_chain_hook_cannot_move_the_boss():
    s = state(); enemy(s, "ogre", (8, 6))
    assert not use(s, "warden", "chain_hook", "ogre1")

def test_intercede_leaps_guards_and_takes_the_attacker():
    s = state(); m = s.heroes["mage"]; w = enemy(s, "wolf", (1, 4))
    assert use(s, "warden", "intercede", "mage")
    assert adjacent(s.heroes["warden"].pos, m.pos)
    assert damage_hero(s, m, 6, attacker=None) == 2
    assert choose_target(s, w).id == "warden"

def test_bulwark_covers_allies_behind_the_shield_against_a_blast():
    s = state(); s.heroes["warden"].resource = 10
    s.heroes["rogue"].pos = (2, 6)                      # directly behind, blast from the east
    use(s, "warden", "bulwark", pos=(6, 6))
    assert damage_hero(s, s.heroes["rogue"], 12, attacker=None, blast=True) == 4
    assert damage_hero(s, s.heroes["rogue"], 12, attacker=None, blast=False) == 12

def test_unbroken_keeps_the_warden_on_one_hp():
    s = state(); w = s.heroes["warden"]; w.resource = 10
    use(s, "warden", "unbroken"); damage_hero(s, w, 500, attacker=None)
    assert w.hp == 1 and w.up
```

- [ ] **Step 2:** Run `uv run pytest tests/test_warden.py -v`. Expected: FAIL (abilities refused: no effect registered).
- [ ] **Step 3:** Implement `abilities/warden.py`.
- [ ] **Step 4:** Run again. Expected: 7 passed.
- [ ] **Step 5: Commit.** Message: `Add the Warden's abilities`.

---

### Task 9: Rogue abilities

**Files:**
- Create: `src/fastcombat/abilities/rogue.py`; import it from `abilities/__init__.py`
- Test: `tests/test_rogue.py`

**Interfaces:**
- Produces effects and checks:
  - `backstab`: check: the Rogue is `hidden`, or the enemy's `target` is set and is not this Rogue, or the enemy is `held` or has a `taunt` stack; needs adjacency. Effect: `roll_many(*dice, bonus)`, doubled when `hidden`; 1 combo point (up to `combo_max`).
  - `eviscerate`: check: `combo >= 1`, adjacent. Effect: `roll_many(dice[0] * combo, dice[1])`, `loud` from the spec; `combo = 0`.
  - `kidney_shot`: check: `combo >= 1`, adjacent, not a boss. Effect: `stun` stack of `alt` cards at `combo == combo_max`, else `cards`; `combo = 0`.
  - `cheap_shot`: adjacent. Effect: `stun` stack of `cards`.
  - `sap`: check: `hidden`, the enemy is not a boss; `range` is 1. Effect: `sap` stack of `cards`.
  - `shadowstep`: the Rogue moves to the free square adjacent to the enemy that is nearest to the Rogue; refused when none is free.
  - `vanish`: `drop_pulls`, then `hidden = True`. (`use_ability` clears `hidden` after an effect; Vanish is the one ability that leaves it set.)
  - Any `stun` put on an enemy also clears its `announced` cast, boss included. A boss never receives the `stun`, `sap` or `sheep` stack itself. Put this in one helper, `combat.control(state, enemy, name: str, cards: int) -> None`, used by every ability that stuns, saps or sheeps.

- [ ] **Step 1: Write the failing tests**

```python
from tests.helpers import state, enemy
from tests.test_warden import use
from fastcombat.combat import add_stack
from fastcombat.units import Announced

def near(s, type="wolf"):
    return enemy(s, type, (3, 5))        # adjacent to the rogue at (2, 5) and the warden at (3, 6)

def test_backstab_from_hiding_doubles_and_works_on_anyone():
    s = state(party=("rogue",), rolls=[3, 4]); w = enemy(s, "brute", (3, 5))
    assert use(s, "rogue", "backstab", "brute1")
    assert w.hp == 30 - 14 and s.heroes["rogue"].combo == 1 and not s.heroes["rogue"].hidden

def test_backstab_needs_the_enemy_to_be_busy_with_someone_else():
    s = state(party=("rogue",)); s.heroes["rogue"].hidden = False; near(s)
    assert not use(s, "rogue", "backstab", "wolf1")
    s2 = state(); s2.heroes["rogue"].hidden = False; near(s2)   # held by the warden
    assert use(s2, "rogue", "backstab", "wolf1")

def test_eviscerate_spends_every_point_and_is_loud():
    s = state(rolls=[2, 2, 2]); r = s.heroes["rogue"]; r.combo = 3; w = near(s)
    add_stack(w, "taunt", 2); use(s, "rogue", "eviscerate", "wolf1")
    assert w.hp == 10 and r.combo == 0 and w.stacks["taunt"].cards == 1

def test_kidney_shot_stuns_two_rounds_at_full_points():
    s = state(); r = s.heroes["rogue"]; r.combo = 5; w = near(s)
    use(s, "rogue", "kidney_shot", "wolf1"); assert w.stacks["stun"].cards == 2
    s2 = state(); s2.heroes["rogue"].combo = 2; w2 = near(s2)
    use(s2, "rogue", "kidney_shot", "wolf1"); assert w2.stacks["stun"].cards == 1

def test_sap_only_from_hiding_and_never_on_a_boss():
    s = state(); w = near(s); assert use(s, "rogue", "sap", "wolf1") and w.stacks["sap"].cards == 4
    assert not use(s, "rogue", "sap", "wolf1")            # no longer hidden
    s2 = state(); near(s2, "ogre"); assert not use(s2, "rogue", "sap", "ogre1")

def test_vanish_drops_the_pull_and_hides():
    s = state(); r = s.heroes["rogue"]; r.hidden = False; w = near(s); w.pulled_by = "rogue"
    use(s, "rogue", "vanish"); assert w.pulled_by is None and r.hidden

def test_a_stun_breaks_a_boss_cast_but_does_not_stun_the_boss():
    s = state(); o = near(s, "ogre")
    o.announced = Announced("skull_crusher", "heavy", s.round + 1, "warden", frozenset(), (6, 6))
    use(s, "rogue", "cheap_shot", "ogre1")
    assert o.announced is None and "stun" not in o.stacks

def test_shadowstep_lands_next_to_the_enemy():
    s = state(); enemy(s, "wolf", (9, 5)); use(s, "rogue", "shadowstep", "wolf1")
    assert s.heroes["rogue"].pos in {(8, 4), (8, 5), (8, 6)}
```

- [ ] **Step 2:** Run `uv run pytest tests/test_rogue.py -v`. Expected: FAIL.
- [ ] **Step 3:** Implement `abilities/rogue.py` and `combat.control`.
- [ ] **Step 4:** Run again. Expected: 8 passed.
- [ ] **Step 5: Commit.** Message: `Add the Rogue's abilities`.

---

### Task 10: Druid abilities

**Files:**
- Create: `src/fastcombat/abilities/druid.py`; import it from `abilities/__init__.py`
- Test: `tests/test_druid.py`

**Interfaces:**
- Produces effects (targets are ally ids; the Druid may target themself):
  - `rejuvenation`: `rejuvenation` stack (`cards`, `value`); replaces an existing one, never stacks. Refused for a downed ally.
  - `regrowth`: `heal_hero(roll_many(*dice, bonus))`; one Seed (up to `seeds_max`); `loud_heal`.
  - `swiftmend`: check: `seeds >= 1`. Cost rule: 0 when the ally's HP is below half their max (a downed ally counts). Effect: spend a Seed; heal `roll_many(*dice, bonus)`.
  - `wild_growth` (`pos`: centre): every hero not out and not down in `within(pos, radius)` gets a `wild_growth` stack (`cards`, `value`).
  - `cleanse`: removes the ally's `poison` stack; refused when there is none.
  - `shadowmeld`: `drop_pulls`; the Druid moves with `walk_away` from all living enemies, up to `value` squares.
  - `nourish`: one plain `dice.roll(dice[1])`, healed on the ally; on the top face the Druid gains `alt` energy (up to the pool).

- [ ] **Step 1: Write the failing tests**

```python
from tests.helpers import state, enemy
from tests.test_warden import use
from fastcombat.combat import damage_hero, add_stack

def test_rejuvenation_does_not_stack():
    s = state(); w = s.heroes["warden"]; s.heroes["druid"].resource = 10
    use(s, "druid", "rejuvenation", "warden"); w.stacks["rejuvenation"].cards = 1
    use(s, "druid", "rejuvenation", "warden")
    assert w.stacks["rejuvenation"].cards == 4 and s.heroes["druid"].resource == 6

def test_regrowth_lands_next_turn_heals_gives_a_seed_and_is_loud():
    from fastcombat.casting import land_casts
    s = state(rolls=[2, 2, 2]); w = s.heroes["warden"]; w.hp = 20; far = enemy(s, "wolf", (12, 2))
    use(s, "druid", "regrowth", "warden"); assert w.hp == 20
    land_casts(s)
    assert w.hp == 30 and s.heroes["druid"].seeds == 1 and far.pulled_by == "druid"

def test_swiftmend_needs_a_seed_and_is_free_on_a_badly_hurt_ally():
    s = state(rolls=[3, 3]); d = s.heroes["druid"]; m = s.heroes["mage"]; m.hp = 10
    assert not use(s, "druid", "swiftmend", "mage")
    d.seeds = 1; assert use(s, "druid", "swiftmend", "mage")
    assert m.hp == 18 and d.seeds == 0 and d.resource == 10

def test_swiftmend_gets_a_downed_ally_up():
    s = state(rolls=[3, 3]); m = s.heroes["mage"]; s.heroes["druid"].seeds = 1
    damage_hero(s, m, 99, attacker=None); use(s, "druid", "swiftmend", "mage")
    assert m.up and m.hp == 8 and m.wounds == 1

def test_wild_growth_gives_two_cards_to_allies_in_the_area():
    s = state(); use(s, "druid", "wild_growth", pos=(2, 6))
    assert s.heroes["warden"].stacks["wild_growth"].cards == 2
    assert s.heroes["rogue"].stacks["wild_growth"].value == 4

def test_nourish_heals_the_roll_and_the_top_face_gives_energy_back():
    s = state(rolls=[6]); d = s.heroes["druid"]; d.resource = 4; w = s.heroes["warden"]; w.hp = 30
    use(s, "druid", "nourish", "warden"); assert w.hp == 36 and d.resource == 6

def test_cleanse_removes_poison():
    s = state(); m = s.heroes["mage"]; add_stack(m, "poison", 3, 2)
    use(s, "druid", "cleanse", "mage"); assert "poison" not in m.stacks

def test_shadowmeld_drops_pulls_and_backs_off():
    s = state(); w = enemy(s, "wolf", (2, 7)); w.pulled_by = "druid"; before = s.heroes["druid"].pos
    use(s, "druid", "shadowmeld"); assert w.pulled_by is None and s.heroes["druid"].pos != before
```

- [ ] **Step 2:** Run `uv run pytest tests/test_druid.py -v`. Expected: FAIL.
- [ ] **Step 3:** Implement `abilities/druid.py`.
- [ ] **Step 4:** Run again. Expected: 8 passed.
- [ ] **Step 5: Commit.** Message: `Add the Druid's abilities`.

---

### Task 11: Mage abilities and Disrupt

**Files:**
- Create: `src/fastcombat/abilities/mage.py`, `src/fastcombat/abilities/shared.py`; import both from `abilities/__init__.py`
- Test: `tests/test_mage.py`

**Interfaces:**
- Produces effects:
  - `arcane_volley` (channel): each hit `roll_many(*dice, bonus)` to the enemy, `loud` from the spec.
  - `firebolt`: `roll_many(*dice, bonus)` to the enemy.
  - `meteor` (`pos`: centre): one `roll_many(*dice, bonus)`, dealt to every living enemy in the area through `damage_enemy` and to every hero in the area (not out) through `damage_hero(attacker=None, blast=True)`.
  - `frost_ring`: `rooted` stack of `cards` on every living enemy adjacent to the Mage.
  - `blink` (`pos`): the Mage moves there; refused when occupied or beyond `range`.
  - `quicken`: `quicken` stack of `cards` on every up hero.
  - `polymorph`: `control(state, enemy, "sheep", cards)`, after removing `sheep` from every other enemy. Refused for a boss.
  - `disrupt` (shared): check: the enemy has an `announced` cast. Effect: clears it.

- [ ] **Step 1: Write the failing tests**

```python
from tests.helpers import state, enemy
from tests.test_warden import use
from fastcombat.casting import land_casts, continue_cast
from fastcombat.combat import add_stack, top_of_party_turn_cards
from fastcombat.targeting import can_move
from fastcombat.units import Announced

def test_each_volley_hit_is_loud():
    s = state(rolls=[1, 1, 1, 1, 1, 1]); m = s.heroes["mage"]; o = enemy(s, "ogre", (8, 5))
    add_stack(o, "taunt", 2); use(s, "mage", "arcane_volley", "ogre1")
    continue_cast(s, m); continue_cast(s, m)
    assert o.hp == 320 - 6 and "taunt" not in o.stacks and o.pulled_by == "mage" and m.resource == 24

def test_meteor_marks_its_area_and_hits_friend_and_foe():
    s = state(rolls=[1] * 8); m = s.heroes["mage"]
    w = enemy(s, "wolf", (8, 5)); g = enemy(s, "goblin", (9, 6)); s.heroes["rogue"].pos = (8, 6)
    use(s, "mage", "meteor", pos=(8, 5)); assert (9, 6) in s.marked["mage"]
    continue_cast(s, m); land_casts(s)
    assert w.hp == 8 and g.dead and s.heroes["rogue"].hp == 28 and m.resource == 20 and "mage" not in s.marked

def test_frost_ring_roots_adjacent_enemies():
    s = state(); w = enemy(s, "wolf", (2, 4)); w.pulled_by = "mage"
    use(s, "mage", "frost_ring"); assert w.stacks["rooted"].cards == 2 and not can_move(s, w)

def test_polymorph_is_one_sheep_at_a_time_and_never_the_boss():
    s = state(); a = enemy(s, "wolf", (8, 5)); b = enemy(s, "wolf", (8, 7)); enemy(s, "ogre", (9, 6))
    use(s, "mage", "polymorph", "wolf1"); land_casts(s); assert a.stacks["sheep"].cards == 4
    use(s, "mage", "polymorph", "wolf2"); land_casts(s)
    assert "sheep" in b.stacks and "sheep" not in a.stacks
    assert not use(s, "mage", "polymorph", "ogre1")

def test_quicken_goes_on_the_whole_party():
    s = state(); use(s, "mage", "quicken")
    assert all(h.stacks["quicken"].cards == 2 for h in s.heroes.values())

def test_disrupt_breaks_a_cast_at_range_for_the_mage_only_then_cools_down():
    s = state(); sh = enemy(s, "shaman", (9, 5))
    sh.announced = Announced("mend", "mend", s.round + 1, None, frozenset(), (0, 0), heal=25)
    assert not use(s, "rogue", "disrupt", "shaman1")      # too far for melee
    assert use(s, "mage", "disrupt", "shaman1") and sh.announced is None
    sh.announced = Announced("mend", "mend", s.round + 1, None, frozenset(), (0, 0), heal=25)
    assert not use(s, "mage", "disrupt", "shaman1")
    for _ in range(3): top_of_party_turn_cards(s)
    assert use(s, "mage", "disrupt", "shaman1")

def test_blink_will_not_land_on_someone():
    s = state(); assert not use(s, "mage", "blink", pos=s.heroes["rogue"].pos)
    assert use(s, "mage", "blink", pos=(1, 1)) and s.heroes["mage"].pos == (1, 1)
```

- [ ] **Step 2:** Run `uv run pytest tests/test_mage.py -v`. Expected: FAIL.
- [ ] **Step 3:** Implement both files.
- [ ] **Step 4:** Run `uv run pytest -v`. Expected: all pass.
- [ ] **Step 5: Commit.** Message: `Add the Mage's abilities and the shared interrupt`.

---

### Task 12: Boss script and announced casts

**Files:**
- Modify: `src/fastcombat/enemy_ai.py`
- Test: `tests/test_boss.py`

Not modelled: the spec lets a stun, forced movement or an enemy interrupt break a hero's cast. No enemy in this fight does any of those, so hero casts only end by landing, cancelling or the hero going down. `drop_cast` is the hook for when an enemy that does is added.

**Interfaces:**
- Produces in `enemy_ai.py`:
  - `announce(state) -> None` (GM turn step 4). For each living boss with no `announced` cast: the first `blast` or `heavy` step that is due (`round >= first and (round - first) % every == 0`) is announced with `lands_round = round + 1`; a blast's `area = within(boss.pos, radius)`; a heavy's `target` is `boss.target`, skipped if `None`. For each living enemy with `cast_every > 0`, not controlled, no `announced` cast, and due by the same rule on `cast_first`/`cast_every`: announce `Announced("mend", "mend", round + 1, None, frozenset(), (0, 0), heal=spec.cast_heal)`.
  - `land_announced(state) -> None` (GM turn step 1). For each living enemy whose `announced.lands_round == state.round`: `blast` rolls once and hits every hero (not out, not down) in the area with `damage_hero(attacker=enemy, blast=True)`; `heavy` rolls and hits its target if still up with `damage_hero(attacker=enemy)`; `mend` heals every living boss by `heal` up to its max. Then `announced = None`. A controlled enemy's cast does not land and is cleared.
  - `throw(state, boss, step) -> None`: in the boss's own turn, when a `throw` step is due: pick with `dice.roll` among up heroes not adjacent to the boss, sorted by id; hit for `roll_many(*dice)` with `damage_hero(attacker=None)`. Nothing if nobody qualifies. Taunts do not affect it.
  - A boss blast area is included in `state.danger_squares()`.

- [ ] **Step 1: Write the failing tests**

```python
from tests.helpers import state, enemy
from tests.test_warden import use
from fastcombat.enemy_ai import gm_turn, announce, land_announced

def boss_state(round, rolls=None):
    s = state(rolls=rolls); o = enemy(s, "ogre", (4, 6)); s.round = round; return s, o

def test_ground_slam_is_announced_a_turn_ahead_and_marked():
    s, o = boss_state(3); announce(s)
    assert o.announced.name == "ground_slam" and o.announced.lands_round == 4
    assert (2, 6) in s.danger_squares() and (7, 6) not in s.danger_squares()

def test_the_slam_misses_anyone_who_walked_out():
    s, o = boss_state(3, rolls=[4, 4, 4]); announce(s); s.round = 4
    s.heroes["rogue"].pos = (9, 9); land_announced(s)
    assert s.heroes["warden"].hp == 48 and s.heroes["rogue"].hp == 36 and o.announced is None

def test_skull_crusher_hits_the_bosss_target_and_unbroken_survives_it():
    s, o = boss_state(5, rolls=[6] * 6); o.target = "warden"; announce(s)
    assert o.announced.kind == "heavy"
    s.heroes["warden"].hp = 20; s.heroes["warden"].resource = 10
    use(s, "warden", "unbroken"); s.round = 6; land_announced(s)
    assert s.heroes["warden"].hp == 1

def test_an_interrupted_mend_heals_nothing():
    s, o = boss_state(2); sh = enemy(s, "shaman", (9, 5)); o.hp = 100; announce(s)
    assert sh.announced.kind == "mend"
    use(s, "mage", "disrupt", "shaman1"); s.round = 3; land_announced(s); assert o.hp == 100

def test_a_mend_that_lands_heals_the_boss():
    s, o = boss_state(2); enemy(s, "shaman", (9, 5)); o.hp = 100; announce(s)
    s.round = 3; land_announced(s); assert o.hp == 125

def test_the_boulder_ignores_taunts_and_never_picks_someone_next_to_the_boss():
    s, o = boss_state(2, rolls=[1, 3, 3, 5, 5]); use(s, "warden", "challenge", "ogre1")
    before = {h.id: h.hp for h in s.heroes.values()}; gm_turn(s)
    hurt = [h.id for h in s.heroes.values() if h.hp < before[h.id] and h.id != "warden"]
    assert len(hurt) == 1
```

  (If the scripted roll order in the last test does not match the implementation's order of rolls, keep the assertion and fix the roll list; the point is one non-Warden hero takes the boulder.)

- [ ] **Step 2:** Run `uv run pytest tests/test_boss.py -v`. Expected: FAIL.
- [ ] **Step 3:** Implement and wire into `gm_turn` steps 1, 3 and 4.
- [ ] **Step 4:** Run `uv run pytest -v`. Expected: all pass.
- [ ] **Step 5: Commit.** Message: `Add the boss script and announced enemy casts`.

---

### Task 13: How each hero plays

**Files:**
- Modify: `src/fastcombat/policies.py`, `src/fastcombat/fight.py` (use `default_policy`)
- Test: `tests/test_policies.py`

**Interfaces:**
- Produces: `WardenPolicy`, `RoguePolicy`, `DruidPolicy`, `MagePolicy`, `POLICIES: dict[str, type]` (names `"warden"`, `"rogue"`, `"druid"`, `"mage"`, `"auto"`), `default_policy(cls: str) -> Policy`.
- Every policy returns only actions for which `can_use` is true; each rule below reads "…and the ability can be used". The first rule that applies wins. Put the list for each class in that class's docstring, in these words.

**Shared rules**
- *Focus* (what to attack): never a controlled enemy. Order: an enemy with an `announced` mend; then non-boss enemies, lowest HP first; then the boss.
- *Moving:* never end in `state.danger_squares()` if a free square outside it is in reach (a hero who is mid-cast and safe stays put). A downed ally adjacent rule below takes priority over range preferences.
- *Haul up:* a hero adjacent to a downed ally hauls them up, unless a Druid is up and has a Seed.

**Warden.** Move: to a square adjacent to the boss (or to the nearest enemy if no boss), outside danger if possible.
1. Haul up.
2. A boss `heavy` is announced on me and it could take me to 0 at its maximum roll: Unbroken.
3. A boss `blast` is announced and at least one ally stands in its area: Bulwark with `pos = boss.pos`.
4. An adjacent enemy has an announced cast: Disrupt.
5. A non-Warden ally at half HP or less is the `target` of an enemy with no `taunt` stack: Intercede on the lowest such ally.
6. The boss has no `taunt` stack: Challenge the boss.
7. Three or more enemies that are neither held nor taunted nor controlled are within War Cry's radius: War Cry.
8. A non-boss enemy that is neither held, taunted nor controlled is in range: Chain Hook the one closest to any non-Warden ally.
9. Auto-attack the focus if adjacent, else the lowest-HP adjacent uncontrolled enemy.

**Rogue.** Move: adjacent to the focus (prefer a square also outside danger).
1. Haul up.
2. Hidden, round 1, and a `shielded` enemy is adjacent or reachable next turn: Sap it (when adjacent).
3. An adjacent enemy has an announced cast: Disrupt, else Cheap Shot.
4. An enemy is pulled by me: Vanish.
5. Hidden: Backstab the focus.
6. Full combo points and the focus is not the boss, or it is the boss with a `taunt` stack: Eviscerate.
7. Full combo points and a non-boss, uncontrolled enemy's `target` is a Druid or Mage and it is adjacent: Kidney Shot.
8. Backstab the focus.
9. The focus is more than twice my move away: Shadowstep.
10. Auto-attack the focus if adjacent.

**Druid.** Move: within Rejuvenation range of the Warden (or the lowest-HP ally if no Warden), and as far from the nearest enemy as that allows.
1. An ally is down: Swiftmend them, else Nourish them.
2. An enemy is pulled by me or adjacent to me: Shadowmeld.
3. An ally is at 35% HP or less: Swiftmend.
4. Mid-cast: continue.
5. The Warden is up without a `rejuvenation` stack: Rejuvenation.
6. Three or more allies at 70% HP or less fit in one Wild Growth area: Wild Growth centred to cover the most.
7. An ally is at 60% HP or less: Regrowth on the lowest.
8. An ally has `poison`: Cleanse.
9. An ally at 80% or less has no `rejuvenation` and I have 6 or more energy: Rejuvenation.
10. An ally is below full HP: Nourish the lowest.
11. Auto-attack the focus if in range.

**Mage.** Move: in spell range of the focus and at least 5 squares from the nearest enemy when possible. While casting (not channelling), stay still unless standing in danger.
1. Haul up.
2. Mid-cast or mid-channel: continue.
3. An uncontrolled enemy is adjacent and not `rooted`: Frost Ring.
4. An enemy in range has an announced cast: Disrupt.
5. No enemy is sheeped and at least two uncontrolled non-boss, non-fodder enemies are alive: Polymorph the one with the most HP that nobody is adjacent to.
6. Some square in range has four or more living enemies and no hero within Meteor's radius: Meteor on the square covering the most.
7. Round 5 or later, every hero is up, and no hero has `quicken`: Quicken.
8. The focus has three or more `taunt` cards: Arcane Volley.
9. Firebolt the focus.
10. Auto-attack the focus if in range.

- [ ] **Step 1: Write the failing tests**

```python
from tests.helpers import state, enemy, GAME
from fastcombat.policies import default_policy, POLICIES
from fastcombat.combat import damage_hero, add_stack
from fastcombat.enemy_ai import announce
from fastcombat.fight import run_fight
from fastcombat.numbers import load_numbers, load_fight

def act(s, hero):
    return default_policy(s.heroes[hero].cls).act(s, s.heroes[hero])

def test_warden_challenges_an_untaunted_boss():
    s = state(); enemy(s, "ogre", (4, 6))
    a = act(s, "warden"); assert (a.ability, a.target) == ("challenge", "ogre1")

def test_warden_hooks_the_wolf_heading_for_the_mage():
    s = state(); o = enemy(s, "ogre", (4, 6)); add_stack(o, "taunt", 3); enemy(s, "wolf", (5, 3))
    a = act(s, "warden"); assert (a.ability, a.target) == ("chain_hook", "wolf1")

def test_rogue_saps_the_brute_on_round_one():
    s = state(); enemy(s, "brute", (3, 4))
    a = act(s, "rogue"); assert (a.ability, a.target) == ("sap", "brute1")

def test_druid_drops_everything_for_a_downed_ally():
    s = state(); s.heroes["druid"].seeds = 1; damage_hero(s, s.heroes["mage"], 99, attacker=None)
    a = act(s, "druid"); assert (a.ability, a.target) == ("swiftmend", "mage")

def test_rogue_hauls_up_when_the_druid_has_no_seed():
    s = state(); m = s.heroes["mage"]; m.pos = (1, 5); damage_hero(s, m, 99, attacker=None)
    a = act(s, "rogue"); assert (a.kind, a.target) == ("haul_up", "mage")

def test_mage_interrupts_the_shaman_before_anything_else():
    s = state(); enemy(s, "ogre", (11, 6)); enemy(s, "shaman", (9, 5)); s.round = 2; announce(s)
    a = act(s, "mage"); assert (a.ability, a.target) == ("disrupt", "shaman1")

def test_heroes_walk_out_of_an_announced_blast():
    s = state(); enemy(s, "ogre", (4, 5)); s.round = 3; announce(s)
    r = s.heroes["rogue"]; dest = default_policy("rogue").move(s, r)
    assert dest not in s.danger_squares()

def test_any_party_plays_the_real_fight_to_an_end():
    n = load_numbers(GAME / "numbers.toml"); f = load_fight(GAME / "fights" / "ogre_warlord.toml")
    for party in (["warden", "rogue", "druid", "mage"], ["rogue", "rogue", "mage"],
                  ["warden", "druid"], ["mage"], ["warden", "rogue", "druid", "mage", "mage"]):
        for seed in range(5):
            r = run_fight(n, f, party, seed=seed)
            assert 1 <= r.rounds <= n.rules["max_rounds"]     # it ended, without an error

def test_the_full_kit_beats_auto_attacks_only():
    n = load_numbers(GAME / "numbers.toml"); f = load_fight(GAME / "fights" / "ogre_warlord.toml")
    party = ["warden", "rogue", "druid", "mage"]
    auto = {h: POLICIES["auto"]() for h in party}
    smart = sum(run_fight(n, f, party, seed=i).won for i in range(30))
    dumb = sum(run_fight(n, f, party, policies=auto, seed=i).won for i in range(30))
    assert smart > dumb
```

- [ ] **Step 2:** Run `uv run pytest tests/test_policies.py -v`. Expected: FAIL, `default_policy` not found.
- [ ] **Step 3:** Implement the four policies and the registry.
- [ ] **Step 4:** Run `uv run pytest -v`. Expected: all pass. If `test_the_full_kit_beats_auto_attacks_only` fails, the policies or the abilities have a bug; do not change numbers to pass it.
- [ ] **Step 5: Commit.** Message: `Add how each hero plays the fight`.

---

### Task 14: Report and command line

**Files:**
- Create: `src/fastcombat/report.py`, `src/fastcombat/cli.py`, `README.md`
- Test: `tests/test_report.py`

**Interfaces:**
- Produces in `report.py`:

```python
@dataclass
class Summary:
    fights: int; win_rate: float; timeout_rate: float
    rounds_median: float; rounds_p10: float; rounds_p90: float
    in_band: float                      # share of fights lasting 18 to 22 rounds
    danger_rate: float                  # share of fights where some hero dropped to 25% HP or went down
    down_rate: dict[str, float]         # share of fights each hero went down at least once
    auto_share: float                   # auto-attack damage / all hero damage
    damage_share: dict[str, float]; healing_share: dict[str, float]
    starved: dict[str, float]           # mean share of rounds starved
    ended_full: dict[str, float]        # share of fights ending at the full pool
    resource_curve: dict[str, list[float]]   # mean resource at each round

@dataclass
class Check:
    name: str; passed: bool; value: str; wanted: str

def summarize(results: list[FightResult]) -> Summary
def check_targets(full: Summary, without: dict[str, Summary]) -> list[Check]
def format_summary(s: Summary) -> str
def format_checks(checks: list[Check]) -> str
```

  `check_targets` returns exactly these checks, in this order:

  | name | passes when |
  |---|---|
  | `length` | `in_band >= 0.60` |
  | `win_rate` | `0.70 <= win_rate <= 0.90` |
  | `no_timeouts` | `timeout_rate == 0` |
  | `danger` | `danger_rate >= 0.50` |
  | `auto_share` | `0.20 <= auto_share <= 0.50` |
  | `resource:<hero>` (one per hero) | `starved < 0.50 and ended_full < 0.50` |
  | `needed:<hero>` (one per entry of `without`) | `full.win_rate - without[hero].win_rate >= 0.20` |

- Produces in `cli.py`: `main(argv: list[str] | None = None) -> int`.
  - `fastcombat run [--fight ogre_warlord] [--n 1000] [--seed 0] [--party warden,rogue,druid,mage] [--numbers PATH] [--set KEY=VALUE ...] [--policy HERO=NAME ...] [--json PATH]`: plays `n` fights with seeds `seed … seed+n-1`, prints `format_summary`. `--set` values are parsed as TOML values and passed as overrides. `--json` writes the Summary as JSON. `--fight` is a name under `game/fights/` or a path.
  - `fastcombat check [same options]`: runs the full party, then the party with each hero removed in turn, prints the summary and `format_checks`, and exits 0 only if every check passed.
  - Unknown ability or hero in `--set`/`--policy`/`--party`: print the error and exit 2.
- `README.md`: what this is in two sentences, the two commands with one example each, where the numbers live, and how to try a change (`--set`).

- [ ] **Step 1: Write the failing tests**

```python
from tests.helpers import GAME
from fastcombat.numbers import load_numbers, load_fight
from fastcombat.fight import run_fight
from fastcombat.report import summarize, check_targets
from fastcombat.cli import main

N = load_numbers(GAME / "numbers.toml"); F = load_fight(GAME / "fights" / "ogre_warlord.toml")
PARTY = ["warden", "rogue", "druid", "mage"]

def test_summary_adds_up():
    s = summarize([run_fight(N, F, PARTY, seed=i) for i in range(20)])
    assert s.fights == 20 and 0 <= s.win_rate <= 1 and s.rounds_p10 <= s.rounds_median <= s.rounds_p90
    assert abs(sum(s.damage_share.values()) - 1) < 1e-9 and 0 <= s.auto_share <= 1
    assert set(s.starved) == set(PARTY)

def test_checks_are_the_agreed_list():
    full = summarize([run_fight(N, F, PARTY, seed=i) for i in range(10)])
    without = {h: summarize([run_fight(N, F, [p for p in PARTY if p != h], seed=i) for i in range(10)]) for h in PARTY}
    names = [c.name for c in check_targets(full, without)]
    assert names == ["length", "win_rate", "no_timeouts", "danger", "auto_share",
                     "resource:warden", "resource:rogue", "resource:druid", "resource:mage",
                     "needed:warden", "needed:rogue", "needed:druid", "needed:mage"]

def test_run_prints_a_summary_and_takes_a_changed_number(capsys):
    assert main(["run", "--n", "5", "--set", "abilities.meteor.cost=12"]) == 0
    assert "win" in capsys.readouterr().out.lower()

def test_a_bad_setting_is_a_clean_error(capsys):
    assert main(["run", "--n", "1", "--set", "abilities.meteor.cots=1"]) == 2
    assert "abilities.meteor.cots" in capsys.readouterr().err

def test_an_unknown_class_in_the_party_is_a_clean_error(capsys):
    assert main(["run", "--n", "1", "--party", "warden,bard"]) == 2
    assert "bard" in capsys.readouterr().err
```

- [ ] **Step 2:** Run `uv run pytest tests/test_report.py -v`. Expected: FAIL, module not found.
- [ ] **Step 3:** Implement `report.py`, `cli.py`, `README.md`.
- [ ] **Step 4:** Run `uv run pytest -v`, then `uv run fastcombat run --n 200`. Expected: all pass; a summary prints in under a minute.
- [ ] **Step 5: Commit.** Message: `Add the report and the command line`.

---

### Task 15: First tuning pass

**Files:**
- Modify: `game/numbers.toml`, `game/fights/ogre_warlord.toml`
- Create: `docs/tuning-log.md`, `tests/test_targets.py`

This task changes numbers only. If a target cannot be met without changing a rule or a policy, stop and write that down in the log under "Needs a decision"; do not change rules to hit a number.

- [ ] **Step 1: Baseline.** Run `uv run fastcombat check --n 1000 --json out/baseline.json`. Start `docs/tuning-log.md` with the date, the command, and the full check table.

- [ ] **Step 2: Tune.** One change at a time, in this order of concern: fight length (boss HP, add HP, hero damage dice), then win rate and danger (enemy damage, hero HP, heal sizes), then resources (costs, regen is fixed by the spec so change costs), then auto share, then the `needed:` checks. Try each change with `--set` first; write it into the TOML only when it helps. Dice sizes per class, the mana and energy pools and regen, and anything the spec states as a rule do not change. After each kept change add one line to the log: what changed, from what to what, why, and the check values after.

- [ ] **Step 3: Confirm.** Run `uv run fastcombat check --n 3000 --seed 100000` (seeds not used while tuning). Paste the table into the log under "Final". If any check still fails, list it under "Not met" with what was tried and the best guess at why.

- [ ] **Step 4: Pin it with a slow test**

```python
import pytest
from fastcombat.cli import main

@pytest.mark.slow
def test_the_numbers_meet_the_targets():
    assert main(["check", "--n", "600", "--seed", "500000"]) == 0
```

  If Step 3 left checks unmet, mark this test `xfail` with the reason copied from the log, instead of loosening a check.

- [ ] **Step 5:** Run `uv run pytest -v` and `uv run pytest -m slow -v`. Expected: all pass (or the one documented `xfail`).

- [ ] **Step 6: Commit.** Message: `Tune the first numbers against the design targets`.

---

## After this plan

The written rules, class sheets, test-fight sheet and printable cards are a second plan, written from the tuned `game/numbers.toml`.
