import 'package:flutter/material.dart';

import 'common.dart';
import '../theme.dart';

/// A horizontal reference line drawn across the chart - Entry/Stop Loss/
/// Target/Exit price, so the trade is visible against the market, not
/// just a bare price series.
class ChartReferenceLine {
  final double price;
  final String label;
  final Color color;

  const ChartReferenceLine({required this.price, required this.label, required this.color});
}

/// Hand-rolled candlestick chart (CustomPainter, no chart package
/// dependency) - wicks + bodies for a list of {Open, High, Low, Close}
/// candles, oldest to newest left-to-right, auto-scaled to the visible
/// price range. Tap/drag anywhere to move a crosshair and read that
/// candle's exact values via onSelect - a bare chart with no numbers on
/// it isn't useful, this is how the user reads a specific point.
class CandlestickChart extends StatefulWidget {
  final List<Map<String, dynamic>> candles;
  final ValueChanged<Map<String, dynamic>?>? onSelect;
  final List<ChartReferenceLine> referenceLines;

  const CandlestickChart({
    super.key,
    required this.candles,
    this.onSelect,
    this.referenceLines = const [],
  });

  @override
  State<CandlestickChart> createState() => _CandlestickChartState();
}

class _CandlestickChartState extends State<CandlestickChart> {
  static const _candleWidth = 8.0;
  static const _height = 280.0;
  static const _axisWidth = 56.0;

  int? _selectedIndex;

  @override
  void initState() {
    super.initState();
    if (widget.candles.isNotEmpty) {
      _selectedIndex = widget.candles.length - 1;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) widget.onSelect?.call(widget.candles[_selectedIndex!]);
      });
    }
  }

  @override
  void didUpdateWidget(covariant CandlestickChart oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.candles.isNotEmpty && widget.candles != oldWidget.candles) {
      _selectedIndex = widget.candles.length - 1;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) widget.onSelect?.call(widget.candles[_selectedIndex!]);
      });
    }
  }

  void _handleTap(Offset localPosition) {
    final index = (localPosition.dx / _candleWidth).floor().clamp(0, widget.candles.length - 1);
    if (index == _selectedIndex) return;
    setState(() => _selectedIndex = index);
    widget.onSelect?.call(widget.candles[index]);
  }

  @override
  Widget build(BuildContext context) {
    if (widget.candles.isEmpty) {
      return const SizedBox(
        height: _height,
        child: Center(
          child: Text('No candle data available for this symbol yet', style: TextStyle(color: mutedColor)),
        ),
      );
    }

    final highs = widget.candles.map((c) => (c['High'] as num).toDouble());
    final lows = widget.candles.map((c) => (c['Low'] as num).toDouble());
    var maxPrice = highs.reduce((a, b) => a > b ? a : b);
    var minPrice = lows.reduce((a, b) => a < b ? a : b);

    for (final line in widget.referenceLines) {
      if (line.price > maxPrice) maxPrice = line.price;
      if (line.price < minPrice) minPrice = line.price;
    }

    // A little headroom so a reference line sitting exactly at the
    // extreme doesn't get drawn flush against the chart edge.
    final pad = (maxPrice - minPrice) * 0.04;
    maxPrice += pad;
    minPrice -= pad;

    return SizedBox(
      height: _height,
      child: Stack(
        children: [
          Positioned.fill(
            right: _axisWidth,
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              reverse: true,
              child: GestureDetector(
                onTapDown: (d) => _handleTap(d.localPosition),
                onHorizontalDragUpdate: (d) => _handleTap(d.localPosition),
                child: CustomPaint(
                  size: Size(widget.candles.length * _candleWidth, _height),
                  painter: _CandlestickPainter(
                    candles: widget.candles,
                    candleWidth: _candleWidth,
                    minPrice: minPrice,
                    maxPrice: maxPrice,
                    selectedIndex: _selectedIndex,
                    referenceLines: widget.referenceLines,
                  ),
                ),
              ),
            ),
          ),
          Positioned(
            right: 0,
            top: 0,
            bottom: 0,
            width: _axisWidth,
            child: _PriceAxis(minPrice: minPrice, maxPrice: maxPrice),
          ),
        ],
      ),
    );
  }
}

