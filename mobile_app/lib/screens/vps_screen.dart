import 'dart:async';

import 'package:flutter/material.dart';

import '../event_driven_realtime_service.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/disclaimer_banner.dart';
import 'live_chart_screen.dart';

// Added 20-Aug-2026 - the VPS's own event-driven paper-trading books
// (strategy/event_driven_runner.py's STRATEGY_NAMES), separated into
// their own tab per the user's own explicit ask - these are a
// different engine (WebSocket, tick-driven) from the ~60 GitHub-
// Actions-polled books on the other tabs.
//
// REDESIGNED same day, second pass - user's own explicit ask after
// seeing the first version: match fyers_options_summary_screen.dart's
// established Summary/Passbook two-tab pattern (Cash/Win rate/Closed
// trades visible directly in the Summary, not hidden behind a tap into
// a detail screen) rather than a bespoke layout. Cash/Win-rate/Closed-
// trades now sit directly on each book's Summary row, matching every
// other strategy screen in this app.
//
// Subscribes to all 4 books' live Firebase streams ONCE here (not per-
// row StreamBuilders) so the Summary tab's aggregate totals (Total
// Cash, overall win rate) and the Passbook tab's dropdown-selected book
// both read from the exact same live state, no risk of the two tabs
// showing numbers computed from different snapshots in time.

const _books = [
  (key: 'st2_threshold_eventdriven', label: 'ST2 Threshold', underlying: 'NIFTY'),
  (key: 'simple_st1_threshold_eventdriven', label: 'Simple ST1 Threshold', underlying: 'NIFTY'),
  (key: 'oi_footprint_eventdriven_nifty', label: 'OI Footprint', underlying: 'NIFTY'),
  (key: 'oi_footprint_eventdriven_banknifty', label: 'OI Footprint', underlying: 'BANKNIFTY'),
];

const _initialCapitalPerBook = 100000.0;

class VpsScreen extends StatefulWidget {
  const VpsScreen({super.key});

  @override
  State<VpsScreen> createState() => _VpsScreenState();
}

class _VpsScreenState extends State<VpsScreen> with SingleTickerProviderStateMixin {
  late final TabController _tabController;
  final Map<String, Map<String, dynamic>?> _portfolios = {};
  final List<StreamSubscription<Map<String, dynamic>?>> _subs = [];
  int _selectedBookIndex = 0;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);

    for (final book in _books) {
      _subs.add(watchEventDrivenPortfolio(book.key).listen((portfolio) {
        if (mounted) setState(() => _portfolios[book.key] = portfolio);
      }));
    }
  }

  @override
  void dispose() {
    for (final sub in _subs) {
      sub.cancel();
    }
    _tabController.dispose();
    super.dispose();
  }

  /// {cash, closedTrades, position, totalPnl, wins, winRate} for one
  /// book - null portfolio (nothing synced yet) still returns a full
  /// row so the Summary table shows every book, not just ones with data.
  Map<String, dynamic> _statsFor(String key) {
    final portfolio = _portfolios[key];
    final closedTrades = List<Map<String, dynamic>>.from(
        (portfolio?['Closed Trades'] ?? []).map((t) => Map<String, dynamic>.from(t)));
    final cash = (portfolio?['Cash'] as num?)?.toDouble() ?? _initialCapitalPerBook;
    final totalPnl = closedTrades.fold<double>(0, (sum, t) => sum + (t['Net PnL'] as num).toDouble());
    final wins = closedTrades.where((t) => (t['Net PnL'] as num) > 0).length;

    return {
      'cash': cash,
      'closedTrades': closedTrades,
      'position': portfolio?['Position'] as Map<String, dynamic>?,
      'totalPnl': totalPnl,
      'wins': wins,
      'winRate': closedTrades.isEmpty ? null : wins / closedTrades.length * 100,
      'hasData': portfolio != null,
    };
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const DisclaimerBanner(),
        Container(
          width: double.infinity,
          margin: const EdgeInsets.fromLTRB(16, 8, 16, 8),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(color: accent2Color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(8)),
          child: const Text(
            'VPS - event-driven (WebSocket, tick-by-tick) engine. Real live premium quotes, paper trades only.',
            style: TextStyle(fontSize: 12, color: accent2Color),
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            children: [
              Expanded(child: _LiveChartButton(index: 'NIFTY')),
              const SizedBox(width: 10),
              Expanded(child: _LiveChartButton(index: 'BANKNIFTY')),
            ],
          ),
        ),
        const SizedBox(height: 4),
        TabBar(
          controller: _tabController,
          labelColor: accent2Color,
          unselectedLabelColor: mutedColor,
          tabs: const [Tab(text: 'Summary'), Tab(text: 'Passbook')],
        ),
        Expanded(
          child: TabBarView(
            controller: _tabController,
            children: [_buildSummaryTab(), _buildPassbookTab()],
          ),
        ),
      ],
    );
  }

  Widget _buildSummaryTab() {
    final rows = _books.map((b) => (book: b, stats: _statsFor(b.key))).toList();

    final totalCash = rows.fold<double>(0, (sum, r) => sum + (r.stats['cash'] as double));
    final totalPnl = rows.fold<double>(0, (sum, r) => sum + (r.stats['totalPnl'] as double));
    final totalClosed = rows.fold<int>(0, (sum, r) => sum + (r.stats['closedTrades'] as List).length);
    final totalWins = rows.fold<int>(0, (sum, r) => sum + (r.stats['wins'] as int));
    final overallWinRate = totalClosed == 0 ? null : totalWins / totalClosed * 100;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        HeroStat(label: 'VPS Total PnL (${rows.length} books)', value: formatSignedRupees(totalPnl), color: pnlColor(totalPnl)),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(child: StatPill(label: 'Total Cash', value: formatRupees(totalCash))),
            const SizedBox(width: 10),
            Expanded(
                child: StatPill(
                    label: 'Win rate', value: overallWinRate == null ? '—' : '${overallWinRate.toStringAsFixed(0)}%')),
          ],
        ),
        const SizedBox(height: 10),
        StatPill(label: 'Closed trades', value: '$totalClosed'),
        const SizedBox(height: 16),
        ...rows.map((r) => _BookSummaryCard(book: r.book, stats: r.stats)),
      ],
    );
  }

  Widget _buildPassbookTab() {
    final selectedBook = _books[_selectedBookIndex];
    final stats = _statsFor(selectedBook.key);
    final closedTrades = stats['closedTrades'] as List<Map<String, dynamic>>;
    final position = stats['position'] as Map<String, dynamic>?;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: surfaceColor,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<int>(
              isExpanded: true,
              value: _selectedBookIndex,
              dropdownColor: surfaceColor,
              style: const TextStyle(fontSize: 13, color: Colors.white),
              items: List.generate(_books.length, (i) {
                final b = _books[i];
                return DropdownMenuItem(value: i, child: Text('${b.label} · ${b.underlying}', style: const TextStyle(fontSize: 13)));
              }),
              onChanged: (i) {
                if (i != null) setState(() => _selectedBookIndex = i);
              },
            ),
          ),
        ),
        const SizedBox(height: 16),
        HeroStat(
            label: 'Total Net PnL', value: formatSignedRupees(stats['totalPnl'] as double), color: pnlColor(stats['totalPnl'] as double)),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(child: StatPill(label: 'Cash', value: formatRupees(stats['cash'] as double))),
            const SizedBox(width: 10),
            Expanded(
                child: StatPill(
                    label: 'Win rate',
                    value: stats['winRate'] == null ? '—' : '${(stats['winRate'] as double).toStringAsFixed(0)}%')),
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
              const Text('Open Position', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: accentColor)),
              const SizedBox(height: 8),
              if (position == null)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 8),
                  child: Text('No open position', style: TextStyle(color: mutedColor)),
                )
              else
                OptionPositionCard(position: position, underlyingLabel: selectedBook.underlying),
            ],
          ),
        ),
        const SizedBox(height: 16),
        if (closedTrades.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 24),
            child: Center(child: Text('No closed trades yet for this book.', style: TextStyle(color: mutedColor))),
          )
        else ...[
          const Text('Closed Trades (Passbook)', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: mutedColor)),
          const SizedBox(height: 8),
          ...closedTrades.reversed.map((t) => OptionClosedTradeCard(trade: t, underlyingLabel: selectedBook.underlying)),
        ],
      ],
    );
  }
}

