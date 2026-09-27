import 'package:flutter/material.dart';
import 'package:jadi_fit_app/models/workout.dart';

/// A card displaying a single workout with expandable exercise list.
class WorkoutCard extends StatefulWidget {
  final WorkoutPlan workout;
  final Function(String exerciseId) onToggleExercise;
  final VoidCallback onMarkComplete;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  const WorkoutCard({
    super.key,
    required this.workout,
    required this.onToggleExercise,
    required this.onMarkComplete,
    required this.onEdit,
    required this.onDelete,
  });

  @override
  State<WorkoutCard> createState() => _WorkoutCardState();
}

class _WorkoutCardState extends State<WorkoutCard> {
  bool _expanded = true;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;
    final workout = widget.workout;
    final doneCount = workout.doneCount;
    final total = workout.totalCount;
    final progress = workout.progress;

    return Container(
      decoration: BoxDecoration(
        color: theme.tertiary,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: workout.completed
              ? theme.primary.withOpacity(0.3)
              : Colors.transparent,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          // Header
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                Row(
                  children: [
                    // Dumbbell icon
                    Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        gradient: workout.completed
                            ? LinearGradient(
                                colors: [theme.primary, theme.secondary],
                                begin: Alignment.topLeft,
                                end: Alignment.bottomRight,
                              )
                            : null,
                        color: workout.completed ? null : theme.outline.withOpacity(0.3),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(
                        Icons.fitness_center,
                        size: 20,
                        color: workout.completed ? theme.onPrimary : theme.onSurface,
                      ),
                    ),
                    const SizedBox(width: 12),
                    // Name / subtitle
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            workout.name,
                            style: TextStyle(
                              fontWeight: FontWeight.w600,
                              fontSize: 15,
                              color: theme.inversePrimary,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            '$total exercises • $doneCount/$total done',
                            style: TextStyle(
                              fontSize: 12,
                              color: theme.onSurface,
                            ),
                          ),
                        ],
                      ),
                    ),
                    // Completed badge
                    if (workout.completed)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: theme.primary.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.check_circle, size: 14, color: theme.primary),
                            const SizedBox(width: 4),
                            Text(
                              'Done',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w500,
                                color: theme.primary,
                              ),
                            ),
                          ],
                        ),
                      ),
                    const SizedBox(width: 8),
                    // Expand toggle
                    InkWell(
                      onTap: () => setState(() => _expanded = !_expanded),
                      borderRadius: BorderRadius.circular(8),
                      child: Padding(
                        padding: const EdgeInsets.all(6),
                        child: Icon(
                          _expanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                          size: 20,
                          color: theme.onSurface,
                        ),
                      ),
                    ),
                  ],
                ),
                // Progress bar
                if (total > 0) ...[
                  const SizedBox(height: 12),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(6),
                    child: LinearProgressIndicator(
                      value: progress,
                      minHeight: 6,
                      backgroundColor: theme.outline.withOpacity(0.3),
                      valueColor: AlwaysStoppedAnimation<Color>(theme.primary),
                    ),
                  ),
                ],
              ],
            ),
          ),
          // Exercises list
          if (_expanded) ...[
            Divider(height: 1, color: theme.outline.withOpacity(0.2)),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Column(
                children: workout.exercises.map((ex) {
                  return InkWell(
                    onTap: () => widget.onToggleExercise(ex.id),
                    borderRadius: BorderRadius.circular(12),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
                      decoration: BoxDecoration(
                        color: ex.completed
                            ? theme.primary.withOpacity(0.05)
                            : Colors.transparent,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            ex.completed
                                ? Icons.check_circle
                                : Icons.circle_outlined,
                            size: 20,
                            color: ex.completed
                                ? theme.primary
                                : theme.onSurface.withOpacity(0.4),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              ex.name,
                              style: TextStyle(
                                fontSize: 14,
                                color: ex.completed
                                    ? theme.onSurface
                                    : theme.inversePrimary,
                                decoration: ex.completed
                                    ? TextDecoration.lineThrough
                                    : null,
                              ),
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 10,
                              vertical: 4,
                            ),
                            decoration: BoxDecoration(
                              color: theme.outline.withOpacity(0.2),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              '${ex.sets}×${ex.reps}',
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w500,
                                color: theme.onSurface,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
            // Action row
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
              child: Row(
                children: [
                  // Mark Complete button
                  Expanded(
                    child: ElevatedButton(
                      onPressed: widget.onMarkComplete,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: workout.completed
                            ? theme.primary.withOpacity(0.1)
                            : theme.primary,
                        foregroundColor: workout.completed
                            ? theme.primary
                            : theme.onPrimary,
                        elevation: workout.completed ? 0 : 2,
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      child: Text(
                        workout.completed ? '✓ Completed' : 'Mark Complete',
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  // Edit button
                  Material(
                    color: theme.outline.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                    child: InkWell(
                      onTap: widget.onEdit,
                      borderRadius: BorderRadius.circular(12),
                      child: Padding(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 12,
                        ),
                        child: Text(
                          'Edit',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w500,
                            color: theme.onSurface,
                          ),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  // Delete button
                  Material(
                    color: Colors.red.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(12),
                    child: InkWell(
                      onTap: widget.onDelete,
                      borderRadius: BorderRadius.circular(12),
                      child: const Padding(
                        padding: EdgeInsets.all(12),
                        child: Icon(Icons.delete_outline, size: 18, color: Colors.red),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}
