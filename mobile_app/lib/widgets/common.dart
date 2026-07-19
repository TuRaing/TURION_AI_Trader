import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../theme.dart';

final _numberFormat = NumberFormat('#,##,##0.##', 'en_IN');
final _dateTimeFormat = DateFormat('d MMM, h:mm a');

String formatRupees(num value) => _numberFormat.format(value);

String formatSignedRupees(num value) {
  final formatted = _numberFormat.format(value.abs());
  return value >= 0 ? '+$formatted' : '-$formatted';
}

/// Best-effort parse of the "YYYY-MM-DD HH:MM:SS" strings the Python
/// backend writes - falls back to the raw string if parsing fails so a
/// format drift never crashes the screen, it just looks a bit uglier.
String formatBackendTimestamp(String? raw) {
  if (raw == null || raw.isEmpty) return '';

  try {
    final parsed = DateFormat('yyyy-MM-dd HH:mm:ss').parse(raw);
    return _dateTimeFormat.format(parsed);
  } catch (_) {
    return raw;
  }
}

/// One of the 2x2(+1) pill-shaped stats on the Portfolio/History headers.
class StatPill extends StatelessWidget {
  final String label;
  final String value;
  final Color? valueColor;
  final Color? backgroundColor;

  const StatPill({
    super.key,
    required this.label,
    required this.value,
    this.valueColor,
    this.backgroundColor,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12),
      decoration: BoxDecoration(
        color: backgroundColor ?? surfaceColor,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Column(
        children: [
          Text(label, style: TextStyle(fontSize: 11, color: valueColor?.withValues(alpha: 0.85) ?? mutedColor)),
          const SizedBox(height: 2),
          Text(value, style: TextStyle(fontSize: 15, fontWeight: FontWeight.w500, color: valueColor)),
        ],
      ),
    );
  }
}

/// The big hero stat at the top of the Portfolio tab - Total PnL, not
/// Cash, because "am I up or down" is the number that actually matters
/// day to day (see the design review earlier in this project).
class HeroStat extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const HeroStat({super.key, required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Column(
        children: [
          Text(label, style: TextStyle(fontSize: 12, color: color)),
          const SizedBox(height: 2),
          Text(value, style: TextStyle(fontSize: 24, fontWeight: FontWeight.w500, color: color)),
        ],
      ),
    );
  }
}

/// Small "what just happened" strip - the most recent closed trade, so
/// opening the app answers "anything new?" without a trip to History.
class EventBanner extends StatelessWidget {
  final String text;
  final bool positive;

  const EventBanner({super.key, required this.text, required this.positive});

  @override
  Widget build(BuildContext context) {
    final color = positive ? successColor : dangerColor;

    return Container(
      margin: const EdgeInsets.fromLTRB(16, 10, 16, 0),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Icon(positive ? Icons.check_circle_outline : Icons.cancel_outlined, size: 14, color: color),
          const SizedBox(width: 8),
          Expanded(child: Text(text, style: TextStyle(fontSize: 12, color: color))),
        ],
      ),
    );
  }
}

class OpenPositionCard extends StatelessWidget {
  final String symbol;
  final Map<String, dynamic> position;
  final double? currentPrice;

  const OpenPositionCard({super.key, required this.symbol, required this.position, this.currentPrice});