class _PriceAxis extends StatelessWidget {
  final double minPrice;
  final double maxPrice;

  const _PriceAxis({required this.minPrice, required this.maxPrice});

  static const _marginTop = 12.0;
  static const _marginBottom = 12.0;
  static const _levels = 4;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (context, constraints) {
      final chartHeight = constraints.maxHeight - _marginTop - _marginBottom;

      return Stack(
        children: [
          for (var i = 0; i <= _levels; i++)
            Positioned(
              top: _marginTop + (i / _levels) * chartHeight - 7,
              left: 6,
              child: Text(
                formatRupees(maxPrice - (i / _levels) * (maxPrice - minPrice)),
                style: const TextStyle(fontSize: 9, color: mutedColor),
              ),
            ),
        ],
      );
    });
  }
}

class _CandlestickPainter extends CustomPainter {
  final List<Map<String, dynamic>> candles;
  final double candleWidth;
  final double minPrice;
  final double maxPrice;
  final int? selectedIndex;
  final List<ChartReferenceLine> referenceLines;

  _CandlestickPainter({
    required this.candles,
    required this.candleWidth,
    required this.minPrice,
    required this.maxPrice,
    this.selectedIndex,
    this.referenceLines = const [],
  });

  static const _marginTop = 12.0;
  static const _marginBottom = 12.0;

  @override
  void paint(Canvas canvas, Size size) {
    if (candles.isEmpty) return;

    final range = (maxPrice - minPrice) == 0 ? 1.0 : (maxPrice - minPrice);
    final chartHeight = size.height - _marginTop - _marginBottom;

    double yFor(double price) => _marginTop + chartHeight - ((price - minPrice) / range) * chartHeight;

    for (var i = 0; i <= 4; i++) {
      final y = _marginTop + (i / 4) * chartHeight;
      canvas.drawLine(
        Offset(0, y),
        Offset(size.width, y),
        Paint()
          ..color = Colors.white10
          ..strokeWidth = 0.5,
      );
    }

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

    if (selectedIndex != null && selectedIndex! >= 0 && selectedIndex! < candles.length) {
      final x = selectedIndex! * candleWidth + candleWidth / 2;
      canvas.drawLine(
        Offset(x, 0),
        Offset(x, size.height),
        Paint()
          ..color = accentColor.withValues(alpha: 0.7)
          ..strokeWidth = 1,
      );
    }

    for (final line in referenceLines) {
      final y = yFor(line.price);
      _drawDashedLine(canvas, Offset(0, y), Offset(size.width, y), line.color);

      final textPainter = TextPainter(
        text: TextSpan(
          text: ' ${line.label} ${formatRupees(line.price)}',
          style: TextStyle(fontSize: 9, color: line.color, fontWeight: FontWeight.w600, backgroundColor: bgColor),
        ),
        textDirection: TextDirection.ltr,
      )..layout();
      textPainter.paint(canvas, Offset(2, y - textPainter.height - 1));
    }
  }

  void _drawDashedLine(Canvas canvas, Offset start, Offset end, Color color) {
    const dashWidth = 4.0;
    const dashGap = 3.0;
    final paint = Paint()
      ..color = color
      ..strokeWidth = 1;

    final totalDistance = (end - start).distance;
    final direction = (end - start) / totalDistance;
    var distance = 0.0;

    while (distance < totalDistance) {
      final segmentEnd = (distance + dashWidth).clamp(0, totalDistance);
      canvas.drawLine(start + direction * distance, start + direction * segmentEnd.toDouble(), paint);
      distance += dashWidth + dashGap;
    }
  }

  @override
  bool shouldRepaint(covariant _CandlestickPainter oldDelegate) =>
      oldDelegate.candles != candles ||
      oldDelegate.selectedIndex != selectedIndex ||
      oldDelegate.minPrice != minPrice ||
      oldDelegate.maxPrice != maxPrice ||
      oldDelegate.referenceLines != referenceLines;
}
