import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../theme.dart';

// Own small widget set for this app rather than importing the main
// app's mobile_app/lib/widgets/common.dart - that file's formatters
// and cost breakdown are Rupee/NIFTY-specific (formatRupees(),
// lotSizeByIndex, and a cost model calibrated in INR - see strategy/
// crypto_transaction_costs.py's own docstring for the real currency-
// mismatch bug that caused on the Python side when a Rupee cost model
// was applied to USD Deribit premiums; the same mismatch would happen
// here if this app displayed crypto numbers through rupee formatters).
// Only StatPill/HeroStat's pure layout is copied - the rest is written
// fresh for USD, single-leg option positions.

final _numberFormat = NumberFormat('#,##0.##', 'en_US');
final _dateTimeFormat = DateFormat('d MMM, h:mm a');

String formatUsd(num value) => '\$${_numberFormat.format(value)}';

String formatSignedUsd(num value) {
  final formatted = _numberFormat.format(value.abs());
  return value >= 0 ? '+\$$formatted' : '-\$$formatted';
}

/// Best-effort parse of the "YYYY-MM-DD HH:MM:SS" strings the Python
/// backend writes (UTC, since Deribit is a 24/7 market with no IST
/// trading-hours convention to convert to) - falls back to the raw
/// string if parsing fails.
String formatBackendTimestamp(String? raw) {
  if (raw == null || raw.isEmpty) return '';
  try {
    final parsed = DateFormat('yyyy-MM-dd HH:mm:ss').parse(raw);
    return '${_dateTimeFormat.format(parsed)} UTC';
  } catch (_) {
    return raw;
  }
}

class StatPill extends StatelessWidget {
  final String label;
  final String value;
  final Color? valueColor;

  const StatPill({super.key, required this.label, required this.value, this.valueColor});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12),
      decoration: BoxDecoration(
        color: surfaceColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withValues(alpha: 0.06)),
      ),
      child: Column(
        children: [
          Text(label.toUpperCase(),
              style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: faintColor, letterSpacing: 0.4)),
          const SizedBox(height: 3),
          Text(value, style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: valueColor)),
        ],
      ),
    );
  }
}

class HeroStat extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const HeroStat({super.key, required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: surfaceRaisedColor,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: accentColor.withValues(alpha: 0.16)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label.toUpperCase(),
              style: const TextStyle(
                  fontSize: 11, fontWeight: FontWeight.w700, color: accent2Color, letterSpacing: 0.6)),
          const SizedBox(height: 6),
          Text(value,
              style: TextStyle(fontSize: 32, fontWeight: FontWeight.w800, color: color, shadows: glowShadow(color))),
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

/// The live open position for one crypto book - Symbol/Option Type/
/// Entry Premium/Lots, matching strategy/event_driven_engine.py's
/// `new_position` shape (rsi_momentum_decide_fn) exactly, same fields
/// the Python side writes. Tappable - opens the same detail sheet a
/// closed trade gets, plus a View Chart button (see
/// showCryptoTradeDetails below).
class CryptoPositionCard extends StatelessWidget {
  final Map<String, dynamic> position;
  final VoidCallback? onViewChart;

  const CryptoPositionCard({super.key, required this.position, this.onViewChart});

  @override
  Widget build(BuildContext context) {
    final symbol = position['Symbol'] as String? ?? '';
    final optionType = position['Option Type'] as String? ?? '';
    final entryPremium = (position['Entry Premium'] as num).toDouble();
    final lots = position['Lots'];
    final entrySpot = (position['Entry Spot'] as num?)?.toDouble();

    final card = Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
          color: bgColor, border: Border.all(color: Colors.white12, width: 0.5), borderRadius: BorderRadius.circular(8)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(symbol, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
              const SizedBox(width: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                decoration: BoxDecoration(
                  color: (optionType == 'CE' ? successColor : dangerColor).withValues(alpha: 0.18),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(optionType,
                    style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w500,
                        color: optionType == 'CE' ? successColor : dangerColor)),
              ),
              const Spacer(),
              Text('${lots}x lot', style: const TextStyle(fontSize: 12, color: mutedColor)),
            ],
          ),
          const SizedBox(height: 6),
          Text('Entry ${formatUsd(entryPremium)}${entrySpot != null ? ' · spot ${formatUsd(entrySpot)}' : ''}',
              style: const TextStyle(fontSize: 12, color: mutedColor)),
          const SizedBox(height: 4),
          Text('Entered ${formatBackendTimestamp(position['Entry Time'] as String?)}',
              style: const TextStyle(fontSize: 11, color: mutedColor)),
          const SizedBox(height: 4),
          const Row(
            children: [
              Spacer(),
              Icon(Icons.candlestick_chart_outlined, size: 14, color: mutedColor),
              SizedBox(width: 4),
              Text('Tap for details & chart', style: TextStyle(fontSize: 11, color: mutedColor)),
            ],
          ),
        ],
      ),
    );

    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: () => showCryptoTradeDetails(context, trade: position, isOpen: true, onViewChart: onViewChart),
        child: card,
      ),
    );
  }
}

