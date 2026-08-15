import 'package:flutter/material.dart';

import '../api.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/live_clock.dart';
import 'fyers_options_book_detail_screen.dart';

// Added 14-Aug-2026 - user's own explicit request, after ALL_STRATEGIES
// grew from 33 to 59 books today: a flat tab-per-strategy list stopped
// being usable, so this screen groups every book into 4 sections
// instead -
//   New (SL-cap)  - every book carrying the hybrid Stop-Loss cap
//                   (name ends in "_slcap" or starts with
//                   "oi_hybrid_sl") - a distinct experiment cohort,
//                   shown here regardless of its own current PnL sign,
//                   since the point is tracking the fix itself.
//   Profitable    - everything else with Cash > initial capital.
//   Loss-making   - everything else with Cash < initial capital.
//   No data yet   - everything else with zero closed trades (can't be
//                   classified pass/fail without a real result yet).
// Deliberately COMPUTED LIVE from each book's real Cash value on every
// fetch, not a hardcoded list - which book is "profitable" changes day
// to day (several flipped sign today alone), a static list would be
// stale within a day.

const _allBooks = [
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

bool _isSlcap(String name) => name.endsWith('_slcap') || name.startsWith('oi_hybrid_sl');

enum _Group { newSlcap, profitable, lossMaking, noData }

class _BookRow {
  final String name;
  final String indexLabel;
  final String indexKey;
  final double pnl;
  final int trades;
  final _Group group;

  _BookRow({
    required this.name,
    required this.indexLabel,
    required this.indexKey,
    required this.pnl,
    required this.trades,
    required this.group,
  });
}

class FyersOptionsGroupedScreen extends StatefulWidget {
  const FyersOptionsGroupedScreen({super.key});

  @override
  State<FyersOptionsGroupedScreen> createState() => _FyersOptionsGroupedScreenState();
}

class _FyersOptionsGroupedScreenState extends State<FyersOptionsGroupedScreen> {
  List<_BookRow>? _rows;
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
      final rows = <_BookRow>[];

      for (final (name, indexLabel, indexKey) in _allBooks) {
        Map<String, dynamic>? portfolio;
        try {
          portfolio = await fetchJson(fyersOptionsStrategyUrl(name, indexKey));
        } catch (_) {
          portfolio = null;
        }

        final trades = portfolio == null ? 0 : ((portfolio['Closed Trades'] as List?)?.length ?? 0);
        final pnl = realizedPnlFromTrades(portfolio);

        final _Group group;
        if (_isSlcap(name)) {
          group = _Group.newSlcap;
        } else if (trades == 0) {
          group = _Group.noData;
        } else if (pnl > 0) {
          group = _Group.profitable;
        } else {
          group = _Group.lossMaking;
        }

        rows.add(_BookRow(name: name, indexLabel: indexLabel, indexKey: indexKey, pnl: pnl, trades: trades, group: group));
      }

      setState(() {
        _rows = rows;
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
        Expanded(
          child: LoadingErrorWrapper(
            loading: _loading,
            error: _error,
            hasData: _rows != null,
            onRetry: _fetch,
            child: _rows == null ? const SizedBox.shrink() : RefreshIndicator(onRefresh: _fetch, child: _buildBody()),
          ),
        ),
      ],
    );
  }

  Widget _buildBody() {
    final rows = _rows!;
    final newSlcap = rows.where((r) => r.group == _Group.newSlcap).toList();
    final profitable = rows.where((r) => r.group == _Group.profitable).toList();
    final lossMaking = rows.where((r) => r.group == _Group.lossMaking).toList();
    final noData = rows.where((r) => r.group == _Group.noData).toList();

    profitable.sort((a, b) => b.pnl.compareTo(a.pnl));
    lossMaking.sort((a, b) => a.pnl.compareTo(b.pnl));
    newSlcap.sort((a, b) => b.pnl.compareTo(a.pnl));

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(color: accentColor.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(8)),
          child: Text('${rows.length} books, grouped by current result - New (SL-cap) shown regardless of its own PnL.',
              style: const TextStyle(fontSize: 12, color: accentColor)),
        ),
        const SizedBox(height: 16),
        _GroupSection(title: 'New (SL-cap)', icon: Icons.science_outlined, color: accentColor, books: newSlcap),
        _GroupSection(title: 'Profitable', icon: Icons.trending_up, color: successColor, books: profitable),
        _GroupSection(title: 'Loss-making', icon: Icons.trending_down, color: dangerColor, books: lossMaking),
        _GroupSection(title: 'No data yet', icon: Icons.hourglass_empty, color: mutedColor, books: noData),
      ],
    );
  }
}

class _GroupSection extends StatelessWidget {
  final String title;
  final IconData icon;
  final Color color;
  final List<_BookRow> books;

  const _GroupSection({required this.title, required this.icon, required this.color, required this.books});

  @override
  Widget build(BuildContext context) {
    final totalPnl = books.fold<double>(0, (sum, b) => sum + b.pnl);

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 16, color: color),
              const SizedBox(width: 6),
              Text('$title (${books.length})', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: color)),
              const Spacer(),
              if (books.isNotEmpty) Text(formatSignedRupees(totalPnl), style: TextStyle(fontSize: 12, color: color)),
            ],
          ),
          const SizedBox(height: 8),
          if (books.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 4),
              child: Text('None right now', style: TextStyle(fontSize: 12, color: mutedColor)),
            )
          else
            ...books.map((b) => _BookListTile(book: b)),
        ],
      ),
    );
  }
}

class _BookListTile extends StatelessWidget {
  final _BookRow book;

  const _BookListTile({required this.book});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: () => Navigator.push(
            context,
            MaterialPageRoute(
                builder: (_) => FyersOptionsBookDetailScreen(
                      strategyName: book.name,
                      indexLabel: book.indexLabel,
                      indexKey: book.indexKey,
                    ))),
        child: Container(
          margin: const EdgeInsets.only(bottom: 6),
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
          decoration: BoxDecoration(
            color: bgColor,
            border: Border.all(color: Colors.white12, width: 0.5),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('${book.name} · ${book.indexLabel}', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
                    Text('${book.trades} trades', style: const TextStyle(fontSize: 11, color: mutedColor)),
                  ],
                ),
              ),
              Text(formatSignedRupees(book.pnl),
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: pnlColor(book.pnl))),
              const SizedBox(width: 4),
              const Icon(Icons.chevron_right, size: 16, color: mutedColor),
            ],
          ),
        ),
      ),
    );
  }
}
