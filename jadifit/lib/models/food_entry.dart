/// Nutritional information for a food item.
class NutritionInfo {
  final int calories;
  final int protein;
  final int carbs;
  final int fats;
  final int fiber;
  final int sugar;

  const NutritionInfo({
    required this.calories,
    required this.protein,
    required this.carbs,
    required this.fats,
    this.fiber = 0,
    this.sugar = 0,
  });

  NutritionInfo copyWith({
    int? calories,
    int? protein,
    int? carbs,
    int? fats,
    int? fiber,
    int? sugar,
  }) {
    return NutritionInfo(
      calories: calories ?? this.calories,
      protein: protein ?? this.protein,
      carbs: carbs ?? this.carbs,
      fats: fats ?? this.fats,
      fiber: fiber ?? this.fiber,
      sugar: sugar ?? this.sugar,
    );
  }
}

/// A tracked food entry with metadata and nutrition.
class FoodEntry {
  final String id;
  final String name;
  final int weightGrams;
  final String origin;
  final bool isOrganic;
  final NutritionInfo nutrition;
  final DateTime timestamp;
  final String? imagePath;
  final bool savedToLibrary;

  FoodEntry({
    required this.id,
    required this.name,
    required this.weightGrams,
    this.origin = '',
    this.isOrganic = false,
    required this.nutrition,
    required this.timestamp,
    this.imagePath,
    this.savedToLibrary = false,
  });

  FoodEntry copyWith({
    String? id,
    String? name,
    int? weightGrams,
    String? origin,
    bool? isOrganic,
    NutritionInfo? nutrition,
    DateTime? timestamp,
    String? imagePath,
    bool? savedToLibrary,
  }) {
    return FoodEntry(
      id: id ?? this.id,
      name: name ?? this.name,
      weightGrams: weightGrams ?? this.weightGrams,
      origin: origin ?? this.origin,
      isOrganic: isOrganic ?? this.isOrganic,
      nutrition: nutrition ?? this.nutrition,
      timestamp: timestamp ?? this.timestamp,
      imagePath: imagePath ?? this.imagePath,
      savedToLibrary: savedToLibrary ?? this.savedToLibrary,
    );
  }

  /// Emoji icon based on food name heuristic.
  String get emoji {
    final lower = name.toLowerCase();
    if (lower.contains('chicken')) return '🍗';
    if (lower.contains('rice')) return '🍚';
    if (lower.contains('salad')) return '🥗';
    if (lower.contains('egg')) return '🥚';
    if (lower.contains('fish') || lower.contains('salmon')) return '🐟';
    if (lower.contains('steak') || lower.contains('beef')) return '🥩';
    if (lower.contains('pasta') || lower.contains('noodle')) return '🍝';
    if (lower.contains('bread') || lower.contains('toast')) return '🍞';
    if (lower.contains('fruit') || lower.contains('apple')) return '🍎';
    if (lower.contains('banana')) return '🍌';
    if (lower.contains('milk') || lower.contains('yogurt')) return '🥛';
    if (lower.contains('pizza')) return '🍕';
    if (lower.contains('burger')) return '🍔';
    if (lower.contains('soup')) return '🍲';
    if (lower.contains('cake') || lower.contains('dessert')) return '🍰';
    if (lower.contains('smoothie') || lower.contains('juice')) return '🥤';
    return '🍽️';
  }

  /// Formatted date string.
  String get formattedDate {
    const months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    return '${days[timestamp.weekday - 1]} ${timestamp.day} ${months[timestamp.month - 1]}';
  }

  /// Time-of-day string.
  String get formattedTime {
    final h = timestamp.hour;
    final m = timestamp.minute.toString().padLeft(2, '0');
    final period = h >= 12 ? 'PM' : 'AM';
    final hour = h == 0 ? 12 : (h > 12 ? h - 12 : h);
    return '$hour:$m $period';
  }
}

/// Sample data for development.
List<FoodEntry> getSampleFoodEntries() {
  final now = DateTime.now();
  return [
    FoodEntry(
      id: 'food-1',
      name: 'Grilled Chicken',
      weightGrams: 150,
      origin: 'Local farm',
      isOrganic: true,
      nutrition: const NutritionInfo(
        calories: 320,
        protein: 48,
        carbs: 2,
        fats: 12,
        fiber: 0,
        sugar: 0,
      ),
      timestamp: now.subtract(const Duration(hours: 2)),
      savedToLibrary: true,
    ),
    FoodEntry(
      id: 'food-2',
      name: 'Brown Rice',
      weightGrams: 200,
      origin: '',
      isOrganic: false,
      nutrition: const NutritionInfo(
        calories: 216,
        protein: 5,
        carbs: 45,
        fats: 2,
        fiber: 3,
        sugar: 1,
      ),
      timestamp: now.subtract(const Duration(hours: 4)),
    ),
    FoodEntry(
      id: 'food-3',
      name: 'Caesar Salad',
      weightGrams: 180,
      origin: '',
      isOrganic: false,
      nutrition: const NutritionInfo(
        calories: 180,
        protein: 8,
        carbs: 12,
        fats: 10,
        fiber: 4,
        sugar: 3,
      ),
      timestamp: now.subtract(const Duration(days: 1, hours: 1)),
    ),
    FoodEntry(
      id: 'food-4',
      name: 'Salmon Fillet',
      weightGrams: 170,
      origin: 'Norway',
      isOrganic: true,
      nutrition: const NutritionInfo(
        calories: 367,
        protein: 34,
        carbs: 0,
        fats: 22,
        fiber: 0,
        sugar: 0,
      ),
      timestamp: now.subtract(const Duration(days: 1, hours: 6)),
    ),
    FoodEntry(
      id: 'food-5',
      name: 'Banana Smoothie',
      weightGrams: 300,
      origin: '',
      isOrganic: false,
      nutrition: const NutritionInfo(
        calories: 220,
        protein: 6,
        carbs: 42,
        fats: 3,
        fiber: 4,
        sugar: 28,
      ),
      timestamp: now.subtract(const Duration(days: 2, hours: 3)),
    ),
  ];
}
