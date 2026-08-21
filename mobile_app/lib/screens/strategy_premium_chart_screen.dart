import 'dart:async';

import 'package:flutter/material.dart';

import '../candle_aggregation.dart';
import '../event_driven_realtime_service.dart';
import '../theme.dart';
import '../widgets/candlestick_chart.dart';
import '../widgets/common.dart';
import '../widgets/timeframe_selector.dart';

// Added 21-Aug-2026, at the user's own request - a live chart showing
// EXACTLY where a specific event-driven book's current position sits
// against its own Entry/Target/Stop-Loss, on the option's own PREMIUM
// (not the underlying's spot price). Deliberately NOT the spot-price
// approximation originally discussed: this app's own existing options
// screens (fyers_multi_strategy_options_screen.dart) already made this
// exact call once before - ChartScreen there only ever plots Entry
// Spot, never Target/SL, specifically because premium and spot move on
// different scales and a spot-equivalent line would need an estimated
// delta, not a real one. A real broker app charts an option position
// against its own premium for the same reason - so this screen does
// the same, fed by strategy/event_driven_runner.py's own on_message()
// (see that file's 21-Aug-2026 note), which already knows the exact
// CE/PE symbol this book is actually trading (run_tick_collector.py's
// own ATM pick is independent and can differ).
//
// Target/Stop-Loss premiums are computed here from the SAME formula
// strategy/event_driven_engine.py's rsi_momentum_decide_fn/
// oi_footprint_decide_fn actually use (_net_pnl/_hybrid_stop_loss_cap)
// - EXCEPT the round-trip transaction cost term (options_transaction_
// costs.py's calculate_options_round_trip_cost()), which is small,
// known, and deliberately omitted rather than duplicating that
// formula's own real-money-rounding logic a second time in Dart. The
// lines are therefore very close but not bit-for-bit identical to the
// real trigger point - labelled honestly in the info banner below.

class StrategyPremiumChartScreen extends StatefulWidget {
  final String strategyKey;
  final String strategyLabel;
  final Map<String, dynamic> position; // Entry Premium, Option Type, Lots, Capital Deployed
  final int lotSize;
  final double initialCapital;
  final double hybridSlCapPct;
  final double? targetNetPct;
  final double? stopLossPct;
  final double? targetRupees;
  final double? stopLossRupees;

  const StrategyPremiumChartScreen({
    super.key,
    required this.strategyKey,
    required this.strategyLabel,
    required this.position,
    required this.lotSize,
    required this.initialCapital,
    required this.hybridSlCapPct,
    this.targetNetPct,
    this.stopLossPct,
    this.targetRupees,
    this.stopLossRupees,
  });

  @override
  State<StrategyPremiumChartScreen> createState() => _StrategyPremiumChartScreenState();
}

class _StrategyPremiumChartScreenState extends State<StrategyPremiumChartScreen> {
  // CHANGED 21-Aug-2026 - see live_chart_screen.dart's matching note;
  // must stay equal to strategy/tick_collector.py's own
  // LiveCandleAggregator max_candles.
  static const _maxCandles = 400;

  final List<Map<String, dynamic>> _candles = [];
  Map<String, dynamic>? _selected;
  StreamSubscription<Map<String, dynamic>?>? _sub;
  DateTime? _lastTickAt;
  int _timeframeMinutes = 1;

  String get _leg => widget.position['Option Type'] == 'PE' ? 'PE' : 'CE';

  @override
  void initState() {
    super.initState();
    _seedFromHistory();
    _sub = watchStrategyTick(widget.strategyKey, _leg).listen(_onTick);
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }

  // Same history-then-live race handling as live_chart_screen.dart's
  // own _seedFromHistory() - see that file's matching comment.
  Future<void> _seedFromHistory() async {
    final history = await fetchStrategyCandles(widget.strategyKey, _leg);

    if (!mounted || history.isEmpty) return;

    setState(() {
      final seeded = <Map<String, dynamic>>[];

      for (final candle in history) {
        final timestamp = candle['Timestamp'] as String?;
        if (timestamp == null || timestamp.length < 16) continue;

        seeded.add({
          '_minuteKey': timestamp.substring(0, 16),
          'Timestamp': timestamp,
          'Open': (candle['Open'] as num).toDouble(),
          'High': (candle['High'] as num).toDouble(),
          'Low': (candle['Low'] as num).toDouble(),
          'Close': (candle['Close'] as num).toDouble(),
          if (candle['Volume'] != null) 'Volume': (candle['Volume'] as num).toDouble(),
        });
      }

      if (seeded.isNotEmpty && _candles.isNotEmpty &&
          seeded.last['_minuteKey'] == _candles.first['_minuteKey']) {
        seeded.removeLast();
      }

      _candles.insertAll(0, seeded);
      if (_candles.length > _maxCandles) {
        _candles.removeRange(0, _candles.length - _maxCandles);
      }
    });
  }

