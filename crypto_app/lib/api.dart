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

// Added 29-Aug-2026, at the user's own request for a live candlestick
// chart - reads the SAME strategy_ticks/strategy_candles paths
// report/firebase_realtime_sync.py's sync_strategy_tick()/sync_
// strategy_candles() write (see run_crypto_options_engine.py's own
// matching 29-Aug-2026 note for the on_tick() wiring on the Python
// side). `leg` is "CE" or "PE".

String _strategyCandlesUrl(String strategyName, String leg) =>
    '$_rtdbBase/strategy_candles/$strategyName/$leg.json';
String _strategyTickUrl(String strategyName, String leg) => '$_rtdbBase/strategy_ticks/$strategyName/$leg.json';

/// One-time fetch of the rolling closed-candle history for one leg -
/// seeds the chart on open. [] if nothing has synced yet.
Future<List<Map<String, dynamic>>> fetchStrategyCandles(String strategyName, String leg) async {
  final uri = Uri.parse('${_strategyCandlesUrl(strategyName, leg)}?t=${DateTime.now().millisecondsSinceEpoch}');
  final response = await http.get(uri).timeout(const Duration(seconds: 15));

  if (response.statusCode != 200 || response.body == 'null') {
    return [];
  }

  final raw = json.decode(response.body);
  return _castCandleList(raw);
}

/// The latest single tick for one leg - polled periodically (this app
/// has no live Stream, see this file's own top comment) to keep the
/// CURRENT, still-forming candle updating between backend candle
/// closes. Null if nothing has synced yet.
Future<Map<String, dynamic>?> fetchStrategyTick(String strategyName, String leg) async {
  final uri = Uri.parse('${_strategyTickUrl(strategyName, leg)}?t=${DateTime.now().millisecondsSinceEpoch}');
  final response = await http.get(uri).timeout(const Duration(seconds: 15));

  if (response.statusCode != 200 || response.body == 'null') {
    return null;
  }

  return json.decode(response.body) as Map<String, dynamic>;
}

/// Firebase can return a JSON array OR a Map with numeric string keys
/// for the same logical list, depending on how it was written (a
/// known quirk - see mobile_app/lib/event_driven_realtime_service.dart's
/// own 21-Aug-2026 note about this exact behavior for the SDK; the
/// REST API is more consistent but this stays defensive rather than
/// assuming).
List<Map<String, dynamic>> _castCandleList(dynamic raw) {
  if (raw is List) {
    return raw.whereType<Object>().map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  if (raw is Map) {
    final entries = raw.entries.toList()
      ..sort((a, b) => (int.tryParse(a.key.toString()) ?? 0).compareTo(int.tryParse(b.key.toString()) ?? 0));
    return entries.map((e) => Map<String, dynamic>.from(e.value as Map)).toList();
  }

  return <Map<String, dynamic>>[];
}
