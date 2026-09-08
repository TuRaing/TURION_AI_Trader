#!/bin/bash
# Added 08-Sep-2026, at the user's own explicit request, right after a
# real 3-day silent outage (see doc/CRYPTO_PROJECT_STATUS.md's own
# "[FIXED, 08-Sep-2026] All 7 crypto units silently down" entry) - a
# transient Deribit 503 crashed all 7 units at startup, systemd's own
# StartLimitBurst exhausted within ~30 seconds and gave up, and NOTHING
# was watching - the outage was only caught by chance via a routine
# PnL check. run_crypto_options_engine.py's own new retry logic (see
# that file's _retry_on_transient_error()) should prevent this exact
# failure mode going forward, but this health-check is the safety net
# for anything else that could still leave a unit in `failed` state
# (an unrelated crash, a VM reboot racing a dependency, etc.) -
# checked every 5 minutes via deploy/turion-crypto-healthcheck.timer,
# not left to be noticed by chance again.
#
# Deliberately a plain bash script, not Python - the one thing this
# needs (systemctl is-active/reset-failed/start) has no real advantage
# from a bigger runtime, and a script this small has one less thing
# that can itself fail to start.

UNITS=(
    turion-crypto-options
    turion-crypto-options-eth
    turion-crypto-options-btc-profitlock
    turion-crypto-options-eth-profitlock
    turion-crypto-options-btc-rsi70
    turion-crypto-options-eth-rsi70
    turion-crypto-options-btc-rsi70-lock
)

REPAIRED=()

for unit in "${UNITS[@]}"; do
    if ! sudo systemctl is-active --quiet "$unit"; then
        echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - $unit is NOT active, repairing..."
        sudo systemctl reset-failed "$unit" 2>&1
        sudo systemctl start "$unit" 2>&1
        sleep 2
        if sudo systemctl is-active --quiet "$unit"; then
            echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - $unit repaired successfully."
        else
            echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - $unit STILL NOT ACTIVE after repair attempt - needs manual attention."
        fi
        REPAIRED+=("$unit")
    fi
done

# Best-effort push notification (same channel/topic the NIFTY side's
# own connection-issue alerts already use - see strategy/event_driven_
# runner.py's _alert_connection_issue()) - only sent if at least one
# unit needed repair, so a normal healthy check stays silent. Never
# blocks/fails the health-check itself if Firebase isn't configured or
# the notification send fails - send_push_notification() already
# degrades gracefully on its own.
if [ ${#REPAIRED[@]} -gt 0 ]; then
    UNITS_LIST=$(IFS=', '; echo "${REPAIRED[*]}")
    cd ~/turion-crypto || exit 0
    ./venv/bin/python3 -c "
from report.push_notifier import send_push_notification
send_push_notification('TURION Crypto - Auto-Repaired', 'Restarted: ${UNITS_LIST}')
" 2>&1 || true
fi
