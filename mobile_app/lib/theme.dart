import 'package:flutter/material.dart';

const bgColor = Color(0xFF1E1E2E);
const surfaceColor = Color(0xFF313244);
const appBarColor = Color(0xFF181825);
const accentColor = Color(0xFF89B4FA);
const successColor = Color(0xFFA6E3A1);
const dangerColor = Color(0xFFF38BA8);
const mutedColor = Color(0xFF9399B2);

Color pnlColor(num pnl) => pnl >= 0 ? successColor : dangerColor;

ThemeData buildAppTheme() {
  return ThemeData(
    brightness: Brightness.dark,
    scaffoldBackgroundColor: bgColor,
    cardColor: surfaceColor,
    colorScheme: ColorScheme.fromSeed(
      seedColor: accentColor,
      brightness: Brightness.dark,
    ),
    appBarTheme: const AppBarTheme(backgroundColor: appBarColor),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      backgroundColor: appBarColor,
      selectedItemColor: accentColor,
      unselectedItemColor: mutedColor,
      type: BottomNavigationBarType.fixed,
    ),
  );
}
