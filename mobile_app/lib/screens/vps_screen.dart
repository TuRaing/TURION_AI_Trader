import 'package:flutter/material.dart';

import '../event_driven_realtime_service.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/disclaimer_banner.dart';
import 'fyers_login_screen.dart';
import 'live_chart_screen.dart';

// Added 20-Aug-2026 - the VPS's own event-driven paper-trading books
// (strategy/event_driven_runner.py's STRATEGY_NAMES), separated into
// their own tab per the user's own explicit ask.
//
// REDESIGNED same day, THIRD pass - user's own explicit correction:
// NOT the Summary/Passbook two-tab pattern (fyers_options_summary_
// screen.dart) - that was the wrong reference. The right one is
// fyers_multi_strategy_options_screen.dart's layout: one top-level tab
// PER STRATEGY, each tab showing everything directly (login button,
// PnL, Cash/Win rate, Closed count, Position, Closed Trades) in one
// scroll - no separate aggregate table, no dropdown-based passbook.
// Matches EXACTLY what every other strategy tab in this app already
// looks like, per the user's own screenshots of the Threshold Options
// tab.

const _books = [
  (key: 'st2_threshold_eventdriven', label: 'ST2 Threshold', underlying: 'NIFTY'),
  (key: 'simple_st1_threshold_eventdriven', label: 'Simple ST1 Threshold', underlying: 'NIFTY'),
  (key: 'oi_footprint_eventdriven_nifty', label: 'OI Footprint', underlying: 'NIFTY'),
  (key: 'oi_footprint_eventdriven_banknifty', label: 'OI Footprint', underlying: 'BANKNIFTY'),
  // Added 21-Aug-2026 - the two new daily-profit-lock variant books
  // (strategy/event_driven_runner.py's STRATEGY_NAMES, same day) -
  // separate books running alongside the plain ones above, not a
  // replacement of them.
  (key: 'st2_threshold_lock_eventdriven', label: 'ST2 Threshold (2% Lock)', underlying: 'NIFTY'),
  (key: 'simple_st1_threshold_lock_eventdriven', label: 'Simple ST1 Threshold (2% Lock)', underlying: 'NIFTY'),
];

class VpsScreen extends StatefulWidget {
  const VpsScreen({super.key});

  @override
  State<VpsScreen> createState() => _VpsScreenState();
}

class _VpsScreenState extends State<VpsScreen> with SingleTickerProviderStateMixin {
  late final TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _books.length, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const DisclaimerBanner(),
        Container(
          width: double.infinity,
          margin: const EdgeInsets.fromLTRB(16, 8, 16, 0),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(color: accent2Color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(8)),
          child: const Text(
            'VPS - event-driven (WebSocket, tick-by-tick) engine, each with its own ₹1,00,000 - real live premium quotes, paper trades only.',
            style: TextStyle(fontSize: 12, color: accent2Color),
          ),
        ),
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Align(alignment: Alignment.centerLeft, child: FyersLoginButton()),
        ),
        TabBar(
          controller: _tabController,
          isScrollable: true,
          labelColor: accent2Color,
          unselectedLabelColor: mutedColor,
          tabs: _books.map((b) => Tab(text: '${b.label} · ${b.underlying}')).toList(),
        ),
        Expanded(
          child: TabBarView(
            controller: _tabController,
            children: _books.map((b) => _BookPortfolio(book: b)).toList(),
          ),
        ),
      ],
    );
  }
}

class _BookPortfolio extends StatelessWidget {
  final ({String key, String label, String underlying}) book;

  const _BookPortfolio({required this.book});

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<Map<String, dynamic>?>(
      stream: watchEventDrivenPortfolio(book.key),
      builder: (context, snapshot) {
        // Same fallback every other strategy screen in this app already
        // uses (fetchJson(...) ?? {...}) - show the FULL structure with
        // starting-capital defaults rather than hiding it behind a
        // "no data yet" message. The VPS hasn't traded yet today (or
        // ever, until B18's first real live run), which is a real,
        // expected, temporary state - not a reason to hide the layout.
        final portfolio = snapshot.data ?? {'Cash': 100000, 'Position': null, 'Closed Trades': []};

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
            HeroStat(label: '${book.underlying} Total Net PnL', value: formatSignedRupees(totalPnl), color: pnlColor(totalPnl)),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(child: StatPill(label: 'Cash', value: formatRupees(cash))),
                const SizedBox(width: 10),
                Expanded(
                    child: StatPill(
                        label: 'Win rate', value: winRate == null ? '—' : '${winRate.toStringAsFixed(0)}%')),
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
                  Text('${book.underlying} Position',
                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: accentColor)),
                  const SizedBox(height: 8),
                  if (position == null)
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 8),
                      child: Text('No open option position', style: TextStyle(color: mutedColor)),
                    )
                  else
                    OptionPositionCard(
                      position: position,
                      underlyingLabel: book.underlying,
                      // Genuine tick-by-tick live chart (not the ~15-
                      // min-refresh static one every other tab's
                      // onViewChart opens) - the VPS's own underlying is
                      // exactly what run_tick_collector.py streams live.
                      onViewChart: () => Navigator.push(
                          context, MaterialPageRoute(builder: (_) => LiveChartScreen(index: book.underlying))),
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
                    underlyingLabel: book.underlying,
                    onViewChart: () => Navigator.push(
                        context, MaterialPageRoute(builder: (_) => LiveChartScreen(index: book.underlying))),
                  )),
          ],
        );
      },
    );
  }
}
