import 'package:flutter/material.dart';
import 'package:jadi_fit_app/themes/dark_mode.dart';
import 'package:jadi_fit_app/themes/light_mode.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:jadi_fit_app/services.auth/user_service.dart';

class ThemeProvider with ChangeNotifier {
  ThemeData _themeData = lightMode;
  static const String _themeKey = 'isDarkMode';
  final UserService _userService = UserService();

  ThemeProvider() {
    _loadTheme();
  }

  ThemeData get themeData => _themeData;
  bool get isDarkMode => _themeData == darkMode;

  // Load theme: First try Firestore, fallback to local
  Future<void> _loadTheme() async {
    try {
      // Try loading from Firestore (synced across devices)
      final prefs = await _userService.getUserPreferences();
      if (prefs != null && prefs.containsKey('isDarkMode')) {
        final isDark = prefs['isDarkMode'] as bool;
        _themeData = isDark ? darkMode : lightMode;
        notifyListeners();
        return;
      }
    } catch (e) {
      print('Could not load theme from Firestore: $e');
    }

    // Fallback to local SharedPreferences
    final sharedPrefs = await SharedPreferences.getInstance();
    final isDark = sharedPrefs.getBool(_themeKey) ?? false;
    _themeData = isDark ? darkMode : lightMode;
    notifyListeners();
  }

  // Save theme to both local and Firestore
  Future<void> _saveTheme(bool isDark) async {
    // Save locally (instant)
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_themeKey, isDark);

    // Save to Firestore (synced across devices)
    try {
      await _userService.saveUserPreferences(isDarkMode: isDark);
    } catch (e) {
      print('Could not sync theme to Firestore: $e');
    }
  }

  set themeData(ThemeData themeData) {
    _themeData = themeData;
    _saveTheme(_themeData == darkMode);
    notifyListeners();
  }

  void toggleTheme() {
    if (_themeData == lightMode) {
      themeData = darkMode;
    } else {
      themeData = lightMode;
    }
  }
}