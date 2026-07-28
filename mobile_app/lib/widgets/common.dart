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
  final String typeLabel;
  final Color typeColor;
  final VoidCallback? onTap;

  const OpenPositionCard({
    super.key,
    required this.symbol,
    required this.position,
    this.currentPrice,
    this.typeLabel = 'Swing',
    this.typeColor = mutedColor,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final entryPrice = (position['Entry Price'] as num).toDouble();
    final stopLoss = (position['Stop Loss'] as num).toDouble();
    final quantity = (position['Quantity'] as num?)?.toInt() ?? 1;
    final entryTime = formatBackendTimestamp(position['Entry Time'] as String?);
    // Watchlist (Swing) only ever opens BUY (see paper_trading.py); Best
    // Trade (Intraday) positions carry their own real Direction (BUY/SELL).
    final direction = position['Direction'] as String? ?? 'BUY';
    final isBuy = direction == 'BUY';

    // Without a live quote we can only show cost basis, not live P&L -
    // callers that have a current price (none yet) can pass it in later.
    final movePct = currentPrice == null ? null : ((currentPrice! - entryPrice) / entryPrice * 100);
    final moveRupees = currentPrice == null ? null : ((currentPrice! - entryPrice) * quantity);
    final isUp = (movePct ?? 0) >= 0;

    final card = Container(
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
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                      decoration: BoxDecoration(
                        color: (isBuy ? successColor : dangerColor).withValues(alpha: 0.18),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(direction,
                          style: TextStyle(
                              fontSize: 10, fontWeight: FontWeight.w500, color: isBuy ? successColor : dangerColor)),
                    ),
                    const SizedBox(width: 4),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                      decoration: BoxDecoration(
                        color: typeColor.withValues(alpha: 0.18),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(typeLabel,
                          style: TextStyle(fontSize: 10, fontWeight: FontWeight.w500, color: typeColor)),
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

    if (onTap == null) return card;

    return Material(
      color: Colors.transparent,
      child: InkWell(borderRadius: BorderRadius.circular(8), onTap: onTap, child: card),
    );
  }
}

class ClosedTradeCard extends StatelessWidget {
  final Map<String, dynamic> trade;
  final String typeLabel;
  final Color typeColor;
  final VoidCallback? onViewChart;

  const ClosedTradeCard({
    super.key,
    required this.trade,
    this.typeLabel = 'Swing',
    this.typeColor = mutedColor,
    this.onViewChart,
  });

  @override
  Widget build(BuildContext context) {
    final symbol = trade['Symbol'] ?? trade['Name'] ?? 'NIFTY 50';
    final pnl = (trade['PnL'] as num).toDouble();
    final win = pnl > 0;
    final entryPrice = (trade['Entry Price'] as num).toDouble();
    final exitPrice = (trade['Exit Price'] as num).toDouble();
    final exitReason = trade['Exit Reason'] ?? '';
    final exitTime = formatBackendTimestamp(trade['Exit Time'] as String?);

    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: () => _showTradeDetails(context, trade, typeLabel, onViewChart),
        child: Container(
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
                  const SizedBox(width: 6),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                    decoration: BoxDecoration(
                      color: typeColor.withValues(alpha: 0.18),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(typeLabel,
                        style: TextStyle(fontSize: 10, fontWeight: FontWeight.w500, color: typeColor)),
                  ),
                  const Spacer(),
                  Text(formatSignedRupees(pnl),
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: win ? successColor : dangerColor)),
                  const SizedBox(width: 4),
                  const Icon(Icons.chevron_right, size: 16, color: mutedColor),
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
        ),
      ),
    );
  }
}

void _showTradeDetails(
    BuildContext context, Map<String, dynamic> trade, String typeLabel, VoidCallback? onViewChart) {
  final symbol = trade['Symbol'] ?? trade['Name'] ?? 'NIFTY 50';
  final name = trade['Name'];
  final direction = trade['Direction'];
  final pnl = (trade['PnL'] as num).toDouble();
  final win = pnl > 0;
  final entryPrice = (trade['Entry Price'] as num).toDouble();
  final exitPrice = (trade['Exit Price'] as num).toDouble();
  final quantity = trade['Quantity'] as num?;
  final exitReason = trade['Exit Reason'] ?? '—';
  final entryTimeRaw = trade['Entry Time'] as String?;
  final exitTimeRaw = trade['Exit Time'] as String?;
  final entryTime = formatBackendTimestamp(entryTimeRaw);
  final exitTime = formatBackendTimestamp(exitTimeRaw);

  final returnPct = entryPrice == 0 ? null : (exitPrice - entryPrice) / entryPrice * 100;

  Duration? holding;
  if (entryTimeRaw != null && exitTimeRaw != null) {
    try {
      final entryDt = DateFormat('yyyy-MM-dd HH:mm:ss').parse(entryTimeRaw);
      final exitDt = DateFormat('yyyy-MM-dd HH:mm:ss').parse(exitTimeRaw);
      holding = exitDt.difference(entryDt);
    } catch (_) {
      holding = null;
    }
  }

  showModalBottomSheet(
    context: context,
    backgroundColor: surfaceColor,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
    ),
    builder: (context) {
      return SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  CircleAvatar(
                    radius: 15,
                    backgroundColor: (win ? successColor : dangerColor).withValues(alpha: 0.18),
                    child: Icon(win ? Icons.check : Icons.close, size: 16, color: win ? successColor : dangerColor),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text('$symbol', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                  ),
                  Text(formatSignedRupees(pnl),
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: win ? successColor : dangerColor)),
                ],
              ),
              if (returnPct != null)
                Padding(
                  padding: const EdgeInsets.only(top: 2, left: 40),
                  child: Text(
                    '${returnPct >= 0 ? '+' : ''}${returnPct.toStringAsFixed(2)}%',
                    style: TextStyle(fontSize: 12, color: win ? successColor : dangerColor),
                  ),
                ),
              const SizedBox(height: 16),
              const Divider(color: Colors.white12, height: 1),
              const SizedBox(height: 16),
              _DetailRow(label: 'Type', value: typeLabel),
              if (name != null && name != symbol) _DetailRow(label: 'Name', value: '$name'),
              if (direction != null) _DetailRow(label: 'Direction', value: '$direction'),
              _DetailRow(label: 'Quantity', value: quantity != null ? '$quantity' : '—'),
              _DetailRow(label: 'Entry Price', value: formatRupees(entryPrice)),
              _DetailRow(label: 'Entry Time', value: entryTime.isNotEmpty ? entryTime : '—'),
              _DetailRow(label: 'Exit Price', value: formatRupees(exitPrice)),
              _DetailRow(label: 'Exit Time', value: exitTime.isNotEmpty ? exitTime : '—'),
              _DetailRow(label: 'Exit Reason', value: '$exitReason'),
              if (holding != null) _DetailRow(label: 'Held for', value: _formatDuration(holding)),
              if (onViewChart != null) ...[
                const SizedBox(height: 8),
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: () {
                      Navigator.pop(context);
                      onViewChart();
                    },
                    icon: const Icon(Icons.show_chart, size: 18),
                    label: const Text('View Chart'),
                  ),
                ),
              ],
            ],
          ),
        ),
      );
    },
  );
}

String _formatDuration(Duration d) {
  final days = d.inDays;
  final hours = d.inHours % 24;
  final minutes = d.inMinutes % 60;

  if (days > 0) return '$days d $hours h';
  if (hours > 0) return '$hours h $minutes m';
  return '$minutes m';
}

class _DetailRow extends StatelessWidget {
  final String label;
  final String value;

  const _DetailRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 13, color: mutedColor)),
          Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
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
