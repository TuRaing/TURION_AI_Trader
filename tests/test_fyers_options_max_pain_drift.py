import datetime

from strategy.fyers_options_max_pain_drift import (
    make_max_pain_drift_config,
    _compute_max_pain,
    _classify_max_pain_drift,
    _within_expiry_window,
)


def test_make_max_pain_drift_config_nifty():
    cfg = make_max_pain_drift_config("NIFTY")

    assert cfg["lot_size"] == 75
    assert cfg["strike_step"] == 50
    assert cfg["portfolio_file"] == "reports/fyers_options_max_pain_drift_nifty_portfolio.json"


def test_make_max_pain_drift_config_banknifty():
    cfg = make_max_pain_drift_config("BANKNIFTY")

    assert cfg["lot_size"] == 30
    assert cfg["strike_step"] == 100


def _legs(rows):
    # rows: list of (strike, option_type, oi)
    legs = [{"strike_price": -1, "ltp": 24555}]  # the spot leg, should be ignored
    for strike, opt_type, oi in rows:
        legs.append({"strike_price": strike, "option_type": opt_type, "oi": oi})
    return legs


def test_compute_max_pain_picks_the_minimum_payout_strike():
    # OI concentrated at the extremes (heavy CE writing far above,
    # heavy PE writing far below), balanced in the middle - the
    # middle strike should minimize aggregate payout to writers.
    legs = _legs([
        (100, "CE", 10), (100, "PE", 100),
        (200, "CE", 50), (200, "PE", 50),
        (300, "CE", 100), (300, "PE", 10),
    ])

    assert _compute_max_pain(legs, strike_step=100) == 200


def test_compute_max_pain_none_with_no_usable_strikes():
    assert _compute_max_pain([{"strike_price": -1, "ltp": 24555}], strike_step=50) is None


def test_classify_drift_none_without_previous():
    assert _classify_max_pain_drift(None, 24600, strike_step=50) is None


def test_classify_drift_ce_when_max_pain_moves_up_enough():
    assert _classify_max_pain_drift(24500, 24650, strike_step=50) == "CE"


def test_classify_drift_pe_when_max_pain_moves_down_enough():
    assert _classify_max_pain_drift(24600, 24450, strike_step=50) == "PE"


def test_classify_drift_none_when_change_too_small():
    # Only 1 strike-step of movement - below the 2-strike default noise floor.
    assert _classify_max_pain_drift(24500, 24550, strike_step=50, min_drift_strikes=2) is None


def test_within_expiry_window_true_on_expiry_day_itself():
    now = datetime.datetime(2026, 8, 11, 10, 0, 0)
    expiry = datetime.date(2026, 8, 11)

    assert _within_expiry_window(expiry, now, max_days=2) is True


def test_within_expiry_window_true_inside_the_window():
    now = datetime.datetime(2026, 8, 10, 10, 0, 0)
    expiry = datetime.date(2026, 8, 11)

    assert _within_expiry_window(expiry, now, max_days=2) is True


def test_within_expiry_window_false_too_far_out():
    now = datetime.datetime(2026, 8, 5, 10, 0, 0)
    expiry = datetime.date(2026, 8, 11)

    assert _within_expiry_window(expiry, now, max_days=2) is False


def test_within_expiry_window_false_after_expiry_has_passed():
    now = datetime.datetime(2026, 8, 12, 10, 0, 0)
    expiry = datetime.date(2026, 8, 11)

    assert _within_expiry_window(expiry, now, max_days=2) is False


def test_within_expiry_window_false_when_expiry_unparseable():
    now = datetime.datetime(2026, 8, 11, 10, 0, 0)

    assert _within_expiry_window(None, now, max_days=2) is False
