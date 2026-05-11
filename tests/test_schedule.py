from datetime import datetime

from fly_run import seconds_until_next_hour


def test_mid_hour():
    now = datetime(2026, 5, 11, 23, 8, 0)
    assert seconds_until_next_hour(now) == 52 * 60


def test_just_after_top_of_hour():
    now = datetime(2026, 5, 11, 23, 0, 1)
    assert seconds_until_next_hour(now) == 3599


def test_exactly_top_of_hour_waits_full_hour():
    now = datetime(2026, 5, 11, 23, 0, 0)
    assert seconds_until_next_hour(now) == 3600


def test_last_second_of_hour():
    now = datetime(2026, 5, 11, 23, 59, 59)
    assert seconds_until_next_hour(now) == 1


def test_crosses_midnight():
    now = datetime(2026, 5, 11, 23, 45, 0)
    assert seconds_until_next_hour(now) == 15 * 60


def test_always_positive():
    for hour in range(24):
        for minute in (0, 17, 30, 59):
            now = datetime(2026, 5, 11, hour, minute, 0)
            assert seconds_until_next_hour(now) > 0