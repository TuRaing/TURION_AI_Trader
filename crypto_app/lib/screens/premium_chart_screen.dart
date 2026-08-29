import 'dart:async';

import 'package:flutter/material.dart';

import '../api.dart';
import '../theme.dart';
import '../widgets/candlestick_chart.dart';
import '../widgets/common.dart';

// Added 29-Aug-2026, at the user's own request - a live CE/PE premium
// candlestick chart, same real-data (not spot-approximated) approach
// as the main app's strategy_premium_chart_screen.dart, but polling
// (see api.dart's own top comment for why this app has no live
// Firebase Stream) instead of a Stream subscription: seeds from
// fetchStrategyCandles() once, then re-polls fetchStrategyTick() every
// few seconds and merges the latest tick into the current, still-
// forming 1-min candle client-side - same bucket-merge logic the main
// app's _onTick() uses, just pulled instead of pushed.

class PremiumChartScreen extends StatefulWidget {
  final String strategyKey;
  final String bookLabel;
  final String leg;
  final String symbol;
  final List<ChartReferenceLine> referenceLines;

  const PremiumChartScreen({
    super.key,
    required this.strategyKey,
    required this.bookLabel,
    required this.leg,
    required this.symbol,
    required this.referenceLines,
  });

  @override
  State<PremiumChartScreen> createState() => _PremiumChartScreenState();
}

class _PremiumChartScreenState extends State<PremiumChartScreen> {
  static const _maxCandles = 400;

  final List<Map<String, dynamic>> _candles = [];
  Map<String, dynamic>? _selected;
  Timer? _pollTimer;
  DateTime? _lastTickAt;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _seedFromHistory();
    _pollTimer = Timer.periodic(const Duration(seconds: 3), (_) => _pollTick());
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  Future<void> _seedFromHistory() async {
    final history = await fetchStrategyCandles(widget.strategyKey, widget.leg);
    if (!mounted) return;

    setState(() {
      for (final candle in history) {
        final timestamp = candle['Timestamp'] as String?;
        if (timestamp == null || timestamp.length < 16) continue;

        _candles.add({
          '_minuteKey': timestamp.substring(0, 16),
          'Timestamp': timestamp,
          'Open': (candle['Open'] as num).toDouble(),
          'High': (candle['High'] as num).toDouble(),
          'Low': (candle['Low'] as num).toDouble(),
          'Close': (candle['Close'] as num).toDouble(),
        });
      }
      if (_candles.length > _maxCandles) {
        _candles.removeRange(0, _candles.length - _maxCandles);
      }
      _loading = false;
    });
  }

  Future<void> _pollTick() async {
    final tick = await fetchStrategyTick(widget.strategyKey, widget.leg);
    if (!mounted || tick == null) return;

    final ltp = (tick['ltp'] as num?)?.toDouble();
    final timestamp = tick['timestamp'] as String?;
    if (ltp == null || timestamp == null || timestamp.length < 16) return;

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
      appBar: AppBar(title: Text('${widget.bookLabel} · ${widget.leg} Premium')),
      body: Column(
        children: [
          Container(
            width: double.infinity,
            margin: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(color: accent2Color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(8)),
            child: Text(
              _lastTickAt == null
                  ? 'Waiting for the first live ${widget.leg} premium tick from the VM...'
                  : '${widget.symbol} - lines are Entry/Target/SL estimates; a real close always follows the actual trade record.',
              style: const TextStyle(fontSize: 12, color: accent2Color),
            ),
          ),
          if (_selected != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              child: Wrap(
                spacing: 16,
                runSpacing: 4,
                children: [
                  Text(formatBackendTimestamp(_selected!['Timestamp'] as String?),
                      style: const TextStyle(fontSize: 12, color: mutedColor)),
                  Text('O ${formatUsd(_selected!['Open'] as num)}', style: const TextStyle(fontSize: 12)),
                  Text('H ${formatUsd(_selected!['High'] as num)}', style: const TextStyle(fontSize: 12)),
                  Text('L ${formatUsd(_selected!['Low'] as num)}', style: const TextStyle(fontSize: 12)),
                  Text('C ${formatUsd(_selected!['Close'] as num)}', style: const TextStyle(fontSize: 12)),
                ],
              ),
            ),
          const SizedBox(height: 8),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : CandlestickChart(
                    candles: _candles,
                    referenceLines: widget.referenceLines,
                    onSelect: (c) => setState(() => _selected = c),
                  ),
          ),
        ],
      ),
    );
  }
}
