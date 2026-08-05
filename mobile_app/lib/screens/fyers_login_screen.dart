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

enum _Stage { idle, triggering, success, error }

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

    setState(() => _stage = _Stage.triggering);

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
        setState(() => _stage = _Stage.success);
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
        _Stage.success => const Center(
            child: Padding(
              padding: EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.check_circle_outline, size: 48, color: successColor),
                  SizedBox(height: 16),
                  Text(
                    'Triggered! Today\'s Fyers data collection and paper trading is running '
                    'in the background (GitHub Actions). Check the Fyers/Options tabs in a '
                    'few minutes.',
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
