from fastcombat.grid import distance, adjacent, within, behind, walk, walk_away, approach, nearest_free, free_next_to, on_map

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

def test_a_walker_already_in_reach_stays_put_even_if_its_square_is_in_blocked():
    # Later code passes every filled square as blocked, the walker's own included.
    assert walk((4, 0), (5, 0), 5, {(4, 0), (5, 0)}, 10, 10, reach=1) == (4, 0)

def test_walk_away_stays_put_when_moving_gains_nothing():
    # Stepping sideways keeps the threat 5 away, so the fewest steps (none) wins.
    assert walk_away((0, 0), [(0, 5)], 3, set(), 3, 10) == (0, 0)

def test_walk_goes_round_a_partial_wall():
    assert walk((0, 0), (2, 0), 5, {(1, 0)}, 3, 2) == (2, 0)

def test_walk_with_no_reach_cannot_end_on_a_blocked_goal():
    assert walk((0, 0), (5, 0), 10, {(5, 0)}, 10, 10) == (0, 0)

def test_negative_steps_mean_stay_put():
    assert walk((0, 0), (9, 0), -3, set(), 10, 10) == (0, 0)
    assert approach((0, 0), (9, 0), -3, set(), 10, 10) == (0, 0)


# `approach` is `walk` for a crowd. The corridor below is one square tall, and
# the goal at (5, 0) has bodies on both sides, so nobody can get next to it.
BOXED_IN = {(4, 0), (5, 0), (6, 0)}

def test_approach_walks_like_walk_when_there_is_a_way():
    assert approach((0, 0), (9, 0), 3, set(), 10, 10) == walk((0, 0), (9, 0), 3, set(), 10, 10) == (3, 0)
    assert approach((0, 0), (2, 0), 5, {(1, 0)}, 3, 2) == (2, 0)

def test_approach_gets_as_close_as_it_can_to_a_boxed_in_goal():
    assert walk((0, 0), (5, 0), 10, BOXED_IN, 10, 1, reach=1) == (0, 0)      # walk gives up
    assert approach((0, 0), (5, 0), 10, BOXED_IN, 10, 1, reach=1) == (3, 0)
    assert approach((0, 0), (5, 0), 2, BOXED_IN, 10, 1, reach=1) == (2, 0)   # only as far as its steps

def test_approach_stays_put_when_nothing_it_can_reach_is_closer():
    assert approach((3, 0), (5, 0), 10, BOXED_IN | {(3, 0)}, 10, 1, reach=1) == (3, 0)

def test_approach_stops_at_the_first_closest_square_it_finds():
    # A wall of bodies right across the map. Every square of column 3 is 2
    # from the goal and two steps away; straight ahead is looked at first.
    wall = {(4, y) for y in range(5)}
    assert approach((1, 2), (5, 2), 5, wall, 7, 5, reach=1) == (3, 2)
    assert approach((1, 0), (5, 2), 5, wall, 7, 5, reach=1) == (3, 0)

def test_nearest_free_is_the_square_itself_or_the_closest_one_left():
    assert nearest_free((2, 2), set(), 5, 5) == (2, 2)
    assert nearest_free((2, 2), {(2, 2)}, 5, 5) == (3, 2)               # the search looks right first
    ring = within((2, 2), 1, 5, 5)                                     # taken squares do not block the search
    assert distance(nearest_free((2, 2), ring, 5, 5), (2, 2)) == 2
    assert nearest_free((0, 0), within((0, 0), 1, 2, 2), 2, 2) is None   # the whole map is taken

def test_free_next_to_is_the_free_square_in_the_ring_closest_to_a_spot():
    assert free_next_to((3, 6), (8, 6), set(), 16, 12) == (4, 6)
    assert free_next_to((3, 6), (8, 6), {(4, 6)}, 16, 12) == (4, 7)     # (4, 5) is just as close; the fixed order picks
    assert free_next_to((3, 6), (3, 10), set(), 16, 12) == (3, 7)        # straight steps come before diagonal ones
    assert free_next_to((0, 0), (5, 5), {(1, 0), (0, 1), (1, 1)}, 16, 12) is None   # the rest is off the map

def test_on_map_is_every_square_from_the_top_left_corner_to_one_short_of_the_size():
    assert on_map((0, 0), 4, 3) and on_map((3, 2), 4, 3)
    assert not on_map((4, 2), 4, 3) and not on_map((3, 3), 4, 3)
    assert not on_map((-1, 0), 4, 3) and not on_map((0, -1), 4, 3)
