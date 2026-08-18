import 'package:firebase_database/firebase_database.dart';

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
  final ref = FirebaseDatabase.instance.ref('$_eventDrivenPortfolioPath/$strategyName');

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
