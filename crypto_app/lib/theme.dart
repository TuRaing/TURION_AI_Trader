import 'package:flutter/material.dart';

// Same dark/neon palette as the main TURION AI Trader app
// (mobile_app/lib/theme.dart) - copied, not imported, since this is a
// genuinely separate Flutter project (own pubspec/APK), per the
// user's explicit "same style, separate app" ask. Keep in sync by
// hand if the main app's palette ever changes - a small, static file,
// low risk of drifting unnoticed.

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

List<BoxShadow> glowShadow(Color color, {double blur = 24, double alpha = 0.45}) {
  return [BoxShadow(color: color.withValues(alpha: alpha), blurRadius: blur, spreadRadius: 0)];
}

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
    tabBarTheme: const TabBarThemeData(
      labelColor: accent2Color,
      unselectedLabelColor: faintColor,
      indicatorColor: accent2Color,
    ),
  );
}
