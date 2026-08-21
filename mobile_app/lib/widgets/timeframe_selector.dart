import 'package:flutter/material.dart';

import '../theme.dart';

// Added 21-Aug-2026, at the user's own request (matching a real
// broker app's own chart) - a small row of buttons letting the user
// pick the candle timeframe (1/5/10/15 min). Shared by live_chart_
// screen.dart and strategy_premium_chart_screen.dart - both already
// hold their own real 1-min candle history/live stream, and candle_
// aggregation.dart's aggregateCandles() derives every coarser
// timeframe from that same data client-side, so this widget only
// needs to report which one is selected, not fetch anything itself.

const timeframeOptions = [1, 5, 10, 15];

class TimeframeSelector extends StatelessWidget {
  final int selected;
  final ValueChanged<int> onChanged;

  const TimeframeSelector({super.key, required this.selected, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        for (final minutes in timeframeOptions) ...[
          _TimeframeButton(
            label: '${minutes}m',
            isSelected: minutes == selected,
            onTap: () => onChanged(minutes),
          ),
          const SizedBox(width: 8),
        ],
      ],
    );
  }
}

class _TimeframeButton extends StatelessWidget {
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _TimeframeButton({required this.label, required this.isSelected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: isSelected ? accentColor.withValues(alpha: 0.25) : surfaceColor,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: isSelected ? accentColor : Colors.white12),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w600,
            color: isSelected ? accentColor : mutedColor,
          ),
        ),
      ),
    );
  }
}
