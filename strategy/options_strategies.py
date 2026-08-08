from strategy.fyers_options_engine import make_strategy, check_or_open as check_or_open_generic
from strategy.fyers_options_st4 import make_st4_config, check_or_open as check_or_open_st4
from strategy.fyers_options_gapfill import make_gapfill_config, check_or_open as check_or_open_gapfill
from strategy.fyers_options_vix_filter import make_vix_filter_config, check_or_open as check_or_open_vix_filter

# Added 06-Aug-2026 - the named-strategy roster for the multi-strategy
# options paper trading the user asked for: several live strategies
# running in parallel, each on both NIFTY and BANKNIFTY with its own
# full Rs 1,00,000. Built one strategy at a time (phased, per the
# user's own request) - only simple_st1 exists so far; st2/st3/st4
# get added the same way once each is ready.

# simple_st1 - a tuned version of strategy/fyers_options_paper_
# trading.py's live rules (that file is untouched - this is a
# separate engine/portfolio). Same RSI-momentum entry, but the
# Target/Stop-Loss ratio is retuned after 06-Aug's real-day finding:
# the original 2%/5% split needed a >71% win rate just to break even
# (5/(5+2)), and a real day at 61.2% win rate still lost money. Moved
# to a SYMMETRIC 3%/3% - breakeven only needs >50% win rate, without
# claiming false precision from an untested ratio search (unlike st2/
# st3 below, which reuse a specific ratio this repo did already sweep
# - see strategy/nifty_options_backtest.py, on Black-Scholes-estimated
# premiums though, not real ones).
SIMPLE_ST1_NIFTY = make_strategy("simple_st1", "NIFTY", target_net_pct=3.0, stop_loss_pct=3.0)
SIMPLE_ST1_BANKNIFTY = make_strategy("simple_st1", "BANKNIFTY", target_net_pct=3.0, stop_loss_pct=3.0)

# st2 - same RSI-momentum entry as simple_st1, but reusing the exact
# Target 5% / Stop-Loss 2% ratio that strategy/nifty_options_
# backtest.py's forced-entry NIFTY sweep found best-by-far on 06-Aug
# (+50.45% over 57 days) - see doc/06aug26_SESSION_LOG.md. That sweep
# used Black-Scholes-ESTIMATED premiums and an unvalidated forced-
# entry direction rule, so this is testing whether the same ratio
# still helps once real quotes replace the estimate - not a claim the
# backtest number will repeat live.
ST2_NIFTY = make_strategy("st2", "NIFTY", target_net_pct=5.0, stop_loss_pct=2.0)
ST2_BANKNIFTY = make_strategy("st2", "BANKNIFTY", target_net_pct=5.0, stop_loss_pct=2.0)

# st3 - same RSI-momentum entry, reusing the Target 5% / Stop-Loss 5%
# combo that came out best overall in nifty_options_backtest.py's
# 06-Aug sweep (+69.03%/57 days, Black-Scholes-estimated premiums,
# see doc/06aug26_SESSION_LOG.md) - same caveat as st2: testing the
# ratio against real quotes, not expecting the backtest number to
# repeat live.
ST3_NIFTY = make_strategy("st3", "NIFTY", target_net_pct=5.0, stop_loss_pct=5.0)
ST3_BANKNIFTY = make_strategy("st3", "BANKNIFTY", target_net_pct=5.0, stop_loss_pct=5.0)

# st4 - materially different entry/exit logic (multi-timeframe + ADX
# alignment, one trade/day, trailing stop after a rupee profit
# threshold) - see strategy/fyers_options_st4.py for the full design
# reasoning. Its check_or_open has a different signature source than
# the generic engine's, so ALL_STRATEGIES pairs each config with the
# function that actually runs it.
ST4_NIFTY = make_st4_config("NIFTY")
ST4_BANKNIFTY = make_st4_config("BANKNIFTY")

# gapfill - added 07/08-Aug-2026 after simple_st1/st2/st3/st4's first
# real trading day (07-Aug) lost broadly across all 8 books despite
# 3 different Target/Stop-Loss ratios - pointed at the shared RSI-
# momentum ENTRY signal itself lacking edge, not the exit tuning.
# This strategy deliberately uses a DIFFERENT entry mechanism (Gap-
# Fill - see strategy/fyers_options_gapfill.py) instead of another
# ratio variant on the same signal.
GAPFILL_NIFTY = make_gapfill_config("NIFTY")
GAPFILL_BANKNIFTY = make_gapfill_config("BANKNIFTY")

