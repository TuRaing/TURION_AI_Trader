import 'package:flutter/material.dart';

/// Shown at the top of every tab - this is paper trading only, every
/// number in this app is a simulation, and no automation here ever
/// places a real order. Kept short and constant on purpose so it can't
/// be missed by scrolling past it once.
class DisclaimerBanner extends StatelessWidget {
  const DisclaimerBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      color: Colors.white.withValues(alpha: 0.04),
      child: const Row(
        children: [
          Icon(Icons.info_outline, size: 14, color: Colors.white54),
          SizedBox(width: 6),
          Expanded(
            child: Text(
              'Paper trading only. Recommendations, not financial advice. Final action is yours.',
              style: TextStyle(fontSize: 11, color: Colors.white54),
            ),
          ),
        ],
      ),
    );
  }
}
