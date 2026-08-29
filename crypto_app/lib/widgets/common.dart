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
/// the Python side writes.
class CryptoPositionCard extends StatelessWidget {
  final Map<String, dynamic> position;

  const CryptoPositionCard({super.key, required this.position});

  @override
  Widget build(BuildContext context) {
    final symbol = position['Symbol'] as String? ?? '';
    final optionType = position['Option Type'] as String? ?? '';
    final entryPremium = (position['Entry Premium'] as num).toDouble();
    final lots = position['Lots'];
    final entrySpot = (position['Entry Spot'] as num?)?.toDouble();

    return Container(
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
        ],
      ),
    );
  }
}

/// One closed trade row, matching event_driven_engine.py's
/// `trade_record` shape exactly (Symbol/Option Type/Entry-Exit
/// Premium/Exit Reason/Net PnL).
class CryptoClosedTradeCard extends StatelessWidget {
  final Map<String, dynamic> trade;

  const CryptoClosedTradeCard({super.key, required this.trade});

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

    return Container(
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
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: win ? successColor : dangerColor)),
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
    );
  }
}
