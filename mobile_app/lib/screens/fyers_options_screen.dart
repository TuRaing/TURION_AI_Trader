import 'package:flutter/material.dart';

import '../api.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/disclaimer_banner.dart';
import '../widgets/live_clock.dart';
import 'fyers_login_screen.dart';

// Added 04-Aug-2026 - shows the Fyers OPTIONS paper trading portfolio
// (strategy/fyers_options_paper_trading.py) - split out into its own
// bottom-nav tab (separate from the "Fyers" tab, which shows the
// equity Swing/Intraday Fyers engines instead) at the user's request.
//
// Every price shown here is a REAL Fyers quote (bid/ask/LTP) at the
// moment it was recorded - not the Black-Scholes ESTIMATE strategy/
// nifty_options_backtest.py used for its 03-Aug backtest research.
// TEST DATA ONLY - paper trades, not live trading.

class FyersOptionsScreen extends StatefulWidget {
  const FyersOptionsScreen({super.key});

  @override
  State<FyersOptionsScreen> createState() => _FyersOptionsScreenState();
}

class _FyersOptionsScreenState extends State<FyersOptionsScreen> {
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
      final result = await fetchJson(fyersOptionsPortfolioUrl);
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
            'Fyers Options (test) - real live premium quotes, paper trades only.',
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
    final position = portfolio['Position'] as Map<String, dynamic>?;
    final closedTrades = List<Map<String, dynamic>>.from(
        (portfolio['Closed Trades'] ?? []).map((t) => Map<String, dynamic>.from(t)));

    final totalPnl = closedTrades.fold<double>(0, (sum, t) => sum + (t['Net PnL'] as num).toDouble());
    final wins = closedTrades.where((t) => (t['Net PnL'] as num) > 0).length;
    final winRate = closedTrades.isEmpty ? null : (wins / closedTrades.length * 100);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        HeroStat(label: 'Options Total Net PnL', value: formatSignedRupees(totalPnl), color: pnlColor(totalPnl)),
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
        StatPill(label: 'Closed trades', value: '${closedTrades.length}'),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(color: surfaceColor, borderRadius: BorderRadius.circular(12)),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Today\'s Option Position',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: accentColor)),
              const SizedBox(height: 8),
              if (position == null)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 8),
                  child: Text('No open option position', style: TextStyle(color: mutedColor)),
                )
              else
                OptionPositionCard(position: position),
            ],
          ),
        ),
        const SizedBox(height: 16),
        if (closedTrades.isNotEmpty) ...[
          const Text('Closed Option Trades',
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: mutedColor)),
          const SizedBox(height: 8),
          ...closedTrades.reversed.map((t) => OptionClosedTradeCard(trade: t)),
        ],
      ],
    );
  }
}
