from strategy.fyers_options_credit_spread import (
    make_credit_spread_config,
    _compute_strikes,
    _strikes_needed,
    _leg_premium,
    _target_hit,
    _stop_loss_hit,
)


def test_make_credit_spread_config_nifty():
    cfg = make_credit_spread_config("NIFTY")

    assert cfg["lot_size"] == 75
    assert cfg["strike_step"] == 50
    assert cfg["width_points"] == 150
    assert cfg["portfolio_file"] == "reports/fyers_options_credit_spread_nifty_portfolio.json"


def test_make_credit_spread_config_banknifty():
    cfg = make_credit_spread_config("BANKNIFTY")

    assert cfg["lot_size"] == 30
    assert cfg["strike_step"] == 100


def test_make_credit_spread_config_custom_width():
    cfg = make_credit_spread_config("NIFTY", width_points=200)

    assert cfg["width_points"] == 200


def test_compute_strikes_put_spread_both_below_spot():
    # Bull Put Spread - sold when RSI is bullish/neutral, both legs
    # sit BELOW spot (bet spot doesn't fall through them).
    short_strike, long_strike = _compute_strikes(spot=24600, option_type="PE", strike_step=50, width_points=150)

    assert short_strike < 24600
    assert long_strike < short_strike  # protection leg further away


def test_compute_strikes_call_spread_both_above_spot():
    short_strike, long_strike = _compute_strikes(spot=24600, option_type="CE", strike_step=50, width_points=150)

    assert short_strike > 24600
    assert long_strike > short_strike


def test_compute_strikes_rounds_to_strike_step():
    short_strike, long_strike = _compute_strikes(spot=24613, option_type="PE", strike_step=50, width_points=150)

    assert short_strike % 50 == 0


def test_strikes_needed_nifty_realistic_distance():
    # Regression case (caught 10-Aug live) - NIFTY spot ~24587, short
    # ~1.5% OTM, long 150 points further. The fixed strike_count=15
    # this project first tried happened to cover this one.
    short_strike, long_strike = _compute_strikes(spot=24587, option_type="PE", strike_step=50, width_points=150)

    assert _strikes_needed(24587, long_strike, 50) <= 15


def test_strikes_needed_banknifty_realistic_distance():
    # Regression case (caught 10-Aug live) - BANKNIFTY spot ~57600,
    # short strike computed at 58400+/CE side. A fixed strike_count=15
    # was NOT enough here ("Could not find both spread legs" still
    # fired live) - this is why the fetch is now sized dynamically
    # instead of using a fixed guess.
    short_strike, long_strike = _compute_strikes(spot=57600, option_type="CE", strike_step=100, width_points=150)

    needed = _strikes_needed(57600, long_strike, 100)

    assert needed >= 1
    # The whole point of the fix: whatever the real distance is, asking
    # for at least that many strikes (+ buffer) must include the long
    # leg - i.e. spot +/- needed*strike_step must reach past long_strike.
    assert abs(long_strike - 57600) <= needed * 100


def test_strikes_needed_rounds_up_and_has_a_floor_of_one():
    assert _strikes_needed(spot=24500, long_strike=24500, strike_step=50) == 1
    assert _strikes_needed(spot=24500, long_strike=24560, strike_step=50) == 2


def test_leg_premium_prefers_ltp():
    assert _leg_premium({"ltp": 120, "bid": 118, "ask": 122}) == 120


def test_leg_premium_falls_back_to_bid_ask_midpoint():
    assert _leg_premium({"ltp": 0, "bid": 100, "ask": 110}) == 105


def test_target_hit_at_50_percent_of_credit_banked():
    # Received Rs 20 credit, cost to close has fallen to Rs 10 (half
    # banked) - exactly at the 50% target.
    assert _target_hit(entry_credit=20, cost_to_close_now=10) is True


def test_target_hit_false_when_still_early():
    assert _target_hit(entry_credit=20, cost_to_close_now=18) is False


def test_target_hit_false_with_zero_credit():
    assert _target_hit(entry_credit=0, cost_to_close_now=0) is False


def test_stop_loss_hit_at_2x_credit():
    assert _stop_loss_hit(entry_credit=20, cost_to_close_now=40) is True


def test_stop_loss_not_hit_below_2x_credit():
    assert _stop_loss_hit(entry_credit=20, cost_to_close_now=35) is False
