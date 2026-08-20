import 'dart:async';

import 'package:flutter/material.dart';

import '../event_driven_realtime_service.dart';
import '../theme.dart';
import '../widgets/candlestick_chart.dart';
import '../widgets/common.dart';

// Added 20-Aug-2026 - genuine tick-by-tick live candlestick chart
// (user's own explicit ask: "same as Fyers/TradingView"), fed directly
// by run_tick_collector.py's per-tick Firebase sync (event_driven_
// realtime_service.dart's watchLiveTick()) - NOT the existing
// ChartScreen's ~15-min-refresh reports/candles.json path, which stays
// unchanged for every other screen that already uses it.
//
// Candle aggregation (raw ticks -> 1-min OHLC) happens HERE, client-
// side in Dart, not on the backend - the backend only ever sends the
// single latest raw tick per leg (see report/firebase_realtime_sync.
// py's sync_live_tick(), one SET per tick, no history kept there).
// Capped to the most recent 120 candles (2 hours) to keep the chart
// widget's paint cost bounded during a long session.

class LiveChartScreen extends StatefulWidget {
  final String index; // 'NIFTY' or 'BANKNIFTY'

  const LiveChartScreen({super.key, required this.index});

  @override
  State<LiveChartScreen> createState() => _LiveChartScreenState();
}

class _LiveChartScreenState extends State<LiveChartScreen> {
  static const _maxCandles = 120;

  final List<Map<String, dynamic>> _candles = [];
  Map<String, dynamic>? _selected;
  StreamSubscription<Map<String, dynamic>?>? _sub;
  DateTime? _lastTickAt;

  @override
  void initState() {
    super.initState();
    _sub = watchLiveTick(widget.index, 'SPOT').listen(_onTick);
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }

  void _onTick(Map<String, dynamic>? tick) {
    if (tick == null) return;

    final ltp = (tick['ltp'] as num?)?.toDouble();
    final timestamp = tick['timestamp'] as String?;

    if (ltp == null || timestamp == null || timestamp.length < 16) return;

    // "YYYY-MM-DD HH:MM:SS.mmm" -> "YYYY-MM-DD HH:MM" - the 1-min
    // bucket this tick belongs to.
    final minuteKey = timestamp.substring(0, 16);

    setState(() {
      _lastTickAt = DateTime.now();

      if (_candles.isNotEmpty && _candles.last['_minuteKey'] == minuteKey) {
        final current = _candles.last;
        if (ltp > (current['High'] as num)) current['High'] = ltp;
        if (ltp < (current['Low'] as num)) current['Low'] = ltp;
        current['Close'] = ltp;
      } else {
        _candles.add({
          '_minuteKey': minuteKey,
          'Timestamp': '$minuteKey:00',
          'Open': ltp,
          'High': ltp,
          'Low': ltp,
          'Close': ltp,
        });
        if (_candles.length > _maxCandles) {
          _candles.removeAt(0);
        }
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('${widget.index} · Live')),
      body: Column(
        children: [
          Container(
            width: double.infinity,
            margin: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(color: accent2Color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(8)),
            child: Text(
              _lastTickAt == null
                  ? 'Waiting for the first live tick from the VPS...'
                  : 'Tick-by-tick live from the VPS - 1-min candles building in real time.',
              style: const TextStyle(fontSize: 12, color: accent2Color),
            ),
          ),
          if (_selected != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Wrap(
                spacing: 16,
                runSpacing: 4,
                children: [
                  Text(formatBackendTimestamp(_selected!['Timestamp'] as String?),
                      style: const TextStyle(fontSize: 12, color: mutedColor)),
                  Text('O ${formatRupees(_selected!['Open'] as num)}', style: const TextStyle(fontSize: 12)),
                  Text('H ${formatRupees(_selected!['High'] as num)}', style: const TextStyle(fontSize: 12)),
                  Text('L ${formatRupees(_selected!['Low'] as num)}', style: const TextStyle(fontSize: 12)),
                  Text('C ${formatRupees(_selected!['Close'] as num)}', style: const TextStyle(fontSize: 12)),
                ],
              ),
            ),
          const SizedBox(height: 8),
          Expanded(
            child: _candles.isEmpty
                ? const Center(child: CircularProgressIndicator())
                : CandlestickChart(
                    candles: _candles,
                    onSelect: (c) => setState(() => _selected = c),
                  ),
          ),
        ],
      ),
    );
  }
}
