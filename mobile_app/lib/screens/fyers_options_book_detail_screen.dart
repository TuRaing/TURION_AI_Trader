import 'package:flutter/material.dart';

import '../api.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/live_clock.dart';
import 'chart_screen.dart';

// Added 14-Aug-2026 - a single-book (one strategy x one index) detail
// screen, opened by tapping a row in FyersOptionsGroupedScreen. Shows
// the same open-position/closed-trades content the per-strategy tabs
// already show (fyers_multi_strategy_options_screen.dart), but for
// exactly one book - reused instead of duplicated, since the grouped
// screen navigates by (name, index) not by "which tab am I already
// inside".

class FyersOptionsBookDetailScreen extends StatefulWidget {
  final String strategyName;
  final String indexLabel; // 'NIFTY' or 'BANKNIFTY'
  final String indexKey; // 'nifty' or 'banknifty'

  const FyersOptionsBookDetailScreen({
    super.key,
    required this.strategyName,
    required this.indexLabel,
    required this.indexKey,
  });

  @override
  State<FyersOptionsBookDetailScreen> createState() => _FyersOptionsBookDetailScreenState();
}

class _FyersOptionsBookDetailScreenState extends State<FyersOptionsBookDetailScreen> {
  Map<String, dynamic>? _portfolio;
  bool _loading = true;
  String? _error;
  DateTime? _lastFetched;

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
      final result = await fetchJson(fyersOptionsStrategyUrl(widget.strategyName, widget.indexKey));
      setState(() {
        _portfolio = result ?? {'Cash': 100000, 'Position': null, 'Closed Trades': []};
        _lastFetched = DateTime.now();
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
      appBar: AppBar(title: Text('${widget.strategyName} · ${widget.indexLabel}')),
      body: Column(
        children: [
          LiveClockHeader(lastUpdated: _lastFetched),
          Expanded(
            child: LoadingErrorWrapper(
              loading: _loading,
              error: _error,
              hasData: _portfolio != null,
              onRetry: _fetch,
              child: _portfolio == null
                  ? const SizedBox.shrink()
                  : RefreshIndicator(onRefresh: _fetch, child: _buildBody()),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBody() {
    final portfolio = _portfolio!;
    final cash = (portfolio['Cash'] as num).toDouble();
    final position = portfolio['Position'] as Map<String, dynamic>?;
    final closedTrades = List<Map<String, dynamic>>.from(
        (portfolio['Closed Trades'] ?? []).map((t) => Map<String, dynamic>.from(t)));

    final totalPnl = cash - 100000;
    final wins = closedTrades.where((t) => (t['Net PnL'] as num? ?? 0) > 0).length;
    final winRate = closedTrades.isEmpty ? null : (wins / closedTrades.length * 100);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        HeroStat(label: 'Total PnL', value: formatSignedRupees(totalPnl), color: pnlColor(totalPnl)),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(child: StatPill(label: 'Cash', value: formatRupees(cash))),
            const SizedBox(width: 10),
            Expanded(
              child: StatPill(label: 'Win rate', value: winRate == null ? '—' : '${winRate.toStringAsFixed(0)}%'),
            ),
          ],
        ),
        const SizedBox(height: 10),
        StatPill(label: 'Closed trades', value: '${closedTrades.length}'),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(color: surfaceColor, borderRadius: BorderRadius.circular(12)),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('${widget.indexLabel} Position',
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: accentColor)),
              const SizedBox(height: 8),
              if (position == null)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 8),
                  child: Text('No open position', style: TextStyle(color: mutedColor)),
                )
              else
                OptionPositionCard(
                  position: position,
                  underlyingLabel: widget.indexLabel,
                  onViewChart: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (_) => ChartScreen(
                                symbol: widget.indexLabel,
                                candleDataUrl: fyersCandlesUrl,
                                entryPrice: (position['Entry Spot'] as num?)?.toDouble(),
                                direction: position['Option Type'] == 'PE' ? 'SELL' : 'BUY',
                              ))),
                ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        Text('Closed Trades (${closedTrades.length})',
            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: mutedColor)),
        const SizedBox(height: 8),
        if (closedTrades.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 12),
            child: Text('No closed trades yet', style: TextStyle(color: mutedColor)),
          )
        else
          ...closedTrades.reversed.map((t) => OptionClosedTradeCard(
                trade: t,
                underlyingLabel: widget.indexLabel,
                onViewChart: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (_) => ChartScreen(
                              symbol: widget.indexLabel,
                              candleDataUrl: fyersCandlesUrl,
                              entryPrice: (t['Entry Spot'] as num?)?.toDouble(),
                              direction: t['Option Type'] == 'PE' ? 'SELL' : 'BUY',
                            ))),
              )),
      ],
    );
  }
}
