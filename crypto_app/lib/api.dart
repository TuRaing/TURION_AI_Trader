import 'dart:convert';
import 'package:http/http.dart' as http;

// Reads the SAME Firebase Realtime Database path run_crypto_options_
// engine.py already writes to on the VM (report/firebase_realtime_
// sync.py's sync_portfolio(), path "event_driven_portfolios/
// {strategy_name}") - see mobile_app/lib/event_driven_realtime_
// service.dart for the main app's equivalent, which uses the
// firebase_database SDK + a live Stream. This app deliberately uses
// plain HTTPS REST polling instead: the RTDB's read rules are already
// public (confirmed via a direct curl, 29-Aug-2026), so no
// firebase_core/firebase_database SDK, no google-services.json, no
// per-app Firebase Console registration is needed at all for a
// read-only, single-purpose app - the entire backend integration is
// one URL.
const _rtdbBase = 'https://turion-ai-trader-default-rtdb.asia-southeast1.firebasedatabase.app';

/// `strategyName` matches run_crypto_options_engine.py's own
/// STRATEGY_NAME ("rsi_momentum_crypto_btc" / "rsi_momentum_crypto_eth").
String portfolioUrl(String strategyName) => '$_rtdbBase/event_driven_portfolios/$strategyName.json';

/// Cache-busted fetch (matches mobile_app/lib/api.dart's own fetchJson
/// pattern) - null on "no data yet" (a book that hasn't synced a
/// single tick since deploy) rather than an error, same as a 404
/// elsewhere in this project.
Future<Map<String, dynamic>?> fetchPortfolio(String strategyName) async {
  final uri = Uri.parse('${portfolioUrl(strategyName)}?t=${DateTime.now().millisecondsSinceEpoch}');
  final response = await http.get(uri).timeout(const Duration(seconds: 15));

  if (response.statusCode != 200) {
    throw Exception('Firebase returned ${response.statusCode}');
  }

  if (response.body == 'null') {
    return null;
  }

  return json.decode(response.body) as Map<String, dynamic>;
}
