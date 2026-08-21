import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_database/firebase_database.dart';

// FIXED 21-Aug-2026 - real bug caught live: the app's VPS tab, live
// chart, AND Checks tab were all stuck on their loading spinner
// forever, on a real device, with real data already confirmed present
// in Firebase (verified directly via the REST API). Root cause:
// mobile_app/android/app/google-services.json has no "firebase_url"
// key (it predates the Realtime Database being enabled on this
// project, 20-Aug), and this project's RTDB instance lives in a
// NON-default region (asia-southeast1/Singapore, not the us-central1
// every `FirebaseDatabase.instance` call implicitly assumes without an
// explicit URL) - see doc/PROJECT_STATUS.md's 20-Aug "FIREBASE PART A"
// entry. Every `FirebaseDatabase.instance` call below silently
// resolved to a database that doesn't exist, so `ref.onValue` never
// fired even once - not an error, just permanently pending, which is
// exactly why the UI never left its CircularProgressIndicator. FIX:
// one shared instance built with the real databaseURL explicitly, used
// everywhere below instead of the bare `.instance` getter - robust to
// google-services.json never being regenerated with a "firebase_url"
// key, since the URL now lives in code, not a config file this repo
// doesn't control the regeneration of.
final _database = FirebaseDatabase.instanceFor(
  app: Firebase.app(),
  databaseURL: 'https://turion-ai-trader-default-rtdb.asia-southeast1.firebasedatabase.app',
);

// Added 18-Aug-2026 - the app-side half of the Firebase Realtime
// Database live-data path (see doc/PROJECT_STATUS.md's LIVE-DATA
// ARCHITECTURE entry and report/firebase_realtime_sync.py on the
// Python/VPS side, which writes to the SAME path structure this reads
// from). DIFFERENT Firebase product from the app's existing
// firebase_messaging setup (main.dart) - that's one-way push
// notifications; this is a live, subscribable data store, so the app
// no longer needs to periodically re-fetch a GitHub-hosted JSON file
// (api.dart's fetchJson() pattern) for the event-driven books
// specifically - Firebase pushes updates the instant the VPS writes
// them.
//
// NOT LIVE-TESTED - no VPS exists yet, no Realtime Database enabled
// in the Firebase Console yet either (a one-time manual step, not
// code). Written to match the documented firebase_database package
// API (DatabaseReference.onValue -> a Stream<DatabaseEvent>) - same
// "code-prep now, verify once the real pieces exist" discipline as
// tonight's Python-side WebSocket work.
//
// ONLY for the 4 NEW event-driven books (see strategy/event_driven_
// runner.py's STRATEGY_NAMES) - the 63 existing live books keep using
// api.dart's GitHub-raw-file polling unchanged, per this project's
// "never modify a working module" rule; this is an ADDITIONAL path,
// not a replacement of the existing screens' data source.

const _eventDrivenPortfolioPath = 'event_driven_portfolios';

/// One live-updating stream of a single event-driven book's portfolio
/// state (Cash/Position/Closed Trades), matching the JSON shape
/// report/firebase_realtime_sync.py's sync_portfolio() writes.
/// `strategyName` is the same key strategy/event_driven_runner.py's
/// STRATEGY_NAMES uses (e.g. "st2_threshold_eventdriven").
///
/// Emits null if the path has no data yet (book hasn't traded / synced
/// since Realtime Database was enabled) rather than throwing - the UI
/// should treat null the same way api.dart's fetchJson() already
/// treats a 404 (a legitimate "nothing yet" state, not an error).
Stream<Map<String, dynamic>?> watchEventDrivenPortfolio(String strategyName) {
  final ref = _database.ref('$_eventDrivenPortfolioPath/$strategyName');

  return ref.onValue.map((DatabaseEvent event) {
    final raw = event.snapshot.value;

    if (raw == null) {
      return null;
    }

    // Realtime Database returns nested Map<Object?, Object?> (dynamic
    // keys), not the Map<String, dynamic> the rest of this app's JSON
    // handling expects (see api.dart's fetchJson()) - convert once
    // here so every caller gets the same familiar shape.
    return _deepCastToStringKeyedMap(raw);
  });
}

// Added 20-Aug-2026 - two more live streams, same path structure the
// Python side writes (report/firebase_realtime_sync.py's sync_live_
// tick()/sync_health_check()) - for the new VPS tab's live chart and
// the new Checks tab.

const _liveTicksPath = 'live_ticks';
const _healthChecksPath = 'health_checks';

/// One live-updating stream of the latest tick for one leg (SPOT/CE/PE)
/// of one index (NIFTY/BANKNIFTY) - overwritten on every real tick by
/// run_tick_collector.py, so this is always "right now", not a history
/// (the VPS's own local JSONL archive is the history). Emits null if
/// the collector hasn't produced a tick for this leg yet today.
Stream<Map<String, dynamic>?> watchLiveTick(String index, String leg) {
  final ref = _database.ref('$_liveTicksPath/$index/$leg');

  return ref.onValue.map((DatabaseEvent event) {
    final raw = event.snapshot.value;
    return raw == null ? null : _deepCastToStringKeyedMap(raw);
  });
}

