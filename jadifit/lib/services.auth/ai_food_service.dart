import 'dart:io';
import 'dart:convert';
import 'package:flutter/services.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:google_generative_ai/google_generative_ai.dart';
import 'package:http/http.dart' as http;
import 'package:jadi_fit_app/models/food_entry.dart';

class AIFoodService {
  static String get _geminiApiKey {
    final key = dotenv.env['GEMINI_API_KEY'];
    if (key == null || key.isEmpty) {
      throw Exception('GEMINI_API_KEY not found in .env file');
    }
    return key;
  }

  GenerativeModel? _geminiModel;

  Future<void> initialize() async {
    try {
      // ✅ List all available models
      print('🔍 Fetching available Gemini models...');

      final url = Uri.parse(
          'https://generativelanguage.googleapis.com/v1beta/models?key=$_geminiApiKey'
      );

      final response = await http.get(url);

      String? modelToUse;

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        print('📋 Available models:');

        for (var model in data['models']) {
          final name = model['name'] as String;
          final displayName = model['displayName'] as String;
          final supportedMethods = model['supportedGenerationMethods'] as List;

          print('  - $name');
          print('    Display: $displayName');
          print('    Methods: $supportedMethods');
          print('');

          // ✅ Find a model that supports generateContent
          if (supportedMethods.contains('generateContent') &&
              (name.contains('gemini') || name.contains('vision'))) {
            modelToUse ??= name.replaceAll('models/', ''); // Get first suitable model
          }
        }
      } else {
        print('❌ API Error: ${response.statusCode}');
        print('Response: ${response.body}');
      }

      // ✅ Initialize the model
      if (modelToUse != null) {
        print('🎯 Using model: $modelToUse');
        _geminiModel = GenerativeModel(
          model: modelToUse,
          apiKey: _geminiApiKey,
        );
        print('✅ AI Food Service initialized successfully');
      } else {
        throw Exception('No suitable Gemini model found');
      }

    } catch (e) {
      print('❌ Error: $e');
      rethrow;
    }
  }

  Future<FoodAnalysisResult> analyzeFoodImage(String imagePath) async {
    if (_geminiModel == null) {
      throw Exception('Gemini model not initialized');
    }

    try {
      final imageBytes = await File(imagePath).readAsBytes();

      final prompt = '''
You are a professional nutritionist AI. Analyze this food image carefully and provide accurate nutritional information.

IMPORTANT INSTRUCTIONS:
1. Identify the exact food item(s) in the image
2. Estimate realistic portion size based on visual cues
3. Provide accurate nutritional values based on standard food databases
4. If you cannot identify the food clearly, set name to "unidentified"
5. All numeric values must be realistic and positive numbers
6. Return ONLY valid JSON, no markdown formatting, no extra text

JSON format (return exactly this structure):
{
  "name": "specific food name (e.g., 'Grilled Chicken Breast', 'Margherita Pizza')",
  "weight_grams": estimated weight in grams (realistic number between 50-1000),
  "calories": total calories (realistic number),
  "protein": protein in grams (realistic number),
  "carbs": carbohydrates in grams (realistic number),
  "fats": fats in grams (realistic number),
  "fiber": fiber in grams (realistic number, can be 0),
  "sugar": sugar in grams (realistic number, can be 0),
  "origin": cuisine type or origin (e.g., "Italian", "American", "Asian"),
  "is_organic": true or false based on visual indicators,
  "description": one detailed sentence describing the food and preparation method
}

VALIDATION RULES:
- calories should roughly equal: (protein × 4) + (carbs × 4) + (fats × 9)
- All numbers must be positive
- Weight should be realistic for the portion shown
- Description must be specific and detailed
''';

      final content = [
        Content.multi([
          TextPart(prompt),
          DataPart('image/jpeg', imageBytes),
        ])
      ];

      print('🔍 Analyzing food image with Gemini...');
      final response = await _geminiModel!.generateContent(content);
      final jsonText = response.text?.trim() ?? '';

      print('📊 Gemini raw response: $jsonText');

      if (jsonText.isEmpty) {
        throw Exception('Gemini returned empty response');
      }

      return _parseGeminiResponse(jsonText);
    } catch (e) {
      print('❌ Error analyzing food: $e');
      rethrow; // ✅ Don't return fallback data, throw error instead
    }
  }

  FoodAnalysisResult _parseGeminiResponse(String jsonText) {
    try {
      // Clean up response
      String cleaned = jsonText
          .replaceAll('```json', '')
          .replaceAll('```', '')
          .replaceAll('`', '')
          .trim();

      // Remove any text before the first {
      int startIndex = cleaned.indexOf('{');
      if (startIndex > 0) {
        cleaned = cleaned.substring(startIndex);
      }

      // Remove any text after the last }
      int endIndex = cleaned.lastIndexOf('}');
      if (endIndex > 0 && endIndex < cleaned.length - 1) {
        cleaned = cleaned.substring(0, endIndex + 1);
      }

      print('🧹 Cleaned JSON: $cleaned');

      final data = jsonDecode(cleaned) as Map<String, dynamic>;

      // ✅ Validate required fields exist
      if (data['name'] == null ||
          data['name'] == 'unidentified' ||
          (data['name'] as String).isEmpty) {
        throw Exception('Could not identify food in image');
      }

      // ✅ Validate numeric values are realistic
      final calories = _parseNumeric(data['calories'], 'calories');
      final protein = _parseNumeric(data['protein'], 'protein');
      final carbs = _parseNumeric(data['carbs'], 'carbs');
      final fats = _parseNumeric(data['fats'], 'fats');
      final fiber = _parseNumeric(data['fiber'], 'fiber');
      final sugar = _parseNumeric(data['sugar'], 'sugar');
      final weightGrams = _parseNumeric(data['weight_grams'], 'weight_grams');

      // ✅ Sanity check on calories
      if (calories < 1 || calories > 5000) {
        throw Exception('Invalid calorie value: $calories');
      }

      if (weightGrams < 1 || weightGrams > 5000) {
        throw Exception('Invalid weight value: $weightGrams');
      }

      return FoodAnalysisResult(
        name: data['name'] as String,
        weightGrams: weightGrams,
        nutrition: NutritionInfo(
          calories: calories,
          protein: protein,
          carbs: carbs,
          fats: fats,
          fiber: fiber,
          sugar: sugar,
        ),
        origin: (data['origin'] as String?) ?? 'Unknown',
        isOrganic: data['is_organic'] == true,
        description: (data['description'] as String?) ?? '',
      );
    } catch (e) {
      print('⚠️ Failed to parse Gemini response: $e');
      print('Raw response was: $jsonText');
      throw Exception('Failed to parse AI response: $e');
    }
  }

  // ✅ Helper to safely parse numeric values
  int _parseNumeric(dynamic value, String fieldName) {
    if (value == null) {
      throw Exception('Missing required field: $fieldName');
    }

    if (value is int) return value;
    if (value is double) return value.round();
    if (value is String) {
      final parsed = int.tryParse(value);
      if (parsed != null) return parsed;
    }

    throw Exception('Invalid numeric value for $fieldName: $value');
  }

  void dispose() {
    // Nothing to dispose
  }
}

class FoodAnalysisResult {
  final String name;
  final int weightGrams;
  final NutritionInfo nutrition;
  final String origin;
  final bool isOrganic;
  final String description;

  FoodAnalysisResult({
    required this.name,
    required this.weightGrams,
    required this.nutrition,
    required this.origin,
    required this.isOrganic,
    required this.description,
  });
}