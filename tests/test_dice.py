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
