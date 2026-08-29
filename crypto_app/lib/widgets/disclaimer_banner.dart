import 'package:flutter/material.dart';

/// Same banner text/style as the main app - paper trading only, no
/// real order is ever placed, real Deribit market data / simulated
/// money.
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
              'Paper trading only, real Deribit market data. No real order is ever placed.',
              style: TextStyle(fontSize: 11, color: Colors.white54),
            ),
          ),
        ],
      ),
    );
  }
}
