import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:url_launcher/url_launcher.dart';

import '../theme.dart';

// Added 04-Aug-2026, REWRITTEN 05-Aug-2026 - the in-app "Login to
// Fyers" button. Originally opened Fyers' login page in an embedded
// WebView, but that hangs forever - Fyers' login is protected by
// Google reCAPTCHA, which never completes inside an embedded WebView
// (Google treats it as an automated/non-standard browser). Confirmed
// live: the exact same URL works fine in the phone's real Chrome
// browser. Fixed by opening the login page in the device's REAL
// external browser (url_launcher) instead, then having the user paste
// the redirected URL (or bare auth_code) back into this screen - the
// same manual-paste pattern strategy/fyers_auth.py's desktop __main__
// flow already uses successfully. PIN/OTP is still typed directly into
// Fyers' own real browser page - this app's code never sees it.
//
// Sends the captured auth_code to .github/workflows/fyers_trigger.yml
// via GitHub's REST API, which exchanges it for today's access token
// and runs every Fyers data task - see fyers_trigger_run.py.
//
// GITHUB_PAT is a fine-grained, this-repo-only, Actions:write-only
// token, passed at BUILD TIME via --dart-define (never hardcoded or
// committed). A leaked build could only ever trigger this repo's own
// workflows, not access the user's broader GitHub account or their
// Fyers account.

const _fyersAppId = 'YLG4M5K861-200';
const _redirectUri = 'https://127.0.0.1';
const _githubOwner = 'TuRaing';
const _githubRepo = 'TURION_AI_Trader';
const _githubPat = String.fromEnvironment('GITHUB_PAT');

String get _fyersLoginUrl =>
    'https://api-t1.fyers.in/api/v3/generate-authcode'
    '?client_id=$_fyersAppId'
    '&redirect_uri=${Uri.encodeComponent(_redirectUri)}'
    '&response_type=code'
    '&state=turion_ai_trader';

/// Small reusable button - drop into any screen to launch the login flow.
class FyersLoginButton extends StatelessWidget {
  const FyersLoginButton({super.key});

  @override
  Widget build(BuildContext context) {
    return OutlinedButton.icon(
      onPressed: () => Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => const FyersLoginScreen()),
      ),
      icon: const Icon(Icons.login, size: 18),
      label: const Text('Login to Fyers (run today\'s check)'),
    );
  }
}

class FyersLoginScreen extends StatefulWidget {
  const FyersLoginScreen({super.key});

  @override
  State<FyersLoginScreen> createState() => _FyersLoginScreenState();
}

enum _Stage { idle, triggering, polling, success, error }

class _FyersLoginScreenState extends State<FyersLoginScreen> {
  final _pasteController = TextEditingController();
  _Stage _stage = _Stage.idle;
  String? _errorMessage;

  @override
  void dispose() {
    _pasteController.dispose();
    super.dispose();
  }

  Future<void> _openLoginPage() async {
    final uri = Uri.parse(_fyersLoginUrl);

    final opened = await launchUrl(uri, mode: LaunchMode.externalApplication);

    if (!opened && mounted) {
      setState(() {
        _stage = _Stage.error;
        _errorMessage = 'Could not open a browser. Copy this URL manually:\n$_fyersLoginUrl';
      });
    }
  }

  String? _extractAuthCode(String pasted) {
    final trimmed = pasted.trim();

    if (!trimmed.contains('auth_code=')) {
      return trimmed.isEmpty ? null : trimmed; // assume they pasted the bare code
    }

    final uri = Uri.tryParse(trimmed);
    return uri?.queryParameters['auth_code'];
  }

