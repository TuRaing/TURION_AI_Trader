import 'package:flutter/material.dart';

import '../api.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/disclaimer_banner.dart';
import '../widgets/live_clock.dart';
import 'chart_screen.dart';
import 'fyers_login_screen.dart';

// Added 04-Aug-2026 - Fyers-sourced counterpart to portfolio_screen.dart,
// showing reports/fyers_test_portfolio.json / fyers_best_trade_
// portfolio.json instead of the live yfinance ones. Same layout/logic,
// deliberately kept as a near-duplicate rather than a shared parametrized
// widget, per this repo's "don't touch a working module" preference -
// portfolio_screen.dart (the live screen) stays completely untouched.
// TEST DATA ONLY - these are Fyers paper-trading engines still being
// proven out in parallel with the live yfinance ones, not live trading.
//
// RESTORED to this equity view same day after a brief detour where this
// screen showed Options data instead - the user asked for that to be
// its own separate tab (see fyers_options_screen.dart) rather than
// replacing this one.

class FyersPortfolioScreen extends StatefulWidget {
  const FyersPortfolioScreen({super.key});

  @override
  State<FyersPortfolioScreen> createState() => _FyersPortfolioScreenState();
}

class _FyersPortfolioScreenState extends State<FyersPortfolioScreen> {
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
      final results = await Future.wait([fetchJson(fyersPortfolioUrl), fetchJson(fyersBestTradePortfolioUrl)]);
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
        Container(
          width: double.infinity,
          margin: const EdgeInsets.fromLTRB(16, 0, 16, 8),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(color: accentColor.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(8)),
          child: const Text(
            'Fyers (test) - real broker data, paper trades only, still being proven in parallel with yfinance.',
            style: TextStyle(fontSize: 12, color: accentColor),
          ),
        ),
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 16),
          child: Align(alignment: Alignment.centerLeft, child: FyersLoginButton()),
        ),
        const SizedBox(height: 8),
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

    final intradayClosedTrades = List<Map<String, dynamic>>.from(
        (_bestTradePortfolio?['Closed Trades'] ?? []).map((t) => Map<String, dynamic>.from(t)));
    final latestIntradayTrade = intradayClosedTrades.isNotEmpty ? intradayClosedTrades.last : null;

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
        HeroStat(label: 'Swing Total PnL (Fyers)', value: formatSignedRupees(totalPnl), color: pnlColor(totalPnl)),
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
              Text('Swing — Open Positions (${positions.length})',
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: mutedColor)),
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
                          context,
                          MaterialPageRoute(
                              builder: (_) => ChartScreen(
                                    symbol: e.key,
                                    entryPrice: (e.value['Entry Price'] as num).toDouble(),
                                    stopLoss: (e.value['Stop Loss'] as num?)?.toDouble(),
                                    target: (e.value['Target'] as num?)?.toDouble(),
                                    direction: e.value['Direction'] as String? ?? 'BUY',
                                  ))),
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
              if (intradayPosition == null && latestIntradayTrade == null)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 8),
                  child: Text('No open intraday position today', style: TextStyle(color: mutedColor)),
                )
              else if (intradayPosition == null)
                ClosedTradeCard(
                  trade: latestIntradayTrade!,
                  typeLabel: 'Intraday',
                  typeColor: accentColor,
                )
              else
                OpenPositionCard(
                  symbol: intradaySymbol!,
                  position: intradayPosition,
                  typeLabel: 'Intraday',
                  typeColor: accentColor,
                  onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (_) => ChartScreen(
                                symbol: intradaySymbol,
                                entryPrice: (intradayPosition['Entry Price'] as num).toDouble(),
                                stopLoss: (intradayPosition['Stop Loss'] as num?)?.toDouble(),
                                target: (intradayPosition['Target'] as num?)?.toDouble(),
                                direction: intradayPosition['Direction'] as String? ?? 'BUY',
                              ))),
                ),
            ],
          ),
        ),
      ],
    );
  }
}
