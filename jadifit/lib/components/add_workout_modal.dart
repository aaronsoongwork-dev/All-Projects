import 'package:flutter/material.dart';
import 'package:jadi_fit_app/models/workout.dart';

/// Bottom‑sheet modal for adding or editing a workout plan.
class AddWorkoutModal extends StatefulWidget {
  final WorkoutPlan? existing; // null → create mode
  final void Function(String name, List<Exercise> exercises) onSave;

  const AddWorkoutModal({
    super.key,
    this.existing,
    required this.onSave,
  });

  /// Shows the modal as a bottom sheet and returns when dismissed.
  static Future<void> show(
    BuildContext context, {
    WorkoutPlan? existing,
    required void Function(String name, List<Exercise> exercises) onSave,
  }) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => AddWorkoutModal(existing: existing, onSave: onSave),
    );
  }

  @override
  State<AddWorkoutModal> createState() => _AddWorkoutModalState();
}

class _AddWorkoutModalState extends State<AddWorkoutModal> {
  late TextEditingController _nameCtrl;
  late List<_ExerciseRow> _rows;

  @override
  void initState() {
    super.initState();
    if (widget.existing != null) {
      _nameCtrl = TextEditingController(text: widget.existing!.name);
      _rows = widget.existing!.exercises
          .map((e) => _ExerciseRow(
                name: TextEditingController(text: e.name),
                sets: TextEditingController(text: '${e.sets}'),
                reps: TextEditingController(text: '${e.reps}'),
              ))
          .toList();
    } else {
      _nameCtrl = TextEditingController();
      _rows = [_ExerciseRow.empty()];
    }
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    for (final r in _rows) {
      r.dispose();
    }
    super.dispose();
  }

  void _addRow() => setState(() => _rows.add(_ExerciseRow.empty()));

  void _removeRow(int i) {
    if (_rows.length <= 1) return;
    setState(() {
      _rows[i].dispose();
      _rows.removeAt(i);
    });
  }

  void _save() {
    final name = _nameCtrl.text.trim();
    if (name.isEmpty) return;

    final exercises = <Exercise>[];
    for (final r in _rows) {
      final eName = r.name.text.trim();
      if (eName.isEmpty) continue;
      exercises.add(Exercise(
        id: DateTime.now().microsecondsSinceEpoch.toString(),
        name: eName,
        sets: int.tryParse(r.sets.text) ?? 3,
        reps: int.tryParse(r.reps.text) ?? 10,
      ));
    }
    if (exercises.isEmpty) return;
    widget.onSave(name, exercises);
    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;
    final bottom = MediaQuery.of(context).viewInsets.bottom;
    final isEdit = widget.existing != null;

    return Container(
      margin: EdgeInsets.only(bottom: bottom),
      decoration: BoxDecoration(
        color: theme.tertiary,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Drag handle
            Center(
              child: Container(
                width: 48,
                height: 5,
                decoration: BoxDecoration(
                  color: theme.outline.withOpacity(0.4),
                  borderRadius: BorderRadius.circular(100),
                ),
              ),
            ),
            const SizedBox(height: 16),
            // Title
            Text(
              isEdit ? 'Edit Workout' : 'Add Workout',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: theme.inversePrimary,
              ),
            ),
            const SizedBox(height: 20),
            // Workout name field
            _buildTextField(
              controller: _nameCtrl,
              hint: 'Workout name',
              theme: theme,
            ),
            const SizedBox(height: 20),
            // "Exercises" heading
            Row(
              children: [
                Text(
                  'Exercises',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: theme.inversePrimary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            // Exercise rows
            ...List.generate(_rows.length, (i) {
              final r = _rows[i];
              return Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Row(
                  children: [
                    Expanded(
                      flex: 4,
                      child: _buildTextField(
                        controller: r.name,
                        hint: 'Exercise name',
                        theme: theme,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      flex: 1,
                      child: _buildTextField(
                        controller: r.sets,
                        hint: 'Sets',
                        theme: theme,
                        keyboardType: TextInputType.number,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      flex: 1,
                      child: _buildTextField(
                        controller: r.reps,
                        hint: 'Reps',
                        theme: theme,
                        keyboardType: TextInputType.number,
                      ),
                    ),
                    if (_rows.length > 1) ...[
                      const SizedBox(width: 4),
                      InkWell(
                        onTap: () => _removeRow(i),
                        borderRadius: BorderRadius.circular(8),
                        child: Padding(
                          padding: const EdgeInsets.all(6),
                          child: Icon(Icons.remove_circle_outline,
                              size: 20, color: Colors.red.withOpacity(0.6)),
                        ),
                      ),
                    ],
                  ],
                ),
              );
            }),
            // Add exercise button
            Align(
              alignment: Alignment.centerLeft,
              child: TextButton.icon(
                onPressed: _addRow,
                icon: Icon(Icons.add_circle_outline, size: 18, color: theme.primary),
                label: Text(
                  'Add exercise',
                  style: TextStyle(
                    color: theme.primary,
                    fontWeight: FontWeight.w500,
                    fontSize: 13,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),
            // Save button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _save,
                style: ElevatedButton.styleFrom(
                  backgroundColor: theme.primary,
                  foregroundColor: theme.onPrimary,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                  elevation: 0,
                ),
                child: Text(
                  isEdit ? 'Save Changes' : 'Add Workout',
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTextField({
    required TextEditingController controller,
    required String hint,
    required ColorScheme theme,
    TextInputType keyboardType = TextInputType.text,
  }) {
    return TextField(
      controller: controller,
      keyboardType: keyboardType,
      style: TextStyle(color: theme.inversePrimary, fontSize: 14),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: TextStyle(color: theme.onSurface.withOpacity(0.5), fontSize: 14),
        filled: true,
        fillColor: theme.surface,
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: theme.outline.withOpacity(0.3)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: theme.outline.withOpacity(0.3)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: theme.primary, width: 1.5),
        ),
      ),
    );
  }
}

/// Internal helper to hold the controllers for one exercise row.
class _ExerciseRow {
  final TextEditingController name;
  final TextEditingController sets;
  final TextEditingController reps;

  _ExerciseRow({
    required this.name,
    required this.sets,
    required this.reps,
  });

  factory _ExerciseRow.empty() => _ExerciseRow(
        name: TextEditingController(),
        sets: TextEditingController(text: '3'),
        reps: TextEditingController(text: '10'),
      );

  void dispose() {
    name.dispose();
    sets.dispose();
    reps.dispose();
  }
}
