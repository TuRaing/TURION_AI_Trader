import 'package:flutter/material.dart';

import '../api.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/live_clock.dart';

// Added 08-Aug-2026 - user's direct request: one combined table across
// every options paper-trading book (originally 20: 5 strategies x 2
// indices x {original, threshold}; grew to 23 same day with vix_filter
// (BANKNIFTY-only) and oi_footprint (both indices)), showing each
// book's Initial Amount, Current Amount, Profit, plus totals across
// all of them.
// Every book starts with the same Rs 1,00,000 (cfg["initial_capital"]
// default in strategy/fyers_options_engine.py/fyers_options_st4.py/
// fyers_options_gapfill.py) - Initial Amount is hardcoded here to
// match that, not fetched, since the portfolio JSON files don't store
// it separately (only "Cash", which already reflects all REALIZED
// P&L). "Current Amount" here means Cash (realized-basis), same
// convention the rest of the app already uses for the "Cash" stat -
// it does not add an open position's unrealized mark-to-market value.
//
// Added 15-Aug-2026 - second tab, user's direct request: a bank-
// passbook-style date-wise ledger (Date / that day's P&L / running
// Balance) PER BOOK (not a combined total - the user was explicit:
// "मला total चं passbook नको आहे, मला प्रत्येक strategy चं passbook
// पाहिजे") - a dropdown picks one of the 59 books, then shows that
// book's own Closed Trades grouped by Exit Time's date, running
// balance starting from its own Rs 1,00,000. Built from the SAME
// already-fetched data the Summary tab pulls - no new backend
// endpoint, no second fetch on dropdown change.

const _initialAmountPerBook = 100000.0;

const _books = [
  ('simple_st1', 'NIFTY', 'nifty'),
  ('simple_st1', 'BANKNIFTY', 'banknifty'),
  ('st2', 'NIFTY', 'nifty'),
  ('st2', 'BANKNIFTY', 'banknifty'),
  ('st3', 'NIFTY', 'nifty'),
  ('st3', 'BANKNIFTY', 'banknifty'),
  ('st4', 'NIFTY', 'nifty'),
  ('st4', 'BANKNIFTY', 'banknifty'),
  ('gapfill', 'NIFTY', 'nifty'),
  ('gapfill', 'BANKNIFTY', 'banknifty'),
  ('simple_st1_threshold', 'NIFTY', 'nifty'),
  ('simple_st1_threshold', 'BANKNIFTY', 'banknifty'),
  ('st2_threshold', 'NIFTY', 'nifty'),
  ('st2_threshold', 'BANKNIFTY', 'banknifty'),
  ('st3_threshold', 'NIFTY', 'nifty'),
  ('st3_threshold', 'BANKNIFTY', 'banknifty'),
  ('st4_threshold', 'NIFTY', 'nifty'),
  ('st4_threshold', 'BANKNIFTY', 'banknifty'),
  ('gapfill_threshold', 'NIFTY', 'nifty'),
  ('gapfill_threshold', 'BANKNIFTY', 'banknifty'),
  ('vix_filter', 'BANKNIFTY', 'banknifty'),
  ('oi_footprint', 'NIFTY', 'nifty'),
  ('oi_footprint', 'BANKNIFTY', 'banknifty'),
  ('credit_spread', 'NIFTY', 'nifty'),
  ('credit_spread', 'BANKNIFTY', 'banknifty'),
  ('pcr_momentum', 'NIFTY', 'nifty'),
  ('pcr_momentum', 'BANKNIFTY', 'banknifty'),
  ('max_pain_drift', 'NIFTY', 'nifty'),
  ('max_pain_drift', 'BANKNIFTY', 'banknifty'),
  ('pcr_vix_combo', 'NIFTY', 'nifty'),
  ('pcr_vix_combo', 'BANKNIFTY', 'banknifty'),
  ('oi_iv_combo', 'NIFTY', 'nifty'),
  ('oi_iv_combo', 'BANKNIFTY', 'banknifty'),
  ('simple_st1_slcap', 'NIFTY', 'nifty'),
  ('simple_st1_slcap', 'BANKNIFTY', 'banknifty'),
  ('st2_slcap', 'NIFTY', 'nifty'),
  ('st2_slcap', 'BANKNIFTY', 'banknifty'),
  ('st3_slcap', 'NIFTY', 'nifty'),
  ('st3_slcap', 'BANKNIFTY', 'banknifty'),
  ('st3_threshold_slcap', 'NIFTY', 'nifty'),
  ('st2_threshold_slcap', 'BANKNIFTY', 'banknifty'),
  ('simple_st1_threshold_slcap', 'NIFTY', 'nifty'),
  ('simple_st1_threshold_slcap', 'BANKNIFTY', 'banknifty'),
  ('st2_threshold_slcap', 'NIFTY', 'nifty'),
  ('st3_threshold_slcap', 'BANKNIFTY', 'banknifty'),
  ('st4_threshold_slcap', 'NIFTY', 'nifty'),
  ('st4_threshold_slcap', 'BANKNIFTY', 'banknifty'),
  ('oi_hybrid_sl', 'NIFTY', 'nifty'),
  ('oi_hybrid_sl', 'BANKNIFTY', 'banknifty'),
  ('oi_hybrid_sl_trailing', 'NIFTY', 'nifty'),
  ('oi_hybrid_sl_trailing', 'BANKNIFTY', 'banknifty'),
  ('oi_hybrid_sl_atr', 'NIFTY', 'nifty'),
  ('oi_hybrid_sl_atr', 'BANKNIFTY', 'banknifty'),
  ('oi_hybrid_sl_breakeven', 'NIFTY', 'nifty'),
  ('oi_hybrid_sl_breakeven', 'BANKNIFTY', 'banknifty'),
  ('oi_hybrid_sl_laddered', 'NIFTY', 'nifty'),
  ('oi_hybrid_sl_laddered', 'BANKNIFTY', 'banknifty'),
  ('oi_hybrid_sl_indicator', 'NIFTY', 'nifty'),
  ('oi_hybrid_sl_indicator', 'BANKNIFTY', 'banknifty'),
];

