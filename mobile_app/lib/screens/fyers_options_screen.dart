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
                _OptionPositionCard(position: position),
            ],
          ),
        ),
        const SizedBox(height: 16),
        if (closedTrades.isNotEmpty) ...[
          const Text('Closed Option Trades',
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: mutedColor)),
          const SizedBox(height: 8),
          ...closedTrades.reversed.map((t) => _OptionClosedTradeCard(trade: t)),
        ],
      ],
    );
  }
}

class _OptionPositionCard extends StatelessWidget {
  final Map<String, dynamic> position;

  const _OptionPositionCard({required this.position});

  @override
  Widget build(BuildContext context) {
    final optionType = position['Option Type'] as String? ?? '';
    final strike = position['Strike'];
    final entryPremium = (position['Entry Premium'] as num).toDouble();
    final lastPremium = (position['Last Premium'] as num?)?.toDouble() ?? entryPremium;
    final lots = position['Lots'];
    final movePct = entryPremium == 0 ? 0.0 : (lastPremium - entryPremium) / entryPremium * 100;

    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(color: bgColor, border: Border.all(color: Colors.white12, width: 0.5), borderRadius: BorderRadius.circular(8)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text('NIFTY $strike $optionType', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
              const Spacer(),
              Text('${lots}x lot', style: const TextStyle(fontSize: 12, color: mutedColor)),
            ],
          ),
          const SizedBox(height: 6),
          Text('Entry ${formatRupees(entryPremium)} → Last ${formatRupees(lastPremium)} (${movePct >= 0 ? '+' : ''}${movePct.toStringAsFixed(1)}%)',
              style: TextStyle(fontSize: 12, color: movePct >= 0 ? successColor : dangerColor)),
          const SizedBox(height: 4),
          Text(
              'Entered ${formatBackendTimestamp(position['Entry Time'] as String?)} · '
              'Checked ${formatBackendTimestamp(position['Last Checked'] as String?)}',
              style: const TextStyle(fontSize: 11, color: mutedColor)),
        ],
      ),
    );
  }
}

class _OptionClosedTradeCard extends StatelessWidget {
  final Map<String, dynamic> trade;

  const _OptionClosedTradeCard({required this.trade});

  @override
  Widget build(BuildContext context) {
    final pnl = (trade['Net PnL'] as num).toDouble();
    final win = pnl > 0;
    final optionType = trade['Option Type'] as String? ?? '';
    final strike = trade['Strike'];
    final entryPremium = (trade['Entry Premium'] as num).toDouble();
    final exitPremium = (trade['Exit Premium'] as num).toDouble();
    final exitReason = trade['Exit Reason'] ?? '';
    final exitTime = formatBackendTimestamp(trade['Exit Time'] as String?);

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(color: bgColor, border: Border.all(color: Colors.white12, width: 0.5), borderRadius: BorderRadius.circular(8)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(
                radius: 13,
                backgroundColor: (win ? successColor : dangerColor).withValues(alpha: 0.18),
                child: Icon(win ? Icons.check : Icons.close, size: 14, color: win ? successColor : dangerColor),
              ),
              const SizedBox(width: 8),
              Text('NIFTY $strike $optionType', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
              const Spacer(),
              Text(formatSignedRupees(pnl),
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: win ? successColor : dangerColor)),
            ],
          ),
          const SizedBox(height: 4),
          Padding(
            padding: const EdgeInsets.only(left: 34),
            child: Text(
              '$exitReason · ${formatRupees(entryPremium)} to ${formatRupees(exitPremium)}${exitTime.isNotEmpty ? ' · $exitTime' : ''}',
              style: const TextStyle(fontSize: 11, color: mutedColor),
            ),
          ),
        ],
      ),
    );
  }
}
