from strategy.fyers_options_engine import make_strategy

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

ALL_STRATEGIES = [
    SIMPLE_ST1_NIFTY,
    SIMPLE_ST1_BANKNIFTY,
    ST2_NIFTY,
    ST2_BANKNIFTY,
    ST3_NIFTY,
    ST3_BANKNIFTY,
]
