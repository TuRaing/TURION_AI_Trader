#!/bin/bash
# Added 26-Aug-2026, real recurring incident: this repo's own file
# ownership on the VPS has drifted to root TWICE within 48 hours
# (25-Aug: blocked the daily 08:00 IST deploy.sh auto-restart for
# ~2 hours after a real login, undetected until a human noticed;
# 26-Aug: 7 more files, same root cause - Claude running git/file
# operations directly as root over SSH instead of as `turion`).
# "Remember to chown after every root-SSH session" already failed
# once, live, despite being written down - this is the safety net
# instead: install as a root crontab entry running every 5 minutes,
# so any future drift (from this cause or any other) self-heals
# within minutes, well before it could ever block a real scheduled
# operation like the 08:00 IST restart.
#
# Install (one-time, VPS-side):
#   crontab -u root -e
#   */5 * * * * /opt/turion/TURION_AI_Trader/deploy/fix_ownership.sh
#
# Deliberately silent on the common case (nothing to fix) - only
# writes to the log when it actually finds and corrects drift, so the
# log itself becomes a real record of how often this happens, not
# noise to scroll past.

REPO_DIR="/opt/turion/TURION_AI_Trader"
LOG_FILE="/var/log/turion-ownership-fix.log"

drifted=$(find "$REPO_DIR" -not -user turion 2>/dev/null)

if [ -n "$drifted" ]; then
    {
        echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - found $(echo "$drifted" | wc -l) non-turion-owned file(s), fixing:"
        echo "$drifted"
        chown -R turion:turion "$REPO_DIR"
        echo "  -> fixed."
    } >> "$LOG_FILE"
fi
