import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:jadi_fit_app/services.auth/user_service.dart';

class UserProvider with ChangeNotifier {
  final UserService _userService = UserService();
  final FirebaseAuth _auth = FirebaseAuth.instance;

  bool _isNewUser = false;
  bool get isNewUser => _isNewUser;

  // User data - NO DEFAULT VALUES
  String _displayName = '';
  String _email = '';
  int _age = 0;
  String _gender = '';
  double _height = 0.0;
  double _weight = 0.0;
  bool _isDarkMode = false;
  bool _isLoading = true;

  // Goals - NO DEFAULT VALUES
  double _targetWeight = 0.0;
  int _weeklyWorkoutGoal = 0;
  int _dailyCalorieBurnGoal = 0;

  // Current progress
  int _currentWeeklyWorkouts = 0;
  int _currentDailyCaloriesBurned = 0;

  // Getters
  String get displayName => _displayName;
  String get email => _email;
  int get age => _age;
  String get gender => _gender;
  double get height => _height;
  double get weight => _weight;
  bool get isDarkMode => _isDarkMode;
  bool get isLoading => _isLoading;

  // Goal getters
  double get targetWeight => _targetWeight;
  int get weeklyWorkoutGoal => _weeklyWorkoutGoal;
  int get dailyCalorieBurnGoal => _dailyCalorieBurnGoal;
  int get currentWeeklyWorkouts => _currentWeeklyWorkouts;
  int get currentDailyCaloriesBurned => _currentDailyCaloriesBurned;

  // Check if profile is complete
  bool get isProfileComplete {
    return _age > 0 &&
        _height > 0 &&
        _weight > 0 &&
        _targetWeight > 0 &&
        _gender.isNotEmpty;
  }

  // Get first name only
  String get firstName {
    if (_displayName.isEmpty) return 'User';
    return _displayName.split(' ').first;
  }

  // Progress calculations (0.0 to 1.0)
  double get weightProgress {
    if (_weight <= 0 || _targetWeight <= 0) return 0.0;
    if (_weight <= _targetWeight) return 1.0;

    double startWeight = _targetWeight + 10;
    double totalToLose = startWeight - _targetWeight;
    double lostSoFar = startWeight - _weight;

    double progress = (lostSoFar / totalToLose).clamp(0.0, 1.0);
    return progress;
  }

  double get workoutProgress {
    if (_weeklyWorkoutGoal <= 0) return 0.0;
    return (_currentWeeklyWorkouts / _weeklyWorkoutGoal).clamp(0.0, 1.0);
  }

  double get calorieBurnProgress {
    if (_dailyCalorieBurnGoal <= 0) return 0.0;
    return (_currentDailyCaloriesBurned / _dailyCalorieBurnGoal).clamp(0.0, 1.0);
  }

  // BMI calculation
  double get bmi {
    if (_height <= 0 || _weight <= 0) return 0;
    double heightInMeters = _height / 100;
    return _weight / (heightInMeters * heightInMeters);
  }

  // Load user data from Firestore
  Future<void> loadUserData() async {
    _isLoading = true;
    notifyListeners();

    try {
      final currentUser = _auth.currentUser;
      if (currentUser == null) {
        _isLoading = false;
        notifyListeners();
        return;
      }

      _email = currentUser.email ?? '';

      final userData = await _userService.getUserPreferences();

      if (userData != null) {
        // ✅ FIX: Load isNewUser from Firestore
        _isNewUser = userData['isNewUser'] ?? false;

        // NO FALLBACK VALUES - use what's in Firestore or keep at 0/empty
        _displayName = userData['displayName'] ?? '';
        _age = userData['age'] ?? 0;
        _gender = userData['gender'] ?? '';
        _height = (userData['height'] ?? 0.0).toDouble();
        _weight = (userData['weight'] ?? 0.0).toDouble();
        _isDarkMode = userData['isDarkMode'] ?? false;
        _targetWeight = (userData['targetWeight'] ?? 0.0).toDouble();
        _weeklyWorkoutGoal = userData['weeklyWorkoutGoal'] ?? 0;
        _dailyCalorieBurnGoal = userData['dailyCalorieBurnGoal'] ?? 0;
        _currentWeeklyWorkouts = userData['currentWeeklyWorkouts'] ?? 0;
        _currentDailyCaloriesBurned = userData['currentDailyCaloriesBurned'] ?? 0;
      }
    } catch (e) {
      print('Error loading user data: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> updateProfile({
    String? displayName,
    int? age,
    String? gender,
    double? height,
    double? weight,
    double? targetWeight,
    int? weeklyWorkoutGoal,
    int? dailyCalorieBurnGoal,
  }) async {
    try {
      final updates = <String, dynamic>{};

      if (displayName != null) {
        _displayName = displayName;
        updates['displayName'] = displayName;
      }
      if (age != null) {
        _age = age;
        updates['age'] = age;
      }
      if (gender != null) {
        _gender = gender;
        updates['gender'] = gender;
      }
      if (height != null) {
        _height = height;
        updates['height'] = height;
      }
      if (weight != null) {
        _weight = weight;
        updates['weight'] = weight;
      }
      if (targetWeight != null) {
        _targetWeight = targetWeight;
        updates['targetWeight'] = targetWeight;
      }
      if (weeklyWorkoutGoal != null) {
        _weeklyWorkoutGoal = weeklyWorkoutGoal;
        updates['weeklyWorkoutGoal'] = weeklyWorkoutGoal;
      }
      if (dailyCalorieBurnGoal != null) {
        _dailyCalorieBurnGoal = dailyCalorieBurnGoal;
        updates['dailyCalorieBurnGoal'] = dailyCalorieBurnGoal;
      }

      // ✅ Mark as no longer a new user after completing profile
      _isNewUser = false;
      updates['isNewUser'] = false;

      // ✅ Notify listeners IMMEDIATELY after updating local state
      notifyListeners();

      // Then save to Firestore (async)
      if (updates.isNotEmpty) {
        await _userService.updateUserProfile(updates);
      }
    } catch (e) {
      print('Error updating profile: $e');
      rethrow;
    }
  }

  void incrementWorkout() {
    _currentWeeklyWorkouts++;
    notifyListeners();
  }

  void addCaloriesBurned(int calories) {
    _currentDailyCaloriesBurned += calories;
    notifyListeners();
  }

  void resetWeeklyWorkouts() {
    _currentWeeklyWorkouts = 0;
    notifyListeners();
  }

  void resetDailyCalories() {
    _currentDailyCaloriesBurned = 0;
    notifyListeners();
  }

  // Clear data on logout
  void clearData() {
    _displayName = '';
    _email = '';
    _age = 0;
    _gender = '';
    _height = 0.0;
    _weight = 0.0;
    _isDarkMode = false;
    _isLoading = true;
    _targetWeight = 0.0;
    _weeklyWorkoutGoal = 0;
    _dailyCalorieBurnGoal = 0;
    _currentWeeklyWorkouts = 0;
    _currentDailyCaloriesBurned = 0;
    _isNewUser = false;
    notifyListeners();
  }
}