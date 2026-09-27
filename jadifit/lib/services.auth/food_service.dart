import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:jadi_fit_app/models/food_entry.dart';

/// Provider that manages food entries (log + saved library).
class FoodProvider with ChangeNotifier {
  final List<FoodEntry> _entries = [];
  final _uuid = const Uuid();
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  final FirebaseAuth _auth = FirebaseAuth.instance;

  String? get _currentUserId => _auth.currentUser?.uid;

  FoodProvider() {
    // Load from Firestore on init
    loadFromFirestore();
  }

  /// All logged food entries, newest first.
  List<FoodEntry> get entries =>
      List.unmodifiable(_entries..sort((a, b) => b.timestamp.compareTo(a.timestamp)));

  /// Entries saved to the user's library.
  List<FoodEntry> get savedEntries =>
      entries.where((e) => e.savedToLibrary).toList();

  /// Entries from today.
  List<FoodEntry> get todayEntries {
    final now = DateTime.now();
    return entries
        .where((e) =>
    e.timestamp.year == now.year &&
        e.timestamp.month == now.month &&
        e.timestamp.day == now.day)
        .toList();
  }

  /// Total calories consumed today.
  int get todayCalories =>
      todayEntries.fold(0, (sum, e) => sum + e.nutrition.calories);

  /// Add a new food entry to the log and Firestore.
  FoodEntry addEntry({
    required String name,
    required int weightGrams,
    String origin = '',
    bool isOrganic = false,
    required NutritionInfo nutrition,
    String? imagePath,
    bool saveToLibrary = false,
  }) {
    final entry = FoodEntry(
      id: _uuid.v4(),
      name: name,
      weightGrams: weightGrams,
      origin: origin,
      isOrganic: isOrganic,
      nutrition: nutrition,
      timestamp: DateTime.now(),
      imagePath: imagePath,
      savedToLibrary: saveToLibrary,
    );

    _entries.add(entry);
    notifyListeners();

    // ✅ Save to Firestore
    _saveToFirestore(entry);

    return entry;
  }

  /// Remove a food entry.
  void removeEntry(String id) {
    _entries.removeWhere((e) => e.id == id);
    notifyListeners();

    // Remove from Firestore
    _deleteFromFirestore(id);
  }

  /// Toggle the saved-to-library flag.
  void toggleSaved(String id) {
    final idx = _entries.indexWhere((e) => e.id == id);
    if (idx != -1) {
      final old = _entries[idx];
      _entries[idx] = old.copyWith(savedToLibrary: !old.savedToLibrary);
      notifyListeners();

      // Update Firestore
      _saveToFirestore(_entries[idx]);
    }
  }

  /// Update a food entry.
  void updateEntry(FoodEntry updated) {
    final idx = _entries.indexWhere((e) => e.id == updated.id);
    if (idx != -1) {
      _entries[idx] = updated;
      notifyListeners();

      // Update Firestore
      _saveToFirestore(updated);
    }
  }

  /// Group entries by date key for the history view.
  Map<String, List<FoodEntry>> get entriesByDate {
    final map = <String, List<FoodEntry>>{};
    for (final entry in entries) {
      final key = entry.formattedDate;
      map.putIfAbsent(key, () => []).add(entry);
    }
    return map;
  }

  // ✅ Save entry to Firestore
  Future<void> _saveToFirestore(FoodEntry entry) async {
    final uid = _currentUserId;
    if (uid == null) {
      print('⚠️ User not authenticated, skipping Firestore save');
      return;
    }

    try {
      await _firestore
          .collection('users')
          .doc(uid)
          .collection('foodEntries')
          .doc(entry.id)
          .set({
        'id': entry.id,
        'name': entry.name,
        'weightGrams': entry.weightGrams,
        'origin': entry.origin,
        'isOrganic': entry.isOrganic,
        'calories': entry.nutrition.calories,
        'protein': entry.nutrition.protein,
        'carbs': entry.nutrition.carbs,
        'fats': entry.nutrition.fats,
        'fiber': entry.nutrition.fiber,
        'sugar': entry.nutrition.sugar,
        'timestamp': Timestamp.fromDate(entry.timestamp),
        'imagePath': entry.imagePath,
        'savedToLibrary': entry.savedToLibrary,
      });

      print('✅ Food entry saved to Firestore: ${entry.name}');
    } catch (e) {
      print('❌ Error saving to Firestore: $e');
    }
  }

  // ✅ Load entries from Firestore on app start
  Future<void> loadFromFirestore() async {
    final uid = _currentUserId;
    if (uid == null) return;

    try {
      final snapshot = await _firestore
          .collection('users')
          .doc(uid)
          .collection('foodEntries')
          .orderBy('timestamp', descending: true)
          .get();

      _entries.clear();

      for (var doc in snapshot.docs) {
        final data = doc.data();
        _entries.add(FoodEntry(
          id: data['id'] ?? doc.id,
          name: data['name'] ?? '',
          weightGrams: data['weightGrams'] ?? 0,
          origin: data['origin'] ?? '',
          isOrganic: data['isOrganic'] ?? false,
          nutrition: NutritionInfo(
            calories: data['calories'] ?? 0,
            protein: data['protein'] ?? 0,
            carbs: data['carbs'] ?? 0,
            fats: data['fats'] ?? 0,
            fiber: data['fiber'] ?? 0,
            sugar: data['sugar'] ?? 0,
          ),
          timestamp: (data['timestamp'] as Timestamp?)?.toDate() ?? DateTime.now(),
          imagePath: data['imagePath'],
          savedToLibrary: data['savedToLibrary'] ?? false,
        ));
      }

      notifyListeners();
      print('✅ Loaded ${_entries.length} food entries from Firestore');
    } catch (e) {
      print('❌ Error loading from Firestore: $e');
    }
  }

  // ✅ Delete from Firestore
  Future<void> _deleteFromFirestore(String id) async {
    final uid = _currentUserId;
    if (uid == null) return;

    try {
      await _firestore
          .collection('users')
          .doc(uid)
          .collection('foodEntries')
          .doc(id)
          .delete();

      print('✅ Food entry deleted from Firestore: $id');
    } catch (e) {
      print('❌ Error deleting from Firestore: $e');
    }
  }
}