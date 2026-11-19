from app.pricing import deposit_for


def test_deposit_is_the_set_amount():
    assert deposit_for(3500, 1500) == 1500  # €35 set -> €15 deposit


def test_deposit_is_the_same_with_extras():
    assert deposit_for(3500 + 1000, 1500) == 1500  # set + removal -> still €15


def test_deposit_never_more_than_the_total():
    assert deposit_for(1000, 1500) == 1000  # a €10 booking can't need a €15 deposit
