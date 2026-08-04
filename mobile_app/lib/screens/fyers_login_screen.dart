import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:webview_flutter/webview_flutter.dart';

import '../theme.dart';

// Added 04-Aug-2026 - the in-app "Login to Fyers" button. Opens Fyers'
// real OAuth login page in an in-app WebView (PIN/OTP is typed
// directly into Fyers' own page - this app's code never sees it),
// detects the redirect containing auth_code, then triggers
// .github/workflows/fyers_trigger.yml via GitHub's REST API, which
// exchanges that one-time code for today's access token and runs every
// Fyers data task in one job (see fyers_trigger_run.py) - the token
// never persists anywhere beyond that single run.
//
// GITHUB_PAT is a fine-grained, this-repo-only, Actions:write-only
// token, passed at BUILD TIME via --dart-define (never hardcoded or
// committed) - see the build command noted in doc/04aug26_SESSION_LOG.md.
// A leaked build could only ever trigger this repo's own workflows,
// not access the user's broader GitHub account or their Fyers account.

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

enum _Stage { loadingLogin, awaitingLogin, triggering, success, error }

class _FyersLoginScreenState extends State<FyersLoginScreen> {
  late final WebViewController _controller;
  _Stage _stage = _Stage.loadingLogin;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();

    if (_githubPat.isEmpty) {
      _stage = _Stage.error;
      _errorMessage = 'App was built without a GITHUB_PAT (--dart-define) - '
          'the trigger cannot be sent. Rebuild with the token.';
      return;
    }

    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageStarted: (_) => setState(() => _stage = _Stage.awaitingLogin),
          onNavigationRequest: (request) {
            if (request.url.startsWith(_redirectUri)) {
              _handleRedirect(request.url);
              return NavigationDecision.prevent;
            }
            return NavigationDecision.navigate;
          },
        ),
      )
      ..loadRequest(Uri.parse(_fyersLoginUrl));
  }

  void _handleRedirect(String url) {
    final authCode = Uri.parse(url).queryParameters['auth_code'];

    if (authCode == null || authCode.isEmpty) {
      setState(() {
        _stage = _Stage.error;
        _errorMessage = 'Login redirect did not contain an auth_code.';
      });
      return;
    }

    _triggerWorkflow(authCode);
  }

  Future<void> _triggerWorkflow(String authCode) async {
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
        _Stage.loadingLogin || _Stage.awaitingLogin => WebViewWidget(controller: _controller),
        _Stage.triggering => const Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(),
                SizedBox(height: 16),
                Text('Login captured - starting today\'s Fyers run...'),
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
        _Stage.error => Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.error_outline, size: 48, color: dangerColor),
                  const SizedBox(height: 16),
                  Text(_errorMessage ?? 'Something went wrong.', textAlign: TextAlign.center),
                ],
              ),
            ),
          ),
      },
    );
  }
}
