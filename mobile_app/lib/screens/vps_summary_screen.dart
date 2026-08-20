import 'dart:async';

import 'package:flutter/material.dart';

import '../event_driven_realtime_service.dart';
import '../theme.dart';
import '../widgets/common.dart';

// Added 20-Aug-2026 - a SEPARATE tab from VPS (vps_screen.dart), at the
// user's own explicit request: the SAME combined Summary/Passbook
// layout screens/fyers_options_summary_screen.dart already uses for
// the 60+ GitHub-Actions-polled books (one combined table across every
// book + a per-book date-wise ledger), just fed by the VPS's 4 event-
// driven books' LIVE Firebase streams instead of a one-time GitHub-
// raw-file fetch. vps_screen.dart (per-book tabs, matches the Options
// tab layout) is untouched - this is an addition, not a replacement.

const _initialAmountPerBook = 100000.0;

const _books = [
  (key: 'st2_threshold_eventdriven', label: 'ST2 Threshold', underlying: 'NIFTY'),
  (key: 'simple_st1_threshold_eventdriven', label: 'Simple ST1 Threshold', underlying: 'NIFTY'),
  (key: 'oi_footprint_eventdriven_nifty', label: 'OI Footprint', underlying: 'NIFTY'),
  (key: 'oi_footprint_eventdriven_banknifty', label: 'OI Footprint', underlying: 'BANKNIFTY'),
];

class VpsSummaryScreen extends StatefulWidget {
  const VpsSummaryScreen({super.key});

  @override
  State<VpsSummaryScreen> createState() => _VpsSummaryScreenState();
}

class _VpsSummaryScreenState extends State<VpsSummaryScreen> with SingleTickerProviderStateMixin {
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

  /// Same row shape fyers_options_summary_screen.dart builds - current
  /// amount (Cash), realized profit, and a date-wise passbook ledger -
  /// just read from the live-streamed portfolio instead of a fetched one.
  Map<String, dynamic> _rowFor(({String key, String label, String underlying}) book) {
    final portfolio = _portfolios[book.key];
    final currentAmount = portfolio == null ? _initialAmountPerBook : (portfolio['Cash'] as num).toDouble();
    final closedTrades = (portfolio?['Closed Trades'] as List?) ?? [];

    final dailyPnlByDate = <String, double>{};
    for (final t in closedTrades) {
      final trade = t as Map<String, dynamic>;
      final exitTime = trade['Exit Time'] as String?;
      if (exitTime == null || exitTime.length < 10) continue;

      final date = exitTime.substring(0, 10);
      final netPnl = (trade['Net PnL'] as num).toDouble();
      dailyPnlByDate[date] = (dailyPnlByDate[date] ?? 0) + netPnl;
    }

    final sortedDates = dailyPnlByDate.keys.toList()..sort();
    var runningBalance = _initialAmountPerBook;
    final passbook = <Map<String, dynamic>>[];
    for (final date in sortedDates) {
      runningBalance += dailyPnlByDate[date]!;
      passbook.add({'date': date, 'pnl': dailyPnlByDate[date]!, 'balance': runningBalance});
    }

    final profit = closedTrades.fold<double>(0, (sum, t) => sum + ((t as Map)['Net PnL'] as num).toDouble());

    return {'book': book, 'current': currentAmount, 'profit': profit, 'passbook': passbook};
  }

  @override
  Widget build(BuildContext context) {
    final rows = _books.map(_rowFor).toList();

    return Column(
      children: [
        TabBar(
          controller: _tabController,
          labelColor: accent2Color,
          unselectedLabelColor: mutedColor,
          tabs: const [Tab(text: 'Summary'), Tab(text: 'Passbook')],
        ),
        Expanded(
          child: TabBarView(
            controller: _tabController,
            children: [_buildSummaryTab(rows), _buildPassbookTab(rows)],
          ),
        ),
      ],
    );
  }

