import 'package:flutter/material.dart';

import '../api.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/disclaimer_banner.dart';
import '../widgets/live_clock.dart';
import 'chart_screen.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  Map<String, dynamic>? _portfolio;
  Map<String, dynamic>? _bestTradePortfolio;
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
      final results = await Future.wait([fetchJson(portfolioUrl), fetchJson(bestTradePortfolioUrl)]);
      setState(() {
        _portfolio = results[0] ?? {'Cash': 100000, 'Positions': {}, 'Closed Trades': []};
        _bestTradePortfolio = results[1];
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
    return Column(
      children: [
        LiveClockHeader(lastUpdated: _lastFetched),
        const DisclaimerBanner(),
        Expanded(
          child: LoadingErrorWrapper(
            loading: _loading,
            error: _error,
            hasData: _portfolio != null,
            onRetry: _fetch,
            child: RefreshIndicator(onRefresh: _fetch, child: _buildBody()),
          ),
        ),
      ],
    );
  }

  Widget _buildBody() {
    final portfolio = _portfolio!;
    final cash = (portfolio['Cash'] as num).toDouble();
    final closedTrades = List<Map<String, dynamic>>.from(
        (portfolio['Closed Trades'] ?? []).map((t) => Map<String, dynamic>.from(t)));

    final totalPnl = closedTrades.fold<double>(0, (sum, t) => sum + (t['PnL'] as num).toDouble());
    final wins = closedTrades.where((t) => (t['PnL'] as num) > 0).length;
    final winRate = closedTrades.isEmpty ? null : (wins / closedTrades.length * 100);

    final intradayClosedTrades = List<Map<String, dynamic>>.from(
        (_bestTradePortfolio?['Closed Trades'] ?? []).map((t) => Map<String, dynamic>.from(t)));
    final intradayTotalPnl = intradayClosedTrades.fold<double>(0, (sum, t) => sum + (t['PnL'] as num).toDouble());
    final intradayWins = intradayClosedTrades.where((t) => (t['PnL'] as num) > 0).length;
    final intradayWinRate =
        intradayClosedTrades.isEmpty ? null : (intradayWins / intradayClosedTrades.length * 100);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        HeroStat(label: 'Swing Total PnL', value: formatSignedRupees(totalPnl), color: pnlColor(totalPnl)),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(child: StatPill(label: 'Cash', value: formatRupees(cash))),
            const SizedBox(width: 10),
            Expanded(
              child: StatPill(
                label: 'Win rate',
                value: winRate == null ? '—' : '${winRate.toStringAsFixed(0)}%',
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        StatPill(label: 'Swing closed trades', value: '${closedTrades.length}'),
        const SizedBox(height: 16),
        Text('Swing (Closed)', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: mutedColor)),
        const SizedBox(height: 8),
        if (closedTrades.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 12),
            child: Text('No closed trades yet', style: TextStyle(color: mutedColor)),
          )
        else
          ...closedTrades.reversed.map((t) => ClosedTradeCard(
                trade: t,
                typeLabel: 'Swing',
                typeColor: mutedColor,
                onViewChart: () => Navigator.push(context,
                    MaterialPageRoute(builder: (_) => ChartScreen(symbol: (t['Symbol'] ?? t['Name']).toString()))),
              )),
        const SizedBox(height: 24),
        HeroStat(
            label: 'Intraday Total PnL', value: formatSignedRupees(intradayTotalPnl), color: pnlColor(intradayTotalPnl)),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: StatPill(
                label: 'Win rate',
                value: intradayWinRate == null ? '—' : '${intradayWinRate.toStringAsFixed(0)}%',
              ),
            ),
            const SizedBox(width: 10),
            Expanded(child: StatPill(label: 'Closed trades', value: '${intradayClosedTrades.length}')),
          ],
        ),
        const SizedBox(height: 16),
        const Text('Intraday (Closed)', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: accentColor)),
        const SizedBox(height: 8),
        if (intradayClosedTrades.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 12),
            child: Text('No closed intraday trades yet', style: TextStyle(color: mutedColor)),
          )
        else
          ...intradayClosedTrades.reversed.map((t) => ClosedTradeCard(
                trade: t,
                typeLabel: 'Intraday',
                typeColor: accentColor,
                onViewChart: () => Navigator.push(context,
                    MaterialPageRoute(builder: (_) => ChartScreen(symbol: (t['Name'] ?? t['Symbol']).toString()))),
              )),
      ],
    );
  }
}
