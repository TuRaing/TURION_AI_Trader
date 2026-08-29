import 'package:flutter/material.dart';

import '../theme.dart';

/// Same 4-blob mesh background as the main app
/// (mobile_app/lib/widgets/mesh_background.dart) - copied verbatim.
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
