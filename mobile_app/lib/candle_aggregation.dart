// Added 21-Aug-2026, at the user's own request: a timeframe selector
// (1/5/10/15 min) for the live charts. Built entirely client-side from
// the existing 1-min candle history/live stream - no new backend data
// needed, since every coarser timeframe is just a grouping of the same
// 1-min candles the app already has. Pure function, no widget/state -
// both live_chart_screen.dart and strategy_premium_chart_screen.dart
// call this the same way.

/// Groups a list of 1-min OHLC(V) candles (oldest-first, the shape
/// LiveCandleAggregator/the app's own tick-by-tick aggregation already
/// produce) into `minutes`-wide buckets, real-clock-aligned (a 5-min
/// bucket starts at :00/:05/:10/..., not at an arbitrary offset).
/// `minutes == 1` returns the input unchanged (no work to do). Volume
/// is summed across the buckets that make it up when present; omitted
/// entirely when the input candles don't carry it (matches the
/// underlying SPOT candles, which never have real volume - see
/// strategy/tick_collector.py's own LiveCandleAggregator.on_tick()).
List<Map<String, dynamic>> aggregateCandles(List<Map<String, dynamic>> oneMinCandles, int minutes) {
  if (minutes <= 1 || oneMinCandles.isEmpty) {
    return oneMinCandles;
  }

  final buckets = <Map<String, dynamic>>[];

  for (final candle in oneMinCandles) {
    final timestamp = candle['Timestamp'] as String?;
    if (timestamp == null || timestamp.length < 16) continue;

    final bucketTimestamp = _floorToBucket(timestamp, minutes);

    if (buckets.isNotEmpty && buckets.last['Timestamp'] == bucketTimestamp) {
      final bucket = buckets.last;
      final high = (candle['High'] as num).toDouble();
      final low = (candle['Low'] as num).toDouble();
      if (high > (bucket['High'] as num)) bucket['High'] = high;
      if (low < (bucket['Low'] as num)) bucket['Low'] = low;
      bucket['Close'] = candle['Close'];
      if (candle.containsKey('Volume')) {
        bucket['Volume'] = ((bucket['Volume'] as num?) ?? 0) + ((candle['Volume'] as num?) ?? 0);
      }
      continue;
    }

    buckets.add({
      'Timestamp': bucketTimestamp,
      'Open': candle['Open'],
      'High': candle['High'],
      'Low': candle['Low'],
      'Close': candle['Close'],
      if (candle.containsKey('Volume')) 'Volume': candle['Volume'],
    });
  }

  return buckets;
}

/// "YYYY-MM-DD HH:MM:00" for the `minutes`-wide bucket a 1-min candle's
/// own "YYYY-MM-DD HH:MM:00" timestamp falls into (minute floored down
/// to the nearest multiple of `minutes`).
String _floorToBucket(String timestamp, int minutes) {
  final datePart = timestamp.substring(0, 11); // "YYYY-MM-DD "
  final hour = timestamp.substring(11, 13);
  final minute = int.parse(timestamp.substring(14, 16));
  final bucketMinute = (minute ~/ minutes) * minutes;

  return '$datePart$hour:${bucketMinute.toString().padLeft(2, '0')}:00';
}
