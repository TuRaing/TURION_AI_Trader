import datetime

import yfinance as yf
import pandas as pd

from indicators.rsi import calculate_rsi
from indicators.black_scholes import black_scholes_price
from strategy.options_transaction_costs import calculate_options_round_trip_cost

# Added 03-Aug-2026 - researched at the user's suggestion: a NIFTY options
# money-management strategy, deploying the full capital into one ATM
# option each day, booking a fixed % NET (after estimated real costs)
# profit target, cutting losses at a fixed % Stop-Loss. Two entry modes:
# the default always-fire RSI>=50 tie-break (guarantees a trade every
# day, but is not this repo's actual tested signal), or
# use_momentum_vix_filter=True to use the real tested Momentum(RSI)+VIX
# signal from strategy/momentum_vix_backtest.py instead (fires less than
# once per day - see that parameter's docstring for the important NIFTY
# vs BANKNIFTY caveat).
#
# TWO CAVEATS, both explained in more depth in their own modules:
# 1. No real historical NIFTY option premium data exists (confirmed
#    30-Jul - NSE's option chain API only serves today's live snapshot).
#    This backtest ESTIMATES premium from spot + India VIX via
#    Black-Scholes (indicators/black_scholes.py) - a theoretical
#    approximation, not a real traded price.
# 2. Real weekly-expiry days-to-expiry isn't reconstructed from history
#    here (NSE has changed the weekly-expiry weekday more than once -
#    this repo already documented BANKNIFTY's weekly expiry being
#    discontinued Nov-2024). days_to_expiry is a fixed, configurable
#    approximation instead of a real expiry calendar.
#
# Analysis only - not wired into any paper trading or live automation.
# Options logic kept fully separate from equity/index signal logic, per
# this repo's rule.

STRIKE_STEP = 50  # NIFTY option strikes are quoted in steps of 50 (BANKNIFTY: 100)


def _flatten(series):

    if hasattr(series, "columns"):
        return series.iloc[:, 0]

    return series


