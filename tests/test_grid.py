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

def test_a_walker_already_in_reach_stays_put_even_if_its_square_is_in_blocked():
    # Later code passes every filled square as blocked, the walker's own included.
    assert walk((4, 0), (5, 0), 5, {(4, 0), (5, 0)}, 10, 10, reach=1) == (4, 0)

def test_walk_away_stays_put_when_moving_gains_nothing():
    # Stepping sideways keeps the threat 5 away, so the fewest steps (none) wins.
    assert walk_away((0, 0), [(0, 5)], 3, set(), 3, 10) == (0, 0)