  // Added 21-Aug-2026, alongside chart volume bars - Fyers' own
  // vol_traded_today (carried in every live tick as "volume", see
  // strategy/event_driven_runner.py's on_message()) is CUMULATIVE
  // since market open, not a per-tick delta - tracks the cumulative
  // reading at the CURRENT candle's own open and subtracts it back out
  // on every tick, same logic as strategy/tick_collector.py's own
  // LiveCandleAggregator.on_tick(), just re-derived here client-side
  // since this screen builds its own current (still-forming) candle
  // live rather than waiting for the next backend sync.
  double? _volumeAtBucketOpen;

  void _onTick(Map<String, dynamic>? tick) {
    if (tick == null) return;

    final ltp = (tick['ltp'] as num?)?.toDouble();
    final timestamp = tick['timestamp'] as String?;
    final cumulativeVolume = (tick['volume'] as num?)?.toDouble();

    if (ltp == null || timestamp == null || timestamp.length < 16) return;

    final minuteKey = timestamp.substring(0, 16);

    setState(() {
      _lastTickAt = DateTime.now();

      if (_candles.isNotEmpty && _candles.last['_minuteKey'] == minuteKey) {
        final current = _candles.last;
        if (ltp > (current['High'] as num)) current['High'] = ltp;
        if (ltp < (current['Low'] as num)) current['Low'] = ltp;
        current['Close'] = ltp;
        if (cumulativeVolume != null && _volumeAtBucketOpen != null) {
          current['Volume'] = cumulativeVolume - _volumeAtBucketOpen!;
        }
      } else {
        _volumeAtBucketOpen = cumulativeVolume;
        _candles.add({
          '_minuteKey': minuteKey,
          'Timestamp': '$minuteKey:00',
          'Open': ltp,
          'High': ltp,
          'Low': ltp,
          'Close': ltp,
          if (cumulativeVolume != null) 'Volume': 0.0,
        });
        if (_candles.length > _maxCandles) {
          _candles.removeAt(0);
        }
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final entryPremium = (widget.position['Entry Premium'] as num).toDouble();
    final lots = (widget.position['Lots'] as num).toInt();
    final capitalDeployed = (widget.position['Capital Deployed'] as num).toDouble();
    final quantity = lots * widget.lotSize;

    final targetPremium = widget.targetNetPct != null
        ? entryPremium + (widget.targetNetPct! / 100 * widget.initialCapital) / quantity
        : entryPremium + widget.targetRupees! / quantity;

    final flatCap = widget.initialCapital * widget.hybridSlCapPct / 100;
    final pctCap = capitalDeployed * widget.hybridSlCapPct / 100;
    final hybridCap = flatCap < pctCap ? flatCap : pctCap;
    final slPremium = entryPremium - hybridCap / quantity;

    final referenceLines = [
      ChartReferenceLine(price: entryPremium, label: 'Entry', color: accentColor),
      ChartReferenceLine(price: targetPremium, label: 'Target', color: successColor),
      ChartReferenceLine(price: slPremium, label: 'SL', color: dangerColor),
    ];

    final displayCandles = aggregateCandles(_candles, _timeframeMinutes);

    return Scaffold(
      appBar: AppBar(title: Text('${widget.strategyLabel} · $_leg Premium')),
      body: Column(
        children: [
          Container(
            width: double.infinity,
            margin: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(color: accent2Color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(8)),
            child: Text(
              _lastTickAt == null
                  ? 'Waiting for the first live $_leg premium tick from the VPS...'
                  : 'Target/SL are estimates (real trigger also nets a small transaction cost) - the actual close reason always comes from the Closed Trade record.',
              style: const TextStyle(fontSize: 12, color: accent2Color),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: TimeframeSelector(
              selected: _timeframeMinutes,
              onChanged: (minutes) => setState(() => _timeframeMinutes = minutes),
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
            child: displayCandles.isEmpty
                ? const Center(child: CircularProgressIndicator())
                : CandlestickChart(
                    candles: displayCandles,
                    referenceLines: referenceLines,
                    onSelect: (c) => setState(() => _selected = c),
                  ),
          ),
        ],
      ),
    );
  }
}
