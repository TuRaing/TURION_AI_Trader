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
// Actions-polled books on the other tabs, and now that the VPS
// actually exists and syncs live via Firebase Realtime Database
// (event_driven_realtime_service.dart), they deserve their own place
// rather than being buried among the polling-based screens.

const _books = [
  (key: 'st2_threshold_eventdriven', label: 'ST2 Threshold', underlying: 'NIFTY'),
  (key: 'simple_st1_threshold_eventdriven', label: 'Simple ST1 Threshold', underlying: 'NIFTY'),
  (key: 'oi_footprint_eventdriven_nifty', label: 'OI Footprint', underlying: 'NIFTY'),
  (key: 'oi_footprint_eventdriven_banknifty', label: 'OI Footprint', underlying: 'BANKNIFTY'),
];

class VpsScreen extends StatelessWidget {
  const VpsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const DisclaimerBanner(),
        const SizedBox(height: 8),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(color: accent2Color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(8)),
          child: const Text(
            'VPS - event-driven (WebSocket, tick-by-tick) engine. Real live premium quotes, paper trades only.',
            style: TextStyle(fontSize: 12, color: accent2Color),
          ),
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(child: _LiveChartButton(index: 'NIFTY')),
            const SizedBox(width: 10),
            Expanded(child: _LiveChartButton(index: 'BANKNIFTY')),
          ],
        ),
        const SizedBox(height: 16),
        ..._books.map((book) => _BookSummaryCard(book: book)),
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

  const _BookSummaryCard({required this.book});

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<Map<String, dynamic>?>(
      stream: watchEventDrivenPortfolio(book.key),
      builder: (context, snapshot) {
        final portfolio = snapshot.data;
        final closedTrades = List<Map<String, dynamic>>.from(
            (portfolio?['Closed Trades'] ?? []).map((t) => Map<String, dynamic>.from(t)));
        final position = portfolio?['Position'] as Map<String, dynamic>?;
        final totalPnl = closedTrades.fold<double>(0, (sum, t) => sum + (t['Net PnL'] as num).toDouble());

        return Card(
          margin: const EdgeInsets.only(bottom: 10),
          color: surfaceColor,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: InkWell(
            borderRadius: BorderRadius.circular(12),
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => VpsPassbookScreen(book: book)),
            ),
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('${book.label} · ${book.underlying}',
                            style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                        const SizedBox(height: 4),
                        Text(
                          portfolio == null
                              ? 'No data synced yet'
                              : '${closedTrades.length} closed · ${position == null ? "no open position" : "1 open position"}',
                          style: const TextStyle(fontSize: 12, color: mutedColor),
                        ),
                      ],
                    ),
                  ),
                  if (portfolio != null)
                    Text(formatSignedRupees(totalPnl),
                        style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: pnlColor(totalPnl))),
                  const SizedBox(width: 6),
                  const Icon(Icons.chevron_right, color: mutedColor),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

/// The "passbook" - full live detail for one VPS book (Cash, open
/// Position, every Closed Trade) - opened by tapping its summary card.
class VpsPassbookScreen extends StatelessWidget {
  final ({String key, String label, String underlying}) book;

  const VpsPassbookScreen({super.key, required this.book});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('${book.label} · ${book.underlying}')),
      body: StreamBuilder<Map<String, dynamic>?>(
        stream: watchEventDrivenPortfolio(book.key),
        builder: (context, snapshot) {
          final portfolio = snapshot.data;

          if (portfolio == null) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Text('No data synced from the VPS yet for this book.', style: TextStyle(color: mutedColor)),
              ),
            );
          }

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
              HeroStat(label: 'Total Net PnL', value: formatSignedRupees(totalPnl), color: pnlColor(totalPnl)),
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
                    const Text('Open Position',
                        style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: accentColor)),
                    const SizedBox(height: 8),
                    if (position == null)
                      const Padding(
                        padding: EdgeInsets.symmetric(vertical: 8),
                        child: Text('No open position', style: TextStyle(color: mutedColor)),
                      )
                    else
                      OptionPositionCard(position: position, underlyingLabel: book.underlying),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              if (closedTrades.isNotEmpty) ...[
                const Text('Closed Trades (Passbook)',
                    style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: mutedColor)),
                const SizedBox(height: 8),
                ...closedTrades.reversed.map((t) => OptionClosedTradeCard(trade: t, underlyingLabel: book.underlying)),
              ],
            ],
          );
        },
      ),
    );
  }
}
