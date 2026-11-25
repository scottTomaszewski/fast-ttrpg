"""The map: squares, how far apart they are, areas, and walking.

A square is a pair (x, y). The top-left square is (0, 0). Every step costs 1,
even a diagonal one, so the distance between two squares is the larger of the
x gap and the y gap.
"""

from collections import deque
from collections.abc import Iterator

Pos = tuple[int, int]

# The eight ways to step, straight ones first. Always looking in the same
# order means the same fight always walks the same way.
DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def distance(a: Pos, b: Pos) -> int:
    """How many steps from `a` to `b`, with diagonals costing 1."""
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def adjacent(a: Pos, b: Pos) -> bool:
    """True for the eight squares around `a`. Your own square does not count."""
    return distance(a, b) == 1


def within(center: Pos, radius: int, width: int, height: int) -> set[Pos]:
    """Every square on the map no more than `radius` steps from `center`."""
    cx, cy = center
    return {
        (x, y)
        for x in range(max(0, cx - radius), min(width, cx + radius + 1))
        for y in range(max(0, cy - radius), min(height, cy + radius + 1))
    }


def behind(shield: Pos, source: Pos, depth: int, width: int, height: int) -> set[Pos]:
    """The squares in the shelter of a shield.

    These are the squares within `depth` of the shield that are farther from
    the blast's `source` than the shield is.
    """
    shield_gap = distance(shield, source)
    return {
        square
        for square in within(shield, depth, width, height)
        if distance(square, source) > shield_gap
    }


def walk(
    start: Pos,
    goal: Pos,
    steps: int,
    blocked: set[Pos],
    width: int,
    height: int,
    reach: int = 0,
) -> Pos:
    """Where you end up walking toward `goal`.

    You head for the nearest free square that is within `reach` of `goal`,
    along a shortest path that never passes through or stops on a blocked
    square, and you stop after `steps` steps. Your own square never counts as
    blocked. If you are already close enough, or there is no way there, you
    stay on `start`. Fewer than 0 steps is the same as 0.
    """
    blocked = blocked - {start}
    path = _path_to(start, goal, reach, blocked, width, height)
    if path is None:
        return start
    return path[min(max(steps, 0), len(path) - 1)]


def approach(
    start: Pos,
    goal: Pos,
    steps: int,
    blocked: set[Pos],
    width: int,
    height: int,
    reach: int = 0,
) -> Pos:
    """Like `walk`, but when there is no way to get within `reach` of `goal`,
    you still get as close as you can.

    That happens when the goal is boxed in by bodies. You then go to the
    square, no more than `steps` steps away, that is closest to `goal`. If
    several are just as close, the one that takes the fewest steps wins, then
    the one the search finds first. If nothing you can reach is closer than
    where you stand, you stay on `start`. This way a crowd does not freeze
    the ones at the back.
    """
    blocked = blocked - {start}
    path = _path_to(start, goal, reach, blocked, width, height)
    if path is not None:
        return path[min(max(steps, 0), len(path) - 1)]
    best = start
    best_gap = distance(start, goal)
    for square, taken in _spread(start, blocked, width, height, {}):
        if taken > steps:
            break
        gap = distance(square, goal)
        if gap < best_gap:
            best, best_gap = square, gap
    return best


def walk_away(
    start: Pos,
    threats: list[Pos],
    steps: int,
    blocked: set[Pos],
    width: int,
    height: int,
) -> Pos:
    """Where to run to, within `steps` steps, to get away from `threats`.

    Picks the square whose nearest threat is farthest away. If several squares
    are just as good, the one that takes the fewest steps wins, so you only
    move when moving helps. Your own square never counts as blocked.
    """
    if not threats:
        return start
    blocked = blocked - {start}
    best = start
    best_gap = min(distance(start, threat) for threat in threats)
    for square, taken in _spread(start, blocked, width, height, {}):
        if taken > steps:
            break
        gap = min(distance(square, threat) for threat in threats)
        if gap > best_gap:
            best, best_gap = square, gap
    return best


def nearest_free(square: Pos, taken: set[Pos], width: int, height: int) -> Pos | None:
    """The free square closest to `square`; `square` itself when it is free.

    If several are just as close, the one the search finds first wins. Taken
    squares do not get in the way of the search, because nobody walks there:
    this is for putting something down. None when the whole map is taken.
    """
    for spot, _ in _spread(square, set(), width, height, {}):
        if spot not in taken:
            return spot
    return None


def free_next_to(
    center: Pos, toward: Pos, taken: set[Pos], width: int, height: int
) -> Pos | None:
    """The free square next to `center` that is closest to `toward`.

    This is for putting someone next to `center` without walking there, like
    a leap or a pull. If several are just as close, the first in DIRECTIONS
    wins. None when every square next to `center` is taken or off the map.
    """
    free = []
    for dx, dy in DIRECTIONS:
        square = (center[0] + dx, center[1] + dy)
        if 0 <= square[0] < width and 0 <= square[1] < height and square not in taken:
            free.append(square)
    return min(free, key=lambda square: distance(square, toward), default=None)


def _path_to(
    start: Pos,
    goal: Pos,
    reach: int,
    blocked: set[Pos],
    width: int,
    height: int,
) -> list[Pos] | None:
    """The shortest path from `start` to a free square within `reach` of `goal`.

    The path starts with `start` and ends on that square. It is None when
    there is no way there.
    """
    targets = within(goal, reach, width, height) - blocked
    if not targets:
        return None
    came_from: dict[Pos, Pos | None] = {}
    for square, _ in _spread(start, blocked, width, height, came_from):
        if square in targets:
            path = [square]
            while came_from[path[-1]] is not None:
                path.append(came_from[path[-1]])
            path.reverse()
            return path
    return None


def _spread(
    start: Pos,
    blocked: set[Pos],
    width: int,
    height: int,
    came_from: dict[Pos, Pos | None],
) -> Iterator[tuple[Pos, int]]:
    """Look outward from `start`, one step at a time (breadth-first).

    Gives back every square you can walk to, nearest first, with the number of
    steps it takes. `came_from` is filled in as it goes: for each square, the
    square you stepped from to get there (None for `start`).
    """
    came_from[start] = None
    taken = {start: 0}
    queue = deque([start])
    while queue:
        here = queue.popleft()
        yield here, taken[here]
        for dx, dy in DIRECTIONS:
            there = (here[0] + dx, here[1] + dy)
            if there in came_from or there in blocked:
                continue
            if not (0 <= there[0] < width and 0 <= there[1] < height):
                continue
            came_from[there] = here
            taken[there] = taken[here] + 1
            queue.append(there)
