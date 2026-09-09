# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260909-001

--------------------------------------------------

Date

09-Sep-2026 (covers 07, 08, 09-Sep - three daily VPS login checks,
none individually doc'd until now)

--------------------------------------------------

04-SEP'S CRONTAB-RESTART FIX FINALLY CONFIRMED WORKING - TWO CLEAN
LIVE DAYS (07-Sep, 08-Sep). The "verify tomorrow" item flagged 04-Sep
(re: the `/var/log/turion-daily-restart.log` permission fix for the
unconditional 07:58 IST restart) never got a same-week live test since
05/06-Sep were the weekend. Both real trading days since then confirm
it working correctly, standalone, without deploy.sh's 08:00 IST
restart needing to coincidentally cover for it:

- 07-Sep: 07:58 IST restart fired on its own (`journalctl` shows a
  clean Stop/Start + "Got today's access_token via Firebase" +
  "Successfully connected"), independent of deploy.sh's own 08:00 IST
  restart 2 minutes later (which also succeeded, redundantly).
- 08-Sep: identical clean pattern, same 2-minute gap between the two
  restarts, both successful.

This closes out the open item from 04-Sep's log - the fix is proven,
not just theoretically correct.

==================================================

MONDAY/TUESDAY PNL (07, 08-Sep) - ALL 14 LIVE BOOKS, FROM VPS DIRECT.

07-Sep (Monday) - rough day, most books negative:

    Book                                  Trades   PnL
    oi_footprint_banknifty                  7      +373.88
    oi_footprint_nifty                      6     -1194.13
    oi_footprint_quote_banknifty            8      -977.74
    oi_footprint_quote_nifty                4     -3520.66
    simple_st1_threshold                    4    -11040.47
    simple_st1_threshold_lock               4    -11040.47
    simple_st1_threshold_lock_quote0.5%     2     -4225.73
    simple_st1_threshold_lock_quote1%       2     -4225.73
    simple_st1_threshold_lock_quote2%       2     -4225.73
    st2_threshold                           4     -4964.05
    st2_threshold_lock                      2     +2041.80
    st2_threshold_lock_quote0.5%            2     -4225.73
    st2_threshold_lock_quote1%              2     -4225.73
    st2_threshold_lock_quote2%              2     -4225.73
    TOTAL                                  51    -55676.22

08-Sep (Tuesday) - clear recovery, especially the "_lock*" families:

    Book                                  Trades   PnL
    oi_footprint_banknifty                  4      -246.91
    oi_footprint_nifty                      3     -2855.66
    oi_footprint_quote_banknifty            4      -617.09
    oi_footprint_quote_nifty                3     -2608.96
    simple_st1_threshold                    4     -1657.09
    simple_st1_threshold_lock               2     +3329.17
    simple_st1_threshold_lock_quote0.5%     2     +3080.66
    simple_st1_threshold_lock_quote1%       2     +3080.66
    simple_st1_threshold_lock_quote2%       2     +3080.66
    st2_threshold                           4     -1657.09
    st2_threshold_lock                      2     +3329.17
    st2_threshold_lock_quote0.5%            2     +3080.66
    st2_threshold_lock_quote1%              2     +3080.66
    st2_threshold_lock_quote2%              2     +3080.66
    TOTAL                                  38    +15499.50

oi_footprint family stayed roughly flat/negative both days; the
"_lock*" RSI-momentum variants flipped from the week's worst performers
(07-Sep) to the best (08-Sep) - no new gate/fix involved, just genuine
day-to-day market variance, consistent with this week's broader
finding that no artificial gate reliably improves on this.

==================================================

09-SEP MORNING - REAL, SELF-HEALED INCIDENT: FYERS API RATE-LIMIT (429)
FROM TWO CONCURRENT LOGIN SESSIONS. Sequence (all times IST):

- 07:58 - scheduled restart fires, connects fine with the token
  already in Firebase (from an earlier, presumably automated
  fyers_trigger.yml run - NOT the user's own manual login).
- 08:00 - deploy.sh's own restart fires too (redundant as always),
  also connects fine with the same token.
- 08:08 - user's own manual login lands, creating a SECOND, separate
  Fyers session while the engine's first session (from 07:58) was
  still actively live and mid-flight on an OI-snapshot option-chain
  call. The two concurrent sessions hitting Fyers' API around the same
  moment tripped Fyers' own rate limiter: `RuntimeError: Fyers option
  chain fetch failed for NSE:NIFTYBANK-INDEX: {'message': 'request
  limit reached', 'code': 429...}` - crashed the main process
  (uncaught, `Main process exited, code=exited, status=1/FAILURE`).
- 08:09 - systemd's existing `Restart=on-failure` policy (no crontab
  or manual action involved) restarted the service automatically 10
  seconds later, picked up the user's freshly-logged-in token, and
  reconnected cleanly. Total downtime ~10 seconds, no manual
  intervention needed, no further errors since.

Root cause confirmed by the user directly: they logged in manually
AFTER 08:00 IST, by which point the engine was already running on an
earlier (automated) token - the manual login created a second Fyers
session that collided with the running one's own API traffic. Not a
bug in this project's own code - existing `Restart=on-failure` already
handled it correctly and automatically. No fix needed or made; noting
it here only because it's a previously-unseen failure signature this
week (a live rate-limit crash, not a stale-token one) and the exact
trigger (two concurrent login sessions) is worth recognizing quickly
if it recurs.

==================================================

Status

🟢 Stable

Current Version

v0.0.71 (unchanged - no code/config changes this session, monitoring
and documentation only)

--------------------------------------------------

Next Session

1. The 04-Sep crontab-restart fix is now considered proven (2 clean
   live days) - no further verification needed, can be treated as
   closed/stable going forward.

2. If the Fyers 429 rate-limit crash recurs, consider whether it's
   worth a small stagger between the 07:58 automated restart and
   deploy.sh's 08:00 restart (currently only 2 minutes apart) to leave
   more headroom before a user's own manual login - not urgent given
   systemd's existing self-heal already covers it in ~10 seconds.

==================================================
