import datetime

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

# Added 19-Aug-2026 - REAL BUG FOUND via a live incident, not theory:
# every one of this project's strategy modules computed
# `past_squareoff = (now_ist.hour, now_ist.minute) >= squareoff_time`
# independently (13 separate copies across strategy/fyers_options_*.py,
# plus 2 more in strategy/live_tick_harness.py for the event-driven
# engine) - comparing ONLY time-of-day, with zero awareness of the
# calendar date. A position opened one day and still open when next
# checked (e.g. the next morning, before that day's own squareoff_time)
# is NOT force-closed, because e.g. (8,33) is not >= (15,15) - it just
# keeps running with a stale entry, unprotected, until the ordinary
# Stop-Loss/Target math eventually happens to catch up.
#
# CAUGHT LIVE, 19-Aug-2026: simple_st1_slcap/NIFTY opened a CE at
# 14:56 IST on 18-Aug, was never checked again before that day's own
# 15:15 IST squareoff cutoff, sat overnight completely unmonitored
# (no scheduled workflow runs outside market hours), and was only
# picked up again the next morning (08:33 IST, 19-Aug) - past_squareoff
# was False at that moment (still morning), so the squareoff path never
# fired; the position was only closed because its Stop-Loss math
# eventually registered the loss, by which point the option premium had
# collapsed from Rs 37.3 to Rs 0.05 (essentially worthless) - a
# Rs 1,23,027 loss against an intended Rs 2,000 hybrid-cap Stop-Loss
# (61x overshoot), on a book that ALREADY had hybrid_sl_cap_pct=2.0
# set. A tighter Stop-Loss cap would not have prevented this - the
# real gap was date-blindness, not a loose cap. 10 other books hit the
# identical overnight-carry pattern the same night (PROJECT_STATUS.md/
# session log has the full list) - this was systemic, not a one-off.
#
# FIX: one shared, single well-tested function, used everywhere this
# check happens, instead of 15 independent copies that could each
# silently drift or be missed during a future edit - reduces exactly
# the "same bug fixed in one place, still broken in the other 14"
# risk this rewrite itself is meant to close. Used by BOTH engines -
# the older polling engine (12 modules) AND the event-driven engine
# (strategy/live_tick_harness.py, both runner classes) - the same
# date-blindness applies there too: a position still open when the
# VPS process restarts the next morning (e.g. deploy.sh's daily
# 08:00 IST cron restart) would hit the identical gap otherwise. See
# the entry_stored_as_utc parameter below - the two engines store
# "Entry Time" differently, and this function accounts for both
# rather than assuming one.


def is_past_squareoff(position_entry_time_str, now_ist, squareoff_time, entry_stored_as_utc=True):
    """
    True if an open intraday position should be force-closed right
    now - either because it is still open from a PREVIOUS calendar
    day (in IST) regardless of the current time-of-day, or because
    today's own squareoff_time has been reached.

    Parameters
    ----------
    position_entry_time_str : str, "%Y-%m-%d %H:%M:%S" - the position's
        stored "Entry Time".
    now_ist : datetime.datetime, timezone-aware, already converted to
        IST (e.g. datetime.datetime.now(IST)).
    squareoff_time : (hour, minute) tuple, IST.
    entry_stored_as_utc : bool, default True - this project stores
        "Entry Time" in TWO different ways depending on which engine
        wrote it (confirmed 19-Aug-2026, see PROJECT_STATUS.md's
        UTC-vs-IST entry - not yet unified project-wide, a known,
        deliberately deferred issue): the older polling engine
        (strategy/fyers_options_*.py, 12 modules) stores naive UTC
        (datetime.datetime.now().strftime(...), no tzinfo, despite
        looking like a plain timestamp) - the default here. The
        event-driven engine (strategy/event_driven_engine.py, via
        live_tick_harness.py) stores the tick's own already-IST
        timestamp directly - pass entry_stored_as_utc=False for that
        caller, or this function would wrongly shift it by 5:30 and
        could misjudge which calendar day the position was opened on.

    Returns
    -------
    bool
    """

    entry_naive = datetime.datetime.strptime(position_entry_time_str, "%Y-%m-%d %H:%M:%S")

    if entry_stored_as_utc:
        entry_date_ist = entry_naive.replace(tzinfo=datetime.timezone.utc).astimezone(IST).date()
    else:
        entry_date_ist = entry_naive.date()

    if entry_date_ist < now_ist.date():
        return True

    return (now_ist.hour, now_ist.minute) >= squareoff_time
