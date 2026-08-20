import 'package:flutter/material.dart';

import '../event_driven_realtime_service.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/disclaimer_banner.dart';

// Added 20-Aug-2026 - replaces the News and History tabs (user's own
// explicit ask, 20-Aug: rarely used, and now that the VPS runs the
// pre-market/running-market/after-market health checks around the
// clock, seeing THOSE results in the app is more useful). Reads
// report/firebase_realtime_sync.py's sync_health_check() feed live -
// no polling, updates the instant a new check lands.

class ChecksScreen extends StatelessWidget {
  const ChecksScreen({super.key});

  static const _sections = [
    _CheckSection(type: 'pre_market', label: 'Pre-Market', color: accentColor),
    _CheckSection(type: 'market', label: 'Market', color: successColor),
    _CheckSection(type: 'after_market', label: 'After-Market', color: mutedColor),
  ];

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const DisclaimerBanner(),
        const SizedBox(height: 8),
        const Text(
          'Live from the VPS - pre-market, running-market, and after-market '
          'health checks, as they happen.',
          style: TextStyle(fontSize: 12, color: mutedColor),
        ),
        const SizedBox(height: 16),
        _CheckFeed(section: _sections[0]),
        const SizedBox(height: 20),
        _CheckFeed(section: _sections[1]),
        const SizedBox(height: 20),
        _CheckFeed(section: _sections[2]),
      ],
    );
  }
}

class _CheckSection {
  final String type;
  final String label;
  final Color color;

  const _CheckSection({required this.type, required this.label, required this.color});
}

class _CheckFeed extends StatelessWidget {
  final _CheckSection section;

  const _CheckFeed({required this.section});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(width: 8, height: 8, decoration: BoxDecoration(color: section.color, shape: BoxShape.circle)),
            const SizedBox(width: 8),
            Text(section.label,
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: section.color)),
          ],
        ),
        const SizedBox(height: 8),
        StreamBuilder<List<Map<String, dynamic>>>(
          stream: watchHealthChecks(section.type, limit: 10),
          builder: (context, snapshot) {
            if (!snapshot.hasData) {
              return const Padding(
                padding: EdgeInsets.symmetric(vertical: 12),
                child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
              );
            }

            final checks = snapshot.data!;

            if (checks.isEmpty) {
              return const Padding(
                padding: EdgeInsets.symmetric(vertical: 8),
                child: Text('No checks synced yet', style: TextStyle(color: mutedColor)),
              );
            }

            return Column(children: checks.map((c) => _CheckCard(check: c)).toList());
          },
        ),
      ],
    );
  }
}

class _CheckCard extends StatefulWidget {
  final Map<String, dynamic> check;

  const _CheckCard({required this.check});

  @override
  State<_CheckCard> createState() => _CheckCardState();
}

class _CheckCardState extends State<_CheckCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final report = (widget.check['report'] as String? ?? '').trim();
    final timestamp = formatBackendTimestamp(widget.check['timestamp'] as String?);

    // First non-heading line as a one-line summary when collapsed -
    // report/market_checks.py's own report text starts with "# ..."
    // then blank, then the first real checklist line.
    final lines = report.split('\n').where((l) => l.trim().isNotEmpty && !l.startsWith('#')).toList();
    final flagged = lines.where((l) => l.trimLeft().startsWith('- [x]')).length;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: surfaceColor, borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        onTap: () => setState(() => _expanded = !_expanded),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(timestamp,
                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                ),
                if (flagged > 0)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                        color: dangerColor.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(20)),
                    child: Text('$flagged flagged',
                        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: dangerColor)),
                  )
                else
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                        color: successColor.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(20)),
                    child: const Text('OK',
                        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: successColor)),
                  ),
                Icon(_expanded ? Icons.expand_less : Icons.expand_more, size: 20, color: mutedColor),
              ],
            ),
            if (_expanded) ...[
              const SizedBox(height: 8),
              Text(
                lines.join('\n'),
                style: const TextStyle(fontSize: 12, fontFamily: 'monospace', color: mutedColor, height: 1.5),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