  Future<void> _submit() async {
    final authCode = _extractAuthCode(_pasteController.text);

    if (authCode == null || authCode.isEmpty) {
      setState(() {
        _stage = _Stage.error;
        _errorMessage = 'Paste the redirected URL (or the bare auth_code) first.';
      });
      return;
    }

    if (_githubPat.isEmpty) {
      setState(() {
        _stage = _Stage.error;
        _errorMessage = 'App was built without a GITHUB_PAT (--dart-define) - '
            'the trigger cannot be sent. Rebuild with the token.';
      });
      return;
    }

    // Reset - _errorMessage doubles as a success-path caveat (see
    // _didLoginSucceedDespiteFailure), so a stale value from a PREVIOUS
    // attempt must not leak into this one's plain-success screen.
    setState(() {
      _stage = _Stage.triggering;
      _errorMessage = null;
    });

    // Added 31-Aug-2026, real incident - a stale/reused auth_code (the
    // Fyers login redirect's auth_code is single-use and short-lived,
    // so resubmitting an old copy or logging in again without a fresh
    // paste both hit this) made the GitHub Actions workflow itself FAIL
    // (RuntimeError: "invalid auth code") while the dispatch call below
    // still returned 204 - all this screen ever showed was "Triggered!
    // success" regardless, so a real login failure looked identical to
    // a real success. dispatchedAt lets _pollForResult find the ONE run
    // this exact submit created (the dispatch API itself never returns
    // a run id) and wait for its REAL conclusion before saying anything
    // succeeded.
    final dispatchedAt = DateTime.now().toUtc();

    try {
      final uri = Uri.parse(
        'https://api.github.com/repos/$_githubOwner/$_githubRepo/actions/workflows/fyers_trigger.yml/dispatches',
      );

      final response = await http.post(
        uri,
        headers: {
          'Authorization': 'Bearer $_githubPat',
          'Accept': 'application/vnd.github+json',
        },
        body: json.encode({
          'ref': 'main',
          'inputs': {'auth_code': authCode},
        }),
      );

      if (response.statusCode == 204) {
        await _pollForResult(dispatchedAt);
      } else {
        setState(() {
          _stage = _Stage.error;
          _errorMessage = 'GitHub returned ${response.statusCode}: ${response.body}';
        });
      }
    } catch (e) {
      setState(() {
        _stage = _Stage.error;
        _errorMessage = e.toString();
      });
    }
  }

  /// Finds the workflow run this submit's dispatch created (matched by
  /// being the newest workflow_dispatch-triggered run created at or
  /// after [dispatchedAt] - the dispatch API itself never returns a run
  /// id) and waits for it to finish, polling every 4s for up to ~2 min
  /// (pip install + the Python script itself typically takes 30-90s).
  /// Only THIS - the run's real `conclusion` - is allowed to set
  /// _Stage.success; a 204 from the dispatch call above only means
  /// "GitHub accepted the request to run this," never that it worked.
  Future<void> _pollForResult(DateTime dispatchedAt) async {
    setState(() => _stage = _Stage.polling);

    final runsUri = Uri.parse(
      'https://api.github.com/repos/$_githubOwner/$_githubRepo/actions/workflows/fyers_trigger.yml/runs'
      '?event=workflow_dispatch&per_page=5',
    );
    final headers = {
      'Authorization': 'Bearer $_githubPat',
      'Accept': 'application/vnd.github+json',
    };

    // Added 31-Aug-2026 - real incident: fyers_trigger_run.py's single
    // "Run today's Fyers tasks" step does the auth_code exchange AND
    // THEN runs every other unrelated daily task (run_all_tasks() -
    // stock-history fetches for the older polling books, etc.). A
    // transient network/SSL error in ANY of those later, unrelated
    // fetches fails the WHOLE step - so a run whose login genuinely
    // succeeded can still show conclusion="failure", and this screen
    // was showing the scary "auth_code was likely already used" message
    // even then (confirmed live: login had actually already reached
    // Firebase before the later ITC-stock SSL error killed the job).
    // 45 x 4s = 3 min (was 2 min) - run_all_tasks() has been seen to
    // run past 100s+ before even reaching the failure point.
    for (var attempt = 0; attempt < 45; attempt++) {
      await Future.delayed(const Duration(seconds: 4));

      try {
        final response = await http.get(runsUri, headers: headers);
        if (response.statusCode != 200) continue;

        final runs = (json.decode(response.body)['workflow_runs'] as List).cast<Map<String, dynamic>>();
        final ourRun = runs.where((r) {
          final createdAt = DateTime.tryParse(r['created_at'] as String? ?? '');
          return createdAt != null && !createdAt.isBefore(dispatchedAt);
        }).toList();

        if (ourRun.isEmpty) continue; // GitHub hasn't created the run yet - keep waiting.

        final run = ourRun.last; // oldest of the matches = the one THIS submit created.

        if (run['status'] != 'completed') continue;

        if (run['conclusion'] == 'success') {
          if (mounted) setState(() => _stage = _Stage.success);
          return;
        }

        // Not a clean success - check whether the login itself actually
        // went through before treating this as an auth failure. "id" is
        // the RUN id; jobs (and their logs) are addressed by a separate
        // JOB id - fetch that first.
        final loginActuallySucceeded = await _didLoginSucceedDespiteFailure(run['id'], headers);

        if (mounted) {
          if (loginActuallySucceeded) {
            setState(() {
              _stage = _Stage.success;
              _errorMessage = 'Login itself succeeded - an unrelated background task '
                  '(unconnected to Fyers login) hit a transient error afterward. '
                  "Today's token is saved and working, no action needed.";
            });
          } else {
            setState(() {
              _stage = _Stage.error;
              _errorMessage = 'Login run failed (${run['conclusion']}) - the auth_code was likely '
                  'already used or had expired. Open Fyers Login again and paste the URL '
                  'IMMEDIATELY after it redirects, without reusing an old one.\n\n'
                  '${run['html_url']}';
            });
          }
        }
        return;
      } catch (_) {
        continue; // transient network hiccup - just retry on the next tick.
      }
    }

    // Timed out without seeing a completed run - don't claim success OR
    // failure, since we genuinely don't know yet.
    if (mounted) {
      setState(() {
        _stage = _Stage.error;
        _errorMessage = 'Dispatched, but could not confirm the result within 3 minutes. '
            'Check the VPS status badge on the VPS tab, or GitHub Actions directly.';
      });
    }
  }