# THRESHOLD group - added 08-Aug-2026, user's direct request: keep the
# 5 original strategies exactly as they are (no gate), and separately
# run the SAME 5 strategies with the daily profit-lock gate turned on
# (daily_profit_lock=True - see fyers_options_engine.py's make_
# strategy()/DAILY_PROFIT_LOCK_RS), as their own 5 books x 2 indices =
# 10 independent paper portfolios, shown in the app's new "Threshold
# Options" tab instead of mixed into the original Options tab. Same
# entry/exit logic as their non-threshold counterpart, only the extra
# "stop opening new trades once today's realized profit hits Rs 2,000"
# gate differs. group="threshold" lets fyers_multi_strategy_options_
# run.py's STRATEGY_NAME filter run all 5 together with one trigger.
SIMPLE_ST1_TH_NIFTY = make_strategy("simple_st1_threshold", "NIFTY", target_net_pct=3.0, stop_loss_pct=3.0,
                                     daily_profit_lock=True, group="threshold")
SIMPLE_ST1_TH_BANKNIFTY = make_strategy("simple_st1_threshold", "BANKNIFTY", target_net_pct=3.0, stop_loss_pct=3.0,
                                         daily_profit_lock=True, group="threshold")
ST2_TH_NIFTY = make_strategy("st2_threshold", "NIFTY", target_net_pct=5.0, stop_loss_pct=2.0,
                              daily_profit_lock=True, group="threshold")
ST2_TH_BANKNIFTY = make_strategy("st2_threshold", "BANKNIFTY", target_net_pct=5.0, stop_loss_pct=2.0,
                                  daily_profit_lock=True, group="threshold")
ST3_TH_NIFTY = make_strategy("st3_threshold", "NIFTY", target_net_pct=5.0, stop_loss_pct=5.0,
                              daily_profit_lock=True, group="threshold")
ST3_TH_BANKNIFTY = make_strategy("st3_threshold", "BANKNIFTY", target_net_pct=5.0, stop_loss_pct=5.0,
                                  daily_profit_lock=True, group="threshold")
ST4_TH_NIFTY = make_st4_config("NIFTY", name="st4_threshold", daily_profit_lock=True, group="threshold")
ST4_TH_BANKNIFTY = make_st4_config("BANKNIFTY", name="st4_threshold", daily_profit_lock=True, group="threshold")
GAPFILL_TH_NIFTY = make_gapfill_config("NIFTY", name="gapfill_threshold", daily_profit_lock=True, group="threshold")
GAPFILL_TH_BANKNIFTY = make_gapfill_config("BANKNIFTY", name="gapfill_threshold", daily_profit_lock=True,
                                            group="threshold")

# vix_filter - added 08-Aug-2026, user's direct request to bring back
# 22-Jul's own validated-but-never-deployed finding: Momentum(RSI) +
# India VIX percentile-band filter, BANKNIFTY ONLY (NIFTY was rejected
# under this exact combo - see strategy/fyers_options_vix_filter.py's
# module docstring for the full reasoning). Deliberately a SEPARATE
# strategy/book, not a modification of simple_st1/st2/st3's existing
# BANKNIFTY entries - those already have live trade history toward
# the 1-week review; changing their signal mid-week would contaminate
# that comparison.
VIX_FILTER_BANKNIFTY = make_vix_filter_config()

ALL_STRATEGIES = [
    (check_or_open_generic, SIMPLE_ST1_NIFTY),
    (check_or_open_generic, SIMPLE_ST1_BANKNIFTY),
    (check_or_open_generic, ST2_NIFTY),
    (check_or_open_generic, ST2_BANKNIFTY),
    (check_or_open_generic, ST3_NIFTY),
    (check_or_open_generic, ST3_BANKNIFTY),
    (check_or_open_st4, ST4_NIFTY),
    (check_or_open_st4, ST4_BANKNIFTY),
    (check_or_open_gapfill, GAPFILL_NIFTY),
    (check_or_open_gapfill, GAPFILL_BANKNIFTY),
    (check_or_open_generic, SIMPLE_ST1_TH_NIFTY),
    (check_or_open_generic, SIMPLE_ST1_TH_BANKNIFTY),
    (check_or_open_generic, ST2_TH_NIFTY),
    (check_or_open_generic, ST2_TH_BANKNIFTY),
    (check_or_open_generic, ST3_TH_NIFTY),
    (check_or_open_generic, ST3_TH_BANKNIFTY),
    (check_or_open_st4, ST4_TH_NIFTY),
    (check_or_open_st4, ST4_TH_BANKNIFTY),
    (check_or_open_gapfill, GAPFILL_TH_NIFTY),
    (check_or_open_gapfill, GAPFILL_TH_BANKNIFTY),
    (check_or_open_vix_filter, VIX_FILTER_BANKNIFTY),
]
