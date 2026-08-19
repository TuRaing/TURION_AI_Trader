import datetime

from report.market_checks import (
    detect_crash,
    intended_stop_loss_cap,
    detect_unusual_trade,
    summarize_daily_pnl,
    detect_stale_workflow,
    format_running_market_checklist,
    market_check_log_filename,
    format_pre_market_checklist,
)

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def test_detect_crash_false_on_a_calm_day():
    # Today's real move (~-0.41% NIFTY, -0.35% BANKNIFTY, per this
    # session's own check) - nowhere near alert-worthy.
    is_crash, reason = detect_crash(-0.41, -0.35, threshold_pct=2.0)

    assert is_crash is False
    assert reason is None


def test_detect_crash_true_when_nifty_crosses_threshold():
    is_crash, reason = detect_crash(-2.5, -0.5, threshold_pct=2.0)

    assert is_crash is True
    assert "NIFTY" in reason
    assert "BANKNIFTY" not in reason


def test_detect_crash_true_when_banknifty_crosses_threshold():
    is_crash, reason = detect_crash(-0.5, 2.1, threshold_pct=2.0)

    assert is_crash is True
    assert "BANKNIFTY" in reason


def test_detect_crash_direction_agnostic_a_spike_up_also_counts():
    is_crash, reason = detect_crash(3.0, 0.0, threshold_pct=2.0)

    assert is_crash is True
    assert "+3.00%" in reason


def test_intended_stop_loss_cap_matches_the_known_live_incident():
    # simple_st1_slcap/NIFTY's real 19-Aug incident: entry 37.3, 44
    # lots, NIFTY lot_size 75 -> capital deployed 1,23,090 - the
    # intended cap this session already hand-computed for it was
    # exactly Rs 2,000 (flat cap binds, not the %-of-deployed side).
    cap = intended_stop_loss_cap(initial_capital=100000, capital_deployed=123090)

    assert cap == 2000.0


def test_detect_unusual_trade_flags_the_known_live_incident():
    # The exact real trade: entry 37.3, exit 0.05, 44 lots, NIFTY -
    # Net PnL -123,027.15, a 61.5x overshoot of the Rs 2,000 cap.
    trade = {"Net PnL": -123027.15, "Entry Premium": 37.3, "Lots": 44}

    is_unusual, reason = detect_unusual_trade(trade, lot_size=75, overshoot_multiple=3.0)

    assert is_unusual is True
    assert "123,027" in reason


def test_detect_unusual_trade_false_for_ordinary_overshoot():
    # A typical ~2x check-interval overshoot (not the extreme
    # date-blind-squareoff case) - real, but under the 3x bar.
    trade = {"Net PnL": -3800.0, "Entry Premium": 60.0, "Lots": 25}  # cap ~= min(2000, 1900*2%*... )

    is_unusual, reason = detect_unusual_trade(trade, lot_size=75, overshoot_multiple=3.0)

    assert is_unusual is False
    assert reason is None


def test_detect_unusual_trade_never_flags_a_win():
    trade = {"Net PnL": 50000.0, "Entry Premium": 37.3, "Lots": 44}

    is_unusual, reason = detect_unusual_trade(trade, lot_size=75)

    assert is_unusual is False


def test_summarize_daily_pnl_aggregates_across_books():
    books = {
        "oi_footprint_banknifty": [
            {"Net PnL": 5000.0}, {"Net PnL": 3000.0}, {"Net PnL": 3583.93},
        ],
        "st2_nifty": [
            {"Net PnL": -17537.52},
        ],
        "no_activity_book": [],
    }

    summary = summarize_daily_pnl(books)

    assert summary["total_trades"] == 4
    assert summary["wins"] == 3
    assert summary["losses"] == 1
    assert summary["total_pnl"] == round(5000.0 + 3000.0 + 3583.93 - 17537.52, 2)
    # Worst book first.
    assert summary["per_book"][0]["name"] == "st2_nifty"
    assert summary["per_book"][-1]["name"] == "oi_footprint_banknifty"


def test_detect_stale_workflow_false_when_recent():
    now = datetime.datetime(2026, 8, 20, 10, 0, tzinfo=IST)
    last_run = now - datetime.timedelta(minutes=5)

    is_stale, gap = detect_stale_workflow(last_run, now, max_gap_minutes=15)

    assert is_stale is False
    assert gap == 5.0