def run_nifty_options_backtest(
    symbol="^NSEI",
    vix_symbol="^INDIAVIX",
    period="60d",
    interval="5m",
    capital=100000,
    lot_size=75,
    strike_step=STRIKE_STEP,
    days_to_expiry=3,
    risk_free_rate=0.065,
    target_net_pct=1.0,
    stop_loss_pct=1.0,
    entry_time="09:20",
    squareoff_time="15:15",
    hold_iv_fixed_at_entry=True,
    use_momentum_vix_filter=False,
    rsi_bullish=60,
    rsi_bearish=40,
    vix_percentile_low=0.20,
    vix_percentile_high=0.80,
    vix_lookback_candles=125,
):
    """
    Backtests an index options money-management strategy (NIFTY by
    default; pass symbol="^NSEBANK", lot_size=30, strike_step=100 to
    test the same rules on BANKNIFTY instead - NOTE BANKNIFTY's weekly
    expiry was discontinued Nov-2024 per NSE/SEBI rules, monthly only
    now, so the fixed days_to_expiry approximation this backtest uses
    is considerably less realistic for BANKNIFTY than for NIFTY, which
    still has weekly expiry):

    - Exactly one trade per trading day, entered at the first 5m candle at
      or after entry_time.
    - Direction picked from that candle's RSI: CE if RSI >= 50 (bullish
      lean), PE otherwise - always has a side, unlike a >60/<40 threshold,
      so a trade is never skipped for lack of a strong-enough signal.
    - Strike: nearest ATM (spot rounded to the nearest STRIKE_STEP).
    - Position size: as many lots as the full `capital` affords at the
      estimated entry premium (floor division - unused capital sits
      idle that day if it doesn't divide evenly into a whole lot).
    - Exit at whichever comes first: NET P&L (after estimated real
      options costs) >= +target_net_pct% of capital ("Target"), NET P&L
      <= -stop_loss_pct% of capital ("Stop Loss"), or squareoff_time
      ("Square-Off") - mirrors this repo's existing intraday-only
      guarantee (Best Trade Engine's forced 14:45 square-off).

    Premium is re-estimated every candle via Black-Scholes (spot moves,
    time-to-expiry ticks down by the real elapsed time) - see
    indicators/black_scholes.py. No look-ahead: every decision at a
    candle only uses that candle's own data and earlier.

    hold_iv_fixed_at_entry : bool
        Updated 03-Aug-2026, default True - if True, the implied
        volatility used for every candle's repricing is frozen at
        entry_time's India VIX reading for the rest of that day; only
        spot and time-to-expiry keep moving. Found necessary after an
        early version repriced off the LIVE, continuously-updating VIX
        every candle: at 5m and even 1m granularity this made Stop-Loss
        exits overshoot their nominal threshold by 4-9x (e.g. a nominal
        -0.5% SL realizing -4.48% avg / -13.76% worst at 5m) because the
        raw VIX index has its own tick-to-tick calculation noise that a
        real option's IV does not track that literally - not a real
        market dynamic, an artifact of this estimation method. If False,
        restores the old live-VIX-every-candle behavior (kept only for
        comparison/debugging, not recommended for reading results).

    use_momentum_vix_filter : bool
        Updated 03-Aug-2026, default False - if True, replaces the
        default "always trade, direction from RSI>=50" rule with this
        repo's actual TESTED signal (strategy/momentum_vix_backtest.py's
        22-Jul Momentum+VIX filter: RSI > rsi_bullish for CE, RSI <
        rsi_bearish for PE, only while India VIX sits inside its own
        recent [vix_percentile_low, vix_percentile_high] rolling
        percentile band). Scans every candle from entry_time to
        squareoff_time for the first one where the filter fires, instead
        of checking only the single entry_time candle - so this trades
        LESS than once per day (a day with no qualifying candle is
        skipped), unlike the default mode's guaranteed-daily-entry rule.
        CAVEAT carried over from momentum_vix_backtest.py: that 22-Jul
        test found this filter had NO reliable directional edge on
        NIFTY specifically (only 9/42 combos positive) - it was only
        BANKNIFTY where 38/42 combos were positive. Using it here on
        NIFTY is testing the properly-validated signal as requested, not
        a claim that it's expected to perform well on this index.
    rsi_bullish, rsi_bearish : float
        RSI thresholds - see strategy/momentum_vix_backtest.py.
    vix_percentile_low, vix_percentile_high, vix_lookback_candles :
        VIX rolling percentile band - see strategy/momentum_vix_backtest.py.
        Only used when use_momentum_vix_filter is True.

    Returns
    -------
    dict summary (see _summarize), or {"Error": str} if either symbol has
    no usable data.
    """

    price_data = yf.download(symbol, period=period, interval=interval, progress=False)
    vix_data = yf.download(vix_symbol, period=period, interval=interval, progress=False)

    if price_data.empty:
        return {"Error": f"No usable {interval} data for {symbol}"}

    if vix_data.empty:
        return {"Error": f"No usable {interval} data for {vix_symbol}"}

    close = _flatten(price_data["Close"])
    rsi = calculate_rsi(price_data)
    vix_close = _flatten(vix_data["Close"])

    vix_frame = {"VIX": vix_close}

    if use_momentum_vix_filter:
        vix_frame["VIX Low Band"] = vix_close.rolling(vix_lookback_candles).quantile(vix_percentile_low)
        vix_frame["VIX High Band"] = vix_close.rolling(vix_lookback_candles).quantile(vix_percentile_high)

    merged = pd.merge_asof(
        pd.DataFrame({"Close": close, "RSI": rsi}).reset_index(),
        pd.DataFrame(vix_frame).reset_index(),
        on=price_data.index.name or "Datetime",
        direction="backward",
    ).set_index(price_data.index.name or "Datetime")

    entry_hh, entry_mm = (int(part) for part in entry_time.split(":"))
    entry_cutoff = datetime.time(entry_hh, entry_mm)

    squareoff_hh, squareoff_mm = (int(part) for part in squareoff_time.split(":"))
    squareoff_cutoff = datetime.time(squareoff_hh, squareoff_mm)

    time_to_expiry_years_0 = days_to_expiry / 365.0

    day_results = []

    for trading_day, day_rows in merged.groupby(merged.index.date):

        window = day_rows[(day_rows.index.time >= entry_cutoff) & (day_rows.index.time <= squareoff_cutoff)]

        if window.empty:
            day_results.append({"Date": trading_day, "Skipped": "No candle at/after entry_time"})
            continue

        entry_timestamp = None
        entry_row = None
        option_type = None

        if use_momentum_vix_filter:

            for timestamp, row in window.iterrows():

                if pd.isna(row["RSI"]) or pd.isna(row["VIX"]) or pd.isna(row.get("VIX Low Band")):
                    continue

                vix_in_band = row["VIX Low Band"] <= row["VIX"] <= row["VIX High Band"]

                if not vix_in_band:
                    continue

                if row["RSI"] > rsi_bullish:
                    entry_timestamp, entry_row, option_type = timestamp, row, "CE"
                    break

                if row["RSI"] < rsi_bearish:
                    entry_timestamp, entry_row, option_type = timestamp, row, "PE"
                    break

            if entry_timestamp is None:
                day_results.append({"Date": trading_day, "Skipped": "No aligned Momentum+VIX signal fired"})
                continue

        else:

            entry_timestamp = window.index[0]
            entry_row = window.iloc[0]

            if pd.isna(entry_row["RSI"]) or pd.isna(entry_row["VIX"]):
                day_results.append({"Date": trading_day, "Skipped": "RSI/VIX not available yet (warmup)"})
                continue

            option_type = "CE" if entry_row["RSI"] >= 50 else "PE"

        spot_entry = float(entry_row["Close"])
        strike = round(spot_entry / strike_step) * strike_step

        entry_premium = black_scholes_price(
            spot_entry, strike, time_to_expiry_years_0, float(entry_row["VIX"]) / 100.0, option_type, risk_free_rate,
        )

        lots = int(capital // (entry_premium * lot_size)) if entry_premium > 0 else 0

        if lots < 1:
            day_results.append({
                "Date": trading_day, "Skipped": "Capital insufficient for 1 lot",
                "Entry Premium": round(entry_premium, 2), "Strike": strike, "Option": option_type,
            })
            continue

        entry_volatility = float(entry_row["VIX"]) / 100.0

        quantity = lots * lot_size
        exit_reason = None
        exit_timestamp = None
        exit_premium = None
        net_pnl = None

        for timestamp, row in day_rows.loc[entry_timestamp:].iterrows():

            if pd.isna(row["Close"]):
                continue

            if hold_iv_fixed_at_entry:
                volatility = entry_volatility
            elif pd.isna(row["VIX"]):
                continue
            else:
                volatility = float(row["VIX"]) / 100.0

            elapsed_years = (timestamp - entry_timestamp).total_seconds() / (365.0 * 24 * 3600)
            time_to_expiry_years = max(time_to_expiry_years_0 - elapsed_years, 1e-6)

            current_premium = black_scholes_price(
                float(row["Close"]), strike, time_to_expiry_years, volatility, option_type, risk_free_rate,
            )

            gross_pnl = (current_premium - entry_premium) * quantity
            cost = calculate_options_round_trip_cost(entry_premium, current_premium, lot_size, lots)
            candidate_net_pnl = gross_pnl - cost
            candidate_net_pnl_pct = candidate_net_pnl / capital * 100

            at_squareoff = timestamp.time() >= squareoff_cutoff
            is_last_candle = timestamp == day_rows.index[-1]

            if candidate_net_pnl_pct >= target_net_pct:
                exit_reason, exit_timestamp, exit_premium, net_pnl = "Target", timestamp, current_premium, candidate_net_pnl
                break

            if candidate_net_pnl_pct <= -stop_loss_pct:
                exit_reason, exit_timestamp, exit_premium, net_pnl = "Stop Loss", timestamp, current_premium, candidate_net_pnl
                break

            if at_squareoff or is_last_candle:
                reason = "Square-Off" if at_squareoff else "End Of Data"
                exit_reason, exit_timestamp, exit_premium, net_pnl = reason, timestamp, current_premium, candidate_net_pnl
                break

        day_results.append({
            "Date": trading_day,
            "Option": option_type,
            "Strike": strike,
            "Entry Time": entry_timestamp,
            "Entry Premium": round(entry_premium, 2),
            "Lots": lots,
            "Quantity": quantity,
            "Exit Time": exit_timestamp,
            "Exit Premium": round(exit_premium, 2) if exit_premium is not None else None,
            "Exit Reason": exit_reason,
            "Net PnL": round(net_pnl, 2) if net_pnl is not None else None,
            "Net PnL %": round(net_pnl / capital * 100, 3) if net_pnl is not None else None,
        })

    return _summarize(day_results, capital)


def _summarize(day_results, capital):

    traded = [d for d in day_results if "Skipped" not in d]
    skipped = [d for d in day_results if "Skipped" in d]

    wins = [d for d in traded if d["Net PnL"] > 0]
    losses = [d for d in traded if d["Net PnL"] <= 0]

    total_net_pnl = sum(d["Net PnL"] for d in traded)
    win_rate = (len(wins) / len(traded) * 100) if traded else 0

    exit_reasons = {}
    for d in traded:
        exit_reasons[d["Exit Reason"]] = exit_reasons.get(d["Exit Reason"], 0) + 1

    return {
        "Trading Days": len(day_results),
        "Days Traded": len(traded),
        "Days Skipped": len(skipped),
        "Skip Reasons": {r: sum(1 for d in skipped if d["Skipped"] == r) for r in {d["Skipped"] for d in skipped}},
        "Wins": len(wins),
        "Losses": len(losses),
        "Win Rate": round(win_rate, 2),
        "Total Net PnL": round(total_net_pnl, 2),
        "Total Net PnL %": round(total_net_pnl / capital * 100, 2),
        "Avg Net PnL % Per Trading Day": round(total_net_pnl / capital * 100 / len(traded), 3) if traded else 0,
        "Exit Reasons": exit_reasons,
        "Days": day_results,
    }
