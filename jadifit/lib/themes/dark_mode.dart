import 'package:flutter/material.dart';

ThemeData darkMode = ThemeData(
  colorScheme: ColorScheme.dark(
    surface: const Color(0xFF111827), // Dark background
    primary: const Color(0xFF10b981), // Green primary
    secondary: const Color(0xFF059669), // Dark green
    tertiary: const Color(0xFF1F2937), // Card background
    inversePrimary: const Color(0xFFF9FAFB), // Light text
    onSurface: const Color(0xFF9CA3AF), // Secondary text
    onPrimary: Colors.white, // Text on primary color
    outline: const Color(0xFF374151), // Borders
  ),
  textTheme: const TextTheme(
    headlineLarge: TextStyle(
      fontSize: 24,
      fontWeight: FontWeight.bold,
      fontFamily: 'Helvetica',
      color: Color(0xFFF9FAFB),
    ),
    headlineSmall: TextStyle(
      fontSize: 18,
      fontWeight: FontWeight.w800,
      fontFamily: 'Helvetica',
      color: Color(0xFFF9FAFB),
    ),
    titleMedium: TextStyle(
      fontSize: 15,
      fontWeight: FontWeight.w700,
      fontFamily: 'Helvetica',
      color: Color(0xFFF9FAFB),
    ),
  ),
);