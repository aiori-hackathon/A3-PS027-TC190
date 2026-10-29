import 'package:flutter/material.dart';

/// GitHub Primer & Linear design tokens for IPv6 Auditor.
class PrimerTheme {
  static const Color bgPage = Color(0xFF0D1117);
  static const Color surfaceCard = Color(0xFF161B22);
  static const Color surfaceSubdued = Color(0xFF0E1319);
  static const Color surfaceHover = Color(0xFF21262D);
  static const Color borderDefault = Color(0xFF30363D);
  static const Color borderMuted = Color(0xFF21262D);

  static const Color textPrimary = Color(0xFFE6EDF3);
  static const Color textMuted = Color(0xFF8B949E);
  static const Color textDim = Color(0xFF6E7681);

  // Semantic Protocol Colors
  static const Color stateV6 = Color(0xFF3FB950);
  static const Color stateV4 = Color(0xFFF85149);
  static const Color stateBroken = Color(0xFFD29922);
  static const Color stateInfo = Color(0xFF58A6FF);

  static const double radiusDefault = 6.0;

  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: bgPage,
      cardColor: surfaceCard,
      colorScheme: const ColorScheme.dark(
        surface: surfaceCard,
        primary: stateInfo,
        secondary: stateV6,
        error: stateV4,
      ),
      textTheme: const TextTheme(
        headlineMedium: TextStyle(
          color: textPrimary,
          fontSize: 28,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.5,
        ),
        titleMedium: TextStyle(
          color: textPrimary,
          fontSize: 16,
          fontWeight: FontWeight.w600,
        ),
        bodyMedium: TextStyle(
          color: textPrimary,
          fontSize: 13,
          fontWeight: FontWeight.w400,
        ),
        bodySmall: TextStyle(
          color: textMuted,
          fontSize: 12,
          fontWeight: FontWeight.w400,
        ),
      ),
    );
  }
}