/// One closed trade row, matching event_driven_engine.py's
/// `trade_record` shape exactly (Symbol/Option Type/Entry-Exit
/// Premium/Exit Reason/Net PnL). Tappable - opens the full detail
/// sheet with a real cost breakdown and a View Chart button.
class CryptoClosedTradeCard extends StatelessWidget {
  final Map<String, dynamic> trade;
  final VoidCallback? onViewChart;

  const CryptoClosedTradeCard({super.key, required this.trade, this.onViewChart});

  @override
  Widget build(BuildContext context) {
    final symbol = trade['Symbol'] as String? ?? '';
    final optionType = trade['Option Type'] as String? ?? '';
    final pnl = (trade['Net PnL'] as num).toDouble();
    final win = pnl > 0;
    final entryPremium = (trade['Entry Premium'] as num).toDouble();
    final exitPremium = (trade['Exit Premium'] as num).toDouble();
    final exitReason = trade['Exit Reason'] as String? ?? '';
    final exitTime = formatBackendTimestamp(trade['Exit Time'] as String?);

    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: () => showCryptoTradeDetails(context, trade: trade, isOpen: false, onViewChart: onViewChart),
        child: Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
              color: bgColor, border: Border.all(color: Colors.white12, width: 0.5), borderRadius: BorderRadius.circular(8)),
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
                  Text('$symbol $optionType', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
                  const Spacer(),
                  Text(formatSignedUsd(pnl),
                      style:
                          TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: win ? successColor : dangerColor)),
                  const SizedBox(width: 4),
                  const Icon(Icons.chevron_right, size: 16, color: mutedColor),
                ],
              ),
              const SizedBox(height: 4),
              Padding(
                padding: const EdgeInsets.only(left: 34),
                child: Text(
                  '$exitReason · ${formatUsd(entryPremium)} to ${formatUsd(exitPremium)}${exitTime.isNotEmpty ? ' · $exitTime' : ''}',
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

/// Deribit's real taker fee, mirrored from strategy/crypto_
/// transaction_costs.py's calculate_crypto_options_round_trip_cost()
/// - percentage-of-premium-turnover, no flat brokerage (unlike the
/// main app's Rupee/NIFTY cost model - see this file's own top
/// comment for why that one is never imported here). Keep this
/// constant in sync with the Python module's TAKER_FEE_PCT by hand if
/// it ever changes - a small, static, rarely-touched number.
const _takerFeePct = 0.03 / 100;

class CryptoCostBreakdown {
  final double fee;

  const CryptoCostBreakdown({required this.fee});

  factory CryptoCostBreakdown.compute({
    required double entryPremium,
    required double exitPremium,
    required int quantity,
  }) {
    final buyValue = entryPremium * quantity;
    final sellValue = exitPremium * quantity;
    return CryptoCostBreakdown(fee: (buyValue + sellValue) * _takerFeePct);
  }
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

/// The full trade-detail bottom sheet - entry/exit/lots and a real
/// cost breakdown, for BOTH the live open position (isOpen: true,
/// PnL is unrealized/estimated) and a closed trade (isOpen: false,
/// PnL is the real recorded Net PnL). Matches the shape of the main
/// app's showOptionTradeDetails() (mobile_app/lib/widgets/common.dart)
/// but USD/crypto-fee-correct throughout - see this file's own top
/// comment for why that one isn't reused directly.
void showCryptoTradeDetails(
  BuildContext context, {
  required Map<String, dynamic> trade,
  required bool isOpen,
  VoidCallback? onViewChart,
}) {
  final symbol = trade['Symbol'] as String? ?? '';
  final optionType = trade['Option Type'] as String? ?? '';
  final lots = (trade['Lots'] as num?)?.toInt() ?? 0;
  final entryPremium = (trade['Entry Premium'] as num).toDouble();
  final exitPremium = isOpen
      ? (trade['Last Premium'] as num?)?.toDouble() ?? entryPremium
      : (trade['Exit Premium'] as num).toDouble();
  final entryTime = formatBackendTimestamp(trade['Entry Time'] as String?);
  final exitTimeRaw = isOpen ? null : trade['Exit Time'] as String?;
  final exitTime = isOpen ? null : formatBackendTimestamp(exitTimeRaw);
  final exitReason = isOpen ? null : (trade['Exit Reason'] as String? ?? '—');
  final recordedNetPnl = isOpen ? null : (trade['Net PnL'] as num?)?.toDouble();

  Duration? holding;
  final entryTimeRaw = trade['Entry Time'] as String?;
  if (!isOpen && entryTimeRaw != null && exitTimeRaw != null) {
    try {
      final entryDt = DateFormat('yyyy-MM-dd HH:mm:ss').parse(entryTimeRaw);
      final exitDt = DateFormat('yyyy-MM-dd HH:mm:ss').parse(exitTimeRaw);
      holding = exitDt.difference(entryDt);
    } catch (_) {
      holding = null;
    }
  }

  final grossPnl = lots > 0 ? (exitPremium - entryPremium) * lots : null;
  final costs = lots > 0
      ? CryptoCostBreakdown.compute(entryPremium: entryPremium, exitPremium: exitPremium, quantity: lots)
      : null;
  final displayPnl = recordedNetPnl ?? (grossPnl != null && costs != null ? grossPnl - costs.fee : null);
  final win = (displayPnl ?? 0) >= 0;

  showModalBottomSheet(
    context: context,
    backgroundColor: surfaceColor,
    isScrollControlled: true,
    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
    builder: (context) {
      return SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    CircleAvatar(
                      radius: 15,
                      backgroundColor: (isOpen ? mutedColor : (win ? successColor : dangerColor)).withValues(alpha: 0.18),
                      child: Icon(
                        isOpen ? Icons.hourglass_top : (win ? Icons.check : Icons.close),
                        size: 16,
                        color: isOpen ? mutedColor : (win ? successColor : dangerColor),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text('$symbol $optionType', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                    ),
                    if (displayPnl != null)
                      Text(
                        '${isOpen ? '~' : ''}${formatSignedUsd(displayPnl)}',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: win ? successColor : dangerColor),
                      ),
                  ],
                ),
                if (isOpen)
                  const Padding(
                    padding: EdgeInsets.only(top: 2, left: 40),
                    child: Text('Still open - unrealized, live premium',
                        style: TextStyle(fontSize: 11, color: mutedColor)),
                  ),
                const SizedBox(height: 16),
                const Divider(color: Colors.white12, height: 1),
                const SizedBox(height: 16),
                _DetailRow(label: 'Lots', value: '$lots'),
                _DetailRow(label: 'Entry Time', value: entryTime.isNotEmpty ? entryTime : '—'),
                _DetailRow(label: 'Entry Premium', value: formatUsd(entryPremium)),
                _DetailRow(label: isOpen ? 'Last Premium' : 'Exit Premium', value: formatUsd(exitPremium)),
                if (!isOpen) ...[
                  _DetailRow(label: 'Exit Time', value: exitTime != null && exitTime.isNotEmpty ? exitTime : '—'),
                  _DetailRow(label: 'Exit Reason', value: exitReason ?? '—'),
                  if (holding != null) _DetailRow(label: 'Held for', value: _formatDuration(holding)),
                ],
                if (grossPnl != null && costs != null) ...[
                  const SizedBox(height: 8),
                  const Divider(color: Colors.white12, height: 1),
                  const SizedBox(height: 8),
                  Text('Trading costs (Deribit taker fee, real - not income tax)',
                      style: TextStyle(fontSize: 11, color: mutedColor.withValues(alpha: 0.9))),
                  const SizedBox(height: 8),
                  _DetailRow(label: 'Gross PnL', value: formatSignedUsd(grossPnl)),
                  _DetailRow(label: 'Deribit taker fee (0.03% × 2)', value: formatSignedUsd(-costs.fee)),
                  const Divider(color: Colors.white12, height: 1),
                  _DetailRow(
                    label: isOpen ? 'Net PnL (est., after fee)' : 'Net PnL (after fee)',
                    value: formatSignedUsd(displayPnl!),
                  ),
                ],
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
        ),
      );
    },
  );
}
