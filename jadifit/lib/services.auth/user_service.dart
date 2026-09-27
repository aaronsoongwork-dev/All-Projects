import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';

class UserService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  final FirebaseAuth _auth = FirebaseAuth.instance;

  // Get current user ID
  String? get currentUserId => _auth.currentUser?.uid;

  // Create user profile on sign-up (MINIMAL DATA ONLY)
  Future<void> createUserProfile({
    required String email,
    String? displayName,
  }) async {
    final uid = currentUserId;
    if (uid == null) {
      throw Exception('User not authenticated');
    }

    try {
      await _firestore.collection('users').doc(uid).set({
        'email': email,
        'displayName': displayName ?? 'JadiFit User',
        'createdAt': FieldValue.serverTimestamp(),
        'isDarkMode': false,
        // ✅ ADD THIS FLAG
        'isNewUser': true,  // Mark as new user
      });
    } catch (e) {
      print('Error creating profile: $e');
      rethrow;
    }
  }

  // Save user preferences to Firestore
  Future<void> saveUserPreferences({
    required bool isDarkMode,
  }) async {
    final uid = currentUserId;
    if (uid == null) {
      throw Exception('User not authenticated');
    }

    try {
      await _firestore.collection('users').doc(uid).set({
        'isDarkMode': isDarkMode,
        'lastUpdated': FieldValue.serverTimestamp(),
      }, SetOptions(merge: true));
    } catch (e) {
      print('Error saving preferences: $e');
      rethrow;
    }
  }

  // Load user preferences from Firestore
  Future<Map<String, dynamic>?> getUserPreferences() async {
    final uid = currentUserId;
    if (uid == null) return null;

    try {
      final doc = await _firestore.collection('users').doc(uid).get();
      return doc.data();
    } catch (e) {
      print('Error loading preferences: $e');
      return null;
    }
  }

  // Update user profile (used by Edit Profile page)
  Future<void> updateUserProfile(Map<String, dynamic> data) async {
    final uid = currentUserId;
    if (uid == null) throw Exception('User not authenticated');

    try {
      await _firestore.collection('users').doc(uid).set(
        data,
        SetOptions(merge: true), // ← IMPORTANT: merge so we don't overwrite email/name
      );
    } catch (e) {
      print('Error updating profile: $e');
      rethrow;
    }
  }

  // Save food entry to Firestore
  Future<void> saveFoodEntry(Map<String, dynamic> entry) async {
    final uid = currentUserId;
    if (uid == null) throw Exception('User not authenticated');

    await _firestore
        .collection('users')
        .doc(uid)
        .collection('foodEntries')
        .add(entry);
  }

  // Save workout plan to Firestore
  Future<void> saveWorkoutPlan(Map<String, dynamic> workout) async {
    final uid = currentUserId;
    if (uid == null) throw Exception('User not authenticated');

    await _firestore
        .collection('users')
        .doc(uid)
        .collection('workouts')
        .add(workout);
  }
}