class FyersOptionsSummaryScreen extends StatefulWidget {
  const FyersOptionsSummaryScreen({super.key});

  @override
  State<FyersOptionsSummaryScreen> createState() => _FyersOptionsSummaryScreenState();
}

class _FyersOptionsSummaryScreenState extends State<FyersOptionsSummaryScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController;

  List<Map<String, dynamic>>? _rows;
  bool _loading = true;
  String? _error;
  int _selectedBookIndex = 0;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _fetch();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _fetch() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final rows = <Map<String, dynamic>>[];

      for (final (strategy, label, indexKey) in _books) {
        Map<String, dynamic>? portfolio;
        try {
          portfolio = await fetchJson(fyersOptionsStrategyUrl(strategy, indexKey));
        } catch (_) {
          portfolio = null;
        }

        final currentAmount = portfolio == null ? _initialAmountPerBook : (portfolio['Cash'] as num).toDouble();

        // This book's OWN date-wise ledger - opening balance is just
        // this one book's Rs 1,00,000, not the combined 59-book total.
        final dailyPnlByDate = <String, double>{};
        final closedTrades = (portfolio?['Closed Trades'] as List?) ?? [];
        for (final t in closedTrades) {
          final trade = t as Map<String, dynamic>;
          final exitTime = trade['Exit Time'] as String?;
          if (exitTime == null || exitTime.length < 10) continue;

          final date = exitTime.substring(0, 10); // "YYYY-MM-DD"
          final netPnl = ((trade['Net PnL'] ?? trade['PnL'] ?? 0) as num).toDouble();

          dailyPnlByDate[date] = (dailyPnlByDate[date] ?? 0) + netPnl;
        }

        final sortedDates = dailyPnlByDate.keys.toList()..sort();
        var runningBalance = _initialAmountPerBook;
        final passbook = <Map<String, dynamic>>[];
        for (final date in sortedDates) {
          final dayPnl = dailyPnlByDate[date]!;
          runningBalance += dayPnl;
          passbook.add({'date': date, 'pnl': dayPnl, 'balance': runningBalance});
        }

        rows.add({
          'strategy': strategy,
          'label': label,
          'current': currentAmount,
          'profit': realizedPnlFromTrades(portfolio),
          'passbook': passbook,
        });
      }

      setState(() {
        _rows = rows;
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
        const LiveClockHeader(),
        TabBar(
          controller: _tabController,
          labelColor: accent2Color,
          unselectedLabelColor: mutedColor,
          tabs: const [
            Tab(text: 'Summary'),
            Tab(text: 'Passbook'),
          ],
        ),
        Expanded(
          child: LoadingErrorWrapper(
            loading: _loading,
            error: _error,
            hasData: _rows != null,
            onRetry: _fetch,
            child: _rows == null
                ? const SizedBox.shrink()
                : TabBarView(
                    controller: _tabController,
                    children: [
                      RefreshIndicator(onRefresh: _fetch, child: _buildSummaryTab()),
                      RefreshIndicator(onRefresh: _fetch, child: _buildPassbookTab()),
                    ],
                  ),
          ),
        ),
      ],
    );
  }

  Widget _buildSummaryTab() {
    final rows = _rows!;
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
            Expanded(
              child: StatPill(
                label: 'Total Current Amount',
                value: formatRupees(totalCurrent),
              ),
            ),
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
              final current = r['current'] as double;
              final profit = r['profit'] as double;

              return DataRow(cells: [
                DataCell(Text(r['strategy'] as String, style: const TextStyle(fontSize: 12))),
                DataCell(Text(r['label'] as String, style: const TextStyle(fontSize: 12))),
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

  Widget _buildPassbookTab() {
    final rows = _rows!;
    final selectedRow = rows[_selectedBookIndex];
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
                final r = rows[i];
                return DropdownMenuItem(
                  value: i,
                  child: Text('${r['strategy']} · ${r['label']}', style: const TextStyle(fontSize: 13)),
                );
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
            '${selectedRow['strategy']} · ${selectedRow['label']} - opening balance ${formatRupees(_initialAmountPerBook)}, one row per day this book closed a trade.',
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