def test_detect_stale_workflow_true_when_gap_exceeds_limit():
    now = datetime.datetime(2026, 8, 20, 10, 0, tzinfo=IST)
    last_run = now - datetime.timedelta(minutes=20)

    is_stale, gap = detect_stale_workflow(last_run, now, max_gap_minutes=15)

    assert is_stale is True
    assert gap == 20.0


def _sample_pnl_summary():
    return summarize_daily_pnl({
        "oi_footprint_banknifty": [{"Net PnL": 5000.0}, {"Net PnL": 3000.0}],
        "st2_nifty": [{"Net PnL": -17537.52}],
    })


def test_format_running_market_checklist_calm_day_all_unchecked():
    now = datetime.datetime(2026, 8, 20, 10, 30, tzinfo=IST)

    report = format_running_market_checklist(
        now_ist=now,
        crash_result=detect_crash(-0.41, -0.35),
        unusual_trades=[],
        pnl_summary=_sample_pnl_summary(),
        strategy_workflows=[
            ("oi_footprint_banknifty", *detect_stale_workflow(now - datetime.timedelta(minutes=5), now)),
            ("st2_nifty", *detect_stale_workflow(now - datetime.timedelta(minutes=8), now)),
        ],
    )

    assert "2026-08-20 10:30:00" in report
    assert "- [ ] Crash check - normal" in report
    assert "- [ ] No unusual trades this check" in report
    assert "- [ ] Strategy working status (2/2 running):" in report
    assert "  - [ ] oi_footprint_banknifty: running (last run 5.0 min ago)" in report
    assert "  - [ ] st2_nifty: running (last run 8.0 min ago)" in report
    assert "Worst book right now: st2_nifty" in report


def test_format_running_market_checklist_flags_crash_unusual_trades_and_stale_strategy():
    now = datetime.datetime(2026, 8, 20, 11, 0, tzinfo=IST)

    report = format_running_market_checklist(
        now_ist=now,
        crash_result=detect_crash(-2.5, -0.5),
        unusual_trades=[("simple_st1_slcap", "Loss Rs 123,027.15 is 61.5x the intended ~Rs 2,000 cap")],
        pnl_summary=_sample_pnl_summary(),
        strategy_workflows=[
            ("oi_footprint_banknifty", False, 5.0),
            ("st2_nifty", True, 22.0),
        ],
    )

    assert "- [x] Crash check: Intraday move" in report
    assert "- [x] Unusual trades found (1):" in report
    assert "simple_st1_slcap: Loss Rs 123,027.15" in report
    assert "- [x] Strategy working status (1/2 running):" in report
    assert "  - [ ] oi_footprint_banknifty: running (last run 5.0 min ago)" in report
    assert "  - [x] st2_nifty: STALE (last run 22.0 min ago)" in report


def test_format_running_market_checklist_omits_strategy_section_when_not_checked():
    now = datetime.datetime(2026, 8, 20, 9, 20, tzinfo=IST)

    report = format_running_market_checklist(
        now_ist=now,
        crash_result=(False, None),
        unusual_trades=[],
        pnl_summary=summarize_daily_pnl({}),
        strategy_workflows=None,
    )

    assert "Strategy working status" not in report
    assert "Rs 0.00" in report


def test_market_check_log_filename_format():
    now = datetime.datetime(2026, 8, 20, 10, 30, 0, tzinfo=IST)

    assert market_check_log_filename(now) == "market_check_20260820_103000.log"


def test_format_pre_market_checklist_all_clear():
    now = datetime.datetime(2026, 8, 20, 8, 45, tzinfo=IST)

    report = format_pre_market_checklist(now, token_ready=True, open_positions=[])

    assert "2026-08-20 08:45:00" in report
    assert "- [ ] Fyers access token ready" in report
    assert "- [ ] No carried-over open positions" in report


def test_format_pre_market_checklist_flags_missing_token_and_carryover():
    now = datetime.datetime(2026, 8, 20, 8, 45, tzinfo=IST)

    report = format_pre_market_checklist(
        now,
        token_ready=False,
        open_positions=[
            ("fyers_options_st2_nifty_portfolio", {"Symbol": "NSE:NIFTY26AUG24050PE", "Entry Time": "2026-08-19 14:38:01"}),
        ],
    )

    assert "- [x] Fyers access token NOT ready - login needed before today's engines can run" in report
    assert "- [x] Carried-over open positions from yesterday (1):" in report
    assert "fyers_options_st2_nifty_portfolio: NSE:NIFTY26AUG24050PE (entered 2026-08-19 14:38:01)" in report
