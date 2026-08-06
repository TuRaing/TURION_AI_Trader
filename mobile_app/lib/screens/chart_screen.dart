import 'package:flutter/material.dart';

import '../api.dart';
import '../theme.dart';
import '../widgets/candlestick_chart.dart';
import '../widgets/common.dart';

/// Full-screen candlestick chart for one symbol, opened by tapping a
/// position/trade on the Portfolio or History tab. Reads reports/
/// candles.json, refreshed roughly every 15 min by paper_trade.yml
/// (see refresh_candles.py) - not a tick-by-tick live feed.
///
/// entryPrice/stopLoss/target/exitPrice are optional - when the caller
/// has them (every open position and closed trade does), they're drawn
/// as reference lines on the chart and summarized against the latest
/// price, so the chart shows where the trade sits against the market,
/// not just a bare price series.
class ChartScreen extends StatefulWidget {
  final String symbol;
  final double? entryPrice;
  final double? stopLoss;
  final double? target;
  final double? exitPrice;
  final String direction;
  // Added 06-Aug-2026 - lets Fyers screens point this at fyersCandlesUrl
  // (refresh_fyers_candles.py's output) instead of the yfinance-only
  // default, without duplicating this whole screen.
  final String candleDataUrl;

  const ChartScreen({
    super.key,
    required this.symbol,
    this.entryPrice,
    this.stopLoss,
    this.target,
    this.exitPrice,
    this.direction = 'BUY',
    this.candleDataUrl = candlesUrl,
  });

  @override
  State<ChartScreen> createState() => _ChartScreenState();
}

class _ChartScreenState extends State<ChartScreen> {
  List<Map<String, dynamic>>? _candles;
  Map<String, dynamic>? _selected;
  String? _generatedAt;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  Future<void> _fetch() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final data = await fetchJson(widget.candleDataUrl);
      final allCandles = Map<String, dynamic>.from(data?['Candles'] ?? {});
      final forSymbol = List<Map<String, dynamic>>.from(
          (allCandles[widget.symbol] ?? []).map((c) => Map<String, dynamic>.from(c)));

      setState(() {
        _candles = forSymbol;
        _selected = forSymbol.isNotEmpty ? forSymbol.last : null;
        _generatedAt = data?['Generated At'] as String?;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.symbol)),
      body: LoadingErrorWrapper(
        loading: _loading,
        error: _error,
        hasData: _candles != null,
        onRetry: _fetch,
        child: RefreshIndicator(onRefresh: _fetch, child: _buildBody()),
      ),
    );
  }

  Widget _buildBody() {
    final candles = _candles ?? [];

    if (candles.isEmpty) {
      return ListView(
        padding: const EdgeInsets.all(16),
        children: const [
          SizedBox(height: 60),
          Center(
              child: Text('No candle data available for this symbol yet', style: TextStyle(color: mutedColor))),
        ],
      );
    }

    final periodHigh = candles.map((c) => (c['High'] as num).toDouble()).reduce((a, b) => a > b ? a : b);
    final periodLow = candles.map((c) => (c['Low'] as num).toDouble()).reduce((a, b) => a < b ? a : b);
    final firstOpen = (candles.first['Open'] as num).toDouble();
    final lastClose = (candles.last['Close'] as num).toDouble();
    final periodChangePct = firstOpen == 0 ? null : (lastClose - firstOpen) / firstOpen * 100;

    final referenceLines = <ChartReferenceLine>[
      if (widget.entryPrice != null)
        ChartReferenceLine(price: widget.entryPrice!, label: 'Entry', color: accentColor),
      if (widget.stopLoss != null)
        ChartReferenceLine(price: widget.stopLoss!, label: 'SL', color: dangerColor),
      if (widget.target != null)
        ChartReferenceLine(price: widget.target!, label: 'Target', color: successColor),
      if (widget.exitPrice != null)
        ChartReferenceLine(price: widget.exitPrice!, label: 'Exit', color: mutedColor),
    ];

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (widget.entryPrice != null)
          _TradeSummaryCard(
            entryPrice: widget.entryPrice!,
            comparePrice: widget.exitPrice ?? lastClose,
            compareLabel: widget.exitPrice != null ? 'Exit price' : 'Current price',
            direction: widget.direction,
          ),
        if (widget.entryPrice != null) const SizedBox(height: 10),
        if (_selected != null) _SelectedCandleInfo(candle: _selected!),
        const SizedBox(height: 10),
        Container(
          padding: const EdgeInsets.fromLTRB(8, 12, 4, 8),
          decoration: BoxDecoration(color: surfaceColor, borderRadius: BorderRadius.circular(12)),
          child: CandlestickChart(
            candles: candles,
            onSelect: (c) => setState(() => _selected = c),
            referenceLines: referenceLines,
          ),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(child: StatPill(label: 'Period High', value: formatRupees(periodHigh))),
            const SizedBox(width: 10),
            Expanded(child: StatPill(label: 'Period Low', value: formatRupees(periodLow))),
            const SizedBox(width: 10),
            Expanded(
              child: StatPill(
                label: 'Change',
                value: periodChangePct == null
                    ? '—'
                    : '${periodChangePct >= 0 ? '+' : ''}${periodChangePct.toStringAsFixed(1)}%',
                valueColor: periodChangePct == null ? null : pnlColor(periodChangePct),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        Text(
          _generatedAt == null
              ? 'Chart refreshes roughly every 15 min while the market is open, not tick-by-tick live. Tap or drag the chart to read a candle.'
              : 'Updated ${formatBackendTimestamp(_generatedAt)} · refreshes roughly every 15 min while the market is open, not tick-by-tick live. Tap or drag the chart to read a candle.',
          style: const TextStyle(fontSize: 11, color: mutedColor),
        ),
      ],
    );
  }
}

