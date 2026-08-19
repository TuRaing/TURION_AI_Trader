# Added 19-Aug-2026 - the analytical core for the 3 daily automated
# checks the user asked for (pre-market, running-market, after-market),
# at the user's own explicit request the same day this session found
# and fixed the date-blind squareoff bug and the UTC-vs-IST timestamp
# bug. Deliberately built as PURE, testable functions operating on
# already-fetched data - no live Fyers/network calls in this module -
# matching this project's established "extract the testable decision,
# keep live I/O wiring thin and separate" split (see strategy/
# execution_backend.py, strategy/squareoff.py for the same pattern).
#
# NOT YET WIRED to an actual scheduled task or push notification -
# that's blocked on the same FIREBASE_SERVICE_ACCOUNT local-env-var
# setup already flagged in doc/19aug26_SESSION_LOG.md's "daily health-
# check plan" entry (needs a fresh Firebase Console key, deferred by
# the user to do alongside tomorrow's VPS/Firebase Part A work). This
# module is the part that COULD be built and tested tonight without
# that - the live-data wiring + Scheduled Task creation + notification
# delivery is next session's work once that key exists.

import datetime


def detect_crash(nifty_change_pct, banknifty_change_pct, threshold_pct=2.0):
    """
    True if EITHER index has moved (up or down) at least threshold_pct
    intraday - the user's own chosen threshold (19-Aug), based on
    today's real ~0.4% "sौम्य bearish" day being nowhere close to
    alert-worthy. Direction-agnostic - a +2% spike is just as much a
    "something unusual is happening, look now" signal as a -2% drop.

    Returns
    -------
    (is_crash: bool, reason: str or None)
    """

    triggers = []

    if abs(nifty_change_pct) >= threshold_pct:
        triggers.append(f"NIFTY {nifty_change_pct:+.2f}%")

    if abs(banknifty_change_pct) >= threshold_pct:
        triggers.append(f"BANKNIFTY {banknifty_change_pct:+.2f}%")

    if not triggers:
        return False, None

    return True, f"Intraday move >= {threshold_pct}%: " + ", ".join(triggers)


def intended_stop_loss_cap(initial_capital, capital_deployed, hybrid_sl_cap_pct=2.0):
    """
    The SAME hybrid-cap formula already used throughout this project
    (strategy/fyers_options_engine.py's _hybrid_stop_loss_cap, and
    today's own real-data backtest) - min(flat %-of-capital,
    %-of-deployed). Used here as a GENERAL anomaly-detection heuristic
    across every book, not a replay of each individual strategy's own
    exact configured stop_loss_pct/hybrid_sl_cap_pct (those differ per
    book and aren't practical to import from 12+ separate modules just
    for a monitoring check) - a real loss many times bigger than what
    this reasonable, representative cap would have been is unusual
    regardless of that book's own precise settings.
    """

    flat_cap = initial_capital * (hybrid_sl_cap_pct / 100)
    pct_cap = capital_deployed * (hybrid_sl_cap_pct / 100)

    return min(flat_cap, pct_cap)


def detect_unusual_trade(trade, lot_size, initial_capital=100000, overshoot_multiple=3.0):
    """
    True if a closed trade's real loss is at least overshoot_multiple
    times the general intended_stop_loss_cap() - the user's own chosen
    threshold (19-Aug, "इंटेंडेड SL cap च्या Nx पट", N=3), picked after
    seeing today's real incidents range from ~2x (ordinary check-
    interval overshoot) up to 61x (the date-blind squareoff bug) -
    3x sits above routine overshoot noise but well below "something is
    seriously wrong" territory.

    Only flags LOSSES - a large win is never "unusual" in the sense
    this check cares about (a blown Stop-Loss, not a lucky Target).

    Parameters
    ----------
    trade : dict - one Closed Trades entry (needs Net PnL, Entry
        Premium, Lots at minimum).
    lot_size : int - 75 (NIFTY) or 30 (BANKNIFTY), the caller's job to
        pass the right one (strategy/fyers_options_engine.py's
        INDEX_CONFIG).

    Returns
    -------
    (is_unusual: bool, reason: str or None)
    """

    net_pnl = trade.get("Net PnL", 0)

    if net_pnl >= 0:
        return False, None

    entry_premium = trade.get("Entry Premium", 0)
    lots = trade.get("Lots", 0)
    capital_deployed = entry_premium * lots * lot_size

    cap = intended_stop_loss_cap(initial_capital, capital_deployed)

    if cap <= 0:
        return False, None

    if abs(net_pnl) >= overshoot_multiple * cap:
        overshoot = abs(net_pnl) / cap
        return True, f"Loss Rs {abs(net_pnl):,.2f} is {overshoot:.1f}x the intended ~Rs {cap:,.0f} cap"

    return False, None