  @override
  Widget build(BuildContext context) {
    final entryPrice = (position['Entry Price'] as num).toDouble();
    final stopLoss = (position['Stop Loss'] as num).toDouble();
    final quantity = (position['Quantity'] as num?)?.toInt() ?? 1;
    final entryTime = formatBackendTimestamp(position['Entry Time'] as String?);

    // Without a live quote we can only show cost basis, not live P&L -
    // callers that have a current price (none yet) can pass it in later.
    final movePct = currentPrice == null ? null : ((currentPrice! - entryPrice) / entryPrice * 100);
    final moveRupees = currentPrice == null ? null : ((currentPrice! - entryPrice) * quantity);
    final isUp = (movePct ?? 0) >= 0;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: bgColor,
        border: Border.all(color: Colors.white12, width: 0.5),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 14,
            backgroundColor: (movePct == null ? mutedColor : (isUp ? successColor : dangerColor)).withValues(alpha: 0.18),
            child: Icon(
              movePct == null ? Icons.remove : (isUp ? Icons.arrow_outward : Icons.south_east),
              size: 14,
              color: movePct == null ? mutedColor : (isUp ? successColor : dangerColor),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(symbol, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
                    const SizedBox(width: 6),
                    // Updated: 2026-07-19 - the watchlist paper-trading engine
                    // only ever opens on a BUY signal (paper_trading.py never
                    // opens SELL/short), so every open position is long by
                    // construction - this tag is a constant, not derived data.
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                      decoration: BoxDecoration(
                        color: successColor.withValues(alpha: 0.18),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: const Text('BUY',
                          style: TextStyle(fontSize: 10, fontWeight: FontWeight.w500, color: successColor)),
                    ),
                  ],
                ),
                Text('Entry ${formatRupees(entryPrice)} · SL ${formatRupees(stopLoss)}',
                    style: const TextStyle(fontSize: 11, color: mutedColor)),
                if (entryTime.isNotEmpty)
                  Text(entryTime, style: const TextStyle(fontSize: 10, color: mutedColor)),
              ],
            ),
          ),
          if (movePct != null)
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text('${movePct >= 0 ? '+' : ''}${movePct.toStringAsFixed(1)}%',
                    style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: isUp ? successColor : dangerColor)),
                Text(formatSignedRupees(moveRupees!),
                    style: TextStyle(fontSize: 11, color: isUp ? successColor : dangerColor)),
              ],
            ),
        ],
      ),
    );
  }
}

class ClosedTradeCard extends StatelessWidget {
  final Map<String, dynamic> trade;

  const ClosedTradeCard({super.key, required this.trade});

  @override
  Widget build(BuildContext context) {
    final symbol = trade['Symbol'] ?? trade['Name'] ?? 'NIFTY 50';
    final pnl = (trade['PnL'] as num).toDouble();
    final win = pnl > 0;
    final entryPrice = (trade['Entry Price'] as num).toDouble();
    final exitPrice = (trade['Exit Price'] as num).toDouble();
    final exitReason = trade['Exit Reason'] ?? '';
    final exitTime = formatBackendTimestamp(trade['Exit Time'] as String?);

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: bgColor,
        border: Border.all(color: Colors.white12, width: 0.5),
        borderRadius: BorderRadius.circular(8),
      ),
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
              Text('$symbol', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
              const Spacer(),
              Text(formatSignedRupees(pnl),
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: win ? successColor : dangerColor)),
            ],
          ),
          const SizedBox(height: 4),
          Padding(
            padding: const EdgeInsets.only(left: 34),
            child: Text(
              '$exitReason · ${formatRupees(entryPrice)} to ${formatRupees(exitPrice)}${exitTime.isNotEmpty ? ' · $exitTime' : ''}',
              style: const TextStyle(fontSize: 11, color: mutedColor),
            ),
          ),
        ],
      ),
    );
  }
}

class LoadingErrorWrapper extends StatelessWidget {
  final bool loading;
  final String? error;
  final bool hasData;
  final VoidCallback onRetry;
  final Widget child;

  const LoadingErrorWrapper({
    super.key,
    required this.loading,
    required this.error,
    required this.hasData,
    required this.onRetry,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    if (loading && !hasData) {
      return const Center(child: CircularProgressIndicator());
    }

    if (error != null && !hasData) {
      return ListView(
        children: [
          const SizedBox(height: 100),
          const Icon(Icons.error_outline, size: 48, color: dangerColor),
          const SizedBox(height: 12),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Text('Could not load data:\n$error', textAlign: TextAlign.center),
          ),
          const SizedBox(height: 12),
          Center(child: TextButton(onPressed: onRetry, child: const Text('Retry'))),
        ],
      );
    }

    return child;
  }
}
