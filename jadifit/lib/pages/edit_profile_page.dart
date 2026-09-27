import 'package:flutter/material.dart';
import 'package:jadi_fit_app/services.auth/user_provider.dart';
import 'package:jadi_fit_app/pages/home_page.dart';
import 'package:provider/provider.dart';

class EditProfilePage extends StatefulWidget {
  final bool isFirstTime;

  const EditProfilePage({super.key, this.isFirstTime = false});

  @override
  State<EditProfilePage> createState() => _EditProfilePageState();
}

class _EditProfilePageState extends State<EditProfilePage> {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();

  int _age = 25;
  String _gender = 'Male';
  double _height = 170;
  double _weight = 70;
  double _targetWeight = 65;
  int _weeklyWorkoutGoal = 5;
  int _dailyCalorieBurnGoal = 500;

  final _genders = ['Male', 'Female', 'Other'];

  @override
  void initState() {
    super.initState();
    // Load current user data
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final userProvider = context.read<UserProvider>();
      setState(() {
        _nameController.text = userProvider.displayName;
        _emailController.text = userProvider.email;

        // ✅ Use provider values if they exist, otherwise keep defaults
        _age = userProvider.age > 0 ? userProvider.age : 25;

        // ✅ FIX: Validate gender is in the list before using it
        if (userProvider.gender.isNotEmpty && _genders.contains(userProvider.gender)) {
          _gender = userProvider.gender;
        } else {
          _gender = 'Male';
        }

        _height = userProvider.height > 0 ? userProvider.height : 170;
        _weight = userProvider.weight > 0 ? userProvider.weight : 70;
        _targetWeight = userProvider.targetWeight > 0 ? userProvider.targetWeight : 65;
        _weeklyWorkoutGoal = userProvider.weeklyWorkoutGoal > 0 ? userProvider.weeklyWorkoutGoal : 5;
        _dailyCalorieBurnGoal = userProvider.dailyCalorieBurnGoal > 0 ? userProvider.dailyCalorieBurnGoal : 500;
      });
    });
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    super.dispose();
  }

  Future<void> _saveProfile() async {
    final userProvider = context.read<UserProvider>();

    // Show loading
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const Center(child: CircularProgressIndicator()),
    );

    try {
      await userProvider.updateProfile(
        displayName: _nameController.text.trim(),
        age: _age,
        gender: _gender,
        height: _height,
        weight: _weight,
        targetWeight: _targetWeight,
        weeklyWorkoutGoal: _weeklyWorkoutGoal,
        dailyCalorieBurnGoal: _dailyCalorieBurnGoal,
      );

      if (mounted) Navigator.pop(context); // Close loading

      if (mounted) {
        if (widget.isFirstTime) {
          // ✅ Clear entire navigation stack - prevents going back to splash
          Navigator.pushAndRemoveUntil(
            context,
            MaterialPageRoute(builder: (context) => const HomePage()),
                (route) => false, // Remove all previous routes
          );
        } else {
          // Just editing - go back
          Navigator.pop(context);
        }
      }
    } catch (e) {
      if (mounted) Navigator.pop(context); // Close loading

      if (mounted) {
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            backgroundColor: Theme.of(context).colorScheme.surface,
            title: Text(
              'Error',
              style: TextStyle(
                  color: Theme.of(context).colorScheme.inversePrimary),
            ),
            content: Text(
              'Failed to save profile. Please try again.',
              style:
              TextStyle(color: Theme.of(context).colorScheme.onSurface),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: Text(
                  'OK',
                  style: TextStyle(
                      color: Theme.of(context).colorScheme.primary),
                ),
              ),
            ],
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;

    return Scaffold(
      backgroundColor: theme.surface,
      appBar: widget.isFirstTime
          ? null
          : AppBar(
        backgroundColor: theme.surface,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: theme.inversePrimary),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          'Edit Profile',
          style: TextStyle(
            color: theme.inversePrimary,
            fontWeight: FontWeight.w800,
            fontSize: 18,
          ),
        ),
        centerTitle: true,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header (only show on first time)
              if (widget.isFirstTime) ...[
                Text(
                  'Complete Your Profile',
                  style: TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                    color: theme.inversePrimary,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Help us personalize your fitness journey',
                  style: TextStyle(
                    fontSize: 16,
                    color: theme.onSurface,
                  ),
                ),
                const SizedBox(height: 32),
              ],

              // Profile Picture
              Center(
                child: Stack(
                  children: [
                    Container(
                      width: 100,
                      height: 100,
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [theme.primary, theme.secondary],
                        ),
                        shape: BoxShape.circle,
                      ),
                      child: Center(
                        child: Text(
                          _nameController.text.isNotEmpty
                              ? _nameController.text[0].toUpperCase()
                              : 'U',
                          style: TextStyle(
                            color: theme.onPrimary,
                            fontSize: 40,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                    Positioned(
                      bottom: 0,
                      right: 0,
                      child: Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: theme.primary,
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          Icons.camera_alt,
                          color: theme.onPrimary,
                          size: 20,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 32),

              // Name
              _buildTextField(
                label: 'Full Name',
                controller: _nameController,
                hint: 'Enter your name',
                theme: theme,
              ),
              const SizedBox(height: 20),

              // Email (disabled)
              _buildTextField(
                label: 'Email',
                controller: _emailController,
                hint: 'your@email.com',
                theme: theme,
                enabled: false,
              ),
              const SizedBox(height: 20),

              // Age
              _buildLabel('Age', theme),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: theme.tertiary,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '$_age years old',
                      style: TextStyle(
                        fontSize: 16,
                        color: theme.inversePrimary,
                      ),
                    ),
                    Row(
                      children: [
                        IconButton(
                          onPressed: () {
                            if (_age > 10) setState(() => _age--);
                          },
                          icon: Icon(Icons.remove_circle_outline,
                              color: theme.primary),
                        ),
                        IconButton(
                          onPressed: () {
                            if (_age < 100) setState(() => _age++);
                          },
                          icon: Icon(Icons.add_circle_outline,
                              color: theme.primary),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Gender
              _buildLabel('Gender', theme),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                decoration: BoxDecoration(
                  color: theme.tertiary,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: DropdownButton<String>(
                  value: _gender,
                  isExpanded: true,
                  underline: const SizedBox(),
                  items: _genders.map((String value) {
                    return DropdownMenuItem<String>(
                      value: value,
                      child: Text(value),
                    );
                  }).toList(),
                  onChanged: (String? newValue) {
                    if (newValue != null) {
                      setState(() => _gender = newValue);
                    }
                  },
                ),
              ),
              const SizedBox(height: 20),

              // Height
              _buildSlider(
                label: 'Height',
                value: _height,
                unit: 'cm',
                min: 100,
                max: 250,
                theme: theme,
                onChanged: (value) => setState(() => _height = value),
              ),
              const SizedBox(height: 20),

              // Current Weight
              _buildSlider(
                label: 'Current Weight',
                value: _weight,
                unit: 'kg',
                min: 30,
                max: 200,
                theme: theme,
                onChanged: (value) => setState(() => _weight = value),
              ),
              const SizedBox(height: 20),

              // Target Weight
              _buildSlider(
                label: 'Target Weight',
                value: _targetWeight,
                unit: 'kg',
                min: 30,
                max: 200,
                theme: theme,
                onChanged: (value) => setState(() => _targetWeight = value),
              ),
              const SizedBox(height: 20),

              // Weekly Workout Goal
              _buildLabel('Weekly Workout Goal', theme),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: theme.tertiary,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '$_weeklyWorkoutGoal workouts per week',
                      style: TextStyle(
                        fontSize: 16,
                        color: theme.inversePrimary,
                      ),
                    ),
                    Row(
                      children: [
                        IconButton(
                          onPressed: () {
                            if (_weeklyWorkoutGoal > 1) {
                              setState(() => _weeklyWorkoutGoal--);
                            }
                          },
                          icon: Icon(Icons.remove_circle_outline,
                              color: theme.primary),
                        ),
                        IconButton(
                          onPressed: () {
                            if (_weeklyWorkoutGoal < 7) {
                              setState(() => _weeklyWorkoutGoal++);
                            }
                          },
                          icon: Icon(Icons.add_circle_outline,
                              color: theme.primary),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Daily Calorie Burn Goal
              _buildSlider(
                label: 'Daily Calorie Burn Goal',
                value: _dailyCalorieBurnGoal.toDouble(),
                unit: 'kcal',
                min: 100,
                max: 1000,
                divisions: 18,
                theme: theme,
                onChanged: (value) =>
                    setState(() => _dailyCalorieBurnGoal = value.toInt()),
              ),
              const SizedBox(height: 32),

              // Save Button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _saveProfile,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: theme.primary,
                    foregroundColor: theme.onPrimary,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                    elevation: 2,
                  ),
                  child: Text(
                    widget.isFirstTime ? 'Complete Setup' : 'Save Changes',
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTextField({
    required String label,
    required TextEditingController controller,
    required String hint,
    required ColorScheme theme,
    bool enabled = true,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildLabel(label, theme),
        const SizedBox(height: 8),
        TextField(
          controller: controller,
          enabled: enabled,
          decoration: InputDecoration(
            hintText: hint,
            filled: true,
            fillColor: theme.tertiary,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: theme.outline),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: theme.outline),
            ),
            disabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: theme.outline.withOpacity(0.3)),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: theme.primary, width: 2),
            ),
            contentPadding: const EdgeInsets.all(16),
          ),
        ),
      ],
    );
  }

  Widget _buildSlider({
    required String label,
    required double value,
    required String unit,
    required double min,
    required double max,
    int? divisions,
    required ColorScheme theme,
    required Function(double) onChanged,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            _buildLabel(label, theme),
            Text(
              '${value.toStringAsFixed(0)} $unit',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: theme.primary,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        SliderTheme(
          data: SliderTheme.of(context).copyWith(
            activeTrackColor: theme.primary,
            inactiveTrackColor: theme.outline.withOpacity(0.3),
            thumbColor: theme.primary,
            overlayColor: theme.primary.withOpacity(0.2),
            trackHeight: 6,
          ),
          child: Slider(
            value: value,
            min: min,
            max: max,
            divisions: divisions ?? (max - min).toInt(),
            onChanged: onChanged,
          ),
        ),
      ],
    );
  }

  Widget _buildLabel(String text, ColorScheme theme) {
    return Text(
      text,
      style: TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w600,
        color: theme.inversePrimary,
      ),
    );
  }
}