def summarize_daily_pnl(books_today_trades):
    """
    Aggregate today's real trade PnL across every book that traded -
    the same computation this session did by hand (via ad-hoc scripts)
    several times today, made into one reusable, tested function
    instead of re-deriving it each time.

    Parameters
    ----------
    books_today_trades : dict of {book_name: list of today's Closed
        Trades dicts} - already filtered to today's date by the
        caller (this function doesn't know "today").

    Returns
    -------
    dict with:
        total_pnl, total_trades, wins, losses,
        per_book: list of (name, trade_count, pnl, wins) sorted worst-first
    """

    total_pnl = 0.0
    total_trades = 0
    wins = 0
    losses = 0
    per_book = []

    for name, trades in books_today_trades.items():

        if not trades:
            continue

        book_pnl = sum(t.get("Net PnL", 0) for t in trades)
        book_wins = sum(1 for t in trades if t.get("Net PnL", 0) > 0)
        book_losses = len(trades) - book_wins

        total_pnl += book_pnl
        total_trades += len(trades)
        wins += book_wins
        losses += book_losses

        per_book.append({
            "name": name,
            "trades": len(trades),
            "pnl": round(book_pnl, 2),
            "wins": book_wins,
        })

    per_book.sort(key=lambda b: b["pnl"])

    return {
        "total_pnl": round(total_pnl, 2),
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "per_book": per_book,
    }


def format_running_market_checklist(now_ist, crash_result, unusual_trades, pnl_summary,
                                     strategy_workflows=None):
    """
    Builds the "running market" tick-checklist the user asked for
    (19-Aug) - a scannable markdown report meant to be written to a
    log file every ~30 min while the market is open, and later also
    sent as the body of a push notification once the Firebase key
    unblocks that (see doc/19aug26_SESSION_LOG.md's daily health-check
    entry). Markdown checkbox syntax ("- [x]"/"- [ ]") rather than
    emoji, per this project's "no emoji unless asked" convention -
    renders as real checkboxes on GitHub/most markdown viewers too.

    Parameters
    ----------
    now_ist : datetime.datetime, IST.
    crash_result : (is_crash, reason) from detect_crash().
    unusual_trades : list of (book_name, reason) from scanning today's
        trades with detect_unusual_trade().
    pnl_summary : dict from summarize_daily_pnl().
    strategy_workflows : list of (strategy_name, is_stale, gap_minutes)
        - one detect_stale_workflow() result per running strategy/book
        (user's own ask, 19-Aug: "यात strategy working पण घाल" - show
        per-strategy whether it's actually alive, not just one generic
        workflow line), or None if not checked this run.

    Returns
    -------
    str - the full markdown report.
    """

    lines = [f"# Market Check - {now_ist.strftime('%Y-%m-%d %H:%M:%S')} IST", ""]

    is_crash, crash_reason = crash_result
    lines.append(f"- [{'x' if is_crash else ' '}] Crash check{f': {crash_reason}' if crash_reason else ' - normal'}")

    if unusual_trades:
        lines.append(f"- [x] Unusual trades found ({len(unusual_trades)}):")
        for name, reason in unusual_trades:
            lines.append(f"  - {name}: {reason}")
    else:
        lines.append("- [ ] No unusual trades this check")

    if strategy_workflows:
        stale = [s for s in strategy_workflows if s[1]]
        running_count = len(strategy_workflows) - len(stale)
        lines.append(
            f"- [{'x' if stale else ' '}] Strategy working status "
            f"({running_count}/{len(strategy_workflows)} running):"
        )
        for name, is_stale, gap_minutes in strategy_workflows:
            tick = "x" if is_stale else " "
            status = "STALE" if is_stale else "running"
            lines.append(f"  - [{tick}] {name}: {status} (last run {gap_minutes} min ago)")

    lines.append(
        f"- [ ] Today's PnL so far: Rs {pnl_summary['total_pnl']:,.2f} "
        f"({pnl_summary['wins']}W/{pnl_summary['losses']}L, {pnl_summary['total_trades']} trades)"
    )

    if pnl_summary["per_book"]:
        worst = pnl_summary["per_book"][0]
        lines.append(f"  - Worst book right now: {worst['name']} (Rs {worst['pnl']:,.2f})")

    return "\n".join(lines) + "\n"