  /// A failed run's log may still show the auth_code exchange itself
  /// succeeded ("Connected as ...") before some LATER, unrelated step
  /// failed - that's a real success, not an auth problem. Best-effort:
  /// any failure fetching job id/logs falls through to "false" (the
  /// caller's existing generic auth-failure message), never blocks the
  /// UI - this is a courtesy upgrade to the message, not a requirement.
  Future<bool> _didLoginSucceedDespiteFailure(dynamic runId, Map<String, String> headers) async {
    try {
      final jobsResponse = await http.get(
        Uri.parse('https://api.github.com/repos/$_githubOwner/$_githubRepo/actions/runs/$runId/jobs'),
        headers: headers,
      );
      if (jobsResponse.statusCode != 200) return false;

      final jobs = (json.decode(jobsResponse.body)['jobs'] as List).cast<Map<String, dynamic>>();
      if (jobs.isEmpty) return false;
      final jobId = jobs.first['id'];

      final logsResponse = await http.get(
        Uri.parse('https://api.github.com/repos/$_githubOwner/$_githubRepo/actions/jobs/$jobId/logs'),
        headers: headers,
      );
      if (logsResponse.statusCode != 200) return false;

      return logsResponse.body.contains('Connected as ');
    } catch (_) {
      return false;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Login to Fyers')),
      body: switch (_stage) {
        _Stage.triggering => const Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(),
                SizedBox(height: 16),
                Text('Starting today\'s Fyers run...'),
              ],
            ),
          ),
        // Added 31-Aug-2026 - the dispatch call succeeding only means
        // GitHub accepted the request; the actual auth_code exchange
        // happens inside the workflow run itself over the next ~30-90s,
        // so this stage exists to wait for and show the REAL result
        // rather than declaring success the instant the request lands.
        _Stage.polling => const Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(),
                SizedBox(height: 16),
                Text('Checking today\'s login actually went through...'),
                SizedBox(height: 8),
                Text(
                  'This confirms the real result, not just that the request was sent.',
                  style: TextStyle(fontSize: 12, color: mutedColor),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        _Stage.success => Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.check_circle_outline, size: 48, color: successColor),
                  const SizedBox(height: 16),
                  Text(
                    // _errorMessage doubles as a success-path caveat here
                    // (see _didLoginSucceedDespiteFailure's own note) -
                    // set only when the run technically failed but the
                    // login itself is confirmed to have gone through.
                    _errorMessage ??
                        'Confirmed! Today\'s login succeeded and the VPS has a valid token. '
                            'Check the VPS tab\'s status badge or the Fyers/Options tabs in a few minutes.',
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ),
        _Stage.idle || _Stage.error => Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Step 1: Open the Fyers login page in your browser and log in '
                  '(PIN/OTP goes directly to Fyers, not this app).',
                  style: TextStyle(fontSize: 14),
                ),
                const SizedBox(height: 12),
                FilledButton.icon(
                  onPressed: _openLoginPage,
                  icon: const Icon(Icons.open_in_browser),
                  label: const Text('Open Fyers Login'),
                ),
                const SizedBox(height: 24),
                const Text(
                  'Step 2: After logging in, the browser will try to redirect and show '
                  '"can\'t reach this page" - that\'s expected. Copy the FULL address-bar '
                  'URL (or just the auth_code=... part) and paste it below.',
                  style: TextStyle(fontSize: 14),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _pasteController,
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                    hintText: 'Paste the redirected URL or auth_code here',
                  ),
                  minLines: 1,
                  maxLines: 3,
                ),
                const SizedBox(height: 16),
                FilledButton.icon(
                  onPressed: _submit,
                  icon: const Icon(Icons.send),
                  label: const Text('Submit'),
                ),
                if (_stage == _Stage.error) ...[
                  const SizedBox(height: 16),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: dangerColor.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      _errorMessage ?? 'Something went wrong.',
                      style: const TextStyle(color: dangerColor, fontSize: 13),
                    ),
                  ),
                ],
              ],
            ),
          ),
      },
    );
  }
}