/// The most recent [limit] health-check runs of one type ("pre_market",
/// "market", or "after_market" - see run_pre_market_check.py/run_
/// market_check.py) newest-first, each with its own "report" text and
/// "timestamp" - a real feed of past runs, not just the latest one.
/// Emits [] if nothing has synced yet (not an error).
Stream<List<Map<String, dynamic>>> watchHealthChecks(String checkType, {int limit = 20}) {
  final ref = _database
      .ref('$_healthChecksPath/$checkType')
      .orderByKey()
      .limitToLast(limit);

  return ref.onValue.map((DatabaseEvent event) {
    final raw = event.snapshot.value;

    if (raw is! Map) {
      return <Map<String, dynamic>>[];
    }

    final entries = raw.entries.map((e) => _deepCastToStringKeyedMap(e.value)).toList();
    // Firebase push() keys sort chronologically as plain strings, and
    // Map iteration order from firebase_database already matches
    // insertion/key order in practice - sort explicitly anyway rather
    // than relying on that, then reverse for newest-first.
    entries.sort((a, b) => (a['timestamp'] as String? ?? '').compareTo(b['timestamp'] as String? ?? ''));
    return entries.reversed.toList();
  });
}

const _strategyTicksPath = 'strategy_ticks';
const _strategyCandlesPath = 'strategy_candles';

/// One live-updating stream of the latest CE/PE premium tick for one
/// event-driven book's own ATM strike (`strategyName` matches strategy/
/// event_driven_runner.py's STRATEGY_NAMES; `leg` is "CE" or "PE").
/// Added 21-Aug-2026, at the user's own request: a real option-premium
/// chart (Entry/Target/Stop-Loss overlaid, exact - matches how a real
/// broker app charts an option position, not a spot-price
/// approximation) for a specific book's CURRENT position. Deliberately
/// SEPARATE from watchLiveTick() above - a strategy's own ATM strike
/// can differ from run_tick_collector.py's independent ATM pick for
/// the same index, so the two are not interchangeable data. Emits null
/// if this leg hasn't ticked yet.
Stream<Map<String, dynamic>?> watchStrategyTick(String strategyName, String leg) {
  final ref = _database.ref('$_strategyTicksPath/$strategyName/$leg');

  return ref.onValue.map((DatabaseEvent event) {
    final raw = event.snapshot.value;
    return raw == null ? null : _deepCastToStringKeyedMap(raw);
  });
}

/// One-time fetch of the rolling 1-min premium-candle history for one
/// event-driven book's CE or PE leg - see watchStrategyTick()'s own
/// note above for the full context. A one-time get() (not a stream),
/// same seed-on-open pattern as fetchLiveCandles() below.
Future<List<Map<String, dynamic>>> fetchStrategyCandles(String strategyName, String leg) async {
  final snapshot = await _database.ref('$_strategyCandlesPath/$strategyName/$leg').get();
  return _castCandleList(snapshot.value);
}

const _liveCandlesPath = 'live_candles';

/// One-time fetch of the rolling 1-min candle history for [index]
/// (NIFTY/BANKNIFTY), maintained server-side by run_tick_collector.py's
/// LiveCandleAggregator and synced once per closed candle (see report/
/// firebase_realtime_sync.py's sync_live_candles()). Added 21-Aug-2026
/// to seed LiveChartScreen on open - real gap found live: the screen's
/// own client-side aggregation had no history to seed from, so opening
/// it showed just one lone building candle instead of a real chart.
/// A one-time get() (not a stream) - the screen keeps updating the
/// CURRENT candle live from its own existing watchLiveTick()
/// subscription afterward; this only needs to run once, at startup.
/// Returns [] if nothing has synced yet (not an error - matches every
/// other "nothing yet" path in this file).
Future<List<Map<String, dynamic>>> fetchLiveCandles(String index) async {
  final snapshot = await _database.ref('$_liveCandlesPath/$index').get();
  return _castCandleList(snapshot.value);
}

// FIXED 21-Aug-2026 - real bug caught live on a real device: both
// fetchLiveCandles() and fetchStrategyCandles() only ever handled
// `raw is List`, so a real backend-synced candle array (confirmed via
// a direct REST check - the data was genuinely there) still rendered
// as a completely empty chart. Root cause: the Realtime Database
// client SDK does not always deserialize a JSON array back into a
// Dart List - depending on how it was written, it can come back as a
// Map with numeric STRING keys ("0","1","2",...) instead (a known
// firebase_database quirk, distinct from the REST API's own behavior,
// which always shows a plain JSON array - exactly why testing this
// via curl looked fine while the app showed nothing). Handles both
// shapes now; the Map case sorts by the numeric key to restore
// oldest-first order.
List<Map<String, dynamic>> _castCandleList(dynamic raw) {
  if (raw is List) {
    return raw.whereType<Object>().map(_deepCastToStringKeyedMap).toList();
  }

  if (raw is Map) {
    final entries = raw.entries.toList()
      ..sort((a, b) =>
          (int.tryParse(a.key.toString()) ?? 0).compareTo(int.tryParse(b.key.toString()) ?? 0));
    return entries.map((e) => _deepCastToStringKeyedMap(e.value)).toList();
  }

  return <Map<String, dynamic>>[];
}

Map<String, dynamic> _deepCastToStringKeyedMap(dynamic value) {
  if (value is Map) {
    return value.map((key, v) => MapEntry(key.toString(), _deepCastValue(v)));
  }
  return <String, dynamic>{};
}

dynamic _deepCastValue(dynamic value) {
  if (value is Map) {
    return _deepCastToStringKeyedMap(value);
  }
  if (value is List) {
    return value.map(_deepCastValue).toList();
  }
  return value;
}
