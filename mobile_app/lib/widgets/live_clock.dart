import 'dart:async';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../theme.dart';

/// Ticking day/date/time header, plus the last-successful-refresh
/// timestamp underneath it. Two different clocks on purpose - the live
/// one shows "now", the "Updated" one is honest about how fresh the data
/// actually is (refreshed every ~15 min by GitHub Actions, not truly live).
class LiveClockHeader extends StatefulWidget {
  final DateTime? lastUpdated;

  const LiveClockHeader({super.key, this.lastUpdated});

  @override
  State<LiveClockHeader> createState() => _LiveClockHeaderState();
}

class _LiveClockHeaderState extends State<LiveClockHeader> {
  late Timer _timer;
  DateTime _now = DateTime.now();

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      setState(() => _now = DateTime.now());
    });
  }

  @override
  void dispose() {
    _timer.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final dayLine = DateFormat('EEEE, d MMM').format(_now);
    final timeLine = DateFormat('h:mm:ss a').format(_now);

    final updatedText = widget.lastUpdated == null
        ? 'Not refreshed yet'
        : 'Updated ${DateFormat('d MMM, h:mm a').format(widget.lastUpdated!)}';

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: Colors.white12, width: 0.5)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(dayLine, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
              const SizedBox(height: 2),
              Text(updatedText, style: const TextStyle(fontSize: 11, color: mutedColor)),
            ],
          ),
          Text(
            timeLine,
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w500,
              fontFeatures: [FontFeature.tabularFigures()],
            ),
          ),
        ],
      ),
    );
  }
}
