import 'package:flutter/material.dart';

import '../api.dart';
import '../theme.dart';
import '../widgets/candlestick_chart.dart';
import '../widgets/common.dart';

/// Full-screen candlestick chart for one symbol, opened by tapping a
/// position/trade on the Portfolio or History tab. Reads reports/
/// candles.json, refreshed roughly every 15 min by paper_trade.yml
/// (see refresh_candles.py) - not a tick-by-tick live feed.
class ChartScreen extends StatefulWidget {
  final String symbol;

  const ChartScreen({super.key, required this.symbol});

  @override
  State<ChartScreen> createState() => _ChartScreenState();
}

class _ChartScreenState extends State<ChartScreen> {
  List<Map<String, dynamic>>? _candles;
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
      final data = await fetchJson(candlesUrl);
      final allCandles = Map<String, dynamic>.from(data?['Candles'] ?? {});
      final forSymbol = List<Map<String, dynamic>>.from(
          (allCandles[widget.symbol] ?? []).map((c) => Map<String, dynamic>.from(c)));

      setState(() {
        _candles = forSymbol;
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
    final lastClose = candles.isNotEmpty ? (candles.last['Close'] as num).toDouble() : null;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (lastClose != null)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Text('Last close: ${formatRupees(lastClose)}',
                style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500)),
          ),
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(color: surfaceColor, borderRadius: BorderRadius.circular(12)),
          child: CandlestickChart(candles: candles),
        ),
        const SizedBox(height: 8),
        Text(
          _generatedAt == null
              ? 'Chart refreshes roughly every 15 min while the market is open, not tick-by-tick live.'
              : 'Updated $_generatedAt · refreshes roughly every 15 min while the market is open, not tick-by-tick live.',
          style: const TextStyle(fontSize: 11, color: mutedColor),
        ),
      ],
    );
  }
}
