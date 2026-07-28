import 'package:flutter/material.dart';

import '../api.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/disclaimer_banner.dart';
import '../widgets/live_clock.dart';
import 'chart_screen.dart';

class PortfolioScreen extends StatefulWidget {
  const PortfolioScreen({super.key});

  @override
  State<PortfolioScreen> createState() => _PortfolioScreenState();
}

class _PortfolioScreenState extends State<PortfolioScreen> {
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
      // Swing (Watchlist) and Intraday (Best Trade) are two fully separate
      // paper portfolios (own capital, own file) - fetched together here
      // only so the app can show both, clearly labeled, in one place.
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
    final positions = Map<String, dynamic>.from(portfolio['Positions'] ?? {});
    final closedTrades = List<Map<String, dynamic>>.from(
        (portfolio['Closed Trades'] ?? []).map((t) => Map<String, dynamic>.from(t)));

    final totalPnl = closedTrades.fold<double>(0, (sum, t) => sum + (t['PnL'] as num).toDouble());
    final wins = closedTrades.where((t) => (t['PnL'] as num) > 0).length;
    final winRate = closedTrades.isEmpty ? null : (wins / closedTrades.length * 100);

    final latestTrade = closedTrades.isNotEmpty ? closedTrades.last : null;

    final intradayPosition = _bestTradePortfolio?['Position'] as Map<String, dynamic>?;
    final intradaySymbol = intradayPosition == null
        ? null
        : (intradayPosition['Name'] ?? intradayPosition['Symbol'] ?? 'NIFTY 50').toString();

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (latestTrade != null)
          EventBanner(
            text:
                '${latestTrade['Symbol'] ?? 'NIFTY 50'} closed ${(latestTrade['Exit Reason'] ?? '').toString().toLowerCase()} '
                '· ${formatSignedRupees((latestTrade['PnL'] as num).toDouble())} · '
                '${formatBackendTimestamp(latestTrade['Exit Time'] as String?)}',
            positive: (latestTrade['PnL'] as num) > 0,
          ),
        const SizedBox(height: 12),
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
        Row(
          children: [
            Expanded(child: StatPill(label: 'Open trade', value: '${positions.length}')),
            const SizedBox(width: 10),
            Expanded(child: StatPill(label: 'Close trade', value: '${closedTrades.length}')),
          ],
        ),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(color: surfaceColor, borderRadius: BorderRadius.circular(12)),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Text('Swing — Open Positions (${positions.length})',
                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: mutedColor)),
                ],
              ),
              const SizedBox(height: 8),
              if (positions.isEmpty)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 8),
                  child: Text('No open positions', style: TextStyle(color: mutedColor)),
                )
              else
                ...positions.entries.map((e) => OpenPositionCard(
                      symbol: e.key,
                      position: e.value,
                      currentPrice: (e.value['Last Price'] as num?)?.toDouble(),
                      typeLabel: 'Swing',
                      typeColor: mutedColor,
                      onTap: () => Navigator.push(
                          context, MaterialPageRoute(builder: (_) => ChartScreen(symbol: e.key))),
                    )),
            ],
          ),
        ),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(color: surfaceColor, borderRadius: BorderRadius.circular(12)),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Intraday — Today\'s Position',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: accentColor)),
              const SizedBox(height: 8),
              if (intradayPosition == null)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 8),
                  child: Text('No open intraday position today', style: TextStyle(color: mutedColor)),
                )
              else
                OpenPositionCard(
                  symbol: intradaySymbol!,
                  position: intradayPosition,
                  typeLabel: 'Intraday',
                  typeColor: accentColor,
                  onTap: () => Navigator.push(
                      context, MaterialPageRoute(builder: (_) => ChartScreen(symbol: intradaySymbol))),
                ),
            ],
          ),
        ),
      ],
    );
  }
}