class _LiveChartButton extends StatelessWidget {
  final String index;

  const _LiveChartButton({required this.index});

  @override
  Widget build(BuildContext context) {
    return OutlinedButton.icon(
      onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => LiveChartScreen(index: index))),
      icon: const Icon(Icons.candlestick_chart, size: 18),
      label: Text(index, style: const TextStyle(fontSize: 13)),
      style: OutlinedButton.styleFrom(
        foregroundColor: accent2Color,
        side: BorderSide(color: accent2Color.withValues(alpha: 0.4)),
        padding: const EdgeInsets.symmetric(vertical: 12),
      ),
    );
  }
}

class _BookSummaryCard extends StatelessWidget {
  final ({String key, String label, String underlying}) book;
  final Map<String, dynamic> stats;

  const _BookSummaryCard({required this.book, required this.stats});

  @override
  Widget build(BuildContext context) {
    final cash = stats['cash'] as double;
    final totalPnl = stats['totalPnl'] as double;
    final winRate = stats['winRate'] as double?;
    final closedCount = (stats['closedTrades'] as List).length;
    final hasData = stats['hasData'] as bool;

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: surfaceColor, borderRadius: BorderRadius.circular(12)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text('${book.label} · ${book.underlying}', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
              ),
              Text(hasData ? formatSignedRupees(totalPnl) : '—',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: hasData ? pnlColor(totalPnl) : mutedColor)),
            ],
          ),
          if (!hasData) ...[
            const SizedBox(height: 4),
            const Text('No data synced from the VPS yet', style: TextStyle(fontSize: 11, color: mutedColor)),
          ],
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(child: StatPill(label: 'Cash', value: formatRupees(cash))),
              const SizedBox(width: 8),
              Expanded(child: StatPill(label: 'Win rate', value: winRate == null ? '—' : '${winRate.toStringAsFixed(0)}%')),
              const SizedBox(width: 8),
              Expanded(child: StatPill(label: 'Closed', value: '$closedCount')),
            ],
          ),
        ],
      ),
    );
  }
}
