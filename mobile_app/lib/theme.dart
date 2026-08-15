import 'package:flutter/material.dart';

// Redesigned 15-Aug-2026 - "cute clean and easy to use" + fluorescent,
// feels-like-a-new-app direction, approved against a mockup (background
// option E - colorful 4-blob mesh) before touching any screen code.
// Old Catppuccin-Mocha-derived palette replaced with a near-black ground
// + electric violet/cyan brand pair + neon success/danger/warning -
// same semantic ROLES (bg/surface/accent/success/danger/muted) so every
// existing screen keeps compiling untouched, only the actual color
// values and a few new glow/gradient helpers are new.

const bgColor = Color(0xFF08060F);
const surfaceColor = Color(0xFF12101D);
const surfaceRaisedColor = Color(0xFF1A1729);
const appBarColor = Color(0xFF030208);
const accentColor = Color(0xFFA855FF);
const accent2Color = Color(0xFF00E5FF);
const successColor = Color(0xFF4CFF8F);
const dangerColor = Color(0xFFFF2F7E);
const warningColor = Color(0xFFFFD60A);
const mutedColor = Color(0xFF9D97BF);
const faintColor = Color(0xFF665F8A);

Color pnlColor(num pnl) => pnl >= 0 ? successColor : dangerColor;

/// Soft neon glow behind a colored number/chip - the signature touch of
/// this redesign (see the mockup's "hero value" text-shadow). Kept as a
/// BoxShadow list so it drops straight into any Container's decoration.
List<BoxShadow> glowShadow(Color color, {double blur = 24, double alpha = 0.45}) {
  return [BoxShadow(color: color.withValues(alpha: alpha), blurRadius: blur, spreadRadius: 0)];
}

/// The 4-blob colorful mesh background (mockup option "E", the one
/// picked) - one RadialGradient per corner, meant to sit behind a
/// Scaffold's body via MeshBackground (widgets/mesh_background.dart).
const meshBlobs = [
  (Alignment(-0.7, -0.7), accentColor, 0.32),
  (Alignment(0.7, -0.7), accent2Color, 0.26),
  (Alignment(0.6, 0.8), dangerColor, 0.20),
  (Alignment(-0.7, 0.8), successColor, 0.14),
];

ThemeData buildAppTheme() {
  return ThemeData(
    brightness: Brightness.dark,
    scaffoldBackgroundColor: bgColor,
    cardColor: surfaceColor,
    colorScheme: ColorScheme.fromSeed(
      seedColor: accentColor,
      brightness: Brightness.dark,
    ),
    appBarTheme: const AppBarTheme(backgroundColor: appBarColor, elevation: 0),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      backgroundColor: appBarColor,
      selectedItemColor: accent2Color,
      unselectedItemColor: faintColor,
      type: BottomNavigationBarType.fixed,
    ),
  );
}
