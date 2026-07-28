import 'package:flutter/material.dart';

import '../theme.dart';

/// Hand-rolled candlestick chart (CustomPainter, no chart package
/// dependency) - draws wicks + bodies for a list of {Open, High, Low,
/// Close} candles, oldest to newest left-to-right, auto-scaled to the
/// visible price range.
class CandlestickChart extends StatelessWidget {
  final List<Map<String, dynamic>> candles;

  const CandlestickChart({super.key, required this.candles});

  @override
  Widget build(BuildContext context) {
    if (candles.isEmpty) {
      return const Center(
        child: Text('No candle data available for this symbol yet', style: TextStyle(color: mutedColor)),
      );
    }

    final candleWidth = 8.0;

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      reverse: true,
      child: CustomPaint(
        size: Size(candles.length * candleWidth, 280),
        painter: _CandlestickPainter(candles: candles, candleWidth: candleWidth),
      ),
    );
  }
}

class _CandlestickPainter extends CustomPainter {
  final List<Map<String, dynamic>> candles;
  final double candleWidth;

  _CandlestickPainter({required this.candles, required this.candleWidth});

  @override
  void paint(Canvas canvas, Size size) {
    if (candles.isEmpty) return;

    final highs = candles.map((c) => (c['High'] as num).toDouble());
    final lows = candles.map((c) => (c['Low'] as num).toDouble());
    final maxPrice = highs.reduce((a, b) => a > b ? a : b);
    final minPrice = lows.reduce((a, b) => a < b ? a : b);
    final range = (maxPrice - minPrice) == 0 ? 1.0 : (maxPrice - minPrice);

    // Small top/bottom margin so wicks never touch the chart edge.
    const marginTop = 12.0;
    const marginBottom = 12.0;
    final chartHeight = size.height - marginTop - marginBottom;

    double yFor(double price) => marginTop + chartHeight - ((price - minPrice) / range) * chartHeight;

    final bodyWidth = candleWidth * 0.6;

    for (var i = 0; i < candles.length; i++) {
      final c = candles[i];
      final open = (c['Open'] as num).toDouble();
      final high = (c['High'] as num).toDouble();
      final low = (c['Low'] as num).toDouble();
      final close = (c['Close'] as num).toDouble();
      final isUp = close >= open;
      final color = isUp ? successColor : dangerColor;
      final x = i * candleWidth + candleWidth / 2;

      canvas.drawLine(
        Offset(x, yFor(high)),
        Offset(x, yFor(low)),
        Paint()
          ..color = color
          ..strokeWidth = 1,
      );

      final bodyTop = yFor(isUp ? close : open);
      final bodyBottomRaw = yFor(isUp ? open : close);
      final bodyBottom = (bodyBottomRaw - bodyTop).abs() < 1 ? bodyTop + 1 : bodyBottomRaw;

      canvas.drawRect(
        Rect.fromLTRB(x - bodyWidth / 2, bodyTop, x + bodyWidth / 2, bodyBottom),
        Paint()..color = color,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _CandlestickPainter oldDelegate) => oldDelegate.candles != candles;
}