def market_check_log_filename(now_ist):
    """
    The log filename for one format_running_market_checklist() report -
    user's own explicit naming choice (19-Aug): "market_check_date_time.log",
    one file per check rather than one append-only file per day, so each
    ~30-min check is independently readable/diffable. Kept as a pure
    string function (no file I/O here) for the same testability reason
    as the rest of this module - the live wiring script writes the
    actual file using this name.

    Parameters
    ----------
    now_ist : datetime.datetime, IST.

    Returns
    -------
    str, e.g. "market_check_20260820_103000.log"
    """

    return f"market_check_{now_ist.strftime('%Y%m%d_%H%M%S')}.log"


def format_pre_market_checklist(now_ist, token_ready, open_positions):
    """
    The first of the user's 3 daily checks (pre-market, running-market,
    after-market) - what matters BEFORE today's first trade, not during
    or after: (1) is a valid Fyers access token ready, since today's
    engines silently do nothing all day without one (same fact already
    called out in deploy/turion-event-driven.service's own comments -
    the user must tap "Login to Fyers" in the app each morning), and
    (2) is any book carrying an OPEN position into today that should
    have squared off yesterday - the exact failure mode of this
    session's own date-blind squareoff bug, so a pre-market carry-over
    is a real, specific red flag here, not a generic sanity check.

    Parameters
    ----------
    now_ist : datetime.datetime, IST.
    token_ready : bool - whether a live Fyers quote fetch just
        succeeded with today's token.
    open_positions : list of (book_name, position_dict) - one entry
        per book whose portfolio's "Position" is currently non-null.

    Returns
    -------
    str - the full markdown report.
    """

    lines = [f"# Pre-Market Check - {now_ist.strftime('%Y-%m-%d %H:%M:%S')} IST", ""]

    lines.append(
        f"- [{' ' if token_ready else 'x'}] Fyers access token"
        f"{' ready' if token_ready else ' NOT ready - login needed before today\'s engines can run'}"
    )

    if open_positions:
        lines.append(f"- [x] Carried-over open positions from yesterday ({len(open_positions)}):")
        for name, position in open_positions:
            symbol = position.get("Symbol", "?")
            entry_time = position.get("Entry Time", "?")
            lines.append(f"  - {name}: {symbol} (entered {entry_time})")
    else:
        lines.append("- [ ] No carried-over open positions")

    return "\n".join(lines) + "\n"


def detect_stale_workflow(last_run_ist, now_ist, max_gap_minutes=15):
    """
    True if a scheduled workflow's last real run is more than
    max_gap_minutes old, DURING market hours - the "एखादा strategy
    workflow मध्येच थांबला/चुकला का" check the user asked for. The
    caller is responsible for only calling this during market hours
    (09:15-15:30 IST) - a stale gap outside that window is expected
    and not a bug (see strategy/squareoff.py's own module docstring
    for the exact same "no scheduled runs outside market hours" fact
    that caused today's real overnight-carry incident).

    Parameters
    ----------
    last_run_ist, now_ist : timezone-aware datetime.datetime, IST.

    Returns
    -------
    (is_stale: bool, gap_minutes: float)
    """

    gap = (now_ist - last_run_ist).total_seconds() / 60

    return gap > max_gap_minutes, round(gap, 1)
