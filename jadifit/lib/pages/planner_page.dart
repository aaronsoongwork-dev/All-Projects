import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:jadi_fit_app/models/workout.dart';
import 'package:jadi_fit_app/components/workout_card.dart';
import 'package:jadi_fit_app/components/add_workout_modal.dart';

class PlannerPage extends StatefulWidget {
  const PlannerPage({super.key});

  @override
  State<PlannerPage> createState() => _PlannerPageState();
}

class _PlannerPageState extends State<PlannerPage> {
  // Calendar & view state
  late DateTime _today;
  late DateTime _selectedDate;
  late DateTime _currentWeekStart;
  bool _monthlyView = false;

  // Workout data keyed by 'yyyy-MM-dd'
  late Map<String, List<WorkoutPlan>> _workouts;

  @override
  void initState() {
    super.initState();
    _today = DateTime.now();
    _selectedDate = _today;
    _currentWeekStart = _getWeekStart(_today);
    _workouts = getSampleWorkoutPlans();
  }

  // ── helpers ──────────────────────────────────────────────

  DateTime _getWeekStart(DateTime d) {
    final diff = d.weekday % 7; // Sunday = 0
    return DateTime(d.year, d.month, d.day - diff);
  }

  String _key(DateTime d) => formatDate(d);

  List<WorkoutPlan> _workoutsFor(DateTime d) => _workouts[_key(d)] ?? [];

  int get _streakDays {
    int streak = 0;
    DateTime cursor = _today;
    while (true) {
      final list = _workoutsFor(cursor);
      if (list.isNotEmpty && list.every((w) => w.completed)) {
        streak++;
        cursor = cursor.subtract(const Duration(days: 1));
      } else {
        break;
      }
    }
    return streak;
  }

  // ── mutation helpers ─────────────────────────────────────

  void _toggleExercise(WorkoutPlan workout, String exerciseId) {
    setState(() {
      final ex = workout.exercises.firstWhere((e) => e.id == exerciseId);
      ex.completed = !ex.completed;
    });
  }

  void _markComplete(WorkoutPlan workout) {
    setState(() {
      workout.completed = !workout.completed;
      for (final e in workout.exercises) {
        e.completed = workout.completed;
      }
    });
  }

  void _deleteWorkout(WorkoutPlan workout) {
    final key = _key(_selectedDate);
    setState(() {
      _workouts[key]?.removeWhere((w) => w.id == workout.id);
      if (_workouts[key]?.isEmpty ?? false) _workouts.remove(key);
    });
  }

  void _openAddModal({WorkoutPlan? existing}) {
    AddWorkoutModal.show(
      context,
      existing: existing,
      onSave: (name, exercises) {
        final key = _key(_selectedDate);
        setState(() {
          if (existing != null) {
            // Edit existing
            final list = _workouts[key];
            if (list != null) {
              final i = list.indexWhere((w) => w.id == existing.id);
              if (i != -1) {
                list[i] = WorkoutPlan(
                  id: existing.id,
                  name: name,
                  exercises: exercises,
                );
              }
            }
          } else {
            // Add new
            final newPlan = WorkoutPlan(
              id: DateTime.now().millisecondsSinceEpoch.toString(),
              name: name,
              exercises: exercises,
            );
            _workouts.putIfAbsent(key, () => []);
            _workouts[key]!.add(newPlan);
          }
        });
      },
    );
  }

  // ── week navigation ──────────────────────────────────────

  void _prevWeek() =>
      setState(() => _currentWeekStart = addDays(_currentWeekStart, -7));

  void _nextWeek() =>
      setState(() => _currentWeekStart = addDays(_currentWeekStart, 7));

  void _prevMonth() => setState(() {
        final cur = DateTime(_currentWeekStart.year, _currentWeekStart.month, 1);
        final prev = DateTime(cur.year, cur.month - 1, 1);
        _currentWeekStart = _getWeekStart(prev);
      });

