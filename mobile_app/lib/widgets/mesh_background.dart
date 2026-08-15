import 'package:flutter/material.dart';

import '../theme.dart';

/// The chosen redesign background (mockup option "E" - a colorful
/// 4-blob mesh). Wraps a screen's body: solid bgColor base, then one
/// soft RadialGradient blob per corner (violet/cyan/pink/green, low
/// alpha) stacked behind the real content, exactly the treatment
/// approved in the design mockup before any screen code changed.
class MeshBackground extends StatelessWidget {
  final Widget child;

  const MeshBackground({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        Container(color: bgColor),
        for (final (alignment, color, alpha) in meshBlobs)
          Positioned.fill(
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: RadialGradient(
                  center: alignment,
                  radius: 0.9,
                  colors: [color.withValues(alpha: alpha), color.withValues(alpha: 0)],
                ),
              ),
            ),
          ),
        child,
      ],
    );
  }
}