class _TradeSummaryCard extends StatelessWidget {
  final double entryPrice;
  final double comparePrice;
  final String compareLabel;
  final String direction;

  const _TradeSummaryCard({
    required this.entryPrice,
    required this.comparePrice,
    required this.compareLabel,
    required this.direction,
  });

  @override
  Widget build(BuildContext context) {
    final isBuy = direction == 'BUY';
    final diff = isBuy ? (comparePrice - entryPrice) : (entryPrice - comparePrice);
    final diffPct = entryPrice == 0 ? null : (diff / entryPrice * 100);
    final color = pnlColor(diff);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(12)),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Entry price', style: TextStyle(fontSize: 11, color: mutedColor)),
                Text(formatRupees(entryPrice), style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
              ],
            ),
          ),
          const Icon(Icons.arrow_forward, size: 16, color: mutedColor),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(compareLabel, style: const TextStyle(fontSize: 11, color: mutedColor)),
                Text(formatRupees(comparePrice), style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(formatSignedRupees(diff), style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: color)),
              if (diffPct != null)
                Text('${diffPct >= 0 ? '+' : ''}${diffPct.toStringAsFixed(2)}%',
                    style: TextStyle(fontSize: 12, color: color)),
            ],
          ),
        ],
      ),
    );
  }
}

class _SelectedCandleInfo extends StatelessWidget {
  final Map<String, dynamic> candle;

  const _SelectedCandleInfo({required this.candle});

  @override
  Widget build(BuildContext context) {
    final open = (candle['Open'] as num).toDouble();
    final high = (candle['High'] as num).toDouble();
    final low = (candle['Low'] as num).toDouble();
    final close = (candle['Close'] as num).toDouble();
    final isUp = close >= open;
    final color = isUp ? successColor : dangerColor;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(12)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(formatBackendTimestamp(candle['Timestamp'] as String?),
                  style: const TextStyle(fontSize: 12, color: mutedColor)),
              const Spacer(),
              Text(formatRupees(close), style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: color)),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _OhlcValue(label: 'O', value: open),
              _OhlcValue(label: 'H', value: high),
              _OhlcValue(label: 'L', value: low),
              _OhlcValue(label: 'C', value: close),
            ],
          ),
        ],
      ),
    );
  }
}

class _OhlcValue extends StatelessWidget {
  final String label;
  final double value;

  const _OhlcValue({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(label, style: const TextStyle(fontSize: 10, color: mutedColor)),
        const SizedBox(height: 2),
        Text(formatRupees(value), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500)),
      ],
    );
  }
}