  Widget _buildSummaryTab(List<Map<String, dynamic>> rows) {
    final totalInitial = _initialAmountPerBook * rows.length;
    final totalCurrent = rows.fold<double>(0, (sum, r) => sum + (r['current'] as double));
    final totalProfit = rows.fold<double>(0, (sum, r) => sum + (r['profit'] as double));

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            Expanded(child: StatPill(label: 'Total Investment', value: formatRupees(totalInitial))),
            const SizedBox(width: 10),
            Expanded(child: StatPill(label: 'Total Current Amount', value: formatRupees(totalCurrent))),
          ],
        ),
        const SizedBox(height: 10),
        HeroStat(
          label: 'Total Profit / Loss (${rows.length} books)',
          value: formatSignedRupees(totalProfit),
          color: pnlColor(totalProfit),
        ),
        const SizedBox(height: 16),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: DataTable(
            headingRowColor: WidgetStateProperty.all(surfaceColor),
            columns: const [
              DataColumn(label: Text('Strategy')),
              DataColumn(label: Text('Index')),
              DataColumn(label: Text('Initial'), numeric: true),
              DataColumn(label: Text('Current'), numeric: true),
              DataColumn(label: Text('Profit'), numeric: true),
            ],
            rows: rows.map((r) {
              final book = r['book'] as ({String key, String label, String underlying});
              final current = r['current'] as double;
              final profit = r['profit'] as double;

              return DataRow(cells: [
                DataCell(Text(book.label, style: const TextStyle(fontSize: 12))),
                DataCell(Text(book.underlying, style: const TextStyle(fontSize: 12))),
                DataCell(Text(formatRupees(_initialAmountPerBook), style: const TextStyle(fontSize: 12))),
                DataCell(Text(formatRupees(current), style: const TextStyle(fontSize: 12))),
                DataCell(Text(
                  formatSignedRupees(profit),
                  style: TextStyle(fontSize: 12, color: pnlColor(profit), fontWeight: FontWeight.w600),
                )),
              ]);
            }).toList(),
          ),
        ),
      ],
    );
  }

  Widget _buildPassbookTab(List<Map<String, dynamic>> rows) {
    final selectedRow = rows[_selectedBookIndex];
    final selectedBook = selectedRow['book'] as ({String key, String label, String underlying});
    final passbook = selectedRow['passbook'] as List<Map<String, dynamic>>;

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
              items: List.generate(rows.length, (i) {
                final b = (rows[i]['book'] as ({String key, String label, String underlying}));
                return DropdownMenuItem(value: i, child: Text('${b.label} · ${b.underlying}', style: const TextStyle(fontSize: 13)));
              }),
              onChanged: (i) {
                if (i != null) setState(() => _selectedBookIndex = i);
              },
            ),
          ),
        ),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(color: accentColor.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(8)),
          child: Text(
            '${selectedBook.label} · ${selectedBook.underlying} - opening balance ${formatRupees(_initialAmountPerBook)}, one row per day this book closed a trade.',
            style: const TextStyle(fontSize: 12, color: accentColor),
          ),
        ),
        const SizedBox(height: 16),
        if (passbook.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 24),
            child: Center(child: Text('No closed trades yet for this book.', style: TextStyle(color: mutedColor))),
          )
        else
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: DataTable(
              headingRowColor: WidgetStateProperty.all(surfaceColor),
              columns: const [
                DataColumn(label: Text('Date')),
                DataColumn(label: Text('Day\'s P&L'), numeric: true),
                DataColumn(label: Text('Balance'), numeric: true),
              ],
              rows: passbook.map((r) {
                final pnl = r['pnl'] as double;
                final balance = r['balance'] as double;

                return DataRow(cells: [
                  DataCell(Text(r['date'] as String, style: const TextStyle(fontSize: 12))),
                  DataCell(Text(
                    formatSignedRupees(pnl),
                    style: TextStyle(fontSize: 12, color: pnlColor(pnl), fontWeight: FontWeight.w600),
                  )),
                  DataCell(Text(formatRupees(balance), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500))),
                ]);
              }).toList(),
            ),
          ),
      ],
    );
  }
}
