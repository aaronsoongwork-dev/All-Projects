import 'package:flutter/material.dart';

ThemeData lightMode = ThemeData(
  colorScheme: ColorScheme.light(
    surface: const Color(0xFFF9FAFB), // Light background
    primary: const Color(0xFF10b981), // Green primary
    secondary: const Color(0xFF059669), // Dark green
    tertiary: Colors.white, // Card background
    inversePrimary: const Color(0xFF111827), // Dark text
    onSurface: const Color(0xFF6B7280), // Secondary text
    onPrimary: Colors.white, // Text on primary color
    outline: const Color(0xFFE5E7EB), // Borders
  ),
  textTheme: const TextTheme(
    headlineLarge: TextStyle(
      fontSize: 24,
      fontWeight: FontWeight.bold,
      fontFamily: 'Helvetica',
      color: Color(0xFF111827),
    ),
    headlineSmall: TextStyle(
      fontSize: 18,
      fontWeight: FontWeight.w800,
      fontFamily: 'Helvetica',
      color: Color(0xFF111827),
    ),
    titleMedium: TextStyle(
      fontSize: 15,
      fontWeight: FontWeight.w700,
      fontFamily: 'Helvetica',
      color: Color(0xFF111827),
    ),
  ),
);