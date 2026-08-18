#!/usr/bin/env bash
set -euo pipefail

# Added 18-Aug-2026 - the "how does code get onto the VPS" piece
# flagged as missing alongside deploy/turion-event-driven.service.
# Same status as everything else in this batch: code-prep only, NOT
# LIVE-TESTED (no VPS exists yet to run this against) - only checked
# for shell syntax (bash -n), not a real deploy.
#
# DESIGN: this script lives IN the repo and runs ON the VPS itself.
# It does NOT push code from a developer machine over SSH - that would
# need SSH key secrets and a known VPS host wired into GitHub Actions,
# an extra exposed surface this project doesn't need. Simplest working
# piece: "update the checkout that's already there, then restart the
# service."
#
# DECIDED 18-Aug-2026 - push-triggered (GitHub Actions on every commit
# to main) was considered and explicitly REJECTED: this repo's main
# branch gets automated "[skip ci]" commits every 1-2 minutes all day
# (cron-job.org driven options-portfolio updates - see git log) that
# have nothing to do with the event-driven engine's own code. Deploying
# on every push would restart the live engine dozens of times a day,
# including mid-market-hours with real positions open - the same class
# of live-connection-drop risk this project already saw hurt a book
# (oi_footprint's overshoot-on-gap-in-checking issue, PROJECT_STATUS.
# md/14-Aug). Pure-manual was also rejected - a daily pre-market
# refresh is routine and easy to forget.
#
# CHOSEN: a VPS-side cron job, once per day, well BEFORE market open
# (09:15 IST) so the restart + fresh WebSocket connection has time to
# settle before it matters - e.g. (once the VPS exists):
#   0 8 * * 1-5 /opt/turion/TURION_AI_Trader/deploy/deploy.sh >> /var/log/turion-deploy.log 2>&1
# (08:00 IST, Mon-Fri only - no reason to deploy on a non-trading day).
# Manual `ssh` + running this script directly is STILL always available
# on top of the cron schedule, for a same-day urgent fix - the cron
# entry is the routine default, not the only path.
#
# A SECOND, separate cron entry belongs alongside this one - see
# deploy/turion-event-driven.service's own "DECIDED" comment for why
# (a login tapped in the app after this 08:00 restart would otherwise
# leave the engine stopped all day) and its exact crontab line.
#
# REPO_DIR must match deploy/turion-event-driven.service's
# WorkingDirectory placeholder - keep both in sync if either changes
# once the real VPS path is known.

REPO_DIR="/opt/turion/TURION_AI_Trader"
VENV_DIR="$REPO_DIR/venv"
SERVICE_NAME="turion-event-driven"
BRANCH="main"

cd "$REPO_DIR"

echo "==> Fetching latest from origin/$BRANCH..."
git fetch origin "$BRANCH"

LOCAL_REV=$(git rev-parse HEAD)
REMOTE_REV=$(git rev-parse "origin/$BRANCH")

if [ "$LOCAL_REV" = "$REMOTE_REV" ]; then
    echo "==> Already up to date ($LOCAL_REV) - nothing to deploy."
    exit 0
fi

# A VPS checkout should never accumulate its own uncommitted edits -
# docs/config for this project live on main via the developer's own
# machine (see CLAUDE.md), not here. Refusing rather than silently
# discarding whatever this is (someone's untracked debugging, a
# half-finished manual fix) via a forced reset/checkout.
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "ERROR: uncommitted local changes on the VPS checkout - refusing to deploy." >&2
    echo "Run 'git status' on the VPS and resolve manually before re-running." >&2
    exit 1
fi

echo "==> Updating $LOCAL_REV -> $REMOTE_REV"
git merge --ff-only "origin/$BRANCH"

echo "==> Installing/updating dependencies..."
"$VENV_DIR/bin/pip" install -q -r requirements.txt

# Needs the deploy user to have passwordless sudo for exactly this
# one systemctl command (`sudo visudo`, restrict the NOPASSWD line to
# this command only) - not set up yet, another VPS-side one-time step
# once the box exists, same category as deploy/turion-event-driven.
# service's own User=/WorkingDirectory placeholders.
echo "==> Restarting $SERVICE_NAME..."
sudo systemctl restart "$SERVICE_NAME"

sleep 2
echo "==> Service status:"
sudo systemctl status "$SERVICE_NAME" --no-pager -l | head -n 15

echo "==> Deploy complete ($REMOTE_REV)."
