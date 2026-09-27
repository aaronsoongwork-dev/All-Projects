/// Model for an individual exercise within a workout.
class Exercise {
  final String id;
  final String name;
  final int sets;
  final int reps;
  bool completed;

  Exercise({
    required this.id,
    required this.name,
    required this.sets,
    required this.reps,
    this.completed = false,
  });

  Exercise copyWith({
    String? id,
    String? name,
    int? sets,
    int? reps,
    bool? completed,
  }) {
    return Exercise(
      id: id ?? this.id,
      name: name ?? this.name,
      sets: sets ?? this.sets,
      reps: reps ?? this.reps,
      completed: completed ?? this.completed,
    );
  }
}

/// Model for a workout plan containing exercises.
class WorkoutPlan {
  final String id;
  final String name;
  final List<Exercise> exercises;
  bool completed;

  WorkoutPlan({
    required this.id,
    required this.name,
    required this.exercises,
    this.completed = false,
  });

  int get doneCount => exercises.where((e) => e.completed).length;
  int get totalCount => exercises.length;
  double get progress => totalCount > 0 ? doneCount / totalCount : 0;

  WorkoutPlan copyWith({
    String? id,
    String? name,
    List<Exercise>? exercises,
    bool? completed,
  }) {
    return WorkoutPlan(
      id: id ?? this.id,
      name: name ?? this.name,
      exercises: exercises ?? this.exercises,
      completed: completed ?? this.completed,
    );
  }
}

/// Helper to format a DateTime as 'yyyy-MM-dd'.
String formatDate(DateTime d) =>
    '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

/// Add days to a DateTime.
DateTime addDays(DateTime d, int n) => d.add(Duration(days: n));

/// Check if two dates are the same day.
bool isSameDay(DateTime a, DateTime b) =>
    a.year == b.year && a.month == b.month && a.day == b.day;

/// Short day names.
const List<String> daysShort = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

/// Full month names.
const List<String> monthNames = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

/// Sample workout data.
Map<String, List<WorkoutPlan>> getSampleWorkoutPlans() {
  return {
    '2026-02-16': [
      WorkoutPlan(id: 'w1', name: 'Upper Body', completed: true, exercises: [
        Exercise(id: 'e1', name: 'Bench Press', sets: 4, reps: 10, completed: true),
        Exercise(id: 'e2', name: 'Shoulder Press', sets: 3, reps: 12, completed: true),
        Exercise(id: 'e3', name: 'Tricep Dips', sets: 3, reps: 15, completed: true),
      ]),
    ],
    '2026-02-17': [
      WorkoutPlan(id: 'w2', name: 'Core & Abs', completed: true, exercises: [
        Exercise(id: 'e4', name: 'Plank', sets: 3, reps: 60, completed: true),
        Exercise(id: 'e5', name: 'Crunches', sets: 4, reps: 20, completed: true),
        Exercise(id: 'e6', name: 'Leg Raises', sets: 3, reps: 15, completed: true),
      ]),
    ],
    '2026-02-19': [
      WorkoutPlan(id: 'w3', name: 'Lower Body', completed: true, exercises: [
        Exercise(id: 'e7', name: 'Squats', sets: 4, reps: 12, completed: true),
        Exercise(id: 'e8', name: 'Lunges', sets: 3, reps: 10, completed: true),
        Exercise(id: 'e9', name: 'Leg Press', sets: 3, reps: 15, completed: true),
      ]),
    ],
    '2026-02-20': [
      WorkoutPlan(id: 'w4', name: 'HIIT Cardio', completed: true, exercises: [
        Exercise(id: 'e10', name: 'Burpees', sets: 3, reps: 15, completed: true),
        Exercise(id: 'e11', name: 'Jump Squats', sets: 3, reps: 20, completed: true),
        Exercise(id: 'e12', name: 'High Knees', sets: 4, reps: 30, completed: true),
      ]),
    ],
    '2026-02-21': [
      WorkoutPlan(id: 'w5', name: 'Full Body', completed: true, exercises: [
        Exercise(id: 'e13', name: 'Deadlift', sets: 3, reps: 8, completed: true),
        Exercise(id: 'e14', name: 'Pull-ups', sets: 3, reps: 10, completed: true),
        Exercise(id: 'e15', name: 'Push-ups', sets: 4, reps: 15, completed: true),
      ]),
    ],
    '2026-02-23': [
      WorkoutPlan(id: 'w6', name: 'Push Day', completed: true, exercises: [
        Exercise(id: 'e16', name: 'Bench Press', sets: 4, reps: 10, completed: true),
        Exercise(id: 'e17', name: 'Incline Press', sets: 3, reps: 12, completed: true),
        Exercise(id: 'e18', name: 'Lateral Raises', sets: 3, reps: 15, completed: true),
      ]),
    ],
    '2026-02-24': [
      WorkoutPlan(id: 'w7', name: 'Pull Day', completed: false, exercises: [
        Exercise(id: 'e19', name: 'Pull-ups', sets: 4, reps: 8, completed: true),
        Exercise(id: 'e20', name: 'Barbell Rows', sets: 3, reps: 10, completed: false),
        Exercise(id: 'e21', name: 'Face Pulls', sets: 3, reps: 15, completed: false),
      ]),
    ],
    '2026-02-25': [
      WorkoutPlan(id: 'w8', name: 'Legs & Glutes', completed: false, exercises: [
        Exercise(id: 'e22', name: 'Squats', sets: 4, reps: 10, completed: false),
        Exercise(id: 'e23', name: 'Romanian DL', sets: 3, reps: 12, completed: false),
        Exercise(id: 'e24', name: 'Hip Thrusts', sets: 3, reps: 15, completed: false),
      ]),
    ],
    '2026-02-26': [
      WorkoutPlan(id: 'w9', name: 'Core & Cardio', completed: false, exercises: [
        Exercise(id: 'e25', name: 'Plank', sets: 3, reps: 60, completed: false),
        Exercise(id: 'e26', name: 'Mountain Climbers', sets: 3, reps: 30, completed: false),
      ]),
    ],
  };
}