  void _nextMonth() => setState(() {
        final cur = DateTime(_currentWeekStart.year, _currentWeekStart.month, 1);
        final next = DateTime(cur.year, cur.month + 1, 1);
        _currentWeekStart = _getWeekStart(next);
      });

  // ── Build ────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;
    final workoutsToday = _workoutsFor(_selectedDate);
    final dateLabel =
        '${monthNames[_selectedDate.month - 1]} ${_selectedDate.day}, ${_selectedDate.year}';

    return Scaffold(
      backgroundColor: theme.surface,
      body: SafeArea(
        child: Column(
          children: [
            // ── Top bar ────────────────────────────────
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 24, 20, 0),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Workout Planner',
                          style: GoogleFonts.plusJakartaSans(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            color: theme.inversePrimary,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          dateLabel,
                          style: TextStyle(
                            fontSize: 13,
                            color: theme.onSurface,
                          ),
                        ),
                      ],
                    ),
                  ),
                  // View toggle
                  Container(
                    decoration: BoxDecoration(
                      color: theme.outline.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        _viewToggleBtn('Week', !_monthlyView, theme),
                        _viewToggleBtn('Month', _monthlyView, theme),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // ── Streak banner ──────────────────────────
            if (_streakDays > 0)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFFE84545), Color(0xFFD63031), Color(0xFFB71540)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(18),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFFE84545).withOpacity(0.4),
                        blurRadius: 14,
                        offset: const Offset(0, 6),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Top row: label + streak number
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Flame icon
                          Container(
                            width: 40,
                            height: 40,
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.18),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Icon(
                              Icons.local_fire_department_rounded,
                              color: Colors.white,
                              size: 22,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'CURRENT STREAK',
                                  style: TextStyle(
                                    color: Colors.white.withOpacity(0.7),
                                    fontSize: 10,
                                    fontWeight: FontWeight.w700,
                                    letterSpacing: 1.2,
                                  ),
                                ),
                                const SizedBox(height: 3),
                                const Text(
                                  'Keep the fire burning!',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 15,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          // Big streak number
                          Text(
                            '$_streakDays',
                            style: TextStyle(
                              color: Colors.white.withOpacity(0.95),
                              fontSize: 40,
                              fontWeight: FontWeight.w900,
                              height: 1,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),
                      // Day indicators row
                      Builder(builder: (_) {
                        // Show the last 7 days ending on _today
                        final last7 = List.generate(
                            7, (i) => _today.subtract(Duration(days: 6 - i)));
                        return Row(
                          children: last7.map((d) {
                            final done = _workoutsFor(d).isNotEmpty &&
                                _workoutsFor(d).every((w) => w.completed);
                            final label = daysShort[d.weekday % 7][0];
                            return Expanded(
                              child: Column(
                                children: [
                                  // Dot / bar
                                  Container(
                                    height: 6,
                                    margin: const EdgeInsets.symmetric(
                                        horizontal: 3),
                                    decoration: BoxDecoration(
                                      color: done
                                          ? Colors.white
                                          : Colors.white.withOpacity(0.2),
                                      borderRadius: BorderRadius.circular(3),
                                    ),
                                  ),
                                  const SizedBox(height: 6),
                                  Text(
                                    label,
                                    style: TextStyle(
                                      fontSize: 10,
                                      fontWeight: FontWeight.w600,
                                      color: done
                                          ? Colors.white
                                          : Colors.white.withOpacity(0.4),
                                    ),
                                  ),
                                ],
                              ),
                            );
                          }).toList(),
                        );
                      }),
                      const SizedBox(height: 8),
                      // "X days completed"
                      Align(
                        alignment: Alignment.centerRight,
                        child: Text(
                          '$_streakDays days completed',
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.6),
                            fontSize: 11,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),

            const SizedBox(height: 35),

            // ── Calendar section ───────────────────────
            _monthlyView ? _buildMonthlyCalendar(theme) : _buildWeeklyStrip(theme),

            const SizedBox(height: 12),

            // ── Workouts list ──────────────────────────
            Expanded(
              child: workoutsToday.isEmpty
                  ? _buildEmptyState(theme)
                  : ListView.separated(
                      padding: const EdgeInsets.fromLTRB(20, 0, 20, 100),
                      itemCount: workoutsToday.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 12),
                      itemBuilder: (_, i) {
                        final w = workoutsToday[i];
                        return WorkoutCard(
                          workout: w,
                          onToggleExercise: (eid) => _toggleExercise(w, eid),
                          onMarkComplete: () => _markComplete(w),
                          onEdit: () => _openAddModal(existing: w),
                          onDelete: () => _deleteWorkout(w),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _openAddModal(),
        backgroundColor: theme.primary,
        child: Icon(Icons.add, color: theme.onPrimary),
      ),
    );
  }

  // ── view toggle button ──────────────────────────────────

  Widget _viewToggleBtn(String label, bool active, ColorScheme theme) {
    return GestureDetector(
      onTap: () => setState(() => _monthlyView = label == 'Month'),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: active ? theme.primary : Colors.transparent,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w600,
            color: active ? theme.onPrimary : theme.onSurface,
          ),
        ),
      ),
    );
  }

  // ── weekly strip ────────────────────────────────────────

  Widget _buildWeeklyStrip(ColorScheme theme) {
    final days = List.generate(7, (i) => addDays(_currentWeekStart, i));

    return Column(
      children: [
        // Nav header
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              InkWell(
                onTap: _prevWeek,
                borderRadius: BorderRadius.circular(8),
                child: Padding(
                  padding: const EdgeInsets.all(6),
                  child: Icon(Icons.chevron_left, color: theme.onSurface),
                ),
              ),
              Text(
                '${monthNames[_currentWeekStart.month - 1]} ${_currentWeekStart.year}',
                style: TextStyle(
                  fontWeight: FontWeight.w600,
                  fontSize: 15,
                  color: theme.inversePrimary,
                ),
              ),
              InkWell(
                onTap: _nextWeek,
                borderRadius: BorderRadius.circular(8),
                child: Padding(
                  padding: const EdgeInsets.all(6),
                  child: Icon(Icons.chevron_right, color: theme.onSurface),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 10),
        // Day pills
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child: Row(
            children: days.map((d) {
              final isSelected = isSameDay(d, _selectedDate);
              final isToday = isSameDay(d, _today);
              final hasWorkout = _workoutsFor(d).isNotEmpty;
              final allDone =
                  hasWorkout && _workoutsFor(d).every((w) => w.completed);

              return Expanded(
                child: GestureDetector(
                  onTap: () => setState(() => _selectedDate = d),
                  child: Container(
                    margin: const EdgeInsets.symmetric(horizontal: 3),
                    padding: const EdgeInsets.symmetric(vertical: 10),
                    decoration: BoxDecoration(
                      color: isSelected
                          ? theme.primary
                          : isToday
                              ? theme.primary.withOpacity(0.08)
                              : Colors.transparent,
                      borderRadius: BorderRadius.circular(14),
                      border: isToday && !isSelected
                          ? Border.all(
                              color: theme.primary.withOpacity(0.3), width: 1)
                          : null,
                    ),
                    child: Column(
                      children: [
                        Text(
                          daysShort[d.weekday % 7],
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.w500,
                            color: isSelected
                                ? theme.onPrimary.withOpacity(0.7)
                                : theme.onSurface,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '${d.day}',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: isSelected
                                ? theme.onPrimary
                                : theme.inversePrimary,
                          ),
                        ),
                        const SizedBox(height: 4),
                        // Workout indicator dot
                        Container(
                          width: 6,
                          height: 6,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: allDone
                                ? (isSelected
                                    ? theme.onPrimary
                                    : theme.primary)
                                : hasWorkout
                                    ? (isSelected
                                        ? theme.onPrimary.withOpacity(0.5)
                                        : theme.onSurface.withOpacity(0.3))
                                    : Colors.transparent,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
        ),
      ],
    );
  }

  // ── monthly calendar ────────────────────────────────────

  Widget _buildMonthlyCalendar(ColorScheme theme) {
    final monthDate =
        DateTime(_currentWeekStart.year, _currentWeekStart.month, 1);
    final daysInMonth =
        DateTime(monthDate.year, monthDate.month + 1, 0).day;
    final firstWeekday = monthDate.weekday % 7; // Sunday-based

    final cells = <Widget>[];
    // Leading blanks
    for (int i = 0; i < firstWeekday; i++) {
      cells.add(const SizedBox());
    }
    // Day cells
    for (int day = 1; day <= daysInMonth; day++) {
      final d = DateTime(monthDate.year, monthDate.month, day);
      final isSelected = isSameDay(d, _selectedDate);
      final isToday = isSameDay(d, _today);
      final hasWorkout = _workoutsFor(d).isNotEmpty;
      final allDone = hasWorkout && _workoutsFor(d).every((w) => w.completed);

      cells.add(
        GestureDetector(
          onTap: () => setState(() => _selectedDate = d),
          child: Container(
            decoration: BoxDecoration(
              color: isSelected ? theme.primary : Colors.transparent,
              borderRadius: BorderRadius.circular(10),
              border: isToday && !isSelected
                  ? Border.all(color: theme.primary.withOpacity(0.3))
                  : null,
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  '$day',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight:
                        isSelected || isToday ? FontWeight.bold : FontWeight.normal,
                    color: isSelected ? theme.onPrimary : theme.inversePrimary,
                  ),
                ),
                if (hasWorkout)
                  Container(
                    margin: const EdgeInsets.only(top: 2),
                    width: 5,
                    height: 5,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: isSelected
                          ? theme.onPrimary
                          : allDone
                              ? theme.primary
                              : theme.onSurface.withOpacity(0.35),
                    ),
                  ),
              ],
            ),
          ),
        ),
      );
    }

    return Column(
      children: [
        // Month nav
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              InkWell(
                onTap: _prevMonth,
                borderRadius: BorderRadius.circular(8),
                child: Padding(
                  padding: const EdgeInsets.all(6),
                  child: Icon(Icons.chevron_left, color: theme.onSurface),
                ),
              ),
              Text(
                '${monthNames[monthDate.month - 1]} ${monthDate.year}',
                style: TextStyle(
                  fontWeight: FontWeight.w600,
                  fontSize: 15,
                  color: theme.inversePrimary,
                ),
              ),
              InkWell(
                onTap: _nextMonth,
                borderRadius: BorderRadius.circular(8),
                child: Padding(
                  padding: const EdgeInsets.all(6),
                  child: Icon(Icons.chevron_right, color: theme.onSurface),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 10),
        // Day-of-week headers
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Row(
            children: daysShort.map((d) {
              return Expanded(
                child: Center(
                  child: Text(
                    d,
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w500,
                      color: theme.onSurface,
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
        ),
        const SizedBox(height: 6),
        // Grid
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: GridView.count(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisCount: 7,
            mainAxisSpacing: 4,
            crossAxisSpacing: 4,
            childAspectRatio: 1.1,
            children: cells,
          ),
        ),
      ],
    );
  }

  // ── empty state ─────────────────────────────────────────

  Widget _buildEmptyState(ColorScheme theme) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 72,
            height: 72,
            decoration: BoxDecoration(
              color: theme.outline.withOpacity(0.15),
              borderRadius: BorderRadius.circular(22),
            ),
            child: Icon(
              Icons.fitness_center,
              size: 32,
              color: theme.onSurface.withOpacity(0.4),
            ),
          ),
          const SizedBox(height: 16),
          Text(
            'No workouts planned',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: theme.inversePrimary,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Tap the + button to add a workout',
            style: TextStyle(fontSize: 13, color: theme.onSurface),
          ),
        ],
      ),
    );
  }
}
