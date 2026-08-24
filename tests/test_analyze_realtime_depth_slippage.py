import datetime

from analyze_realtime_depth_slippage import walk_book, nearest_record


def test_walk_book_fills_within_level_one():
    levels = [{"price": 100.0, "volume": 500, "ord": 3}, {"price": 100.5, "volume": 300, "ord": 2}]

    avg_price, ran_out = walk_book(levels, 300)

    assert avg_price == 100.0
    assert ran_out is False


def test_walk_book_spills_into_level_two():
    levels = [{"price": 100.0, "volume": 500, "ord": 3}, {"price": 100.5, "volume": 300, "ord": 2}]

    avg_price, ran_out = walk_book(levels, 700)

    expected = (500 * 100.0 + 200 * 100.5) / 700
    assert round(avg_price, 4) == round(expected, 4)
    assert ran_out is False


def test_walk_book_exceeds_entire_visible_depth():
    levels = [{"price": 100.0, "volume": 500, "ord": 3}]

    avg_price, ran_out = walk_book(levels, 1000)

    assert avg_price == 100.0  # filled what it could
    assert ran_out is True


def test_walk_book_empty_levels():
    avg_price, ran_out = walk_book([], 100)

    assert avg_price is None
    assert ran_out is True


def test_nearest_record_picks_closest_before_or_after():
    base = datetime.datetime(2026, 8, 24, 10, 0, 0)
    records = [
        {"_dt": base + datetime.timedelta(seconds=0)},
        {"_dt": base + datetime.timedelta(seconds=5)},
        {"_dt": base + datetime.timedelta(seconds=10)},
    ]

    idx = nearest_record(records, base + datetime.timedelta(seconds=6))

    assert idx == 1  # the 5s record is closer to 6s than the 10s one


def test_nearest_record_target_before_all_records():
    base = datetime.datetime(2026, 8, 24, 10, 0, 0)
    records = [{"_dt": base}, {"_dt": base + datetime.timedelta(seconds=5)}]

    idx = nearest_record(records, base - datetime.timedelta(seconds=100))

    assert idx == 0
