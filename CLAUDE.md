# TURION AI Trader — Session Continuity Rules

The user works on this project from multiple devices/sessions
(desktop and mobile, via claude.ai/code and other clients). Two
sessions have already run in parallel on the same repo and diverged
without knowing about each other. Follow these rules at the start and
end of every session to avoid that happening again.

## At the start of every session

1. Run `git fetch origin`, then `git log HEAD..origin/main --oneline`
   to check for commits on `main` you don't have locally. If there
   are any, pull them before doing anything else.
2. Check for other branches with unmerged work:
   `git branch -r` and compare against `main`. If you find a branch
   that looks like it came from another session (e.g. an
   auto-generated name, or a `Claude-Session:` trailer in its commit
   messages), read it before starting - don't duplicate work that's
   already in progress elsewhere.
3. Read `doc/PROJECT_STATUS.md` for the current milestone state and
   known issues before proposing new work.

## During the session

- Docs (`doc/*.md`) live on `main`, not a side branch. Keep it that
  way - a session log only the desktop session can see is useless to
  a mobile session, and vice versa.
- If you discover another session's commits already merged into
  `main` mid-session, say so explicitly and reconcile rather than
  silently overwriting.

## At the end of a session that did real work

1. Add or update a `doc/DDmonYY_SESSION_LOG.md` entry for the day
   (append to today's if one already exists from another session
   rather than creating a duplicate).
2. Update `doc/PROJECT_STATUS.md` (version, milestones, known issues,
   next priorities).
3. Commit and push docs to `main` directly - don't leave them on an
   unmerged branch.

## Project-specific safety rules (carried over from prior sessions)

- Claude never executes a real trade - final action is always the
  user's, even after Broker Integration exists.
- Options (CALL/PUT) trading logic must stay fully separate from the
  normal NIFTY/BankNifty/stock signal and paper-trading logic.
- No engine should make trading decisions in isolation - every engine
  returns structured data; the Report Engine handles presentation.
